"""
Review aşaması İngilizce kalıntı düzelticisi.

Önceki tasarımdaki hata: review'da paragraf başına NER LLM çağrısı
yapılıyordu, bu hem yavaş hem de gereksizdi. Bu modül NER çağrısı
YAPMAZ — sadece:
  1. Sözlük destekli english_detector.find() ile gerçek İngilizce
     kelimeleri tespit eder (Türkçe'yi İngilizce sanma sorunu artık
     sözlük katmanıyla çözüldü)
  2. Hafızadaki (memory.json) characters + terms anahtarlarını
     whitelist olarak kullanır (translate aşamasında zaten NER
     yapılmıştı, sonucu hafızada duruyor)
  3. Whitelist dışında kalan gerçek sorunlu kelimeler varsa
     paragrafı LLM'e gönderip düzeltir

Yani review'da hiçbir ekstra NER çağrısı yok — sadece var olan
hafızayı whitelist olarak kullanıp gerekirse fix_paragraph çağırır.
"""
import time

from . import groq_client as gc
from . import boilerplate
from . import unicode_cleaner
from . import english_detector
from . import dictionary

_FIX_SYSTEM = (
    "Sen profesyonel bir Türkçe editör ve çevirmensin. "
    "Sana verilen paragrafta bazı kelimeler İngilizce kalmış veya bozuk çevrilmiş. "
    "Korunması gereken özel isimler ayrıca belirtilecek — onlara dokunma. "
    "Paragrafı doğal, akıcı Türkçeye çevir/düzelt. "
    "SADECE düzeltilmiş paragrafı döndür, açıklama ekleme."
)


def _build_whitelist(memory: dict) -> set:
    """Hafızadaki karakter ve terim isimlerinden whitelist oluştur (LLM çağrısı yok)."""
    whitelist = set()
    for eng_name, tr_name in memory.get("characters", {}).items():
        whitelist.add(eng_name.lower())
        whitelist.add(tr_name.lower())
        for word in eng_name.split() + tr_name.split():
            if len(word) > 2:
                whitelist.add(word.lower())
    for eng_term, tr_term in memory.get("terms", {}).items():
        whitelist.add(eng_term.lower())
        whitelist.add(tr_term.lower())
        for word in eng_term.split() + tr_term.split():
            if len(word) > 2:
                whitelist.add(word.lower())
    return whitelist


def fix_paragraph(paragraph: str, whitelist: set,
                  bad_words: list, clients: list, key_index: list) -> str:
    """Sorunlu paragrafı LLM'e gönder, düzeltilmiş halini al."""
    protected_str = ", ".join(sorted(whitelist)) if whitelist else "yok"
    user_msg = (
        f"Korunacak isimler ve terimler: {protected_str}\n"
        f"Düzeltilmesi gereken kelimeler: {', '.join(bad_words)}\n\n"
        f"Paragraf:\n{paragraph}"
    )
    result = gc.call(clients, key_index, _FIX_SYSTEM, user_msg)
    time.sleep(1)
    return result


def fix_text(text: str, clients: list, key_index: list, memory: dict) -> str:
    """
    Review aşamasında çevrilmiş metni tara:
    1. Unicode temizle (mixed-script bozuk tokenlar)
    2. Sözlük destekli İngilizce kelime tespiti (heuristic + dictionary)
    3. Hafızadaki whitelist ile karşılaştır (NER çağrısı YOK)
    4. Whitelist dışında sorun varsa paragrafı fix_paragraph ile düzelt
    """
    whitelist = _build_whitelist(memory)
    paragraphs = text.split("\n\n")
    result = []
    fixed_count = 0

    for para in paragraphs:
        stripped = para.strip()

        if stripped.startswith("[EPUB_IMAGE:") or stripped.startswith("#"):
            result.append(para)
            continue

        if boilerplate.is_boilerplate(stripped):
            print(f"    boilerplate atlandı: {stripped[:60]}...")
            continue

        cleaned = unicode_cleaner.clean(para)

        # Sözlük destekli tespit — artık Türkçe'yi İngilizce sanmıyor
        eng_words = english_detector.find(cleaned)
        if not eng_words:
            result.append(cleaned)
            continue

        truly_bad = [w for w in eng_words if w.lower() not in whitelist]
        if not truly_bad:
            result.append(cleaned)
            continue

        print(f"    düzeltiliyor: {truly_bad[:5]}{'...' if len(truly_bad) > 5 else ''}")
        fixed = fix_paragraph(cleaned, whitelist, truly_bad, clients, key_index)
        result.append(fixed)
        fixed_count += 1

    if fixed_count:
        print(f"  {fixed_count} paragraf düzeltildi.")

    # Bu dosyanın taraması bitti — öğrenilen kelimeleri diske yaz
    dictionary.flush()

    return "\n\n".join(result)
