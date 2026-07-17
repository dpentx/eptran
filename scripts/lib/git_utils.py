"""
Git işlemleri ve status.json yönetimi.
"""
import json
import os
import subprocess
import time
from datetime import datetime, timezone, timedelta

STATUS_FILE = "status.json"
STALE_RUNNING_MINUTES = 30


def trigger_workflow(workflow_file: str, **inputs) -> None:
    """
    `gh workflow run` ile başka bir workflow'u (ya da kendini) tetikler.
    GH CLI, ortam değişkeni GH_TOKEN'ı otomatik kullanır (workflow yml'de
    App token'ı bu değişkene atanmış olmalı). **inputs verilirse her biri
    `-f anahtar=değer` olarak eklenir (örn. branch=book/pg2147).
    Tetikleme başarısız olursa (örn. gh kurulu değil, ya da izin sorunu)
    sessizce loglayıp devam ediyoruz — bu, bir sonraki güvenlik ağı
    tetiklemesinde (translate.yml'in periyodik nudge'ı) telafi edilir,
    script'i çökertmeye değmez.
    """
    cmd = ["gh", "workflow", "run", workflow_file]
    for key, value in inputs.items():
        cmd += ["-f", f"{key}={value}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Uyarı: '{workflow_file}' tetiklenemedi: {result.stderr.strip()}")
    else:
        print(f"  '{workflow_file}' tetiklendi.")


def current_branch() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True
    ).stdout.strip()


def _remote_branch_exists(branch: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
        capture_output=True, text=True
    )
    return result.returncode == 0


def create_book_branch(branch: str) -> None:
    """
    main'den yeni bir kitap dalı oluşturup üzerine geçer (henüz push
    etmez — ilk push, o dal üzerinde ilk write_status()/git_push()
    çağrısında, _remote_branch_exists() False olduğu için otomatik
    '-u origin <branch>' ile yapılır).
    """
    subprocess.run(["git", "checkout", "-b", branch], check=True)


def list_active_book_branches() -> list:
    """origin'deki tüm 'book/*' dallarının adlarını döndürür."""
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "book/*"],
        capture_output=True, text=True, check=True
    )
    branches = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        ref = line.split("\t")[-1]  # "refs/heads/book/pg2147"
        branches.append(ref.removeprefix("refs/heads/"))
    return branches


