"""
Sağlayıcı, telif ve lisans metinlerini tespit edip temizler.
translate.py ve review.py tarafından ortak kullanılır.
"""
import re

_PATTERNS = [
    re.compile(r'©|copyright|\ball rights reserved\b|isbn[\s:]\d', re.IGNORECASE),
    re.compile(r'project gutenberg|gutenberg\.org|www\.gutenberg', re.IGNORECASE),
    re.compile(r'epubbooks?\.com|www\.[a-z0-9\-]+\.[a-z]{2,}', re.IGNORECASE),
    re.compile(r'\bebook\s*#?\d+\b', re.IGNORECASE),
    re.compile(r"^(translator'?s?\s*note|note from the translator|çevirmen\s*notu)\b", re.IGNORECASE),
    re.compile(r'bu (yayın|e[\-\s]?kitap).{0,60}(telif|lisans|hak)', re.IGNORECASE),
    re.compile(r"this e[\-\s]?book is for the use of", re.IGNORECASE),
    re.compile(r'(ilk olarak|first published|originally published).{0,60}\d{4}', re.IGNORECASE),
    re.compile(r'^\s*(the\s+)?full\s+project\s+gutenberg', re.IGNORECASE),
    re.compile(r'(limited warranty|indemnity|disclaimer of|distribution of this)', re.IGNORECASE),
    re.compile(r'(1\.e\.\d|1\.f\.\d|section \d+\.)', re.IGNORECASE),
    re.compile(r'(tam lisans|lisans koşulları|garanti reddi|sorumluluk reddi)', re.IGNORECASE),
    re.compile(r'(bağış|vakf[ıa]|elektronik çalışma).{0,60}(hak|lisans|koşul)', re.IGNORECASE),
]

# Lisans bloğu başlangıcını kesen regex
_LICENSE_BLOCK_RE = re.compile(
    r'\n\n.*?(tam lisans|full project gutenberg|start:? full license|'
    r'please read this before|1\.e\.\d|garanti reddi).*',
    re.IGNORECASE | re.DOTALL
)


def is_boilerplate(text: str) -> bool:
    """Metin tamamen boilerplate/lisans içeriği mi?"""
    t = text.strip()
    if not t:
        return True
    for pat in _PATTERNS:
        if pat.search(t):
            return True
    return False


def clean(text: str) -> str:
    """
    Metinden boilerplate paragraflarını ve lisans bloklarını kaldır.
    Gutenberg lisansları genellikle metnin sonunda blok halinde gelir,
    başlangıç noktasından itibaren tamamı kesilir.
    """
    text = _LICENSE_BLOCK_RE.sub('', text)
    paragraphs = text.split("\n\n")
    cleaned = [p for p in paragraphs if not is_boilerplate(p)]
    return "\n\n".join(cleaned).strip()
