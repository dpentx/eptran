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


def get_client():
    """
    GEMINI_API_KEY ortam değişkeninden tek bir key okur (Groq'un
    aksine çoklu key rotasyonu yok — bu araçlar yüksek hacimli ana
    çeviri hattı değil, periyodik QA taraması, tek bir ücretsiz key
    genelde yeterli).

    NOT (Ağustos 2026): `google-generativeai` paketi TAMAMEN
    KULLANIMDAN KALDIRILDI (bakım/güncelleme almıyor) — yerine
    `google-genai` paketi (import google.genai) kullanılıyor. Bu iki
    paketin API'si FARKLI (eskisi genai.GenerativeModel(...), yenisi
    genai.Client(...).models.generate_content(...)) — ileride bir
    yerlerde eski paketle örnek kod görürsen KARIŞTIRMA.

    NOT (Ağustos 2026, günlük kota): Gerçek üretimde `gemini-3.5-flash`
    için ücretsiz katman günde SADECE 20 istekle sınırlı çıktı
    (`GenerateRequestsPerDayPerProjectPerModel-FreeTier: 20`) — 35
    bölümlük bir kitap TEK ÇALIŞTIRMADA bitmiyor. Bazı kaynaklara göre
    "Flash-Lite" modelleri çok daha yüksek günlük kotaya sahip
    (1000-1500/gün), ama bu hesaba/projeye göre değişebiliyor — kesin
    rakam için https://ai.dev/rate-limit kontrol edilmeli. Model adını
    GEMINI_MODEL repository variable'ından değiştirebilirsin (örn.
    "gemini-3.1-flash-lite" deneyebilirsin), ama asıl güvence bu
    DEĞİL — qa_audit.py'nin checkpoint mekanizması: kota hangi model
    için ne olursa olsun, script kesildiği yerden devam edebiliyor
    artık.
    """
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY bulunamadı. GitHub repo Settings > Secrets and "
            "variables > Actions altına eklenmeli."
        )
    client = genai.Client(api_key=key)
    # NOT (Ağustos 2026, gerçek üretim hatası): `os.environ.get("GEMINI_MODEL",
    # _DEFAULT_MODEL)` YANLIŞ — bu sadece ortam değişkeni HİÇ YOKSA
    # varsayılana düşer. Ama workflow'daki `GEMINI_MODEL: ${{ vars.GEMINI_MODEL }}`
    # satırı, repo'da o adda bir "variable" tanımlı DEĞİLSE değişkeni boş
    # STRING olarak enjekte ediyor (yokmuş gibi silmiyor) — yani
    # `os.environ["GEMINI_MODEL"]` var ama `""`. `.get(key, default)` bunu
    # "boş model adı" olarak Gemini'ye gönderiyordu, o da her çağrıda
    # "model is required" hatası veriyordu — 35 bölümlük bir kitapta 3
    # deneme × artan bekleme ile ~17 dakika boşuna dönüp hiçbir gerçek
    # denetim yapmadan "0 şüpheli nokta" ile bitiyordu (yanlışlıkla "temiz"
    # görünüyordu, oysa hiç denetlenmemişti). `or` kullanmak hem "yok" hem
    # "boş" durumunu doğru şekilde varsayılana düşürüyor.
    model_name = os.environ.get("GEMINI_MODEL") or _DEFAULT_MODEL
    return client, model_name


def call(client_info, system_msg: str, user_msg: str, temperature: float = 0.2) -> str | None:
    """
    Gemini'ye system+user mesajı gönderir. Groq'un call() imzasına
    kasıtlı olarak benzer (system_msg/user_msg ayrımı, temperature).

    Rate limit / geçici hatalarda üstel geri çekilmeyle (backoff)
    MAX_EMPTY_RETRIES kez dener, sonra None döner — çağıran taraf None
    kontrolü yapıp mevcut veriyi korumalı (Groq client'la aynı
    sözleşme).

    GÜNLÜK kota hatasında (bkz. DailyQuotaExceeded) HİÇ retry
    yapmadan hemen fırlatır — bu tür bir hata dakikalar içinde
    kendiliğinden düzelmez, denemek zaman kaybı.
    """
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


def extract_json(raw: str):
    """Modelin ```json ... ``` bloğuyla sarabileceği yanıttan JSON çıkar."""
    import json
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
