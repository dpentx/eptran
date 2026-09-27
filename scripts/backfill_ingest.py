"""
Tek seferlik (ama tekrar tekrar güvenle çalıştırılabilir) backfill scripti.

eptran-web'e gönderim mekanizması (convert.py'nin sonundaki push_book
çağrısı) PR #19 ile eklendi — ama bu, SADECE o tarihten SONRA convert
edilen kitaplar için geçerli. main'de zaten önceden tamamlanmış, ama
hiçbir zaman eptran-web'e gönderilmemiş kitaplar var (bkz. output/*/*.epub).
Bu script main'deki her tamamlanmış kitabı tek tek tarayıp push_book()
ile eptran-web'e gönderir.

NOT (Eylül 2026): İlk sürüm epub gönderiyordu, Vercel'in ~4.5MB istek
sınırına tosladı (413). Artık convert.py'nin kendisiyle AYNI yolu
kullanıyor: her kitabın output/<slug>/*.txt bölüm dosyalarını
load_txt_chapters() ile ayrıştırıp format=txt olarak gönderiyor —
bkz. lib/web_ingest.py'nin kendi notu.

Idempotent: aynı kitabı ikinci kez göndermek zararsız — ingest.ts aynı
sourceKey'i güncelleme (upsert) olarak işliyor, kopya novel oluşmuyor.
"""
import os

from lib.web_ingest import push_book
from convert import get_book_metadata, load_txt_chapters


def find_completed_books(output_root="output"):
    books = []
    if not os.path.isdir(output_root):
        return books
    for slug in sorted(os.listdir(output_root)):
        book_dir = os.path.join(output_root, slug)
        if not os.path.isdir(book_dir):
            continue
        epub_path = os.path.join(book_dir, f"{slug}_tr.epub")
        if os.path.exists(epub_path):
            books.append((slug, book_dir))
    return books


def main():
    books = find_completed_books()
    if not books:
        print("output/ altında ciltlenmiş epub bulunamadı.")
        return

    print(f"{len(books)} tamamlanmış kitap bulundu: {', '.join(b[0] for b in books)}")
    print()

    for slug, book_dir in books:
        original_epub_path = f"input/.originals/{slug}.epub"
        if not os.path.exists(original_epub_path):
            original_epub_path = None
        title, author = get_book_metadata(slug, original_epub_path)
        chapters = load_txt_chapters(book_dir)
        print(f"→ {slug}  (\"{title}\"{f' — {author}' if author else ''}, "
              f"{len(chapters)} bölüm)")
        push_book(slug, chapters, title, author)
        print()


if __name__ == "__main__":
    main()
