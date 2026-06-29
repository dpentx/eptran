"""
Türkçe çeviride kalmış İngilizce kelimeleri tespit eder.

İki katmanlı kontrol:
  1. Heuristic — Türkçe ekler ve whitelist (hızlı ön filtre)
  2. Sözlük — kelime gerçekten İngilizce sözlükte var mı (kesin doğrulama)

Bir kelime ancak HER İKİ katmandan da "İngilizce" sinyali alırsa
sonuca dahil edilir. Bu, Türkçe kelimelerin (örn. "bir", "her", "geliyor")
yanlışlıkla İngilizce sanılmasını önler — çünkü onlar sözlük katmanında
elenir.
"""
import re

from . import dictionary

# Türkçede yaygın kullanılan yabancı kökenli ama kabul görmüş kelimeler
_WHITELIST = {
    'olan', 'veya', 'için', 'gibi', 'bile', 'daha', 'kadar', 'beri',
    'önce', 'sonra', 'ancak', 'fakat', 'lakin', 'iken', 'yani', 'hatta',
    'zaten', 'artık', 'ise', 'ama', 'televizyon', 'telefon', 'internet',
    'bilgisayar', 'organizasyon', 'motivasyon', 'pozisyon', 'koleksiyon',
    'prodüksiyon', 'üniversite', 'enstitü', 'akademi',
    # Çok yaygın kısa Türkçe kelimeler — bazıları tesadüfen büyük
    # İngilizce sözlükte de geçiyor (örn. "ben" İngilizce isim, "her"
    # İngilizce zamir, "hasta" İspanyolca kökenli İngilizce ifade).
    # Bunlar Türkçede o kadar sık kullanılır ki yanlış pozitif riski
    # gerçek kazanımdan çok daha yüksek.
    'ben', 'sen', 'biz', 'siz', 'her', 'bir', 'beni', 'seni', 'bizi',
    'sizi', 'benim', 'senin', 'bizim', 'sizin', 'ona', 'onu', 'ondan',
    'hasta', 'can', 'son', 'baba', 'ana', 'kara', 'sol', 'sağ', 'al',
    'var', 'yok', 'çok', 'az', 'tam', 'düz', 'in', 'on', 'el', 'göz',
}

# Türkçe çekim ekleri — bu eklerle biten Latin harfli kelimeler Türkçedir.
# Liste geniş tutuldu çünkü büyük İngilizce sözlük (370k kelime) çok
# büyük olduğu için kısa Türkçe kelimeler bile tesadüfen eşleşebiliyor
# (örn. "zaman", "kalan"). Ek kontrolü asıl güvenilir filtre.
_TR_SUFFIX_RE = re.compile(
    r'(ları|leri|ında|inde|dan|den|lar|ler|ını|ini|'
    r'ına|ine|nın|nin|nun|nün|daki|deki|taki|teki|'
    r'ydı|ydi|ydık|ydınız|ydılar|mış|miş|muş|müş|'
    r'yor|acak|ecek|malı|meli|dır|dir|dur|dür|'
    # Fiil çekimleri / ortaçlar
    r'an|en|arak|erek|ip|up|üp|ken|dıkça|dikçe|'
    r'madan|meden|asıya|esiye|'
    # İyelik + hal ekleri
    r'sı|si|su|sü|nı|ni|nu|nü|ya|ye|da|de|ta|te'
    r')$'
)

_WORD_RE = re.compile(r'\b[a-zA-Z]{4,}\b')


def _passes_heuristic(word_lower: str) -> bool:
    """İlk katman: Türkçe ek/whitelist kontrolünden GEÇMEYEN (yani şüpheli) kelime mi?"""
    if word_lower in _WHITELIST:
        return False
    if _TR_SUFFIX_RE.search(word_lower):
        return False
    return True


def find(paragraph: str) -> list:
    """
    Paragraftaki çevrilmemiş İngilizce kelimeleri döndür.
    Heuristic + sözlük kombinasyonu kullanılır — ikisi de onaylamazsa
    kelime sonuca dahil edilmez (yanlış pozitifi azaltır).
    """
    candidates = _WORD_RE.findall(paragraph)
    result = []
    for w in candidates:
        wl = w.lower()

        # Katman 1: heuristic ön filtre
        if not _passes_heuristic(wl):
            continue

        # Katman 2: sözlük doğrulaması
        if dictionary.is_english_word(wl):
            result.append(w)

    return result
