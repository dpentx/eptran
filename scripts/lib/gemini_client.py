"""
eptran — lib/gemini_client.py

Qwen'in çevirisini BAĞIMSIZ bir modelle (Gemini) denetlemek için ayrı
bir istemci. Bilerek Groq/Qwen'den TAMAMEN ayrı tutuluyor — amaç
"kendi hatasını kendi kontrol eden" bir sistem değil, ikinci, farklı
bir modelin gözünden bakmak (aynı modelin kendi çıktısını kendi
denetlemesi, aynı körlükleri paylaşma riski taşır).

KULLANIM ALANI: Bu istemci SADECE qa_audit.py ve series_suggest.py
tarafından kullanılır — ana çeviri/review hattına (translate.py,
queue_worker.py, review.py) HİÇ dahil değildir. Gemini'nin ücretsiz
katmanı çok daha düşük rate limit'e sahip (Groq'un TPM/RPM'iyle
kıyaslanamaz), bu yüzden bu araçlar hızlı değil, periyodik/isteğe
bağlı çalışacak şekilde tasarlandı.

Model adı ortam değişkeninden okunuyor (GEMINI_MODEL, varsayılan
"gemini-3.5-flash") çünkü Google bu isimleri sık değiştiriyor — kodu
değiştirmeden GitHub Actions secret'ından güncellenebilsin diye.
"""
import os
import time

from google import genai
from google.genai import types

_DEFAULT_MODEL = "gemini-3.5-flash"

MAX_EMPTY_RETRIES = 3


class DailyQuotaExceeded(Exception):
    """
    Gemini'nin ücretsiz katmanının GÜNLÜK istek kotası (RPD — requests
    per day) tükendiğinde fırlatılır. Bu, dakikalık rate limit (RPM)
    gibi "birkaç saniye bekle, geç" türü bir şey DEĞİL — kota gece
    (Google'ın saat dilimine göre) sıfırlanana kadar YENİDEN
    DOLMUYOR. Bu yüzden normal retry/backoff döngüsüne SOKMUYORUZ;
    tespit eder etmez hemen (deneme yapmadan) fırlatıyoruz.

    Gerçek üretimde (knh-11, 17 Ağustos) bu ayrım yokken script, kota
    zaten tükenmiş olduğu halde kalan ~13 bölümün her biri için 3'er
    kez (20-40-60 saniye aralıklarla) boşuna denedi — bir sonuç
    değişmeden onlarca dakika harcadı, sonunda admin sabrı taşıp
    çalıştırmayı iptal etti ve o ana kadarki hiçbir ilerleme
    kaydedilmemişti (checkpoint yoktu — bkz. qa_audit.py).
    """
    pass


class AllKeysExhausted(Exception):
    """Elimizdeki TÜM Gemini key'lerinin günlük kotası tükendiğinde fırlatılır."""
    pass


def get_clients() -> list:
    """
    GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3... ortam
    değişkenlerinden BİRDEN FAZLA key okur (Groq'taki gibi, [(client,
    model_name), ...] listesi olarak).

    ÖNEMLİ SINIRLAMA (Ağustos 2026): Groq'un aksine, Gemini'nin ücretsiz
    katman kotası key başına DEĞİL, Google Cloud PROJESİ başına
    uygulanıyor — gerçek hata mesajında bunu açıkça görüyoruz:
    `quotaId: 'GenerateRequestsPerDayPerProjectPerModel-FreeTier'`
    ("PerProject", "PerKey" değil). Yani AYNI Google hesabından/
    projesinden alınan 2-3 key'in HEPSİ AYNI günlük 20 isteklik havuzu
    paylaşır — sadece key çoğaltmak kotayı ÇARPMAZ. Gerçekten fayda
    görmek için her key AYRI bir Google Cloud projesinden (ideal
    olarak ayrı Google hesaplarından) alınmalı. Buna rağmen bu
    mekanizmayı kuruyoruz çünkü: (a) ayrı projelerden key'ler
    kullanılırsa gerçekten işe yarıyor, (b) tek key'le de olsa
    transient (kalıcı olmayan, dakikalık) hatalarda ikinci bir key'e
    geçmek faydalı olabilir.
    """
    keys = []
    first = os.environ.get("GEMINI_API_KEY")
    if first:
        keys.append(first)
    idx = 2
    while True:
        k = os.environ.get(f"GEMINI_API_KEY_{idx}")
        if not k:
            break
        keys.append(k)
        idx += 1

    if not keys:
        raise ValueError(
            "GEMINI_API_KEY bulunamadı. GitHub repo Settings > Secrets and "
            "variables > Actions altına eklenmeli."
        )

    # NOT (Ağustos 2026, gerçek üretim hatası): `os.environ.get("GEMINI_MODEL",
    # _DEFAULT_MODEL)` YANLIŞ — bu sadece ortam değişkeni HİÇ YOKSA
    # varsayılana düşer. Ama workflow'daki `GEMINI_MODEL: ${{ vars.GEMINI_MODEL }}`
    # satırı, repo'da o adda bir "variable" tanımlı DEĞİLSE değişkeni boş
    # STRING olarak enjekte ediyor (yokmuş gibi silmiyor). `or` kullanmak
    # hem "yok" hem "boş" durumunu doğru şekilde varsayılana düşürüyor.
    model_name = os.environ.get("GEMINI_MODEL") or _DEFAULT_MODEL
    return [(genai.Client(api_key=k), model_name) for k in keys]