def peek_remote_file(branch: str, path: str):
    """
    Bir dalı hiç checkout etmeden, o daldaki bir dosyanın içeriğini okur
    (`git show`). Dosya yoksa None döner. main'de dururken diğer kitap
    dallarının status.json'una bakmak için kullanılıyor (translate.yml'in
    güvenlik ağı taraması).
    """
    subprocess.run(["git", "fetch", "origin", branch], check=True)
    result = subprocess.run(
        ["git", "show", f"origin/{branch}:{path}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout


def open_pr(branch: str, title: str, body: str) -> None:
    """
    `book/<slug>` dalından main'e bir Pull Request açar (zaten açık bir
    tane varsa tekrar açmaz). Kitap tamamen bitince (çeviri+review+epub)
    ÇAĞRILAN TEK PR — ara ilerleme hiçbir zaman main'e dokunmuyor, sadece
    bu PR merge edilince main'e yansıyor.
    """
    existing = subprocess.run(
        ["gh", "pr", "list", "--head", branch, "--json", "number"],
        capture_output=True, text=True
    )
    if existing.returncode == 0 and existing.stdout.strip() not in ("", "[]"):
        print(f"  '{branch}' için zaten açık bir PR var, tekrar açılmıyor.")
        return
    result = subprocess.run(
        ["gh", "pr", "create", "--base", "main", "--head", branch,
         "--title", title, "--body", body],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  Uyarı: PR açılamadı: {result.stderr.strip()}")
    else:
        print(f"  PR açıldı: {result.stdout.strip()}")


def git_push(message: str, max_retries: int = 3) -> None:
    """
    Değişiklikleri commit'leyip ŞU AN ÜZERİNDE BULUNULAN dala push eder
    (branch adı sabit 'main' değil, dinamik olarak tespit ediliyor — bu
    sayede kitap dalları (book/<slug>) da aynı fonksiyonu kullanabiliyor).

    fetch-depth: 0 ve tree-doğrulama sayesinde artık sessiz veri kaybı
    yaşanmıyor — gerçek bir çakışma olursa gürültülü şekilde duruyor.
    Ama bazı çakışmalar GERÇEKTEN GEÇİCİ: örn. bir workflow run'ı
    bitip concurrency kuyruğundaki bir sonraki run hemen başladığında,
    iki tarafın da status.json'a neredeyse aynı anda commit atması gibi.
    Bu yüzden fetch+rebase+push'ı birkaç kez (kısa bir bekleme ile)
    deniyoruz; hepsi başarısız olursa (gerçek/kalıcı bir sorun varsa)
    yine RuntimeError ile duruyoruz — sonsuza kadar sessizce denemiyoruz.
    """
    branch = current_branch()
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        return  # değişiklik yok

    subprocess.run(["git", "commit", "-m", message], check=True)

    # Bu dalın remote'ta karşılığı yoksa (yeni oluşturulan bir kitap
    # dalıysa) ilk push'u -u ile yapıp fonksiyondan çık — henüz
    # rebase edilecek bir origin/<branch> yok.
    if not _remote_branch_exists(branch):
        push = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            capture_output=True, text=True
        )
        if push.returncode != 0:
            raise RuntimeError(f"İlk push başarısız ({branch}):\n{push.stdout}\n{push.stderr}")
        return

    last_error = ""
    for attempt in range(1, max_retries + 1):
        subprocess.run(["git", "fetch", "origin", branch], check=True)
        rebase = subprocess.run(["git", "rebase", f"origin/{branch}"],
                                capture_output=True, text=True)
        if rebase.returncode != 0:
            subprocess.run(["git", "rebase", "--abort"])
            last_error = (
                f"git rebase origin/{branch} başarısız (deneme {attempt}/{max_retries}):\n"
                f"{rebase.stdout}\n{rebase.stderr}"
            )
            if attempt < max_retries:
                wait = 5 * attempt
                print(f"  Uyarı: {last_error}\n  Muhtemelen an'lık bir çakışma (ör. başka "
                      f"bir çalışmanın hemen ardından gelen push'u) — {wait}s sonra "
                      f"tekrar deneniyor.")
                time.sleep(wait)
                continue
            raise RuntimeError(last_error)

        push = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push.returncode != 0:
            last_error = (
                f"git push başarısız (deneme {attempt}/{max_retries}):\n"
                f"{push.stdout}\n{push.stderr}"
            )
            if attempt < max_retries:
                wait = 5 * attempt
                print(f"  Uyarı: {last_error}\n  {wait}s sonra tekrar deneniyor.")
                time.sleep(wait)
                continue
            raise RuntimeError(last_error)

        # Doğrulama: local HEAD içeriği (dosya + status.json) gerçekten
        # origin/<branch>'te mi? (rebase sonrası SHA değişmiş olabilir, o
        # yüzden SHA yerine ağaç içeriğini karşılaştırıyoruz.)
        local_tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, check=True
        ).stdout.strip()
        subprocess.run(["git", "fetch", "origin", branch], check=True)
        remote_tree = subprocess.run(
            ["git", "rev-parse", f"origin/{branch}^{{tree}}"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        if local_tree != remote_tree:
            last_error = (
                f"Push sonrası doğrulama başarısız: local ağaç ile origin/{branch} "
                "eşleşmiyor."
            )
            if attempt < max_retries:
                wait = 5 * attempt
                print(f"  Uyarı: {last_error}\n  {wait}s sonra tekrar deneniyor.")
                time.sleep(wait)
                continue
            raise RuntimeError(
                last_error + " Devam etmek yerine duruluyor (sessiz veri "
                "kaybını önlemek için)."
            )

        return  # başarılı


def read_status() -> dict:
    if not os.path.exists(STATUS_FILE):
        return {}
    with open(STATUS_FILE, encoding="utf-8") as f:
        return json.load(f)


def write_status(data: dict, label: str = "") -> None:
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    git_push(label or f"status: {data.get('updated_at', '')}")


def is_stale_running(status: dict, minutes: int = STALE_RUNNING_MINUTES) -> bool:
    """
    review_status == 'running' ama son güncelleme çok eskiyse
    önceki run crash/timeout olmuştur — kaldığı yerden devam edilmeli.
    """
    updated_at_str = status.get("updated_at")
    if not updated_at_str:
        return True
    try:
        updated_at = datetime.fromisoformat(updated_at_str)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - updated_at > timedelta(minutes=minutes)
    except Exception:
        return True
