"""
eptran-web'e (Astro + Turso) tamamlanan kitapları POST /api/ingest ile
gönderir.

NOT (Eylül 2026, gerçek üretim hatası): İlk sürüm burada ciltlenmiş
epub'ı (resimler dahil, 20-30MB) gönderiyordu. Bu, Vercel'in Serverless
Function istek gövdesi sınırına (~4.5MB) tosladı — 413 Request Entity
Too Large. Oysa eptran-web'in kendi ingest.ts'i epub'ı parse edip SADECE
düz metni (chapters.content) veritabanına yazıyor, resimleri zaten hiç
kullanmıyor. Yani epub göndermek en başından gereksiz bir israftı.

Artık her bölümü ayrı, küçük bir "NNN_slug.txt" dosyası olarak
(convert.py'nin load_txt_chapters()'ının zaten bellekte ayrıştırdığı
title/body ile, orijinal dosyadaki "# " başlık işaretçisi OLMADAN,
ingest.ts'in parseTxtChapter()'ının beklediği "ilk satır = başlık"
biçiminde) gönderiyoruz — tüm kitap için toplam yük genelde birkaç
yüz KB, 4.5MB sınırının çok altında.

Fail-soft: internet/HTTP hatası ya da eksik secret durumunda script'i
ÇÖKERTMEZ, sadece uyarı basar. Kitabın kendisi (epub + main'e PR) bu
adımdan tamamen bağımsız.
"""
import os

import requests

INGEST_TIMEOUT_SECONDS = 60


def push_book(book_slug: str, chapters: list, title: str,
              author: str | None = None, description: str | None = None) -> None:
    """
    eptran-web'in /api/ingest'ine bir kitabın TÜM bölümlerini format=txt
    olarak gönderir.

    chapters: convert.py'nin load_txt_chapters()'ından dönen liste —
              her eleman {"title": ..., "body": ...} içerir.

    WEB_INGEST_URL   : örn. https://eptran-web-virid.vercel.app/api/ingest
    WEB_INGEST_SECRET: eptran-web'deki INGEST_SECRET ile AYNI değer

    İkisinden biri eksikse sessizce (ama görünür bir uyarıyla) atlanır.
    """
    url = os.environ.get("WEB_INGEST_URL")
    secret = os.environ.get("WEB_INGEST_SECRET")

    if not url or not secret:
        print("  Uyarı: WEB_INGEST_URL / WEB_INGEST_SECRET tanımlı değil — "
              "eptran-web'e gönderim atlandı (bkz. README kurulum adımı).")
        return

    if not chapters:
        print("  Uyarı: gönderilecek bölüm yok — eptran-web'e gönderim atlandı.")
        return

    data = {"sourceKey": book_slug, "title": title, "format": "txt"}
    if author:
        data["author"] = author
    if description:
        data["description"] = description

    files = []
    for i, ch in enumerate(chapters):
        # parseTxtChapter ilk satırı başlık olarak alıyor — orijinal
        # dosyadaki "# " markdown işaretçisini burada BİLEREK atıyoruz,
        # yoksa sitede başlıklar "# Editor's Notes" gibi çirkin görünür.
        content = f"{ch['title']}\n\n{ch['body']}"
        fname = f"{i + 1:03d}_{book_slug}.txt"
        files.append(("files[]", (fname, content.encode("utf-8"), "text/plain")))

    try:
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