def _call_single(client_info, system_msg: str, user_msg: str, temperature: float) -> str | None:
    """Tek bir key ile dener. Groq client'la aynı sözleşme: başarısızlıkta None döner."""
    client, model_name = client_info
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_msg,
    )
    empty_retries = 0
    while True:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_msg,
                config=config,
            )
            text = (response.text or "").strip()
            if not text:
                raise ValueError("boş yanıt")
            return text
        except Exception as e:
            msg = str(e)
            # "PerDay" kotası (RPD) — RPM'in aksine bekleyip tekrar
            # denemekle çözülmez, gün değişene kadar tükenmiş kalır.
            # Retry döngüsüne hiç girmeden hemen fırlatıyoruz ki üstteki
            # call() bir sonraki key'e geçebilsin.
            if "PerDay" in msg or "RequestsPerDay" in msg:
                raise DailyQuotaExceeded(msg) from e
            msg_low = msg.lower()
            is_rate_limit = "429" in msg_low or "quota" in msg_low or "rate" in msg_low
            empty_retries += 1
            if empty_retries > MAX_EMPTY_RETRIES:
                print(f"  Gemini hatası ({MAX_EMPTY_RETRIES} denemeden sonra): {e}")
                return None
            wait = 20 * empty_retries if is_rate_limit else 5 * empty_retries
            print(f"  Gemini hatası: {e} — {wait}s sonra tekrar deneniyor "
                  f"({empty_retries}/{MAX_EMPTY_RETRIES})...")
            time.sleep(wait)


def call(clients: list, key_index: list, system_msg: str, user_msg: str,
         temperature: float = 0.2) -> str | None:
    """
    Gemini'ye system+user mesajı gönderir. Groq client'la aynı imza
    deseni: `clients` = get_clients()'ın listesi, `key_index` = tek
    elemanlı mutable liste (örn. [0]) — ardışık call() çağrıları
    arasında "şu an hangi key aktif" durumunu paylaşmak için.

    Bir key günlük kotasını tüketince (DailyQuotaExceeded) o key'i bu
    RUN için "tükenmiş" işaretleyip BİR SONRAKİ key'e otomatik geçer —
    tüm key'ler tükenirse AllKeysExhausted fırlatır. Tek key varsa
    (varsayılan/eski davranış) bu tek adımlık bir döngüdür, davranış
    değişmez.
    """
    exhausted = set()
    n = len(clients)
    while len(exhausted) < n:
        idx = key_index[0] % n
        if idx in exhausted:
            key_index[0] += 1
            continue
        try:
            return _call_single(clients[idx], system_msg, user_msg, temperature)
        except DailyQuotaExceeded:
            print(f"  Key #{idx + 1}/{n} günlük kotası tükendi"
                  + (", sonraki key'e geçiliyor..." if len(exhausted) + 1 < n else "."))
            exhausted.add(idx)
            key_index[0] += 1
    raise AllKeysExhausted(f"Elimizdeki {n} Gemini key'inin de günlük kotası tükendi.")


def extract_json(raw: str):
    """Modelin ```json ... ``` bloğuyla sarabileceği yanıttan JSON çıkar."""
    import json
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
