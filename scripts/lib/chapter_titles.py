"""
Bölüm başlıklarını TEK bir şablona oturtur.

Şablon:   "Bölüm N: Başlık"   (başlık yoksa sadece "Bölüm N")
Özel:     Prolog, Epilog, Ara Bölüm, Sonsöz, Önsöz  ("Prolog: Başlık" gibi)

NEDEN (Ekim 2026, kullanıcı geri bildirimi): Model, bölüm başlığını çevirirken
bazen "Bölüm 12: ...", bazen "Chapter 12: ..." yazıyordu; ayrıca ayraç ve
büyük/küçük harf da değişiyordu. Bunu prompt'la değil, KODLA çözüyoruz —
model ne yazarsa yazsın çıktı hep aynı biçimde olur.

Dosya biçimi DEĞİŞMİYOR: "# <kaynak başlık>\\n\\n<Türkçe başlık>\\n\\n<gövde>".
Sadece ikinci paragraf (Türkçe başlık) normalleştirilir; ilk satır kaynağın
orijinal başlığı olarak kalır (pr_check/qa_audit boilerplate kontrolü ona bakıyor).
"""
import re

_UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
         "seventy": 70, "eighty": 80, "ninety": 90}

# "Chapter Twenty-One" -> 21 (İngilizce sayı sözcükleri, 0-99)
_NUM_WORD = (
    r"(?:(?:" + "|".join(_TENS) + r")(?:[-\s](?:" + "|".join(_UNITS) + r"))?"
    r"|" + "|".join(sorted(_UNITS, key=len, reverse=True)) + r")"
)
_NUM = rf"(?P<num>\d+|{_NUM_WORD})"
_SEP = r"\s*[:：\-–—.]?\s*"

_NUMBERED = re.compile(
    rf"^\s*(?:chapter|bölüm)\s+{_NUM}\b{_SEP}(?P<sub>.*)$", re.IGNORECASE
)

# (regex, Türkçe karşılık)
_SPECIAL = [
    (re.compile(rf"^\s*(?:prologue|prolog)\b{_SEP}(?P<sub>.*)$", re.IGNORECASE), "Prolog"),
    (re.compile(rf"^\s*(?:epilogue|epilog)\b{_SEP}(?P<sub>.*)$", re.IGNORECASE), "Epilog"),
    (re.compile(rf"^\s*(?:interlude|ara\s+bölüm)\b{_SEP}(?P<sub>.*)$", re.IGNORECASE), "Ara Bölüm"),
    (re.compile(rf"^\s*(?:afterword|sonsöz)\b{_SEP}(?P<sub>.*)$", re.IGNORECASE), "Sonsöz"),
    (re.compile(rf"^\s*(?:foreword|preface|önsöz)\b{_SEP}(?P<sub>.*)$", re.IGNORECASE), "Önsöz"),
]


def _to_int(num: str):
    num = num.lower()
    if num.isdigit():
        return int(num)
    parts = re.split(r"[-\s]+", num)
    if len(parts) == 1:
        return _TENS.get(parts[0], _UNITS.get(parts[0]))
    if len(parts) == 2 and parts[0] in _TENS and parts[1] in _UNITS:
        return _TENS[parts[0]] + _UNITS[parts[1]]
    return None


def _clean_sub(sub: str) -> str:
    sub = sub.strip().strip("*_").strip()
    # Başlığı saran tırnaklar / baştaki ayraç artıkları
    sub = re.sub(r'^[\s:：\-–—.]+', '', sub)
    if len(sub) >= 2 and sub[0] in "\"'“”‘’" and sub[-1] in "\"'“”‘’":
        sub = sub[1:-1].strip()
    return sub


def parse(line: str):
    """
    Bir başlık satırını ayrıştırır. Döner: (kind, number, subtitle) ya da None.
      kind: "chapter" | "Prolog" | "Epilog" | "Ara Bölüm" | "Sonsöz" | "Önsöz"
    Başlık kalıbına uymayan her şey için None (örn. normal bir cümle).
    """
    if not line:
        return None
    line = line.strip().lstrip("#").strip()
    m = _NUMBERED.match(line)
    if m:
        n = _to_int(m.group("num"))
        if n is not None:
            return ("chapter", n, _clean_sub(m.group("sub")))
    for rx, tr in _SPECIAL:
        m = rx.match(line)
        if m:
            return (tr, None, _clean_sub(m.group("sub")))
    return None


def render(kind: str, number, subtitle: str) -> str:
    head = f"Bölüm {number}" if kind == "chapter" else kind
    return f"{head}: {subtitle}" if subtitle else head


def normalize_title(line: str, source_title: str = "") -> str:
    """
    Tek bir başlık satırını şablona çevirir. Başlık kalıbına uymuyorsa
    (ör. "* * *", "Çevirmen Notları") satırı DOKUNMADAN geri döner.

    source_title verilirse ve numara taşıyorsa, numara ONDAN alınır —
    model numarayı yanlış yazmış olsa bile kaynak doğru kabul edilir.
    """
    p = parse(line)
    if p is None:
        return line.strip()
    kind, number, sub = p
    if kind == "chapter":
        sp = parse(source_title) if source_title else None
        if sp and sp[0] == "chapter" and sp[1] is not None:
            number = sp[1]
    return render(kind, number, sub)


def _safe_translate(translate_fn, subtitle: str) -> str:
    """Alt başlığı çevirir; herhangi bir hata/saçma çıktıda "" döner (güvenli)."""
    if not translate_fn or not subtitle:
        return ""
    try:
        out = translate_fn(subtitle) or ""
    except Exception:
        return ""
    out = out.strip().splitlines()[0].strip() if out.strip() else ""
    out = _clean_sub(out.rstrip(".").strip())
    if not out or len(out) > max(60, 3 * len(subtitle)):
        return ""
    return out


