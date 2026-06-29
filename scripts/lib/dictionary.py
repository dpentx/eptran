"""
Kademeli İngilizce kelime sözlüğü.

Lookup sırası:
  1. dictionary/learned_words.json  — kitaba özel öğrenilmiş mini sözlük
     (hızlı, küçük, repo'da version kontrollü)
  2. Büyük İngilizce sözlük (dwyl/english-words, ~370k kelime)
     — ilk ihtiyaçta indirilir, çalışma süresince bellekte tutulur,
       repo'ya commit edilmez (4MB şişirmemek için)

Bir kelime büyük sözlükte bulunursa sonuç mini sözlüğe yazılır —
bir dahaki sefere büyük sözlüğe hiç gidilmez.
"""
import json
import os
import urllib.request

LEARNED_PATH = "dictionary/learned_words.json"
BIG_WORDLIST_URL = (
    "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
)
BIG_WORDLIST_CACHE = "/tmp/eptran_en_words_cache.txt"

# Büyük sözlük bir kez yüklenir, modül seviyesinde tutulur (process ömrü boyunca)
_big_wordlist_set = None
_learned_cache = None


def _load_learned() -> dict:
    """Mini sözlüğü diskten yükle, cache'le."""
    global _learned_cache
    if _learned_cache is not None:
        return _learned_cache
    if os.path.exists(LEARNED_PATH):
        with open(LEARNED_PATH, encoding="utf-8") as f:
            _learned_cache = json.load(f)
    else:
        _learned_cache = {}
    return _learned_cache


def _save_learned() -> None:
    """Mini sözlüğü diske yaz."""
    if _learned_cache is None:
        return
    os.makedirs(os.path.dirname(LEARNED_PATH), exist_ok=True)
    with open(LEARNED_PATH, "w", encoding="utf-8") as f:
        json.dump(_learned_cache, f, ensure_ascii=False, indent=2, sort_keys=True)


def _load_big_wordlist() -> set:
    """
    Büyük İngilizce sözlüğü yükle. Önce /tmp cache'ine bak,
    yoksa indir. Process içinde set olarak tutulur (O(1) lookup).
    """
    global _big_wordlist_set
    if _big_wordlist_set is not None:
        return _big_wordlist_set

    if os.path.exists(BIG_WORDLIST_CACHE):
        print("  Büyük sözlük /tmp cache'inden yükleniyor...")
        with open(BIG_WORDLIST_CACHE, encoding="utf-8") as f:
            _big_wordlist_set = set(line.strip().lower() for line in f if line.strip())
        return _big_wordlist_set

    print("  Büyük İngilizce sözlük indiriliyor (ilk kullanım, ~4MB)...")
    try:
        with urllib.request.urlopen(BIG_WORDLIST_URL, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        with open(BIG_WORDLIST_CACHE, "w", encoding="utf-8") as f:
            f.write(raw)
        _big_wordlist_set = set(
            line.strip().lower() for line in raw.splitlines() if line.strip()
        )
        print(f"  Sözlük yüklendi: {len(_big_wordlist_set)} kelime.")
    except Exception as e:
        print(f"  Uyarı: büyük sözlük indirilemedi ({e}), boş set ile devam.")
        _big_wordlist_set = set()

    return _big_wordlist_set


def is_english_word(word: str) -> bool:
    """
    Kelime İngilizce sözlükte var mı?
    Önce mini (öğrenilmiş) sözlüğe bakar, yoksa büyük sözlüğe düşer,
    sonucu mini sözlüğe yazar.
    """
    wl = word.lower().strip(".,;:!?\"'()[]")
    if not wl or not wl.isalpha():
        return False

    learned = _load_learned()
    if wl in learned:
        return learned[wl]

    big = _load_big_wordlist()
    result = wl in big

    learned[wl] = result
    return result


def mark_known(word: str, is_english: bool = False) -> None:
    """
    Bir kelimeyi mini sözlüğe elle işaretle.
    Örn: özel isimler ve terimler için is_english=False kaydedilir,
    böylece bir dahaki sefere İngilizce sanılmaz.
    """
    wl = word.lower().strip(".,;:!?\"'()[]")
    if not wl:
        return
    learned = _load_learned()
    learned[wl] = is_english


def flush() -> None:
    """Mini sözlükteki birikmiş değişiklikleri diske yaz. Bölüm/dosya sonunda çağrılır."""
    _save_learned()
