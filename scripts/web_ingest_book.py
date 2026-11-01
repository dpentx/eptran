"""
eptran — web_ingest_book.py

Bir kitabı (output/<slug>/*.txt) eptran-web'e (okuyucu sitesi) gönderir.
book/<slug> PR'ı MERGE EDİLİNCE .github/workflows/web-ingest-on-merge.yml
tarafından main'in o anki halinden çalıştırılır — böylece onaylanmamış
(reddedilebilecek) çeviriler sitede yayınlanmaz. convert.py'deki push_book()
çağrısı book/* dalında artık ertelenir (bkz. lib/web_ingest.py).

Elle de çalıştırılabilir (repo kökünden, main'de):
  WEB_INGEST_URL=... WEB_INGEST_SECRET=... python scripts/web_ingest_book.py knh-15

Ortam: WEB_INGEST_URL, WEB_INGEST_SECRET.
Fail-soft DEĞİL: kitap bulunamazsa sıfır olmayan kodla çıkar (workflow'da
görünsün diye), ağ hataları ise push_book'un kendi uyarısıyla yutulur.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import convert  # noqa: E402  (load_txt_chapters / get_book_metadata burada)
from lib.web_ingest import push_book  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("Kullanım: python scripts/web_ingest_book.py <kitap-slug>")
        return 2
    slug = sys.argv[1]
    output_dir = os.path.join("output", slug)

    if not os.path.isdir(output_dir):
        print(f"Hata: {output_dir} yok — kitap bu dalda bulunamadı.")
        return 1

    chapters = convert.load_txt_chapters(output_dir)
    if not chapters:
        print(f"Hata: {output_dir} içinde bölüm (.txt) yok.")
        return 1

    original = convert.find_original_epub(slug)
    title, author = convert.get_book_metadata(slug, original)
    print(f"{slug}: {len(chapters)} bölüm, başlık={title!r}, yazar={author!r}")
    push_book(slug, chapters, title, author)
    return 0


if __name__ == "__main__":
    sys.exit(main())
