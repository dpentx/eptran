"""
eptran — publish_library.py

convert.yml'in son adımı: convert.py bittikten sonra bitmiş kitabı
eptran-library'ye yayımlar (bkz. lib/library_publish.py) ve açılan
tamamlanma PR'ına linkleri yorum olarak ekler.

convert.py'ye dokunmaz; onun fonksiyonlarını import eder. Fail-soft:
herhangi bir hatada sadece uyarı basar (workflow adımı ayrıca
continue-on-error ile çalışır), kitabın PR akışını bozmaz.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from convert import find_original_epub, get_book_metadata, load_txt_chapters  # noqa: E402
from lib.git_utils import current_branch, read_status  # noqa: E402
from lib.library_publish import publish_to_library  # noqa: E402


def _comment_on_pr(branch: str, body: str) -> None:
    try:
        num = subprocess.run(
            ["gh", "pr", "list", "--head", branch, "--state", "open",
             "--json", "number", "--jq", ".[0].number"],
            capture_output=True, text=True).stdout.strip()
        if not num:
            print("  Uyarı: açık PR bulunamadı, yorum eklenmedi.")
            return
        subprocess.run(["gh", "pr", "comment", num, "--body", body],
                       capture_output=True, text=True)
    except Exception as e:  # fail-soft
        print(f"  Uyarı: PR yorumu eklenemedi: {e}")


def main() -> None:
    status = read_status()
    book = status.get("book")
    if not book or status.get("convert_status") != "completed":
        print("publish_library: dönüşüm tamamlanmamış, atlandı.")
        return

    epub = status.get("epub_output") or f"output/{book}/{book}_tr.epub"
    chapters = load_txt_chapters(f"output/{book}")
    title, author = get_book_metadata(book, find_original_epub(book))

    info = publish_to_library(book, chapters, epub, title, author, status.get("series"))
    if not info:
        _comment_on_pr(current_branch(),
                       "⚠️ Library'ye yayın başarısız oldu (bkz. convert workflow logu). "
                       "Çeviri bu PR'da duruyor, kaybolmadı.")
        return

    _comment_on_pr(
        current_branch(),
        f"📚 **Library'ye yayınlandı** ({len(chapters)} bölüm)\n\n"
        f"- Bölümler: {info['branch_url']}\n"
        f"- EPUB (draft release): {info['release_url']}\n\n"
        f"Bu PR merge olunca staging ana dala alınır ve release yayımlanır.")


if __name__ == "__main__":
    main()
