"""
Çeviri Hafızası (Translation Memory)

Her kitap için output/<slug>/memory.json dosyasında tutulur:
  - characters : {
        "John": {
            "tr": "John",
            "notes": "Kişilik, rol, diğer karakterlerle ilişkisi, hitap şekli (sen/siz vb.)"
        }
    }
  - terms       : {
        "grimoire": {
            "tr": "büyü kitabı",
            "notes": "Kullanım bağlamı, neden bu karşılık seçildi, alternatif yazımlar"
        }
    }
  - style_notes : {
        "narration": "Anlatım kişisi ve zamanı (1. tekil / 3. tekil, geçmiş/şimdiki zaman)",
        "tone": "Genel ton — resmi/samimi, esprili/ciddi, karanlık/hafif vb.",
        "dialogue": "Diyalog tarzı — kısa-kesik mi, uzun monologlar mı, lehçe/argo var mı",
        "patterns": "Tekrarlayan kalıplar, motifler, sık kullanılan ifadeler"
    }
  - summaries   : ["Bölüm 1: ... (3-4 cümle)", "Bölüm 2: ..."]

İlk bölümden otomatik çıkarılır, sonraki bölümlerde güncellenir.

Not: Eski format (characters/terms'de düz string değer, style_notes'ta düz string)
ile geriye dönük uyumluluk korunur — build_context ve diğer kullanım yerleri
hem eski hem yeni formatı işleyebilir.
"""
import json
import os
import time

from . import groq_client as gc

MEMORY_FILE = "memory.json"
MAX_SUMMARIES = 5

_EXTRACT_SYSTEM = """Sen bir çeviri editörüsün. Sana verilen İngilizce metni analiz et ve aşağıdaki JSON formatında çıktı üret. SADECE JSON döndür, başka hiçbir şey ekleme:

{
  "characters": {
    "İngilizce isim veya lakap": {
      "tr": "Türkçede kullanılacak karşılık",
      "notes": "Karakterin kişiliği, rolü, diğer karakterlerle ilişkisi, konuşma tarzı ve hitap şekli (sen/siz, resmi/samimi) hakkında 1-2 cümle"
    }
  },
  "terms": {
    "özel terim": {
      "tr": "Türkçe karşılık",
      "notes": "Bu terimin bağlamı, neden bu karşılığın seçildiği, dikkat edilmesi gereken noktalar — 1 cümle"
    }
  },
  "style_notes": {
    "narration": "Anlatım kişisi ve zamanı (örn. '3. tekil şahıs, geçmiş zaman')",
    "tone": "Genel ton (örn. 'samimi ve esprili, hafif melankolik anlar var')",
    "dialogue": "Diyalog tarzı (örn. 'kısa ve doğal, argo kullanımı var')",
    "patterns": "Tekrarlayan kalıplar, motifler veya sık kullanılan ifadeler (varsa)"
  }
}

Kurallar:
- Kişi adları genellikle olduğu gibi korunur (John → John)
- Kültüre özgü terimler, büyü/güç adları, unvanlar önemlidir
- notes alanları kısa ama bilgilendirici olsun (1-2 cümle)
- style_notes alanlarının her biri 1 cümle olsun, gözlemlenemiyorsa kısa not düş (örn. "belirsiz")"""

_UPDATE_SYSTEM = """Sen bir çeviri editörüsün. Mevcut çeviri hafızasını yeni bölüm bilgileriyle güncelle.
SADECE güncellenmiş JSON döndür, başka hiçbir şey ekleme.
Mevcut kayıtları silme, sadece yenilerini ekle veya çelişkileri düzelt.
characters ve terms alanlarındaki her girişin "tr" ve "notes" alanlarını koru/güncelle.
style_notes alanındaki narration/tone/dialogue/patterns alt-alanlarını,
yeni bölümde gözlemlenen bilgilerle zenginleştir (üzerine yaz, kaybetme — birleştir).
Aynı JSON şemasını (characters/terms/style_notes/summaries) kullan."""

_SUMMARY_SYSTEM = (
    "Sana verilen Türkçe çeviri metninin 3-4 cümlelik özetini yaz. "
    "Önemli olayları, karakterleri ve bölümün duygusal/anlatısal dönüm noktalarını belirt. "
    "SADECE özeti döndür, başka hiçbir şey ekleme."
)


def _memory_path(output_dir: str) -> str:
    return os.path.join(output_dir, MEMORY_FILE)


def _empty_memory() -> dict:
    return {
        "characters": {},
        "terms": {},
        "style_notes": {
            "narration": "",
            "tone": "",
            "dialogue": "",
            "patterns": "",
        },
        "summaries": [],
    }


def _migrate_entry(value):
    """Eski format (düz string) → yeni format ({"tr": ..., "notes": ...})."""
    if isinstance(value, str):
        return {"tr": value, "notes": ""}
    if isinstance(value, dict):
        return {"tr": value.get("tr", ""), "notes": value.get("notes", "")}
    return {"tr": str(value), "notes": ""}


def _migrate_style_notes(value):
    """Eski format (düz string) → yeni format (dict)."""
    if isinstance(value, dict):
        result = _empty_memory()["style_notes"]
        result.update({k: value.get(k, "") for k in result if k in value})
        return result
    if isinstance(value, str) and value:
        empty = _empty_memory()["style_notes"]
        empty["tone"] = value
        return empty
    return _empty_memory()["style_notes"]


