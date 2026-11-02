"""
eptran — start_next_queue.py

Kuyruktaki (queue/*) bir SONRAKİ kitabı başlatır.

Hâlâ İŞLENEN bir kitap (convert_status != "completed" olan book/*) YOKSA,
yükleme tamamlanmış bekleyen queue/* dalları arasından en eskisini (yükleme
sırasına göre) seçip translate.yml'i o dal ref'iyle tetikler — api/upload.js'in
sistem boşta iken yaptığıyla aynı şey.

ÖNEMLİ (Kasım 2026): Çevirisi/ciltlemesi bitip PR'ı açılmış ama henüz merge
edilmemiş bir kitap "işleniyor" SAYILMAZ. Kuyruk, repo sahibinin PR'ı incelemesini
beklemez; inceleme sonra, vakti gelince yapılır.

Çağıranlar:
  - start-next-on-pr-open.yml: bir book/* PR'ı açılınca (kitap bitti).
  - delete-merged-book-branch.yml: bir book/* PR'ı kapanınca (merge/red).
  - translate.yml'in 6 saatlik cron'u (main'de): kaçan tetiklemeleri
    telafi eden güvenlik ağı.

"Hazır" = dal main'e göre en az 1 commit ilerde (yani dosya gerçekten
YÜKLENMİŞ). Yükleme yarıda kalmış, artık dal başka bir şeye yaramayan
yetim queue/* dalları yok sayılır.

Fail-soft: herhangi bir hatada sadece uyarı basar, sıfır koduyla çıkar — bu
bir yardımcı adım, asıl işlerin (dal silme, cron taraması) başarısını bozmamalı.

Ortam: GH_TOKEN (Actions: write), GITHUB_REPOSITORY.
"""
import json
import os
import subprocess
import sys

REPO = os.environ.get("GITHUB_REPOSITORY", "")
MAIN_BRANCH = os.environ.get("MAIN_BRANCH", "main")


def _gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"gh {' '.join(args)} başarısız")
    return result.stdout


def _branch_names() -> list:
    out = _gh("api", f"repos/{REPO}/branches", "--paginate", "--jq", ".[].name")
    return [line.strip() for line in out.splitlines() if line.strip()]


def _in_progress(branch: str) -> bool:
    """
    book/<slug> dalındaki kitap hâlâ işleniyor mu? status.json'daki
    convert_status "completed" ise bitmiştir (PR açıldı, inceleme bekliyor).
    status.json okunamıyorsa (dal yeni açıldı) temkinli davranıp işleniyor sayarız.
    """
    try:
        raw = _gh(
            "api", "-H", "Accept: application/vnd.github.raw+json",
            f"repos/{REPO}/contents/status.json?ref={branch}",
        )
        return json.loads(raw).get("convert_status") != "completed"
    except Exception:
        return True


def _dispatch_pending(branch: str) -> bool:
    """translate.yml bu dal için zaten kuyrukta/çalışıyor mu? (çift tetiklemeyi önler)"""
    try:
        out = _gh("run", "list", "--workflow", "translate.yml", "--branch", branch,
                  "--json", "status", "--limit", "10")
        runs = json.loads(out or "[]")
    except Exception:
        return False
    return any(r.get("status") in ("queued", "in_progress", "waiting", "pending", "requested")
               for r in runs)


def _upload_info(branch: str):
    """
    (hazır_mı, ilk_yükleme_tarihi) döner. compare, dalın main'e göre kaç
    commit ilerde olduğunu ve o commit'lerin tarihlerini verir; ilk commit
    yükleme commit'idir.
    """
    out = _gh(
        "api", f"repos/{REPO}/compare/{MAIN_BRANCH}...{branch}",
        "--jq", "[.ahead_by, (.commits[0].commit.committer.date // \"\")] | @tsv",
    ).strip()
    ahead, _, date = out.partition("\t")
    return int(ahead or 0) > 0, date


def main() -> None:
    if not REPO:
        print("GITHUB_REPOSITORY tanımlı değil — çıkılıyor.")
        return

    names = _branch_names()
    busy = [n for n in names if n.startswith("book/") and _in_progress(n)]
    if busy:
        print(f"Hâlâ işlenen kitap var ({', '.join(busy)}) — sıradaki başlatılmayacak.")
        return

    ready = []
    for name in (n for n in names if n.startswith("queue/")):
        try:
            is_ready, date = _upload_info(name)
        except Exception as e:
            print(f"  Uyarı: {name} incelenemedi, atlanıyor: {e}")
            continue
        if is_ready:
            ready.append((date, name))
        else:
            print(f"  {name}: yükleme tamamlanmamış (yetim dal olabilir), atlanıyor.")

    if not ready:
        print("Sırada bekleyen kitap yok.")
        return

    ready.sort()  # ISO-8601 tarihler metin olarak da doğru sıralanır
    _, next_branch = ready[0]
    print(f"Sıradaki kitap: {next_branch} (arkasında {len(ready) - 1} kitap daha var).")
    if _dispatch_pending(next_branch):
        print("translate.yml bu dal için zaten kuyrukta/çalışıyor — tekrar tetiklenmiyor.")
        return
    _gh("workflow", "run", "translate.yml", "--ref", next_branch)
    print("translate.yml tetiklendi.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # fail-soft
        print(f"Uyarı: sıradaki kitap başlatılamadı: {e}", file=sys.stderr)
