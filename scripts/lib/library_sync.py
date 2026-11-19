"""
eptran — lib/library_sync.py

Biten bölüm çevirilerini eptran-library'nin staging/<slug> dalına senkronlar
ve status.json'un bir aynasını cilt klasörünün yanına yazar:

    output/<slug>/NNN_<slug>.txt   ──►  <seri>/<slug>/NNN.txt
    status.json                    ──►  <seri>/<slug>/status.json  (ayna)

SINIR (neyin nereye gittiği):
  * eptran'da (book/<slug> dalı) KALANLAR: status.json (ASIL kopya), memory.json,
    .originals/ (İngilizce kaynak parçalar), .translated/ (parça çevirileri).
  * library'ye GİDENLER: sadece biten bölüm metinleri + status aynası; ciltlenmiş
    epub ise git'e değil library Release'ine gider (eptran'da yok sayılır).
  İngilizce kaynak parçalar library'ye ASLA girmez (public repo, telif).

NE ZAMAN ÇALIŞIR: yalnızca LIBRARY_SYNC=1 ise. Kapalıyken (varsayılan) bu modül
hiçbir şey yapmaz; yani bu dosyanın main'e girmesi mevcut davranışı değiştirmez.
Workflow'lar hazır olunca (token'a eptran-library eklenip LIBRARY_SYNC=1
verilince) açılır.

Çağrı yeri: lib/git_utils.py → git_push() başında. Sıra bilinçli olarak
"önce library, sonra eptran": library'ye yazıldıktan sonra çökülürse ilerleme
kaybolmaz (queue_worker ilerlemeyi dosyalardan okur, sayaçtan değil); ters sırada
eksik kalırdı.

GÜVENLİK KURALLARI:
  * Senkron SADECE EKLER/GÜNCELLER, ASLA SİLMEZ. Job başında library'den çekme
    (pull) yapılmadan çalışan bir job'un yerel output/'u boştur; "ayna" gibi
    davranıp silseydik library'deki çeviriler yok olurdu.
  * Sadece book/* dallarında çalışır (main'deki bayat status.json aynayı ezmesin).
  * Kalıcı hata RuntimeError atar; sessizce yutulmaz (git_push'un mantığıyla aynı).
  * Library klonu .library/ altında durur ve .git/info/exclude'a yazılır, yani
    eptran'a commit'lenmez (içinde token'lı remote URL'i olabilir). Biten
    bölüm txt'leri de aynı yolla eptran'da yok sayılır — repo içi .gitignore'a
    DEĞİL, yerel exclude'a yazılır ki özellik kapalıyken davranış değişmesin.

Ortam değişkenleri:
  LIBRARY_SYNC       : "1" ise açık.
  GH_TOKEN           : App token'ı (eptran-library'ye yazabilmeli).
  LIBRARY_REPO       : "sahip/repo" (varsayılan: library_publish.DEFAULT_LIBRARY_REPO)
  LIBRARY_CLONE_URL  : testlerde yerel bir bare repo vermek için.
"""
import json
import os
import re
import shutil
import subprocess
import time

from lib.library_publish import DEFAULT_LIBRARY_REPO, _clone_url, _run, _slug

WORK_DIR = ".library"
STATUS_FILE = "status.json"
# output/<slug>/ doğrudan altındaki biten bölüm dosyaları: 001_<slug>.txt
FINAL_RE = re.compile(r"^(\d{3})_.+\.txt$")
# Library tarafındaki bölüm dosyaları: 001.txt
LIB_FINAL_RE = re.compile(r"^(\d{3})\.txt$")
# Yerel exclude: .originals/.translated altındakiler 4 segment olduğu için eşleşmez.
# Ciltlenmiş epub de eptran'a girmez: library Release'ine gider (publish_library.py).
EXCLUDE_LINES = [f"/{WORK_DIR}/", "output/*/[0-9][0-9][0-9]_*.txt", "output/*/*.epub"]
MAX_ATTEMPTS = 3


def enabled() -> bool:
    return os.environ.get("LIBRARY_SYNC") == "1"


def _load_status() -> dict:
    try:
        with open(STATUS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _current_branch() -> str:
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], check=False)


def _ensure_excludes() -> None:
    """Klonu ve biten txt'leri eptran'da yerel olarak yok say (commit'lenmesin)."""
    path = _run(["git", "rev-parse", "--git-path", "info/exclude"])
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    existing = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = f.read()
    missing = [ln for ln in EXCLUDE_LINES if ln not in existing.splitlines()]
    if missing:
        with open(path, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("\n".join(missing) + "\n")


def _pin_series(status: dict) -> str:
    """Library'deki seri klasörünü İLK senkronda sabitler (status.json'a yazar).

    Seri adı sonradan elle eklenebiliyor (status.json'daki "series"); yol
    ortada değişirse kitap iki klasöre bölünür. O yüzden bir kez sabitleniyor.
    """
    pinned = status.get("library_series")
    if isinstance(pinned, str) and pinned:
        return pinned
    series = _slug(status.get("series") or status.get("book") or "")
    status["library_series"] = series
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    return series


def _identity() -> tuple:
    """Commit kimliği: eptran deposundaki yerel git config'i (bot); yoksa nötr bot."""
    name = _run(["git", "config", "user.name"], check=False) or "eptran-bot"
    mail = _run(["git", "config", "user.email"], check=False) or "eptran-bot@users.noreply.github.com"
    return name, mail


def _repo() -> str:
    return os.environ.get("LIBRARY_REPO", DEFAULT_LIBRARY_REPO)


def _check_token() -> None:
    if not os.environ.get("GH_TOKEN") and not os.environ.get("LIBRARY_CLONE_URL"):
        raise RuntimeError("LIBRARY_SYNC=1 ama GH_TOKEN yok — library'ye yazılamaz.")


def _default_ref(work: str) -> str:
    ref = _run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=work, check=False)
    return ref or "origin/main"


