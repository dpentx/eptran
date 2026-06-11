"""
Unicode script karışımlarını temizler.
Örn: 'unutسام' → 'unut' (Arapça kısım çıkarılır)
"""
import unicodedata


def _script(ch: str) -> str:
    try:
        name = unicodedata.name(ch, '')
        if 'LATIN' in name:    return 'latin'
        if 'ARABIC' in name:   return 'arabic'
        if 'CYRILLIC' in name: return 'cyrillic'
        if 'GREEK' in name:    return 'greek'
        if 'CJK' in name or 'HIRAGANA' in name or 'KATAKANA' in name:
            return 'cjk'
        return 'other'
    except Exception:
        return 'other'


def clean(text: str) -> str:
    """
    Kelime içi script karışımlarını tespit et, Latin olmayan kısımları at.
    Tamamen yabancı script olan bozuk kelimeler sessizce atlanır.
    """
    words = text.split(' ')
    result = []
    for word in words:
        if len(word) < 2:
            result.append(word)
            continue

        scripts = {_script(ch) for ch in word if ch.isalpha()}
        if len(scripts) <= 1:
            result.append(word)
            continue

        # Mixed script: latin olmayan alfabetik karakterleri at
        latin_only = ''.join(
            ch for ch in word
            if not ch.isalpha() or _script(ch) == 'latin'
        )
        if latin_only.strip():
            result.append(latin_only)
            print(f"    unicode temizlendi: '{word}' → '{latin_only}'")
        # Hiç Latin yoksa kelimeyi tamamen atla

    return ' '.join(result)
