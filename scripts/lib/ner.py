"""
Dinamik Named Entity Recognition ve sorunlu paragraf düzeltici.
İngilizce kalmış kelimeler tespit edilince:
  1. NER ile özel isimleri whitelist'e al
  2. Whitelist dışındaki sorunlu kelimeleri LLM ile düzelt
"""
import time

from . import groq_client as gc
from . import unicode_cleaner
from . import english_detector
from . import boilerplate

_NER_SYSTEM = (
    "Sana verilen metindeki özel isimleri listele: kişi adları, yer adları, "
    "kurum/marka adları, kitap/eser adları. "
    "Her ismi yeni satıra yaz. Sadece listeyi döndür, açıklama ekleme. "
    "Eğer özel isim yoksa boş satır döndür."
)

_FIX_SYSTEM = (
    "Sen profesyonel bir Türkçe editör ve çevirmensin. "
    "Sana verilen paragrafta bazı kelimeler İngilizce kalmış veya bozuk çevrilmiş. "
    "Korunması gereken özel isimler ayrıca belirtilecek — onlara dokunma. "
    "Paragrafı doğal, akıcı Türkçeye çevir/düzelt. "
    "SADECE düzeltilmiş paragrafı döndür, açıklama ekleme."
)


def get_entities(paragraph: str, clients: list, key_index: list) -> set:
    """Paragraftaki özel isimleri LLM ile tespit et, küçük harf set olarak döndür."""
    result = gc.call(clients, key_index, _NER_SYSTEM, paragraph)
    time.sleep(1)
    entities = set()
    for line in result.splitlines():
        name = line.strip().strip('-').strip('•').strip()
        if name:
            entities.add(name.lower())
            for word in name.split():
                if len(word) > 2:
                    entities.add(word.lower())
    return entities


def fix_paragraph(paragraph: str, protected: set,
                  bad_words: list, clients: list, key_index: list) -> str:
    """Sorunlu paragrafı LLM'e gönder, düzeltilmiş halini al."""
    protected_str = ", ".join(sorted(protected)) if protected else "yok"
    user_msg = (
        f"Korunacak özel isimler: {protected_str}\n"
        f"Düzeltilmesi gereken kelimeler: {', '.join(bad_words)}\n\n"
        f"Paragraf:\n{paragraph}"
    )
    result = gc.call(clients, key_index, _FIX_SYSTEM, user_msg)
    time.sleep(1)
    return result


def fix_text(text: str, clients: list, key_index: list) -> str:
    """
    Metindeki tüm paragrafları tara:
    1. Unicode temizle
    2. İngilizce kelime tespit et
    3. NER ile özel isimleri whitelist'e al
    4. Whitelist dışında sorun varsa paragrafı yeniden düzelt
    """
    paragraphs = text.split("\n\n")
    result = []
    fixed_count = 0

    for para in paragraphs:
        stripped = para.strip()

        # Koruma altındaki satırlar
        if stripped.startswith("[EPUB_IMAGE:") or stripped.startswith("#"):
            result.append(para)
            continue

        # Boilerplate atla
        if boilerplate.is_boilerplate(stripped):
            print(f"    boilerplate atlandı: {stripped[:60]}...")
            continue

        # Unicode temizle
        cleaned = unicode_cleaner.clean(para)

        # İngilizce kelime tespiti
        eng_words = english_detector.find(cleaned)
        if not eng_words:
            result.append(cleaned)
            continue

        # NER — özel isimleri whitelist'e al
        entities = get_entities(cleaned, clients, key_index)
        truly_bad = [w for w in eng_words if w.lower() not in entities]

        if not truly_bad:
            result.append(cleaned)
            continue

        # Sorunlu paragraf → LLM düzeltmesi
        print(f"    düzeltiliyor: {truly_bad[:5]}{'...' if len(truly_bad) > 5 else ''}")
        fixed = fix_paragraph(cleaned, entities, truly_bad, clients, key_index)
        result.append(fixed)
        fixed_count += 1

    if fixed_count:
        print(f"  {fixed_count} paragraf düzeltildi.")

    return "\n\n".join(result)
