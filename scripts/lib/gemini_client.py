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
    """
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY bulunamadı. GitHub repo Settings > Secrets and "
            "variables > Actions altına eklenmeli."
        )
    client = genai.Client(api_key=key)
    model_name = os.environ.get("GEMINI_MODEL", _DEFAULT_MODEL)
    return client, model_name


def call(client_info, system_msg: str, user_msg: str, temperature: float = 0.2) -> str | None:
    """
    Gemini'ye system+user mesajı gönderir. Groq'un call() imzasına
    kasıtlı olarak benzer (system_msg/user_msg ayrımı, temperature).

    Rate limit / geçici hatalarda üstel geri çekilmeyle (backoff)
    MAX_EMPTY_RETRIES kez dener, sonra None döner — çağıran taraf None
    kontrolü yapıp mevcut veriyi korumalı (Groq client'la aynı
    sözleşme).
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
            msg = str(e).lower()
            is_rate_limit = "429" in msg or "quota" in msg or "rate" in msg
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
