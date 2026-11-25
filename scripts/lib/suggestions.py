"""
eptran — lib/suggestions.py

Okuyucu önerilerini (eptran-web) eptran-library'ye düzeltme PR'ı olarak taşır.

Akış (scripts/apply_suggestions.py bunu çalıştırır):

  1. Web'den bekleyen önerileri çek (GET /api/suggestions, bölüm içeriği yok;
     her öneri sourceKey + chapterIndex taşır).
  2. Library'de <seri>/<sourceKey>/NNN.txt dosyasını bul (NNN = chapterIndex + 1),
     seçilen metni ARADIĞINDA TAM BİR yerde bulursa değiştir; bulamazsa ya da
     belirsizse önerinin durumunu "rejected" yap (tahminle yapıştırma YOK).
  3. Aynı bölümün önerilerini tek bir branch + PR'da topla (oneri/... dalı).
     Durumu "pr_open" + PR adresi olarak güncelle.
  4. PR birleşince: library'den siteyi yeniden okut (POST /api/ingest-library) ve
     durumu "merged" yap; kapatılmışsa "rejected".

Güvenlik: öneriler anonim ve herkese açık bir formdan gelir. Bu yüzden
  * link, HTML, kontrol karakteri, paragraf yapısını bozan ya da başlık satırına
    dokunan öneriler OTOMATİK UYGULANMAZ (rejected);
  * PR gövdesinde kullanıcı metni kod aralığına alınır (mention/markdown enjeksiyonu yok);
  * bir çalıştırmada açılan ve aynı anda açık kalan öneri PR'ı sayısı sınırlıdır;
  * her değişiklik yine de PR'dır: library'ye ancak insan onayıyla girer.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone

from lib.library_publish import DEFAULT_LIBRARY_REPO, _clone_url, _gh, _run

BRANCH_PREFIX = "oneri/"
MAX_OPEN_PRS = 10
MAX_NEW_PRS_PER_RUN = 5


# --------------------------------------------------------------------------
# Metinde yer bulma ve güvenlik denetimi
# --------------------------------------------------------------------------

def _strip_ws(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _occurrences(text: str, needle: str) -> list:
    out, i = [], text.find(needle)
    while i != -1:
        out.append((i, i + len(needle)))
        i = text.find(needle, i + 1)
    return out


def _flex_occurrences(text: str, needle: str) -> list:
    """Boşluk farklarına (satır sonu / çift boşluk) toleranslı arama."""
    parts = [re.escape(p) for p in needle.split()]
    if not parts:
        return []
    return [(m.start(), m.end()) for m in re.finditer(r"\s+".join(parts), text)]


def _context_ok(text: str, start: int, end: int, before: str, after: str) -> bool:
    b, a = _strip_ws(before), _strip_ws(after)
    if b and not _strip_ws(text[max(0, start - 600):start]).endswith(b):
        return False
    if a and not _strip_ws(text[end:end + 600]).startswith(a):
        return False
    return True


def locate(text: str, selected: str, before: str = "", after: str = ""):
    """Seçilen metnin (başlangıç, bitiş) konumu; TAM BİR eşleşme yoksa None.

    Önce birebir, olmazsa boşluk toleranslı arar. Birden fazla yerde geçiyorsa
    contextBefore/contextAfter ile daraltır; hâlâ tek değilse None (belirsiz)."""
    if not selected or not selected.strip():
        return None
    occs = _occurrences(text, selected) or _flex_occurrences(text, selected)
    if len(occs) == 1:
        return occs[0]
    if len(occs) > 1:
        narrowed = [o for o in occs if _context_ok(text, o[0], o[1], before, after)]
        if len(narrowed) == 1:
            return narrowed[0]
    return None


_URL = re.compile(r"https?://|www\.", re.IGNORECASE)
_HTML = re.compile(r"<\s*[a-zA-Z/!]")
_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def unsafe_reason(selected: str, suggested: str):
    """Otomatik uygulanmaması gereken öneri için sebep metni; sorun yoksa None."""
    if _CTRL.search(suggested):
        return "kontrol karakteri içeriyor"
    if _URL.search(suggested):
        return "bağlantı içeriyor"
    if _HTML.search(suggested):
        return "HTML benzeri içerik"
    if suggested.lstrip().startswith("#"):
        return "başlık biçimi ('#') ile başlıyor"
    if "\n\n" in suggested and "\n\n" not in selected:
        return "paragraf yapısını değiştiriyor"
    return None


def apply_to_text(text: str, suggestions: list):
    """Bir bölümün önerilerini sırayla uygular.

    Döner: (yeni_metin, uygulananlar, reddedilenler[(öneri, sebep)]).
    Başlık satırına (yayın biçiminde ilk satır) dokunan öneri uygulanmaz."""
    applied, rejected = [], []
    for s in suggestions:
        reason = unsafe_reason(s["selectedText"], s["suggestedText"])
        if reason:
            rejected.append((s, reason))
            continue
        pos = locate(text, s["selectedText"], s.get("contextBefore", ""), s.get("contextAfter", ""))
        if pos is None:
            rejected.append((s, "metin bölümde tek bir yerde bulunamadı"))
            continue
        title_end = text.find("\n")
        if title_end == -1 or pos[0] < title_end:
            rejected.append((s, "başlık satırına dokunuyor"))
            continue
        text = text[:pos[0]] + s["suggestedText"] + text[pos[1]:]
        applied.append(s)
    return text, applied, rejected


def _code(s: str, limit: int = 300) -> str:
    """Kullanıcı metnini PR gövdesine güvenle koymak için tek satırlık kod aralığı."""
    s = re.sub(r"\s+", " ", s).replace("`", "'").strip()
    if len(s) > limit:
        s = s[:limit] + "…"
    return f"`{s}`"


def pr_title(slug: str, nnn: str, count: int) -> str:
    return f"{slug} {nnn}: okuyucu önerisi ({count} düzeltme)"


def pr_body(slug: str, nnn: str, chapter_title: str, applied: list) -> str:
    lines = [
        f"Okuyucu önerileri, **{slug}** / bölüm **{nnn}** ({_code(chapter_title, 120)}).",
        "",
        "Öneriler anonim bir formdan gelir; metni bu dosyada tek bir yerde bulunan "
        "düzeltmeler otomatik uygulandı. Birleştirmeden önce gözden geçirin. "
        "Birleşince site bölümü yeniden okur.",
        "",
    ]
    for s in applied:
        lines.append(f"- önce: {_code(s['selectedText'])} → sonra: {_code(s['suggestedText'])}")
        if s.get("note"):
            lines.append(f"  - not: {_code(s['note'], 120)}")
        lines.append(f"  - öneri: `{s['id']}`")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Web istemcisi
# --------------------------------------------------------------------------

class WebClient:
    """eptran-web'in bot uçları. base_url, WEB_INGEST_URL'den (".../api/ingest") türetilir."""

    def __init__(self, ingest_url: str, secret: str, timeout: int = 60):
        base = ingest_url.rstrip("/")
        if base.endswith("/api/ingest"):
            base = base[: -len("/api/ingest")]
        self.base = base
        self.secret = secret
        self.timeout = timeout

    def _call(self, method: str, path: str, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            self.base + path, data=data, method=method,
            headers={"Authorization": f"Bearer {self.secret}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8") or "null")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"web {method} {path} -> HTTP {e.code}: {detail}") from None

    def list(self, status: str) -> list:
        return self._call("GET", f"/api/suggestions?status={status}")

    def patch(self, sid: str, status: str, pr_url: str = None):
        body = {"id": sid, "status": status}
        if pr_url:
            body["prUrl"] = pr_url
        return self._call("PATCH", "/api/suggestions", body)

    def ingest_library(self, series: str, slug: str, source_key: str, ref: str = "main"):
        return self._call("POST", "/api/ingest-library",
                          {"series": series, "slug": slug, "sourceKey": source_key, "ref": ref})


# --------------------------------------------------------------------------
# GitHub (gh CLI) — testlerde sahtesi verilir
# --------------------------------------------------------------------------

class Gh:
    def __init__(self, repo: str):
        self.repo = repo

    def pr_create(self, head: str, title: str, body: str) -> str:
        return _gh(["pr", "create", "--repo", self.repo, "--base", "main", "--head", head,
                    "--title", title, "--body", body]).strip().splitlines()[-1]

    def pr_view(self, url: str) -> dict:
        return json.loads(_gh(["pr", "view", url, "--json", "state,mergeCommit"]))

    def open_suggestion_branches(self) -> list:
        out = _gh(["pr", "list", "--repo", self.repo, "--state", "open", "--limit", "100",
                   "--json", "headRefName"])
        return [p["headRefName"] for p in json.loads(out)
                if p["headRefName"].startswith(BRANCH_PREFIX)]


# --------------------------------------------------------------------------
# Library işlemleri
# --------------------------------------------------------------------------

def find_series(work: str, slug: str):
    """<seri>/<slug>/001.txt olan seri klasörünü bulur."""
    for name in sorted(os.listdir(work)):
        if not name.startswith(".") and os.path.isfile(os.path.join(work, name, slug, "001.txt")):
            return name
    return None


def _identity() -> tuple:
    name = os.environ.get("GIT_AUTHOR_NAME") or "eptran-bot"
    mail = os.environ.get("GIT_AUTHOR_EMAIL") or "eptran-bot@users.noreply.github.com"
    return name, mail


def _group_by_chapter(suggestions: list) -> dict:
    groups = {}
    for s in suggestions:
        groups.setdefault((s["sourceKey"], s["chapterIndex"]), []).append(s)
    return groups


def process_pending(suggestions: list, repo: str, web, gh, tmp: str,
                    dry_run: bool = False, max_new_prs: int = MAX_NEW_PRS_PER_RUN,
                    max_open: int = MAX_OPEN_PRS) -> dict:
    """Bekleyen önerilerden library PR'ları açar. web=None ise durum güncellenmez
    (dosya/deneme modu). Özet sayaçlarla döner."""
    stats = {"pr_opened": 0, "applied": 0, "rejected": 0, "skipped_limit": 0, "errors": 0}
    if not suggestions:
        return stats

    work = os.path.join(tmp, "lib")
    _run(["git", "clone", "--depth", "1", _clone_url(repo), work])
    default = _run(["git", "symbolic-ref", "--short", "HEAD"], cwd=work)
    open_branches = gh.open_suggestion_branches() if not dry_run else []
    open_count = len(open_branches)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    for (slug, index), group in sorted(_group_by_chapter(suggestions).items()):
        try:
            series = find_series(work, slug)
            nnn = f"{index + 1:03d}"
            path = os.path.join(work, series, slug, f"{nnn}.txt") if series else None
            if not path or not os.path.isfile(path):
                for s in group:
                    _finish(web, s, "rejected", dry_run, stats, f"{slug} {nnn}: library'de dosya yok")
                continue

            with open(path, encoding="utf-8") as f:
                text = f.read()
            new_text, applied, rejected = apply_to_text(text, group)
            for s, reason in rejected:
                _finish(web, s, "rejected", dry_run, stats, f"{slug} {nnn} {s['id']}: {reason}")
            if not applied:
                continue

            # Aynı bölüm için zaten açık bir öneri PR'ı varsa yenisini açma: iki PR aynı
            # dosyayı değiştirir ve çakışır; ayrıca durum güncellemesi yarım kaldıysa aynı
            # düzeltmenin ikinci kez PR yapılmasını engeller. Öneriler beklemede kalır.
            if any(b.startswith(f"{BRANCH_PREFIX}{slug}-{nnn}-") for b in open_branches):
                stats["skipped_limit"] += len(applied)
                print(f"  {slug} {nnn}: bu bölüm için açık bir öneri PR'ı var, sonraya kaldı.")
                continue

            if stats["pr_opened"] >= max_new_prs or open_count + stats["pr_opened"] >= max_open:
                stats["skipped_limit"] += len(applied)
                print(f"  {slug} {nnn}: PR sınırına ulaşıldı, {len(applied)} öneri sonraki çalıştırmaya kaldı.")
                continue

            title = pr_title(slug, nnn, len(applied))
            body = pr_body(slug, nnn, group[0].get("chapterTitle", ""), applied)
            if dry_run:
                print(f"  [dry-run] PR açılacaktı: {title}\n{body}")
                stats["applied"] += len(applied)
                continue

            branch = f"{BRANCH_PREFIX}{slug}-{nnn}-{stamp}"
            _run(["git", "checkout", "--quiet", default], cwd=work)
            _run(["git", "checkout", "--quiet", "-B", branch], cwd=work)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_text)
            name, mail = _identity()
            _run(["git", "add", "-A"], cwd=work)
            _run(["git", "-c", f"user.name={name}", "-c", f"user.email={mail}", "commit", "--quiet",
                  "-m", title], cwd=work)
            _run(["git", "push", "--quiet", "origin", f"{branch}:{branch}"], cwd=work)
            url = gh.pr_create(branch, title, body)
            stats["pr_opened"] += 1
            stats["applied"] += len(applied)
            print(f"  PR açıldı: {url}")
            for s in applied:
                _finish(web, s, "pr_open", dry_run, stats, None, pr_url=url)
        except Exception as e:  # bir bölümün hatası diğerlerini durdurmasın
            stats["errors"] += 1
            print(f"  HATA ({slug} {index + 1}): {e}")
    return stats


def _finish(web, s: dict, status: str, dry_run: bool, stats: dict, log, pr_url: str = None):
    if log:
        print(f"  reddedildi: {log}")
        stats["rejected"] += 1
    if web is None or dry_run:
        return
    web.patch(s["id"], status, pr_url)


def reconcile_open(suggestions: list, repo: str, web, gh, tmp: str) -> dict:
    """status=pr_open olan önerileri PR durumuna göre kapatır: birleşmişse siteyi
    yeniden okutup 'merged', birleşmeden kapanmışsa 'rejected'."""
    stats = {"merged": 0, "closed": 0, "still_open": 0, "errors": 0}
    by_pr = {}
    for s in suggestions:
        if s.get("prUrl"):
            by_pr.setdefault(s["prUrl"], []).append(s)

    work = None
    for url, group in by_pr.items():
        try:
            info = gh.pr_view(url)
            state = info.get("state")
            if state == "OPEN":
                stats["still_open"] += 1
                continue
            if state == "MERGED":
                if work is None:
                    work = os.path.join(tmp, "lib-reconcile")
                    _run(["git", "clone", "--depth", "1", _clone_url(repo), work])
                ref = (info.get("mergeCommit") or {}).get("oid") or "main"
                done = set()
                for s in group:
                    key = (s["sourceKey"], s["chapterIndex"])
                    if key in done:
                        continue
                    done.add(key)
                    series = find_series(work, s["sourceKey"])
                    if series is None:
                        raise RuntimeError(f"library'de {s['sourceKey']} yok")
                    web.ingest_library(series, s["sourceKey"], s["sourceKey"], ref)
                for s in group:
                    web.patch(s["id"], "merged")
                stats["merged"] += len(group)
            else:  # CLOSED (birleşmeden)
                for s in group:
                    web.patch(s["id"], "rejected")
                stats["closed"] += len(group)
        except Exception as e:
            stats["errors"] += 1
            print(f"  HATA ({url}): {e}")
    return stats


def run(web, repo: str = DEFAULT_LIBRARY_REPO, gh=None, suggestions_file: str = None,
        dry_run: bool = False) -> int:
    """Tüm akış. Hata sayısını döner (0 = temiz)."""
    gh = gh or Gh(repo)
    tmp = tempfile.mkdtemp(prefix="eptran-suggestions-")
    errors = 0
    try:
        if suggestions_file:
            with open(suggestions_file, encoding="utf-8") as f:
                pending = json.load(f)
            print(f"{len(pending)} öneri dosyadan okundu (durum güncellenmeyecek).")
            stats = process_pending(pending, repo, None, gh, tmp, dry_run=dry_run)
            print(f"Özet: {stats}")
            return stats["errors"]

        reconcile = reconcile_open(web.list("pr_open"), repo, web, gh, tmp)
        print(f"PR durumları: {reconcile}")
        errors += reconcile["errors"]

        pending = web.list("pending")
        print(f"{len(pending)} bekleyen öneri.")
        stats = process_pending(pending, repo, web, gh, tmp, dry_run=dry_run)
        print(f"Özet: {stats}")
        errors += stats["errors"]
        return errors
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
