"""
Orijinal epub'dan kapak resmini çıkarıp eptran-web için küçültür.

web_ingest.push_book() bunu, çağıran taraf açıkça bir kapak vermediyse
kendisi kullanır — böylece convert.py ve backfill_ingest.py'de hiçbir
değişiklik gerekmeden hem yeni kitaplar hem eski kitaplar kapağıyla
birlikte gönderilir.
"""
import io
import os

import ebooklib
from ebooklib import epub

MAX_WIDTH = 400
FALLBACK_MAX_BYTES = 1_000_000


def load_cover(book_slug: str, originals_dir: str = "input/.originals"):
    """
    input/.originals/<slug>.epub içinden kapak resmini bulur ve
    (bytes, mime) döner. Bulunamazsa ya da hata olursa None.

    Resim ~400px genişliğe küçültülüp JPEG'e çevrilir (site küçük bir grid
    kartında gösteriyor, DB'ye gömülüyor: birkaç on KB yeter). Pillow yoksa
    ham resim <=1MB ise olduğu gibi, değilse atlanır.

    Fail-soft: kapak çıkarılamaması çeviri/PR/ingest akışını asla etkilemez.
    """
    path = os.path.join(originals_dir, f"{book_slug}.epub")
    if not os.path.exists(path):
        return None

    try:
        book = epub.read_epub(path)

        item = next(iter(book.get_items_of_type(ebooklib.ITEM_COVER)), None)
        if item is None:
            images = list(book.get_items_of_type(ebooklib.ITEM_IMAGE))
            item = next((i for i in images if "cover" in i.get_name().lower()), None)
            if item is None and images:
                item = images[0]
        if item is None:
            return None

        raw = item.get_content()
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(raw)).convert("RGB")
            if img.width > MAX_WIDTH:
                new_h = round(img.height * MAX_WIDTH / img.width)
                img = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=82, optimize=True)
            return buf.getvalue(), "image/jpeg"
        except ImportError:
            mime = getattr(item, "media_type", None) or "image/jpeg"
            return (raw, mime) if len(raw) <= FALLBACK_MAX_BYTES else None
    except Exception as e:
        print(f"  Uyarı: kapak çıkarılamadı: {e}")
        return None