def _normalize(memory: dict) -> dict:
    """Yüklenen hafızayı her zaman güncel şemaya migrate et."""
    base = _empty_memory()

    characters = memory.get("characters", {}) or {}
    base["characters"] = {k: _migrate_entry(v) for k, v in characters.items()}

    terms = memory.get("terms", {}) or {}
    base["terms"] = {k: _migrate_entry(v) for k, v in terms.items()}

    base["style_notes"] = _migrate_style_notes(memory.get("style_notes", {}))

    base["summaries"] = memory.get("summaries", []) or []

    return base


def load(output_dir: str) -> dict:
    """Hafızayı diskten yükle, yoksa boş yapı döndür. Eski formatı migrate eder."""
    path = _memory_path(output_dir)
    if not os.path.exists(path):
        return _empty_memory()
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return _normalize(raw)


def save(output_dir: str, memory: dict) -> None:
    """Hafızayı diske kaydet."""
    path = _memory_path(output_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def _parse_json_response(raw: str):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def extract_from_source(source_text: str, clients: list, key_index: list) -> dict:
    """
    İlk bölümün kaynak (İngilizce) metninden hafıza çıkar.
    Karakter, terim ve stil notlarını döndürür.
    """
    # Uzun metinleri kısalt — hafıza için ilk 4000 karakter yeterli
    sample = source_text[:4000]
    raw = gc.call(clients, key_index, _EXTRACT_SYSTEM, sample, temperature=0.1)
    time.sleep(1)

    try:
        data = _parse_json_response(raw)
        memory = _empty_memory()
        memory["characters"] = {k: _migrate_entry(v) for k, v in data.get("characters", {}).items()}
        memory["terms"] = {k: _migrate_entry(v) for k, v in data.get("terms", {}).items()}
        memory["style_notes"] = _migrate_style_notes(data.get("style_notes", {}))
        return memory
    except json.JSONDecodeError:
        print("  Hafıza çıkarılamadı (JSON parse hatası), boş başlanıyor.")
        return _empty_memory()


def update_from_translation(memory: dict, translated_text: str,
                             clients: list, key_index: list) -> dict:
    """
    Çevrilmiş metinden yeni karakter/terim bilgileri çıkar,
    mevcut hafızayla birleştir.
    """
    sample = translated_text[:3000]
    user_msg = (
        f"Mevcut hafıza:\n{json.dumps(memory, ensure_ascii=False)}\n\n"
        f"Yeni bölüm metni:\n{sample}"
    )
    raw = gc.call(clients, key_index, _UPDATE_SYSTEM, user_msg, temperature=0.1)
    time.sleep(1)

    try:
        data = _parse_json_response(raw)
        updated = _empty_memory()
        updated["characters"] = {k: _migrate_entry(v) for k, v in data.get("characters", {}).items()}
        updated["terms"] = {k: _migrate_entry(v) for k, v in data.get("terms", {}).items()}
        updated["style_notes"] = _migrate_style_notes(data.get("style_notes", {}))
        # summaries'i koru — update endpoint'i değiştirmez
        updated["summaries"] = memory.get("summaries", [])
        return updated
    except json.JSONDecodeError:
        print("  Hafıza güncellenemedi (JSON parse hatası), mevcut korunuyor.")
        return memory


def add_summary(memory: dict, chapter_title: str, translated_text: str,
                clients: list, key_index: list) -> dict:
    """Bölüm özetini hafızaya ekle."""
    sample = translated_text[:3000]
    summary = gc.call(clients, key_index, _SUMMARY_SYSTEM, sample, temperature=0.1)
    time.sleep(1)
    memory["summaries"].append(f"{chapter_title}: {summary}")
    # Son N özeti tut — context window'u şişirme
    memory["summaries"] = memory["summaries"][-MAX_SUMMARIES:]
    return memory


def build_context(memory: dict) -> str:
    """
    Hafızayı translate/review prompt'larına eklenecek context string'e dönüştür.
    Boşsa boş string döner.
    """
    style = memory.get("style_notes", {}) or {}
    has_style = any(style.get(k) for k in ("narration", "tone", "dialogue", "patterns")) \
        if isinstance(style, dict) else bool(style)

    if not any([memory.get("characters"), memory.get("terms"),
                has_style, memory.get("summaries")]):
        return ""

    parts = ["=== ÇEVİRİ HAFIZASI ==="]

    if memory.get("characters"):
        char_lines = []
        for k, v in memory["characters"].items():
            entry = _migrate_entry(v)
            line = f"{k} → {entry['tr']}"
            if entry.get("notes"):
                line += f" ({entry['notes']})"
            char_lines.append(line)
        parts.append("Karakterler: " + "; ".join(char_lines))

    if memory.get("terms"):
        term_lines = []
        for k, v in memory["terms"].items():
            entry = _migrate_entry(v)
            line = f"{k} → {entry['tr']}"
            if entry.get("notes"):
                line += f" ({entry['notes']})"
            term_lines.append(line)
        parts.append("Terimler: " + "; ".join(term_lines))

    if has_style:
        if isinstance(style, dict):
            style_bits = []
            if style.get("narration"):
                style_bits.append(f"Anlatım: {style['narration']}")
            if style.get("tone"):
                style_bits.append(f"Ton: {style['tone']}")
            if style.get("dialogue"):
                style_bits.append(f"Diyalog: {style['dialogue']}")
            if style.get("patterns"):
                style_bits.append(f"Tekrarlayan kalıplar: {style['patterns']}")
            parts.append("Stil: " + " | ".join(style_bits))
        else:
            parts.append(f"Stil: {style}")

    if memory.get("summaries"):
        parts.append("Önceki bölümler:")
        for s in memory["summaries"]:
            parts.append(f"  - {s}")

    parts.append("======================")
    return "\n".join(parts)
