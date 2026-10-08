"""
eptran — lib/library_publish.py

Biten bir kitabı ayrı "eptran-library" reposuna yayımlar:

  * Bölüm metinleri  -> <seri>/<kitap>/NNN.txt   (staging/<kitap> dalı)
  * <seri>/index.json -> kitap girdisi (başlık, bölüm sayısı, epub linki)
  * Ciltlenmiş epub  -> library reposunda DRAFT Release (tag = kitap slug'ı)

Ana repoya (eptran) büyük dosya sokmamanın ilk adımı bu: epub burada
Release'te durur, repoya girmez. Draft release, PR merge olunca
(library_promote.py) yayımlanır; o ana kadar link dışarıdan açılmaz.

Fail-soft: eksik token ya da ağ/git hatasında script'i ÇÖKERTMEZ, uyarı
basıp None döner (bkz. web_ingest.py ile aynı mantık).

Ortam değişkenleri:
  GH_TOKEN         : App token'ı — eptran-library'ye de erişebilmeli
                     (create-github-app-token'da `repositories:` ile).
  LIBRARY_REPO     : "sahip/repo" (varsayılan: dpentx/eptran-library)
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

DEFAULT_LIBRARY_REPO = "dpentx/eptran-library"


def _slug(value: str) -> str:
    s = re.sub(r"[^a-z0-9._-]+", "-", (value or "").strip().lower()).strip("-.")
    return s or "kitap"


def _run(cmd: list, cwd: str | None = None, check: bool = True) -> str:
    """Komutu çalıştırır; hata mesajında token sızmasın diye maskeler."""
    token = os.environ.get("GH_TOKEN", "")
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        if token:
            err = err.replace(token, "***")
        raise RuntimeError(f"{' '.join(cmd[:3])}... başarısız: {err[:400]}")
    return (proc.stdout or "").strip()


def _clone_url(repo: str) -> str:
    # Testlerde yerel bir bare repo vermek için.
    override = os.environ.get("LIBRARY_CLONE_URL")
    if override:
        return override
    token = os.environ["GH_TOKEN"]
    return f"https://x-access-token:{token}@github.com/{repo}.git"


def _gh(args: list) -> str:
    return _run(["gh", *args])


def _gh_ok(args: list) -> bool:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    return proc.returncode == 0


def _ensure_release(repo: str, tag: str, title: str, epub_path: str) -> str:
    """Draft release oluşturur (ya da varsa epub'ı üzerine yazar); asset URL'sini döner."""
    asset_name = os.path.basename(epub_path)
    if _gh_ok(["release", "view", tag, "--repo", repo]):
        _gh(["release", "upload", tag, epub_path, "--clobber", "--repo", repo])
    else:
        _gh(["release", "create", tag, epub_path, "--repo", repo, "--draft",
             "--title", title, "--notes", f"Otomatik yayın: {title}"])
    return f"https://github.com/{repo}/releases/download/{tag}/{asset_name}"


def _load_index(path: str, series_slug: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("ciltler", [])
                return data
        except (OSError, ValueError):
            print(f"  Uyarı: {path} okunamadı, yeniden oluşturuluyor.")
    return {"seri": series_slug, "ad": series_slug, "ciltler": []}


def _series_display_name(series_slug: str) -> str | None:
    """series/<slug>.json içindeki "series" alanını (okunur seri adı) döner.
    (lib/series.py'nin load()'u bu alanı geri vermiyor, o yüzden dosyayı
    doğrudan okuyoruz.)"""
    safe = "".join(c for c in series_slug if c.isalnum() or c in "-_")
    try:
        with open(os.path.join("series", f"{safe}.json"), encoding="utf-8") as f:
            name = json.load(f).get("series")
        return name if isinstance(name, str) and name.strip() else None
    except (OSError, ValueError):
        return None


def publish_to_library(book_slug: str, chapters: list, epub_path: str,
                       title: str, author: str | None = None,
                       series: str | None = None) -> dict | None:
    repo = os.environ.get("LIBRARY_REPO", DEFAULT_LIBRARY_REPO)
    if not os.environ.get("GH_TOKEN") and not os.environ.get("LIBRARY_CLONE_URL"):
        print("  Uyarı: GH_TOKEN yok — library'ye yayın atlandı.")
        return None
    if not chapters:
        print("  Uyarı: yayınlanacak bölüm yok — library'ye yayın atlandı.")
        return None
    if not os.path.exists(epub_path):
        print(f"  Uyarı: {epub_path} yok — library'ye yayın atlandı.")
        return None

    book = _slug(book_slug)
    series_slug = _slug(series) if series else book
    staging = f"staging/{book}"
    tmp = tempfile.mkdtemp(prefix="eptran-library-")
    try:
        # 1) Release önce: index.json'a yazılacak link geçerli olsun.
        epub_url = _ensure_release(repo, book, title, epub_path)

        # 2) Library'yi klonla, staging dalını main'in ucundan (yeniden) kur.
        work = os.path.join(tmp, "lib")
        _run(["git", "clone", _clone_url(repo), work])
        default = _run(["git", "symbolic-ref", "--short", "HEAD"], cwd=work)
        _run(["git", "checkout", "-B", staging, f"origin/{default}"], cwd=work)

        # 3) Bölümleri yaz (eski/artık dosyalar kalmasın diye klasörü sıfırla).
        cilt_dir = os.path.join(work, series_slug, book)
        shutil.rmtree(cilt_dir, ignore_errors=True)
        os.makedirs(cilt_dir)
        for i, ch in enumerate(chapters, start=1):
            with open(os.path.join(cilt_dir, f"{i:03d}.txt"), "w", encoding="utf-8") as f:
                f.write(f"{ch['title']}\n\n{ch['body']}\n")

        # 4) Seri index.json'ı güncelle.
        index_path = os.path.join(work, series_slug, "index.json")
        index = _load_index(index_path, series_slug)
        name = _series_display_name(series_slug)
        if name:
            index["ad"] = name
        entry = {"slug": book, "baslik": title, "yazar": author,
                 "bolum_sayisi": len(chapters), "epub": epub_url}
        index["ciltler"] = sorted(
            [c for c in index["ciltler"] if c.get("slug") != book] + [entry],
            key=lambda c: c.get("slug", ""))
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
            f.write("\n")

        # 5) Commit + push (staging dalı pipeline'a ait, force güvenli).
        name_cfg = _run(["git", "config", "user.name"], check=False) or "eptran-bot"
        mail_cfg = _run(["git", "config", "user.email"], check=False) or "eptran-bot@users.noreply.github.com"
        _run(["git", "add", "-A"], cwd=work)
        if not _run(["git", "status", "--porcelain"], cwd=work):
            print("  library: değişiklik yok (zaten güncel).")
        else:
            _run(["git", "-c", f"user.name={name_cfg}", "-c", f"user.email={mail_cfg}",
                  "commit", "-m", f"{book}: {len(chapters)} bölüm eklendi"], cwd=work)
        _run(["git", "push", "--force", "origin", f"{staging}:{staging}"], cwd=work)

        info = {
            "repo": repo, "branch": staging, "series": series_slug,
            "branch_url": f"https://github.com/{repo}/tree/{staging}",
            "release_url": f"https://github.com/{repo}/releases/tag/{book}",
            "epub_url": epub_url,
        }
        print(f"  library'ye yayınlandı: {info['branch_url']}")
        return info
    except Exception as e:  # fail-soft
        print(f"  Uyarı: library'ye yayın başarısız: {e}")
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
