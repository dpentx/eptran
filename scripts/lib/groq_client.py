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


def call(clients: list, key_index: list, system_msg: str, user_msg: str,
         temperature: float = 0.2) -> str:
    """
    Groq'a system+user mesajı gönder, rate limit'e göre key rotasyonu yap.
    Dönen çıktıyı clean_output() ile temizleyerek döndür.
    """
    while True:
        now = time.time()
        available = [c for c in clients if c["locked_until"] <= now]
        if not available:
            wait = max(int(min(c["locked_until"] for c in clients) - now), 1)
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
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=temperature,
            )
            key_index[0] = (idx + 1) % len(clients)
            raw = response.choices[0].message.content
            if not raw or not raw.strip():
                print(f"  Uyarı: model boş yanıt döndürdü (key {info['id']})")
                return ""
            result = clean_output(raw)
            if not result:
                print(f"  Uyarı: clean_output sonrası boş — ham uzunluk: {len(raw)}")
                print(f"  Ham başlangıç: {raw[:200]!r}")
            return result
        except RateLimitError as e:
            wait = _parse_retry_seconds(e)
            print(f"Key {info['id']} rate limit! {wait}s kilitlendi.")
            info["locked_until"] = time.time() + wait
            key_index[0] = (idx + 1) % len(clients)
        except Exception as e:
            print(f"Hata: {e} — 30s sonra tekrar deneniyor...")
            time.sleep(30)
