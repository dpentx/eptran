"""
eptran-web'e (Astro + Turso) tamamlanan kitapları POST /api/ingest ile
gönderir. eptran-web tarafı zaten hazır ve bekliyordu (bkz. o reponun
README'si ve src/pages/api/ingest.ts) — eksik olan taraf HER ZAMAN
buraydı: eptran'ın hiçbir scripti bu endpoint'i hiç çağırmıyordu.

Tasarım: convert.py, bir kitabın epub ciltlemesini bitirdiği anda
(convert_status == "completed") burayı çağırır. Bu an, README'nin
"Epub varsa her zaman epub tercih edilir" sözleşmesiyle birebir
örtüşüyor — eptran-web'in kendi parseEpub()'ı OPF spine sırasına göre
otomatik bölüyor, biz sadece dosyayı ve iki-üç metadata alanını
gönderiyoruz.

Fail-soft: internet/HTTP hatası ya da eksik secret durumunda script'i
ÇÖKERTMEZ, sadece uyarı basar — projedeki diğer "best-effort" işlemlerle
(bkz. git_utils.trigger_workflow) aynı felsefe. Kitabın kendisi (epub +
main'e PR) bu adımdan tamamen bağımsız, ingest başarısız olsa bile PR
açılmaya devam eder; bir sonraki convert.yml çalıştırması (örn. admin
epub'ı elle düzenleyip tekrar convert tetiklerse) zaten aynı sourceKey
ile tekrar dener.
"""
import os

import requests

INGEST_TIMEOUT_SECONDS = 60


def push_book(book_slug: str, epub_path: str, title: str,
              author: str | None = None, description: str | None = None) -> None:
    """
    eptran-web'in /api/ingest'ine tek bir epub kitabı gönderir.

    WEB_INGEST_URL   : örn. https://eptran-web-virid.vercel.app/api/ingest
    WEB_INGEST_SECRET: eptran-web'deki INGEST_SECRET ile AYNI değer
                        (Vercel projesindeki env var'ın GitHub Actions
                        secret'ı olarak kopyası)

    İkisinden biri eksikse (henüz kurulmamışsa) sessizce (ama görünür bir
    uyarıyla) atlanır — kitabın epub'a ciltlenip main'e PR açılması buna
    bağlı değil.
    """
    url = os.environ.get("WEB_INGEST_URL")
    secret = os.environ.get("WEB_INGEST_SECRET")

    if not url or not secret:
        print("  Uyarı: WEB_INGEST_URL / WEB_INGEST_SECRET tanımlı değil — "
              "eptran-web'e gönderim atlandı (bkz. README kurulum adımı).")
        return

    if not os.path.exists(epub_path):
        print(f"  Uyarı: {epub_path} bulunamadı — eptran-web'e gönderim atlandı.")
        return

    data = {"sourceKey": book_slug, "title": title, "format": "epub"}
    if author:
        data["author"] = author
    if description:
        data["description"] = description

    try:
        with open(epub_path, "rb") as f:
            files = {"file": (os.path.basename(epub_path), f, "application/epub+zip")}
            resp = requests.post(
                url, data=data, files=files,
                headers={"Authorization": f"Bearer {secret}"},
                timeout=INGEST_TIMEOUT_SECONDS,
            )
    except requests.RequestException as e:
        print(f"  Uyarı: eptran-web'e gönderim başarısız (ağ hatası): {e}")
        return

    if resp.status_code != 200:
        print(f"  Uyarı: eptran-web /api/ingest {resp.status_code} döndü: "
              f"{resp.text[:300]}")
        return

    try:
        result = resp.json()
    except ValueError:
        print("  eptran-web'e gönderildi (yanıt JSON değil, ama 200 OK).")
        return

    print(f"  eptran-web'e gönderildi: novelId={result.get('novelId')}, "
          f"yeni bölüm={result.get('chaptersCreated')}, "
          f"güncellenen bölüm={result.get('chaptersUpdated')}")
