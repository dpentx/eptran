"""
eptran — library_pull.py

Job başında (review/qa/pr-check/convert) çağrılır: eptran-library'deki
staging/<slug> bölümlerini yerel output/<slug>/NNN_<slug>.txt olarak yazar;
böylece o adımlar metinleri eskisi gibi yerinde okuyup düzenleyebilir.
Düzenlemeler sonraki write_status() -> git_push() ile library'ye geri gider.

LIBRARY_SYNC=1 değilse hiçbir şey yapmaz. Ayrıntı için lib/library_sync.py.

Ortam: LIBRARY_SYNC, GH_TOKEN (eptran-library'ye erişebilen App token'ı).
"""
from lib import library_sync


def main():
    if not library_sync.enabled():
        print("LIBRARY_SYNC kapalı, library'den çekme atlandı.")
        return
    n = library_sync.pull()
    print(f"Library'den {n} bölüm dosyası çekildi.")


if __name__ == "__main__":
    main()
