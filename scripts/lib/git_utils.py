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


def git_push(message: str, max_retries: int = 3) -> None:
    """
    Değişiklikleri commit'leyip push eder.

    fetch-depth: 0 ve tree-doğrulama sayesinde artık sessiz veri kaybı
    yaşanmıyor — gerçek bir çakışma olursa gürültülü şekilde duruyor.
    Ama bazı çakışmalar GERÇEKTEN GEÇİCİ: örn. bir workflow run'ı
    bitip concurrency kuyruğundaki bir sonraki run hemen başladığında,
    iki tarafın da status.json'a neredeyse aynı anda commit atması gibi.
    Bu yüzden fetch+rebase+push'ı birkaç kez (kısa bir bekleme ile)
    deniyoruz; hepsi başarısız olursa (gerçek/kalıcı bir sorun varsa)
    yine RuntimeError ile duruyoruz — sonsuza kadar sessizce denemiyoruz.
    """
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        return  # değişiklik yok

    subprocess.run(["git", "commit", "-m", message], check=True)

    last_error = ""
    for attempt in range(1, max_retries + 1):
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        rebase = subprocess.run(["git", "rebase", "origin/main"], capture_output=True, text=True)
        if rebase.returncode != 0:
            subprocess.run(["git", "rebase", "--abort"])
            last_error = (
                f"git rebase origin/main başarısız (deneme {attempt}/{max_retries}):\n"
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
        # origin/main'de mi? (rebase sonrası SHA değişmiş olabilir, o
        # yüzden SHA yerine ağaç içeriğini karşılaştırıyoruz.)
        local_tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, check=True
        ).stdout.strip()
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        remote_tree = subprocess.run(
            ["git", "rev-parse", "origin/main^{tree}"], capture_output=True, text=True, check=True
        ).stdout.strip()
        if local_tree != remote_tree:
            last_error = (
                "Push sonrası doğrulama başarısız: local ağaç ile origin/main "
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
