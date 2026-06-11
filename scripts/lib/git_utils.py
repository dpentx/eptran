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
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "pull", "--rebase"], check=True)
        subprocess.run(["git", "push"], check=True)


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
