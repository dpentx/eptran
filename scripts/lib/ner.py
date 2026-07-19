"""
Named Entity Recognition — iki ayrı kullanım:

1. extract_from_source(kaynak_metin):
   Çeviri ÖNCESINDE kaynak (İngilizce) metinden özel isimleri çıkarır.
   Bölüm başına 1 LLM çağrısı. Sonuç hafızaya eklenir ve translate
   prompt'una "şu kelimeleri çevirme" olarak geçilir.

2. fix_text(çevrilmiş_metin, whitelist):
   Review sırasında çevrilmiş metindeki İngilizce kalanları tarar.
   NER çağrısı YAPILMAZ — whitelist olarak hafızadaki isimler kullanılır.
   Sadece sorunlu paragraflar fix_paragraph() ile LLM'e gönderilir.
"""
import time

from . import groq_client as gc
from . import unicode_cleaner
from . import english_detector
from . import boilerplate

# ── Kaynak metin NER (çeviri öncesi) ─────────────────────────────────────────

_SOURCE_NER_SYSTEM = (
    "Sana verilen İngilizce metindeki özel isimleri listele: "
    "kişi adları, yer adları, kurum/organizasyon adları, kitap/eser adları, "
    "unvanlar, takma adlar. "
    "Her ismi yeni satıra yaz. Sadece listeyi döndür, açıklama ekleme. "
    "Eğer özel isim yoksa boş satır döndür."
)


def representative_sample(text: str, max_chars: int = 16000) -> str:
    """
    Metnin TAMAMINI göndermek yerine, baştan/ortadan/sondan temsili
    parçalar alarak yeterince kapsamlı ama sınırlı boyutlu bir örnek
    oluşturur.

    ÖNEMLİ (Temmuz 2026): Eskiden burada sadece ilk N karakter alınıyordu
    ("ilk 6000 karakter yeterli, önemli isimler erken geçer" varsayımıyla)
    — bu, tek chunk'lık kısa bölümlerde doğruydu ama artık bölümler
    4-5k kelimelik parçalara ayrılıp uzun bölümler 5-6 parçaya kadar
    çıkabiliyor (25-30k+ karakter). Sadece başı taramak, bölümün
    ortasında ya da sonunda tanıtılan bir karakteri/terimi tamamen
    kaçırıyordu. reasoning_effort=low ile token bütçesi rahatladığı için
    artık baş+orta+son örneklemeyi karşılayabiliyoruz.
    """
    if len(text) <= max_chars:
        return text
    part = max_chars // 3
    start = text[:part]
    mid_point = len(text) // 2
    middle = text[mid_point - part // 2: mid_point + part // 2]
    end = text[-part:]
    return f"{start}\n\n[...]\n\n{middle}\n\n[...]\n\n{end}"


def extract_from_source(source_text: str, clients: list, key_index: list) -> set:
    """
    Kaynak (İngilizce) metinden özel isimleri çıkar.
    Bölüm başına 1 kez çağrılır, hafızaya eklenir.
    Küçük harf set döner.
    """
    sample = representative_sample(source_text)
    result = gc.call(clients, key_index, _SOURCE_NER_SYSTEM, sample, temperature=0.1)
    time.sleep(1)

    entities = set()
    for line in (result or "").splitlines():
        name = line.strip().strip('-').strip('•').strip()
        if not name:
            continue
        entities.add(name.lower())
        # Çok kelimeli isimlerin her kelimesini de ekle
        for word in name.split():
            if len(word) > 2:
                entities.add(word.lower())
    return entities


def build_protected_str(memory: dict, extra_entities: set = None) -> str:
    """
    Hafızadaki karakter + terim isimlerini ve varsa ek entity'leri
    translate prompt'una eklenecek formata dönüştür.
    """
    protected = set()

    # Hafızadaki karakter ve terim anahtarları (İngilizce orijinal isimler)
    for eng_name in memory.get("characters", {}).keys():
        protected.add(eng_name)
        for word in eng_name.split():
            if len(word) > 2:
                protected.add(word)

    for eng_term in memory.get("terms", {}).keys():
        protected.add(eng_term)

    if extra_entities:
        protected.update(extra_entities)

    if not protected:
        return ""

    names = ", ".join(sorted(protected))
    return f"Aşağıdaki özel isim ve terimleri Türkçeye ÇEVİRME, olduğu gibi bırak: {names}"


# ── Review tarayıcı (çeviri sonrası, NER'siz) ────────────────────────────────

_FIX_SYSTEM = (
    "Sen profesyonel bir Türkçe editör ve çevirmensin. "
    "Sana verilen paragrafta bazı kelimeler İngilizce kalmış veya bozuk çevrilmiş. "
    "Korunması gereken özel isimler ayrıca belirtilecek — onlara dokunma. "
    "Paragrafı doğal, akıcı Türkçeye çevir/düzelt. "
    "SADECE düzeltilmiş paragrafı döndür, açıklama ekleme."
)


def _build_whitelist(memory: dict) -> set:
    """
    Hafızadaki karakter ve terim isimlerinden whitelist oluştur.
    NER çağrısı yapılmaz — hafıza yeterli.
    """
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
    if result is None:
        print("    Uyarı: düzeltme alınamadı (model boş yanıt), paragraf orijinal haliyle korunuyor.")
        return paragraph
    return result


def fix_text(text: str, clients: list, key_index: list, memory: dict = None) -> str:
    """
    Review aşamasında çevrilmiş metni tara:
    1. Unicode temizle
    2. İngilizce kelime tespit et
    3. Hafızadaki whitelist ile karşılaştır (NER çağrısı YOK)
    4. Whitelist dışında sorun varsa paragrafı fix_paragraph ile düzelt
    """
    whitelist = _build_whitelist(memory) if memory else set()
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

        # Unicode temizle
        cleaned = unicode_cleaner.clean(para)

        # İngilizce kelime tespiti
        eng_words = english_detector.find(cleaned)
        if not eng_words:
            result.append(cleaned)
            continue

        # Whitelist dışında sorun var mı?
        truly_bad = [w for w in eng_words if w.lower() not in whitelist]
        if not truly_bad:
            result.append(cleaned)
            continue

        # Sorunlu paragraf → LLM düzeltmesi
        print(f"    düzeltiliyor: {truly_bad[:5]}{'...' if len(truly_bad) > 5 else ''}")
        fixed = fix_paragraph(cleaned, whitelist, truly_bad, clients, key_index)
        result.append(fixed)
        fixed_count += 1

    if fixed_count:
        print(f"  {fixed_count} paragraf düzeltildi.")

    return "\n\n".join(result)
