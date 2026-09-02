"""
eptran — lib/pitfalls.py

KİTAP/SERİ BAĞIMSIZ, GENEL çeviri tuzakları.

series.py'den farkı: series glossary'si BU KİTABA/SERİYE özel gerçekleri
(karakter isimleri, ilişkiler) tutar; bu modül ise HANGİ KİTAP OLURSA
OLSUN geçerli, Qwen'in tekrar tekrar düştüğü GENEL çeviri tuzaklarını
tutar (bkz. common_pitfalls.json'daki _meta alanı).

TASARIM İLKESİ — series.py ile AYNI: otomatik keşif OLUR, otomatik
YAZMA OLMAZ. Bu modül common_pitfalls.json'ı okuyup sistem prompt'una
ekler, ama TERSİNE hiçbir şey yapmaz — bir kitabın çevirisi bu dosyayı
kendiliğinden güncellemez. Yeni bir tuzak örüntüsü keşfedilirse
(genelde bir kitabın Gemini QA denetiminde tekrarlayan bir hata
görülünce), common_pitfalls.json'a ELLE eklenmesi gerekir.
"""

import json
import os

PITFALLS_FILE = "common_pitfalls.json"


def _load_entries() -> list:
    if not os.path.exists(PITFALLS_FILE):
        return []
    try:
        with open(PITFALLS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return data.get("entries", [])


def build_context() -> str:
    """
    common_pitfalls.json'daki genel tuzakları, sistem prompt'una
    eklenecek okunabilir bir blok olarak döner. Dosya yoksa ya da
    boşsa "" döner (çağıran taraf zaten falsy kontrolü yapıyor).
    """
    entries = _load_entries()
    if not entries:
        return ""

    lines = [
        "BİLİNEN GENEL ÇEVİRİ TUZAKLARI (farklı kitaplarda tekrar tekrar "
        "görülmüş hatalar — aşağıdaki örüntülerden biriyle karşılaşırsan "
        "'avoid' ile işaretlenen yanlışa DÜŞME, 'correct' ile verilen "
        "karşılığı kullan):"
    ]
    for entry in entries:
        pattern = entry.get("pattern", "").strip()
        avoid = entry.get("avoid", "").strip()
        correct = entry.get("correct", "").strip()
        if not pattern or not correct:
            continue
        if avoid:
            lines.append(f"- \"{pattern}\" → \"{avoid}\" DEĞİL, \"{correct}\"")
        else:
            lines.append(f"- \"{pattern}\" → \"{correct}\"")

    return "\n".join(lines)
