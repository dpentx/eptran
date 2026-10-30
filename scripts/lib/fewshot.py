"""
eptran — lib/fewshot.py

ELLE seçilmiş "kaynak → iyi Türkçe çeviri" örneklerini (fewshot.json)
çeviri sistem prompt'una ekler. pitfalls.py / series.py ile AYNI felsefe:
otomatik keşif ya da otomatik yazma YOK — hangi örneğin çıtayı temsil
ettiğine sen karar verirsin (bkz. eval/add_pair.py fewshot <id>).

BÜTÇE: Groq free planda qwen3.8-27b'nin TPM tavanı ~8000 (prompt +
completion birlikte). Few-shot her çeviri çağrısına eklendiği için
sıkı sınırlı: en fazla MAX_EXAMPLES örnek, kaynak+çeviri toplamı en fazla
MAX_CHARS karakter. Sığmayan örnek atlanır. fewshot.json boşsa bu modül
hiçbir şey eklemez, yani davranış değişmez.

EPTRAN_FEWSHOT=0 ortam değişkeni few-shot'ı tamamen kapatır (eval'de
"açık/kapalı" karşılaştırması için).
"""

import json
import os

FEWSHOT_FILE = "fewshot.json"
MAX_EXAMPLES = 3
MAX_CHARS = 1200


def _enabled() -> bool:
    return os.environ.get("EPTRAN_FEWSHOT", "1") != "0"


def _load_entries() -> list:
    if not os.path.exists(FEWSHOT_FILE):
        return []
    try:
        with open(FEWSHOT_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return data.get("entries", [])


def pick_examples() -> list:
    """Bütçeye sığan (kaynak, çeviri) çiftlerini sırayla seçer."""
    if not _enabled():
        return []
    picked, used = [], 0
    for entry in _load_entries():
        source = (entry.get("source") or "").strip()
        target = (entry.get("target") or "").strip()
        if not source or not target:
            continue
        size = len(source) + len(target)
        if used + size > MAX_CHARS:
            continue
        picked.append((source, target))
        used += size
        if len(picked) >= MAX_EXAMPLES:
            break
    return picked


def build_context() -> str:
    """Sistem prompt'una eklenecek örnek bloğu; örnek yoksa "" döner."""
    picked = pick_examples()
    if not picked:
        return ""
    blocks = [
        "ÖRNEK ÇEVİRİLER (üslup ve kelime seçimi için kalite çıtası. "
        "Örneklerin İÇERİĞİNİ değil, Türkçeyi ne kadar doğal kurduğunu "
        "örnek al; bu cümleleri çıktına ASLA kopyalama):"
    ]
    for i, (source, target) in enumerate(picked, 1):
        blocks.append(f"Örnek {i}\nİngilizce: {source}\nTürkçe: {target}")
    return "\n\n".join(blocks)
