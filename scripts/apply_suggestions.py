"""
eptran — apply_suggestions.py

Okuyucu önerilerini eptran-library'ye düzeltme PR'ı olarak taşır ve açık öneri
PR'larının sonucunu siteye yansıtır. Ayrıntı için lib/suggestions.py.

Kullanım:
  python scripts/apply_suggestions.py                       # normal akış (cron)
  python scripts/apply_suggestions.py --dry-run             # PR açmadan planı yazdır
  python scripts/apply_suggestions.py --suggestions-file f.json
      # web'e hiç bağlanmadan, dosyadaki önerilerle PR aç (deneme; durum güncellenmez)

Ortam: GH_TOKEN (eptran-library'ye yazma + PR yetkili), WEB_INGEST_URL,
WEB_INGEST_SECRET (normal akışta), LIBRARY_REPO (opsiyonel).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.library_publish import DEFAULT_LIBRARY_REPO  # noqa: E402
from lib.suggestions import WebClient, run  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--suggestions-file")
    args = ap.parse_args()

    repo = os.environ.get("LIBRARY_REPO", DEFAULT_LIBRARY_REPO)
    web = None
    if not args.suggestions_file:
        url = os.environ.get("WEB_INGEST_URL")
        secret = os.environ.get("WEB_INGEST_SECRET")
        if not url or not secret:
            print("WEB_INGEST_URL / WEB_INGEST_SECRET yok — atlandı.")
            return 0
        web = WebClient(url, secret)
    if not os.environ.get("GH_TOKEN") and not os.environ.get("LIBRARY_CLONE_URL"):
        print("GH_TOKEN yok — atlandı.")
        return 0

    errors = run(web, repo, suggestions_file=args.suggestions_file, dry_run=args.dry_run)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
