"""
Named Entity Recognition (çeviri ÖNCESİ).

extract_from_source(kaynak_metin):
   Kaynak (İngilizce) metinden özel isimleri çıkarır. Bölüm başına 1 LLM
   çağrısı. Sonuç hafızaya eklenir ve translate prompt'una "şu kelimeleri
   çevirme" olarak geçilir (bkz. build_protected_str).

NOT (Ekim 2026): Eskiden burada çeviri SONRASI İngilizce kalıntı tarayan
fix_text/fix_paragraph/_build_whitelist da vardı; bunların yerini
review_fix.py aldı ve hiçbir yerden çağrılmıyorlardı, kaldırıldı.
"""
import time

from . import groq_client as gc

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
