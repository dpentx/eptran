"""
Türkçe çeviride kalmış İngilizce kelimeleri tespit eder.
Türkçe eklerle biten veya whitelist'teki kelimeler atlanır.
"""
import re

# Türkçede yaygın kullanılan yabancı kökenli ama kabul görmüş kelimeler
_WHITELIST = {
    'olan', 'veya', 'için', 'gibi', 'bile', 'daha', 'kadar', 'beri',
    'önce', 'sonra', 'ancak', 'fakat', 'lakin', 'iken', 'yani', 'hatta',
    'zaten', 'artık', 'ise', 'ama', 'televizyon', 'telefon', 'internet',
    'bilgisayar', 'organizasyon', 'motivasyon', 'pozisyon', 'koleksiyon',
    'prodüksiyon', 'üniversite', 'enstitü', 'akademi',
}

# Türkçe çekim ekleri — bu eklerle biten Latin harfli kelimeler Türkçedir
_TR_SUFFIX_RE = re.compile(
    r'(ları|leri|ında|inde|dan|den|lar|ler|ını|ini|'
    r'ına|ine|nın|nin|nun|nün|daki|deki|taki|teki|'
    r'ydı|ydi|ydık|ydınız|ydılar|mış|miş|muş|müş)$'
)

_WORD_RE = re.compile(r'\b[a-zA-Z]{3,}\b')


def find(paragraph: str) -> list:
    """
    Paragraftaki çevrilmemiş İngilizce kelimeleri döndür.
    Whitelist ve Türkçe ek kontrolünden geçirilir.
    """
    candidates = _WORD_RE.findall(paragraph)
    result = []
    for w in candidates:
        wl = w.lower()
        if wl in _WHITELIST:
            continue
        if _TR_SUFFIX_RE.search(wl):
            continue
        result.append(w)
    return result
