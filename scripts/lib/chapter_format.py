"""
eptran — lib/chapter_format.py

Bir bölüm dosyasının iki biçimi vardır:

  ÇALIŞMA biçimi (pipeline'ın yazdığı; library'de staging/<slug> dalında durur):

      # <orijinal bölüm başlığı>

      <çevrilmiş başlık satırı, ör. "Bölüm 1: ...">

      <paragraf>

  YAYIN biçimi (library'nin ana dalında; okuyucu sitesi ve düzeltme PR'ları bunu görür):

      <başlık>

      <paragraf>

      <paragraf>

İlk satır başlıktır, boş satırdan sonra gövde gelir. Yayın biçimi de çalışma
biçimini okuyan kurallarla (load_txt_chapters) aynen okunabilir; yani dönüşüm
tek yönlü ve tekrar uygulandığında değişmez (idempotent).

Kural kaynağı scripts/convert.py içindeki load_txt_chapters'tir. Burada onun
dosya başına mantığı AYNEN taşınmıştır (convert.py ebooklib/bs4/lxml ister, bu modül
sadece standart kütüphane + lib/chapter_titles). İki kopyanın ayrışmaması için
scripts/tests/test_chapter_format.py ikisini aynı girdilerle karşılaştırır.
"""
import re

from lib.chapter_titles import normalize_title


def _normalize(s: str) -> str:
    return re.sub(r"\W+", "", s.lower())


def parse_chapter(fname: str, content: str) -> tuple:
    """(başlık, gövde) döner. convert.load_txt_chapters'ın tek dosya mantığı."""
    lines = content.split("\n", 2)
    if lines[0].startswith("#"):
        raw_title = lines[0].lstrip("#").strip()
        body_raw = lines[2].strip() if len(lines) > 2 else ""
    else:
        raw_title = fname
        body_raw = content.strip()

    body_lines = body_raw.split("\n", 1)
    first_line = body_lines[0].strip()

    looks_like_chapter_heading = bool(
        re.match(r"^(bölüm|chapter)\s+\S+", first_line, re.IGNORECASE)
    )

    if _normalize(first_line) and _normalize(first_line) == _normalize(raw_title):
        body_raw = body_lines[1].strip() if len(body_lines) > 1 else ""
    elif _normalize(first_line) and len(first_line) < 120 and (
        looks_like_chapter_heading
        or not first_line.endswith((".", "!", "?", "…"))
    ):
        raw_title = first_line
        body_raw = body_lines[1].strip() if len(body_lines) > 1 else ""

    src_header = lines[0].lstrip("#").strip() if lines[0].startswith("#") else ""
    raw_title = normalize_title(raw_title, src_header)
    return raw_title, body_raw


def to_published(fname: str, content: str) -> str:
    """Çalışma (ya da zaten yayın) biçimindeki bölümü yayın biçimine çevirir."""
    title, body = parse_chapter(fname, content)
    return f"{title}\n\n{body}\n"