def _prepare_branch(work: str, staging: str) -> bool:
    """Yerel klonu staging dalının uzaktaki haline getirir (yoksa main'in ucundan
    kurar). Uzakta dal VARSA True döner."""
    if not os.path.isdir(os.path.join(work, ".git")):
        _run(["git", "clone", "--quiet", _clone_url(_repo()), work])
    exists = bool(_run(["git", "ls-remote", "--heads", "origin", staging], cwd=work, check=False))
    if exists:
        _run(["git", "fetch", "--quiet", "origin", staging], cwd=work)
        _run(["git", "checkout", "--quiet", "-B", staging, f"origin/{staging}"], cwd=work)
    else:
        _run(["git", "fetch", "--quiet", "origin"], cwd=work)
        _run(["git", "checkout", "--quiet", "-B", staging, _default_ref(work)], cwd=work)
    return exists


def _copy_if_changed(src: str, dst: str) -> bool:
    if os.path.exists(dst):
        with open(src, "rb") as a, open(dst, "rb") as b:
            if a.read() == b.read():
                return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    return True


def _sync_once(book: str, lib_book: str, series: str, staging: str) -> bool:
    """Tek deneme: library'yi güncel hale getir → dosyaları kopyala → commit → push.
    Değişiklik yapıldıysa True."""
    work = WORK_DIR
    _prepare_branch(work, staging)

    dest = os.path.join(work, series, lib_book)
    changed = 0

    src_dir = os.path.join("output", book)
    if os.path.isdir(src_dir):
        for name in sorted(os.listdir(src_dir)):
            m = FINAL_RE.match(name)
            path = os.path.join(src_dir, name)
            if m and os.path.isfile(path):
                if _copy_if_changed(path, os.path.join(dest, f"{m.group(1)}.txt")):
                    changed += 1

    if os.path.exists(STATUS_FILE):
        if _copy_if_changed(STATUS_FILE, os.path.join(dest, STATUS_FILE)):
            changed += 1

    _run(["git", "add", "-A"], cwd=work)
    if not _run(["git", "status", "--porcelain"], cwd=work):
        return False
    name, mail = _identity()
    _run(["git", "-c", f"user.name={name}", "-c", f"user.email={mail}",
          "commit", "--quiet", "-m", f"{lib_book}: senkron ({changed} dosya)"], cwd=work)
    _run(["git", "push", "--quiet", "origin", f"{staging}:{staging}"], cwd=work)
    return True


def sync_if_enabled() -> bool:
    """git_push() başında çağrılır. Kapalıysa / book dalında değilse hiçbir şey yapmaz.
    Library'ye bir şey yazıldıysa True."""
    if not enabled():
        return False
    branch = _current_branch()
    if not branch.startswith("book/"):
        return False
    status = _load_status()
    book = status.get("book")
    if not book:
        return False

    _check_token()
    _ensure_excludes()
    series = _pin_series(status)
    lib_book = _slug(book)
    staging = f"staging/{lib_book}"

    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return _sync_once(book, lib_book, series, staging)
        except RuntimeError as e:
            last = e
            if attempt < MAX_ATTEMPTS:
                wait = 3 * attempt
                print(f"  Uyarı: library senkronu başarısız (deneme {attempt}/{MAX_ATTEMPTS}): "
                      f"{e}\n  {wait}s sonra tekrar deneniyor.")
                time.sleep(wait)
    raise RuntimeError(f"library senkronu {MAX_ATTEMPTS} denemede başarısız: {last}")


def pull() -> int:
    """Job başında çağrılır: library'deki staging/<slug> bölümlerini yerel
    output/<slug>/NNN_<slug>.txt olarak yazar (review/qa/pr-check/convert bunları
    yerinde okur ve düzenler). status.json'a DOKUNMAZ (asıl kopya eptran'da).
    Yazılan dosya sayısını döner; staging dalı yoksa 0."""
    if not enabled():
        return 0
    status = _load_status()
    book = status.get("book")
    if not book:
        return 0

    _check_token()
    _ensure_excludes()
    series = _pin_series(status)
    lib_book = _slug(book)
    staging = f"staging/{lib_book}"

    if not _prepare_branch(WORK_DIR, staging):
        return 0
    src_dir = os.path.join(WORK_DIR, series, lib_book)
    if not os.path.isdir(src_dir):
        return 0

    written = 0
    for name in sorted(os.listdir(src_dir)):
        m = LIB_FINAL_RE.match(name)
        if m and _copy_if_changed(os.path.join(src_dir, name),
                                  os.path.join("output", book, f"{m.group(1)}_{book}.txt")):
            written += 1
    return written