def _looks_like_bare_title(line: str) -> bool:
    """Kısa, harf içeren ve cümle gibi bitmeyen satır (ör. "Sonbahar")."""
    line = line.strip()
    return (0 < len(line) <= 60 and any(c.isalpha() for c in line)
            and not line.endswith((".", "!", "?", "…", ",", ";", ":", "”", "\""))
            and line[0] not in "\"“‘'")


def enforce_title_line(source_title: str, translation: str, translate_fn=None):
    """
    Çevrilmiş metnin ilk satırını (modelin yazdığı başlığı) şablona oturtur.
    Döner: (yeni_metin, uyarı_ya_da_None).

      - İlk satır başlık kalıbına uyuyorsa: şablona çevrilir.
      - Model başlığı HİÇ yazmamışsa (gerçek veride sık: knh-15'te 24
        bölümün 7'si) ve kaynak başlığı bölüm/prolog vb. ise, kaynaktan
        türetilen başlık BAŞA EKLENİR. Alt başlık translate_fn ile çevrilir
        (verilmediyse ya da başarısız olursa sadece "Bölüm N").
      - Numarasız özel bölümlerde (Epilogue → "Sonbahar") kısa, başlık-gibi
        ilk satır alt başlık sayılır: "Epilog: Sonbahar".
      - Kaynak başlığı da kalıba uymuyorsa (ör. "* * *"): metne dokunulmaz.
    """
    text = translation.lstrip("\n")
    first, _, rest = text.partition("\n")
    rest = rest.lstrip("\n")
    sp = parse(source_title) if source_title else None

    if parse(first) is not None:
        return normalize_title(first, source_title) + ("\n\n" + rest if rest else ""), None

    if sp is None:
        return translation, None

    kind, number, src_sub = sp

    if kind != "chapter" and _looks_like_bare_title(first):
        return render(kind, number, first.strip()) + ("\n\n" + rest if rest else ""), None

    tr_sub = _safe_translate(translate_fn, src_sub)
    derived = render(kind, number, tr_sub)
    warn = (f"model başlık satırını atlamış, '{derived}' eklendi "
            f"(kaynak: {source_title!r})")
    return derived + "\n\n" + text, warn


if __name__ == "__main__":
    cases = [
        ("Chapter 12: The Selection Exam", "Bölüm 12: The Selection Exam"),
        ("BÖLÜM 3 - Seçme Sınavı", "Bölüm 3: Seçme Sınavı"),
        ("Bölüm 7", "Bölüm 7"),
        ("chapter twenty-one: Kış", "Bölüm 21: Kış"),
        ("Chapter 5. Ay Işığı", "Bölüm 5: Ay Işığı"),
        ("Bölüm 9: “Gece Yarısı”", "Bölüm 9: Gece Yarısı"),
        ("Prologue", "Prolog"),
        ("Epilogue: After", "Epilog: After"),
        ("Interlude: Ay", "Ara Bölüm: Ay"),
        ("Ara Bölüm", "Ara Bölüm"),
        ("Afterword", "Sonsöz"),
        ("* * *", "* * *"),
        ("Çevirmen Notları", "Çevirmen Notları"),
        ("Chapter Notes on a Scandal", "Chapter Notes on a Scandal"),  # sayı yok -> dokunma
        ("Bölüm sonu geldi.", "Bölüm sonu geldi."),
    ]
    for src, want in cases:
        got = normalize_title(src)
        assert got == want, (src, got, want)
    # numara kaynaktan gelir
    assert normalize_title("Bölüm 13: X", "Chapter 12: Y") == "Bölüm 12: X"
    # başlık satırı atlanmışsa eklenir
    out, w = enforce_title_line("Chapter 4: The Fox", "Vurucu güneş...\n\nİkinci paragraf")
    assert out.startswith("Bölüm 4\n\nVurucu") and w, (out, w)
    # eksik başlık + alt başlık çevirisi
    out, w = enforce_title_line("Chapter 4: The Fox", "Vurucu güneş...", translate_fn=lambda s: '"Tilki".')
    assert out == "Bölüm 4: Tilki\n\nVurucu güneş...", out
    # çeviri fonksiyonu patlarsa / saçmalarsa güvenli geri dönüş
    def boom(_): raise RuntimeError("rate limit")
    out, w = enforce_title_line("Chapter 4: The Fox", "Metin.", translate_fn=boom)
    assert out == "Bölüm 4\n\nMetin.", out
    out, w = enforce_title_line("Chapter 4: The Fox", "Metin.", translate_fn=lambda s: "x " * 80)
    assert out == "Bölüm 4\n\nMetin.", out
    # numarasız özel bölüm: kısa başlık-gibi ilk satır alt başlık olur
    out, w = enforce_title_line("Epilogue", "Sonbahar\n\nYapraklar döküldü.")
    assert out == "Epilog: Sonbahar\n\nYapraklar döküldü." and w is None, out
    # ...ama normal bir cümle başlık sanılmaz
    out, w = enforce_title_line("Epilogue", "Yapraklar döküldü.\n\nSonra.")
    assert out.startswith("Epilog\n\nYapraklar") and w, out
    out, w = enforce_title_line("Chapter 4: The Fox", "Chapter 4: Tilki\n\nMetin")
    assert out == "Bölüm 4: Tilki\n\nMetin" and w is None, out
    out, w = enforce_title_line("* * *", "Metin burada.")
    assert out == "Metin burada." and w is None
    print("chapter_titles: tüm testler geçti")
