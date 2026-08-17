"""
eptran — scripts/series_suggest.py

Bir kitabın çevirisi bittiğinde, o kitabın hafızasından (memory.json)
ve özetlerinden yola çıkarak Gemini'ye series/<slug>.json glossary'sine
eklenebilecek YENİ karakter/terim/not önerileri ürettirir.

KESİNLİKLE OTOMATİK YAZMAZ — bkz. lib/series.py'nin tasarım ilkesi:
"otomatik keşif OLUR, otomatik YAZMA OLMAZ". Bu script de aynı ilkeye
uyuyor: önerileri series/<slug>.suggested.json'a yazar, gerçek
series/<slug>.json dosyasına HİÇ dokunmaz. Admin bu öneri dosyasını
inceleyip beğendiklerini elle asıl dosyaya taşır.

Neden otomatik yazmıyoruz: series glossary'si TÜM seriyi (geçmiş VE
gelecek ciltler) etkiliyor — buraya giren bir hata knh-10'daki
Lakan/Lahan karışıklığının 10 bölüme yayılmasından çok daha büyük bir
"blast radius"a sahip olurdu (tüm seri boyunca). Gemini'nin önerileri
genelde isabetli olsa da, "otomatik + geri dönüşü zor + geniş etki
alanı" kombinasyonu bu projede zaten bir kez pahalıya patlamıştı
(review_fix.py'deki ilk tutarlılık kontrolü örneği) — aynı hatayı
seri seviyesinde tekrarlamıyoruz.

Kullanım:
    python scripts/series_suggest.py <kitap-slug>
"""
import argparse
import json
import os

from lib import gemini_client as gem
from lib import series as series_lib


_SUGGEST_SYSTEM = """Sen bir çeviri serisi editörüsün. Sana tamamlanmış bir
kitabın çeviri hafızası (karakterler, terimler) ve bu serinin ZATEN VAR OLAN
glossary'si verilecek. Görevin: glossary'de EKSİK olan ama gelecekteki
ciltlerin tutarlılığı için önemli olabilecek YENİ karakter/terim/not
önerileri üretmek.

Özellikle şunlara odaklan:
- Karakterler arası KARIŞTIRILABİLECEK benzer isimler (örn. iki karakterin
  ismi birbirine çok benziyorsa, hangisinin kim olduğunu netleştiren bir not).
- Aile/unvan ilişkileri (kim kimin kardeşi/çocuğu/vekili gibi) — bunlar
  yanlış çevrilirse anlam tamamen değişir.
- Zaten glossary'de olan bir karakterin BURADA farklı yazıldığını fark
  edersen, bunu da not olarak belirt (glossary'nin kendisi güncellenmeli
  olabilir, ama bunu SEN karar vermiyorsun, sadece işaret ediyorsun).

Glossary'de ZATEN olan karakterleri/terimleri TEKRAR ÖNERME.

SADECE şu JSON formatında yanıt ver:
{"new_characters": {"İngilizce isim": "Türkçe karşılık"},
"new_terms": {"terim": "Türkçe karşılık"},
"new_notes": ["gelecekteki ciltler için önemli, serbest metin bir not", ...]}"""


def suggest_for_book(slug: str, series_slug: str):
    output_dir = f"output/{slug}"
    memory_path = os.path.join(output_dir, "memory.json")
    if not os.path.exists(memory_path):
        print(f"Hata: {memory_path} bulunamadı.")
        return

    with open(memory_path, encoding="utf-8") as f:
        memory = json.load(f)

    existing = series_lib.load(series_slug)
    model = gem.get_client()

    summaries = "\n".join(memory.get("summaries", [])[:40])
    user_msg = (
        f"Kitabın karakterleri: {json.dumps(memory.get('characters', {}), ensure_ascii=False)}\n\n"
        f"Kitabın terimleri: {json.dumps(memory.get('terms', {}), ensure_ascii=False)}\n\n"
        f"Serinin ZATEN VAR OLAN glossary'si — karakterler: "
        f"{json.dumps(existing.get('characters', {}), ensure_ascii=False)}\n"
        f"terimler: {json.dumps(existing.get('terms', {}), ensure_ascii=False)}\n"
        f"notlar: {json.dumps(existing.get('notes', []), ensure_ascii=False)}\n\n"
        f"Kitabın bölüm özetleri:\n{summaries[:6000]}"
    )
    raw = gem.call(model, _SUGGEST_SYSTEM, user_msg, temperature=0.2)
    if raw is None:
        print("Gemini'den yanıt alınamadı, öneri üretilemedi.")
        return

    try:
        data = gem.extract_json(raw)
    except Exception as e:
        print(f"Yanıt ayrıştırılamadı: {e}\nHam yanıt:\n{raw}")
        return

    suggestion = {
        "_meta": (
            f"Bu dosya OTOMATİK ÜRETİLDİ ({slug} kitabından, Gemini ile). "
            f"series/{series_slug}.json'a hiç yazılmadı — beğendiğin "
            f"maddeleri ELLE oraya taşı, sonra bu dosyayı silebilirsin."
        ),
        "source_book": slug,
        "new_characters": data.get("new_characters", {}),
        "new_terms": data.get("new_terms", {}),
        "new_notes": data.get("new_notes", []),
    }

    out_path = os.path.join(series_lib.SERIES_DIR, f"{series_slug}.suggested.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(suggestion, f, ensure_ascii=False, indent=2)

    n = (len(suggestion["new_characters"]) + len(suggestion["new_terms"])
         + len(suggestion["new_notes"]))
    print(f"{n} öneri yazıldı: {out_path}")
    print("Bunlar ASIL series dosyasına otomatik eklenmedi — inceleyip elle taşı.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="Kitap slug'ı, örn. knh-11")
    parser.add_argument("--series", help="Seri slug'ı (verilmezse status.json'dan okunur)")
    args = parser.parse_args()

    series_slug = args.series
    if not series_slug:
        status_path = "status.json"
        if os.path.exists(status_path):
            with open(status_path, encoding="utf-8") as f:
                series_slug = json.load(f).get("series")
    if not series_slug:
        print("Hata: seri belirtilmedi (--series ver ya da status.json'da 'series' olsun).")
    else:
        suggest_for_book(args.slug, series_slug)
