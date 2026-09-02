"""
Groq API bağlantısı, çoklu key rotasyonu ve rate limit yönetimi.
"""
import os
import re
import time

from groq import Groq, RateLimitError

_JUNK_PATTERNS = [
    re.compile(r'^Bölüm:.*\n?', re.MULTILINE),
    re.compile(r'^(?:İşte (?:çeviri|Türkçe çeviri|düzeltilmiş|güncellenmiş).*)\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^(?:Çeviri|Düzeltilmiş metin)\s*:.*\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^Not\s*:.*\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^Sadece çeviri.*\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^(?:Bu metinde|Metinde|Aşağıda).*(?:düzelt|değiştir|güncell).*\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^Açıklama\s*:.*\n?', re.MULTILINE | re.IGNORECASE),
]


def clean_output(text: str) -> str:
    """Model yorumlarını, prompt kalıntılarını ve reasoning bloklarını temizle."""
    # <think>...</think> bloklarını temizle (reasoning modeller: gpt-oss, qwen vb.)
    text = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL)
    for pat in _JUNK_PATTERNS:
        text = pat.sub('', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    result = text.strip()
    if not result:
        print("  Uyarı: clean_output sonucu boş — model boş yanıt döndürdü.")
    return result


def get_clients() -> list:
    clients = []
    for i in range(1, 5):
        key = os.environ.get(f"GROQ_API_KEY_{i}")
        if key:
            clients.append({"client": Groq(api_key=key), "locked_until": 0, "id": i})
            print(f"Key {i} yüklendi.")
    single = os.environ.get("GROQ_API_KEY")
    if single and not clients:
        clients.append({"client": Groq(api_key=single), "locked_until": 0, "id": "Default"})
        print("Tekli GROQ_API_KEY yüklendi.")
    if not clients:
        raise ValueError("Hiçbir GROQ_API_KEY bulunamadı.")
    print(f"Toplam {len(clients)} key aktif.")
    return clients


def _parse_retry_seconds(error_message) -> int:
    match = re.search(r'try again in ([\dhms .]+)', str(error_message))
    if not match:
        return 3600
    time_str = match.group(1).strip()
    total = 0
    for h in re.findall(r'([\d.]+)h', time_str): total += float(h) * 3600
    for m in re.findall(r'([\d.]+)m', time_str): total += float(m) * 60
    for s in re.findall(r'([\d.]+)s', time_str): total += float(s)
    return int(total) + 5


MAX_EMPTY_RETRIES = 3  # model boş yanıt döndürürse bu kadar tekrar dene

# Kuyruk mimarisinde her worker run'ı KISA ÖMÜRLÜ (tek bir parça işleyip
# çıkıyor). Eskiden "tüm keyler kilitli" durumunda süre ne olursa olsun
# (gördüğümüz kadarıyla 72 dakikaya kadar) process içinde uyuyup
# bekliyorduk — bu, kısa ömürlü bir worker için Actions dakikalarını
# boşuna yakar. Bunun yerine: en kısa bekleme MAX_ACCEPTABLE_WAIT'i
# aşıyorsa hemen AllKeysLockedError fırlatıp çıkıyoruz; worker bunu
# yakalayıp bu run'da hiçbir şey commit'lemeden, kendini yeniden
# TETİKLEMEDEN sonlanır — bir sonraki deneme translate.yml'nin
# periyodik "güvenlik ağı" tetiklemesiyle gelir.
MAX_ACCEPTABLE_WAIT = 120  # saniye


class AllKeysLockedError(Exception):
    """Tüm key'ler kilitli ve en kısa bekleme süresi kabul edilebilir eşiği aşıyor."""
    def __init__(self, wait_seconds: int):
        self.wait_seconds = wait_seconds
        super().__init__(f"Tüm keyler kilitli, en kısa bekleme: {wait_seconds}s")

# Groq'un bazı organizasyon/tier'larında TPM (dakikalık token) limiti çok
# düşük olabilir (örn. on_demand tier'da 8000 TPM görülmüştür — qwen3.8-27b
# için de topluluk ölçümleri bunu doğruluyor: ~8000 TPM, prompt+çıktı
# toplamı). Groq, max_completion_tokens'ı "bu istek en fazla bu kadar
# üretebilir" diye PROMPT + bu değer toplamını önceden TPM limitine karşı
# kontrol eder — gerçekte o kadar üretilmese bile istek daha başlamadan 413
# ile reddedilir. Bu yüzden makul/güvenli bir üst sınırla başlıyoruz; 413
# alırsak küçültüp tekrar deneriz (bkz. _shrink_and_retry mantığı call()
# içinde). NOT (Eylül 2026): eski varsayılan (6000) + pitfalls.py'nin
# eklediği ~800 token'lık sabit bağlamla birlikte neredeyse HER istekte
# ilk denemede 413 alınıyordu (loglarda "TPM limiti için çok büyük" art
# arda 2-3 kez görülmesi bundan) — başlangıç değeri düşürüldü. Küçülen
# max_out bir kez düşünce call() içinde geri BÜYÜMÜYOR; yani bir istek TPM
# yüzünden küçülüp sonra gerçekten o kadar token'a sığmayan bir metin
# üretmeye çalışırsa (finish_reason=length), 3 "kesik yanıt" denemesi de
# AYNI küçük bütçeyle yapılır ve genelde hepsi aynı şekilde başarısız olup
# parça atlanır. Bu döngü sık tekrarlanıyorsa (özellikle review/NER
# adımlarında), Groq konsolünde qwen3.8-27b için hesabın gerçek TPM
# tavanına bakmak (Settings > Limits) gerekebilir — 8000 varsayımı
# yanlışsa buradaki sabit onun yerine güncellenmeli.
_DEFAULT_MAX_COMPLETION_TOKENS = 3500
_MIN_MAX_COMPLETION_TOKENS = 1024


def _is_too_large_error(err) -> bool:
    msg = str(err)
    return "413" in msg or "reduce your message size" in msg or "tokens per minute" in msg.lower()


def call(clients: list, key_index: list, system_msg: str, user_msg: str,
         temperature: float = 0.2, reasoning_effort: str = "none") -> str | None:
    """
    Groq'a system+user mesajı gönder, rate limit'e göre key rotasyonu yap.
    Dönen çıktıyı clean_output() ile temizleyerek döndür.

    Model: qwen/qwen3.8-27b (Eylül 2026 itibarıyla — Groq, qwen3.6-27b'yi
    kaldırıp bunu önerdiği için değiştirildi; bkz. aşağıdaki not).
    reasoning_effort="none" hâlâ geçerli ve Groq'ta bu model için
    varsayılan da zaten "none" (Qwen'in kendi native varsayılanı "xhigh"
    olsa da Groq API'si bunu override ediyor) — bu yüzden bu parametrede
    ekstra bir değişiklik gerekmedi. reasoning_effort="none" (varsayılan): gpt-oss ailesi
    HER ZAMAN akıl yürütür ve bu KAPATILAMAZ (en düşük ayarında bile
    ("low") gizlice bir miktar "düşünme" token'ı harcar) — bu yüzden
    gpt-oss-120b'de "low" bile TPM/kesik-yanıt sorunlarını tam çözememişti.
    Qwen3.6 ailesinde ise reasoning_effort="none" akıl yürütmeyi GERÇEKTEN
    ve TAMAMEN kapatıyor — çeviri gibi çok adımlı mantık gerektirmeyen bir
    görev için bütçenin tamamı görünür çıktıya ayrılıyor. Nadiren daha
    derin akıl yürütme gerektiren bir çağrı olursa çağıran taraf
    reasoning_effort="low"/"medium"/"high" geçebilir (Qwen bu seviyeleri
    de destekliyor).

    NOT (Temmuz 2026): Model openai/gpt-oss-120b'den qwen/qwen3.6-27b'ye
    değiştirildi — Groq'un kendisi bu modeli, kaldırılan
    llama-3.3-70b-versatile'ın yerine öneriyor; Artificial Analysis'e göre
    Groq'taki en yüksek zeka puanına sahip model ve çok dilli/yaratıcı
    yazımda güçlü. gpt-oss-120b ile yaşanan bazı çeviri kalitesi sorunları
    (örn. "hatched" kelimesinin "yumurtlamış" diye ters çevrilmesi gibi
    anlam kaymaları) bu değişiklikle azalması bekleniyor — kesin olarak
    doğrulanmadı, gerçek kullanımda izlenmeli.

    NOT (Eylül 2026): qwen3.6-27b'den qwen3.8-27b'ye geçildi — Groq
    qwen3.6-27b'yi e-posta ile deprecate edip bunu önerdi. Qwen'in kendi
    yayınladığı ölçümlerde 3.8, 3.6'ya göre kodlama/ajan görevlerinde
    belirgin şekilde daha iyi (bağımsız doğrulanmadı) ve bağlam penceresi
    çok daha geniş (262K, YaRN ile 1M'e kadar) — bu proje için pratik
    etkisi muhtemelen düşük çünkü bölüm başına gönderilen metin zaten bu
    sınırların çok altında. Aynı mimari aile (dense 27B, görsel+metin),
    API arayüzü ve reasoning_effort davranışı aynı kaldı; tek gerekli
    değişiklik model string'iydi.

    Model boş yanıt döndürürse VEYA yanıt token limiti yüzünden yarıda
    kesilirse (finish_reason == "length") (MAX_EMPTY_RETRIES kez tekrar
    denendikten sonra hâlâ öyleyse) "" DEĞİL None döner. Bu, çağıran kodun
    boş/eksik bir "başarılı" sonuçla var olan içeriği yanlışlıkla ezmesini
    önlemek içindir — çağıranlar None kontrolü yapıp orijinal içeriği
    korumalı.

    Hesabın TPM limiti tek bir isteğin talep ettiği (prompt + max tokens)
    boyuttan küçükse (413/"too large"), bu ASLA retry ile düzelmez —
    max_completion_tokens otomatik küçültülüp hemen (30s beklemeden)
    tekrar denenir; _MIN_MAX_COMPLETION_TOKENS'a inmesine rağmen hâlâ
    reddediliyorsa None döner (30 dakika boşuna döngüye girmek yerine).
    """
    empty_retries = 0
    max_out = _DEFAULT_MAX_COMPLETION_TOKENS
    while True:
        now = time.time()
        available = [c for c in clients if c["locked_until"] <= now]
        if not available:
            wait = max(int(min(c["locked_until"] for c in clients) - now), 1)
            if wait > MAX_ACCEPTABLE_WAIT:
                raise AllKeysLockedError(wait)
            print(f"Tüm keyler limit dışı. {wait}s bekleniyor...")
            time.sleep(wait)
            continue

        idx = key_index[0] % len(clients)
        if clients[idx]["locked_until"] > now:
            for i, c in enumerate(clients):
                if c["locked_until"] <= now:
                    idx = i
                    key_index[0] = i
                    break

        info = clients[idx]
        try:
            response = info["client"].chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=temperature,
                max_completion_tokens=max_out,
                reasoning_effort=reasoning_effort,
            )
            key_index[0] = (idx + 1) % len(clients)
            choice = response.choices[0]
            raw = choice.message.content
            finish_reason = getattr(choice, "finish_reason", None)

            if finish_reason == "length":
                # Model, görünür yanıtı bitirmeden token bütçesini tüketti
                # (genellikle gizli reasoning token'ları yüzünden). raw dolu
                # olabilir ama cümle ortasında kesilmiş olabilir — bunu
                # sessizce "tamamlanmış" gibi kabul ETME.
                print(f"  Uyarı: model yanıtı yarıda kesildi (finish_reason=length, "
                      f"key {info['id']}, ham uzunluk: {len(raw or '')})")
                empty_retries += 1
                if empty_retries <= MAX_EMPTY_RETRIES:
                    wait = 5 * empty_retries
                    print(f"  Kesik yanıt — {wait}s sonra tekrar deneniyor "
                          f"({empty_retries}/{MAX_EMPTY_RETRIES})...")
                    time.sleep(wait)
                    continue
                print(f"  Hata: {MAX_EMPTY_RETRIES} denemeden sonra hâlâ kesik yanıt — "
                      f"içerik korunacak, bu parça ATLANACAK (üzerine yazılmayacak).")
                return None

            if not raw or not raw.strip():
                print(f"  Uyarı: model boş yanıt döndürdü (key {info['id']})")
                empty_retries += 1
                if empty_retries <= MAX_EMPTY_RETRIES:
                    wait = 5 * empty_retries
                    print(f"  Boş yanıt — {wait}s sonra tekrar deneniyor "
                          f"({empty_retries}/{MAX_EMPTY_RETRIES})...")
                    time.sleep(wait)
                    continue
                print(f"  Hata: {MAX_EMPTY_RETRIES} denemeden sonra hâlâ boş yanıt — "
                      f"içerik korunacak, bu parça ATLANACAK (üzerine yazılmayacak).")
                return None
            result = clean_output(raw)
            if not result:
                print(f"  Uyarı: clean_output sonrası boş — ham uzunluk: {len(raw)}")
                print(f"  Ham başlangıç: {raw[:200]!r}")
                empty_retries += 1
                if empty_retries <= MAX_EMPTY_RETRIES:
                    wait = 5 * empty_retries
                    print(f"  {wait}s sonra tekrar deneniyor "
                          f"({empty_retries}/{MAX_EMPTY_RETRIES})...")
                    time.sleep(wait)
                    continue
                print(f"  Hata: {MAX_EMPTY_RETRIES} denemeden sonra hâlâ boş yanıt — "
                      f"içerik korunacak, bu parça ATLANACAK (üzerine yazılmayacak).")
                return None
            return result
        except RateLimitError as e:
            if _is_too_large_error(e):
                # Bu, zamanla düzelen bir rate limit DEĞİL — tek bir isteğin
                # talep ettiği token miktarı hesabın TPM tavanından büyük.
                # Key değiştirmek ya da beklemek işe yaramaz (aynı org'un
                # tavanı); tek çözüm isteği küçültmek.
                if max_out > _MIN_MAX_COMPLETION_TOKENS:
                    max_out = max(max_out // 2, _MIN_MAX_COMPLETION_TOKENS)
                    print(f"  Uyarı: istek TPM limiti için çok büyük (413) — "
                          f"max_completion_tokens {max_out}'a düşürülüp hemen "
                          f"tekrar deneniyor.")
                    continue
                print(f"  Hata: max_completion_tokens zaten {_MIN_MAX_COMPLETION_TOKENS} "
                      f"(minimum) ama istek hâlâ hesabın TPM limitini aşıyor. "
                      f"Bu metin parçası muhtemelen tek başına çok uzun ya da "
                      f"Groq hesabının TPM tavanı (bkz. Groq konsolu > Settings > "
                      f"Billing) çok düşük. Bu parça ATLANIYOR.")
                return None
            wait = _parse_retry_seconds(e)
            print(f"Key {info['id']} rate limit! {wait}s kilitlendi.")
            info["locked_until"] = time.time() + wait
            key_index[0] = (idx + 1) % len(clients)
        except Exception as e:
            if _is_too_large_error(e):
                if max_out > _MIN_MAX_COMPLETION_TOKENS:
                    max_out = max(max_out // 2, _MIN_MAX_COMPLETION_TOKENS)
                    print(f"  Uyarı: istek TPM limiti için çok büyük (413) — "
                          f"max_completion_tokens {max_out}'a düşürülüp hemen "
                          f"tekrar deneniyor.")
                    continue
                print(f"  Hata: max_completion_tokens zaten {_MIN_MAX_COMPLETION_TOKENS} "
                      f"(minimum) ama istek hâlâ hesabın TPM limitini aşıyor. "
                      f"Bu parça ATLANIYOR.")
                return None
            print(f"Hata: {e} — 30s sonra tekrar deneniyor...")
            time.sleep(30)
