"""
eptran — start_next_queue.py

Kuyruktaki (queue/*) bir SONRAKI kitabı başlatır.

Aktif bir kitap (book/*) YOKSA, yükleme tamamlanmış bekleyen queue/* dalları
arasından en eskisini (yükleme sırasına göre) seçip translate.yml'i o dal
ref'iyle tetikler — api/upload.js'in tek kitap boşta iken yaptığıyla aynı şey.

Çağıranlar:
  - delete-merged-book-branch.yml: bir kitabın PR'ı merge olup book/<slug>
    dalı silinince (normal yol).
  - translate.yml'in 6 saatlik cron'u (main'de): kaçan/başarısız tetiklemeleri
    telafi eden güvenlik ağı (örn. PR merge edilmeden dal elle silindiyse).

"Hazır" = dal main'e göre en az 1 commit ilerde (yani dosya gerçekten
YÜKLENMİŞ). Yükleme yarıda kalmış, artık dal başka bir şeye yaramayan
yetim queue/* dalları yok sayılır.

Fail-soft: herhangi bir hatada sadece uyarı basar, sıfır koduyla çıkar — bu
bir yardımcı adım, asıl işlerin (dal silme, cron taraması) başarısını bozmamalı.

Ortam: GH_TOKEN (Actions: write), GITHUB_REPOSITORY.
"""
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
    if any(n.startswith("book/") for n in names):
        print("Aktif bir kitap (book/*) var — sıradaki başlatılmayacak.")
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
    _gh("workflow", "run", "translate.yml", "--ref", next_branch)
    print("translate.yml tetiklendi.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # fail-soft
        print(f"Uyarı: sıradaki kitap başlatılamadı: {e}", file=sys.stderr)
