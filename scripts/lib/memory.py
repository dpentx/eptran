"""
Çeviri Hafızası (Translation Memory)

Her kitap için output/<slug>/memory.json dosyasında tutulur:
  - characters : {"John": "John", "the innkeeper": "hancı"}
  - terms       : {"mana": "mana", "grimoire": "büyü kitabı"}
  - style_notes : "Anlatıcı kısa, kuru cümleler kullanıyor..."
  - summaries   : ["Bölüm 1: ...", "Bölüm 2: ..."]

İlk bölümden otomatik çıkarılır, sonraki bölümlerde güncellenir.
"""
import json
import os
import time

from . import groq_client as gc
from .ner import representative_sample

MEMORY_FILE = "memory.json"

_EXTRACT_SYSTEM = """Sen bir çeviri editörüsün. Sana verilen İngilizce metni analiz et ve aşağıdaki JSON formatında çıktı üret. SADECE JSON döndür, başka hiçbir şey ekleme:

{
  "characters": {"İngilizce isim veya lakap": "Türkçede kullanılacak karşılık"},
  "terms": {"özel terim": "Türkçe karşılık"},
  "style_notes": "Anlatıcının tonu, cümle yapısı, dikkat edilmesi gereken özellikler hakkında 1-2 cümle"
}

Kurallar:
- Kişi adları genellikle olduğu gibi korunur (John → John)
- Kültüre özgü terimler, büyü/güç adları, unvanlar önemlidir
- style_notes kısa ve net olsun"""

_UPDATE_SYSTEM = """Sen bir çeviri editörüsün. Mevcut çeviri hafızasını yeni bölüm bilgileriyle güncelle.
SADECE güncellenmiş JSON döndür, başka hiçbir şey ekleme.
Mevcut kayıtları silme, sadece yenilerini ekle veya çelişkileri düzelt."""

_SUMMARY_SYSTEM = (
    "Sana verilen Türkçe çeviri metninin 1-2 cümlelik özetini yaz. "
    "Önemli olayları ve karakterleri belirt. "
    "SADECE özeti döndür, başka hiçbir şey ekleme."
)


# Hafızada tutulacak tek izin verilen alanlar
_ALLOWED_KEYS = {"characters", "terms", "style_notes", "summaries"}


def _sanitize(memory: dict) -> dict:
    """Model tarafından eklenen izinsiz alanları temizle (örn. book_info)."""
    return {k: v for k, v in memory.items() if k in _ALLOWED_KEYS}


def _memory_path(output_dir: str) -> str:
    return os.path.join(output_dir, MEMORY_FILE)


def load(output_dir: str) -> dict:
    """Hafızayı diskten yükle, yoksa boş yapı döndür. İzinsiz alanları temizler."""
    path = _memory_path(output_dir)
    if not os.path.exists(path):
        return {"characters": {}, "terms": {}, "style_notes": "", "summaries": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data = _sanitize(data)
    # Eksik alanları tamamla
    data.setdefault("characters", {})
    data.setdefault("terms", {})
    data.setdefault("style_notes", "")
    data.setdefault("summaries", [])
    return data


def save(output_dir: str, memory: dict) -> None:
    """Hafızayı diske kaydet. İzinsiz alanları filtrele."""
    path = _memory_path(output_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_sanitize(memory), f, ensure_ascii=False, indent=2)


def extract_from_source(source_text: str, clients: list, key_index: list) -> dict:
    """
    İlk bölümün kaynak (İngilizce) metninden hafıza çıkar.
    Karakter, terim ve stil notlarını döndürür.
    """
    # Baş+orta+son örnekleme — bkz. ner.representative_sample docstring'i.
    # Bu bölüm ilk parçadan çok daha uzunsa (çok parçalı), sadece baştan
    # bakmak sonradan tanıtılan karakterleri/üslup ipuçlarını kaçırabilirdi.
    sample = representative_sample(source_text, max_chars=8000)
    raw = gc.call(clients, key_index, _EXTRACT_SYSTEM, sample, temperature=0.1)
    time.sleep(1)

    try:
        # JSON bloğunu temizle (gc.call boş yanıtta None döndürebilir)
        raw = (raw or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        result = {
            "characters": data.get("characters", {}),
            "terms": data.get("terms", {}),
            "style_notes": data.get("style_notes", ""),
            "summaries": [],
        }
        return _sanitize(result)
    except json.JSONDecodeError:
        print("  Hafıza çıkarılamadı (JSON parse hatası), boş başlanıyor.")
        return {"characters": {}, "terms": {}, "style_notes": "", "summaries": []}


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
        raw = (raw or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        updated = json.loads(raw)
        # İzinsiz alanları temizle
        updated = _sanitize(updated)
        # summaries'i koru — update endpoint'i değiştirmez
        updated["summaries"] = memory.get("summaries", [])
        return updated
    except json.JSONDecodeError:
        print("  Hafıza güncellenemedi (JSON parse hatası), mevcut korunuyor.")
        return memory


def add_summary(memory: dict, chapter_title: str, translated_text: str,
                clients: list, key_index: list) -> dict:
    """Bölüm özetini hafızaya ekle. Boilerplate bölümleri atla."""
    from . import boilerplate as bp

    # Başlık boilerplate ise özet ekleme
    if bp.is_boilerplate(chapter_title):
        print(f"  Özet atlandı (boilerplate başlık): {chapter_title[:60]}")
        return memory

    sample = translated_text[:3000]

    # Çevrilmiş metin de büyük ölçüde boilerplate ise atla
    cleaned_sample = bp.clean(sample)
    if len(cleaned_sample) < 200:
        print(f"  Özet atlandı (boilerplate içerik): {chapter_title[:60]}")
        return memory

    summary = gc.call(clients, key_index, _SUMMARY_SYSTEM, cleaned_sample, temperature=0.1)
    time.sleep(1)
    if not summary:
        print(f"  Özet alınamadı (model boş yanıt döndürdü): {chapter_title[:60]}")
        return memory
    memory["summaries"].append(f"{chapter_title}: {summary}")
    # Son 5 özeti tut — context window'u şişirme
    memory["summaries"] = memory["summaries"][-5:]
    return memory


def build_context(memory: dict) -> str:
    """
    Hafızayı translate/review prompt'larına eklenecek context string'e dönüştür.
    Boşsa boş string döner.
    """
    if not any([memory.get("characters"), memory.get("terms"),
                memory.get("style_notes"), memory.get("summaries")]):
        return ""

    parts = ["=== ÇEVİRİ HAFIZASI ==="]

    if memory.get("characters"):
        chars = ", ".join(f"{k} → {v}" for k, v in memory["characters"].items())
        parts.append(f"Karakterler: {chars}")

    if memory.get("terms"):
        terms = ", ".join(f"{k} → {v}" for k, v in memory["terms"].items())
        parts.append(f"Terimler: {terms}")

    if memory.get("style_notes"):
        parts.append(f"Stil: {memory['style_notes']}")

    if memory.get("summaries"):
        parts.append("Önceki bölümler:")
        for s in memory["summaries"]:
            parts.append(f"  - {s}")

    parts.append("======================")
    return "\n".join(parts)
