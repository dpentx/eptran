"""
eptran — library_promote.py

eptran'daki book/<slug> PR'ı merge olunca çalışır: library reposundaki
staging/<slug> dalının içeriğini library'nin ana dalına alır, draft
Release'i yayımlar ve staging dalını siler.

NEDEN git merge DEĞİL: aynı serinin iki cildi paralel işlenirse ikisi de
<seri>/index.json'a satır ekler ve düz merge "add/add" çakışması verir.
Bu yüzden cilt klasörünü staging'den KOPYALIYOR, index.json'a ise sadece
o cildin girdisini ekliyoruz (ana daldaki güncel index üzerine).

Kullanım: python scripts/library_promote.py <kitap-slug>
Ortam: GH_TOKEN (library'ye yazma yetkili), LIBRARY_REPO (opsiyonel)
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.library_publish import (  # noqa: E402
    DEFAULT_LIBRARY_REPO, _run, _clone_url, _gh, _load_index, _slug,
)

MAX_ATTEMPTS = 3


def _find_series_dir(work: str, staging_ref: str, book: str) -> str:
    """staging dalındaki <seri>/<kitap>/ klasöründen seri adını bulur."""
    files = _run(["git", "ls-tree", "-r", "--name-only", staging_ref], cwd=work).splitlines()
    for path in files:
        parts = path.split("/")
        if len(parts) == 3 and parts[1] == book and parts[2].endswith(".txt"):
            return parts[0]
    raise RuntimeError(f"{staging_ref} içinde '{book}' klasörü bulunamadı")


def _attempt(repo: str, book: str, tmp: str, n: int) -> str:
    work = os.path.join(tmp, f"lib{n}")
    _run(["git", "clone", _clone_url(repo), work])
    default = _run(["git", "symbolic-ref", "--short", "HEAD"], cwd=work)
    staging_ref = f"origin/staging/{book}"
    _run(["git", "rev-parse", "--verify", staging_ref], cwd=work)  # yoksa hata

    series = _find_series_dir(work, staging_ref, book)

    # 1) Cilt klasörünü staging'den al (ana daldaki eski sürümü önce sil).
    shutil.rmtree(os.path.join(work, series, book), ignore_errors=True)
    _run(["git", "checkout", staging_ref, "--", f"{series}/{book}"], cwd=work)

    # 2) Staging'deki index girdisini ana dalın index'ine ekle/güncelle.
    staged = json.loads(_run(["git", "show", f"{staging_ref}:{series}/index.json"], cwd=work))
    entry = next((c for c in staged.get("ciltler", []) if c.get("slug") == book), None)
    if entry is None:
        raise RuntimeError(f"staging index.json'da '{book}' girdisi yok")
    index_path = os.path.join(work, series, "index.json")
    index = _load_index(index_path, series)
    if staged.get("ad") and staged["ad"] != series:
        index["ad"] = staged["ad"]
    index["ciltler"] = sorted(
        [c for c in index["ciltler"] if c.get("slug") != book] + [entry],
        key=lambda c: c.get("slug", ""))
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # 3) Commit + push (yarışta non-fast-forward olursa baştan dene).
    name = _run(["git", "config", "user.name"], check=False) or "eptran-bot"
    mail = _run(["git", "config", "user.email"], check=False) or "eptran-bot@users.noreply.github.com"
    _run(["git", "add", "-A"], cwd=work)
    if _run(["git", "status", "--porcelain"], cwd=work):
        _run(["git", "-c", f"user.name={name}", "-c", f"user.email={mail}",
              "commit", "-m", f"{book}: kütüphaneye alındı"], cwd=work)
        _run(["git", "push", "origin", f"HEAD:{default}"], cwd=work)
    else:
        print("  library: ana dal zaten güncel.")
    return series


def promote(book_slug: str) -> None:
    repo = os.environ.get("LIBRARY_REPO", DEFAULT_LIBRARY_REPO)
    book = _slug(book_slug)
    tmp = tempfile.mkdtemp(prefix="eptran-promote-")
    try:
        last_err = None
        series = None
        for n in range(1, MAX_ATTEMPTS + 1):
            try:
                series = _attempt(repo, book, tmp, n)
                break
            except RuntimeError as e:
                last_err = e
                print(f"  Deneme {n}/{MAX_ATTEMPTS} başarısız: {e}")
        if series is None:
            raise last_err

        # Release'i yayımla (draft -> published), staging dalını temizle.
        _gh(["release", "edit", book, "--draft=false", "--repo", repo])
        work = os.path.join(tmp, "cleanup")
        _run(["git", "clone", "--depth", "1", _clone_url(repo), work])
        _run(["git", "push", "origin", "--delete", f"staging/{book}"], cwd=work, check=False)
        print(f"  library: {series}/{book} yayımlandı, staging/{book} silindi.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Kullanım: python scripts/library_promote.py <kitap-slug>")
    try:
        promote(sys.argv[1])
    except Exception as e:
        print(f"HATA: {e}")
        sys.exit(1)
