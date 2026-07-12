"""
Git işlemleri ve status.json yönetimi.
"""
import json
import os
import subprocess
from datetime import datetime, timezone, timedelta

STATUS_FILE = "status.json"
STALE_RUNNING_MINUTES = 30


def git_push(message: str) -> None:
    """
    Değişiklikleri commit'leyip push eder.

    NOT: Bu fonksiyon artık sık sık (chunk başına bir kez) çağrılıyor
    (checkpoint özelliği). Sığ (shallow) bir clone üzerinde bu kadar sık
    'git pull --rebase' çağırmak kırılgandır — bazı durumlarda rebase,
    daha önce push edilmiş bir local commit'i (ve içindeki dosyayı)
    sessizce kaybettirebilir; push yine de 'başarılı' görünür. Bunun
    önündeki ASIL çözüm workflow'larda actions/checkout'a
    'fetch-depth: 0' eklemek (artık tam geçmişle çekiliyor). Burada ek
    olarak: rebase yerine daha öngörülebilir olan fetch+rebase akışını
    kullanıyoruz ve push sonrası commit'in gerçekten remote'a ulaştığını
    doğruluyoruz — ulaşmadıysa sessizce devam etmek yerine hata basıp
    script'i durduruyoruz (sessiz veri kaybı yerine gürültülü başarısızlık).
    """
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        return  # değişiklik yok

    subprocess.run(["git", "commit", "-m", message], check=True)
    local_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()

    subprocess.run(["git", "fetch", "origin", "main"], check=True)
    rebase = subprocess.run(["git", "rebase", "origin/main"], capture_output=True, text=True)
    if rebase.returncode != 0:
        # Rebase temiz gitmediyse (gerçek çakışma vb.) yarım bırakma —
        # abort edip net bir hatayla dur. Sessizce "en iyi çabayı göster"
        # yaklaşımı tam olarak dosya kaybına yol açan şeydi.
        subprocess.run(["git", "rebase", "--abort"])
        raise RuntimeError(
            f"git rebase origin/main başarısız oldu, commit push edilemedi:\n"
            f"{rebase.stdout}\n{rebase.stderr}"
        )

    push = subprocess.run(["git", "push"], capture_output=True, text=True)
    if push.returncode != 0:
        raise RuntimeError(f"git push başarısız oldu:\n{push.stdout}\n{push.stderr}")

    # Doğrulama: local HEAD içeriği (dosya + status.json) gerçekten
    # origin/main'de mi? (rebase sonrası SHA değişmiş olabilir, o yüzden
    # SHA yerine ağaç içeriğini karşılaştırıyoruz.)
    local_tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, check=True
    ).stdout.strip()
    subprocess.run(["git", "fetch", "origin", "main"], check=True)
    remote_tree = subprocess.run(
        ["git", "rev-parse", "origin/main^{tree}"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if local_tree != remote_tree:
        raise RuntimeError(
            "Push sonrası doğrulama başarısız: local ağaç ile origin/main "
            "eşleşmiyor. Bu, commit'in push edildiği ama içeriğin remote'a "
            "tam yansımadığı anlamına gelebilir — devam etmek yerine "
            "duruluyor (sessiz veri kaybını önlemek için)."
        )


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
