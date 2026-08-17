"""
eptran — scripts/qa_audit.py

Tamamlanmış bir kitabın çevirisini, İngilizce KAYNAKLA karşılaştırarak
Gemini'ye denetletir. Amaç: Qwen'in çevirisindeki hataları (eksik/atlanmış
cümle, anlam kayması, tutarsız terim, kaynakla uyuşmayan 3./1. şahıs
karışıklığı gibi) YAKALAMAK — bu script HİÇBİR ŞEYİ OTOMATİK DÜZELTMEZ,
sadece bir rapor üretir. Sebebini bu projede zaten acı yoldan öğrendik:
"Patron ve Eski Patron" örneğinde ilk bakışta hatalı görünen bir çeviri
aslında doğruydu (bölüm başlığının kasıtlı yankısıydı); otomatik bir
araç bunu körü körüne "düzeltseydi" iyi bir çeviriyi bozardı. Bu yüzden
bu araç sadece ŞÜPHELİ yerleri işaretler, kararı admin'e bırakır.

Kullanım:
    python scripts/qa_audit.py <kitap-slug>

Çıktı:
    output/<slug>/qa_report.md — okunabilir, chapter/paragraf referanslı
    rapor. Var olan bir rapor varsa üzerine yazılır (her taramada temiz
    başlar).

Neden Gemini (Qwen değil): Aynı modelin kendi çıktısını kendi
denetlemesi, aynı kör noktaları paylaşma riski taşır. Farklı bir model
ailesi, farklı hatalara farklı şekilde "takılır" — iki modelin ортak
kaçırdığı şeyler daha az olur.
"""
import argparse
import os
import sys

from lib import gemini_client as gem
from lib import series as series_lib

sys.path.insert(0, os.path.dirname(__file__))
from translate import extract_epub, extract_pdf  # noqa: E402


_AUDIT_SYSTEM = """Sen iki dilli (İngilizce-Türkçe) bir edebi çeviri editörüsün.
Sana bir bölümün İNGİLİZCE kaynağı ve onun TÜRKÇE çevirisi verilecek.
Görevin ÇEVİRİYİ DEĞİL, sadece SORUNLARI bulmak.

Şunları ara:
- ATLANMIŞ: kaynakta olan ama çeviride hiç karşılığı olmayan cümle/paragraf.
- ANLAM_KAYMASI: çeviri kaynaktan gerçekten farklı bir şey söylüyor
  (üslup farkı değil, gerçek anlam hatası).
- TUTARSIZ_TERİM: aynı isim/terim bu bölüm içinde birden fazla farklı
  şekilde çevrilmiş.
- ŞAHIS_UYUŞMAZLIĞI: çeviride 3./1. şahıs karışıklığı var AMA bu
  kaynakta YOK (yani çevirmen hatası, kaynağın kendi üslubu değil —
  bunu ayırt etmek için kaynağı da kontrol et, kaynakta da aynı
  karışıklık varsa bu bir SORUN DEĞİL, atla).

Emin olmadığın, sadece ÜSLUP tercihi olabilecek (örn. "ne yapıyorsun"
vs "ne halt ediyorsun" gibi ton farkları) şeyleri RAPORLAMA — bunlar
gerçek hata değil. Sadece gerçekten emin olduğun, somut sorunları bildir.

SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{"issues": [{"type": "ATLANMIŞ|ANLAM_KAYMASI|TUTARSIZ_TERİM|ŞAHIS_UYUŞMAZLIĞI",
"source_quote": "kaynaktan kısa alıntı (en fazla 15 kelime)",
"translation_quote": "çeviriden kısa alıntı (en fazla 15 kelime, yoksa boş)",
"description": "sorunun kısa açıklaması (1-2 cümle)"}]}
Hiç sorun yoksa {"issues": []} döndür."""


def _load_translated(output_dir: str, index: int, slug: str) -> tuple:
    path = os.path.join(output_dir, f"{index:03d}_{slug}.txt")
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    parts = raw.split("\n\n", 2)
    if parts[0].startswith("#") and len(parts) == 3:
        return parts[1].strip(), parts[2].strip()
    return None, raw.strip()


def _find_original(slug: str) -> str | None:
    for ext in (".epub", ".pdf"):
        path = f"input/.originals/{slug}{ext}"
        if os.path.exists(path):
            return path
    return None


def audit_book(slug: str, max_chapters: int | None = None):
    output_dir = f"output/{slug}"
    orig_path = _find_original(slug)
    if not orig_path:
        print(f"Hata: input/.originals/{slug}.epub|.pdf bulunamadı — "
              f"kaynak metin olmadan denetim yapılamaz.")
        return

    if orig_path.endswith(".epub"):
        chapters, _, _ = extract_epub(orig_path)
    else:
        chapters, _ = extract_pdf(orig_path, slug)

    model = gem.get_client()
    report_lines = [f"# QA Raporu — {slug}", ""]
    total_issues = 0

    n = len(chapters) if max_chapters is None else min(max_chapters, len(chapters))
    for i in range(1, n + 1):
        src_chapter = chapters[i - 1]
        tr_title, tr_body = _load_translated(output_dir, i, slug)
        if tr_body is None:
            print(f"  [{i}/{n}] çeviri dosyası bulunamadı, atlanıyor.")
            continue

        print(f"  [{i}/{n}] {src_chapter['title'][:40]!r} denetleniyor...")
        user_msg = (
            f"KAYNAK (İngilizce):\n{src_chapter['text'][:8000]}\n\n"
            f"ÇEVİRİ (Türkçe):\n{tr_body[:8000]}"
        )
        raw = gem.call(model, _AUDIT_SYSTEM, user_msg, temperature=0.1)
        if raw is None:
            report_lines.append(f"## Bölüm {i}: {src_chapter['title']}")
            report_lines.append("*(Gemini'den yanıt alınamadı, bu bölüm denetlenemedi.)*\n")
            continue

        try:
            data = gem.extract_json(raw)
            issues = data.get("issues", [])
        except Exception as e:
            report_lines.append(f"## Bölüm {i}: {src_chapter['title']}")
            report_lines.append(f"*(Yanıt ayrıştırılamadı: {e})*\n")
            continue

        if issues:
            report_lines.append(f"## Bölüm {i}: {src_chapter['title']} — {len(issues)} sorun")
            for issue in issues:
                report_lines.append(f"- **{issue.get('type', '?')}**: {issue.get('description', '')}")
                if issue.get("source_quote"):
                    report_lines.append(f"  - Kaynak: *\"{issue['source_quote']}\"*")
                if issue.get("translation_quote"):
                    report_lines.append(f"  - Çeviri: *\"{issue['translation_quote']}\"*")
            report_lines.append("")
            total_issues += len(issues)

    report_lines.insert(2, f"**Toplam {total_issues} şüpheli nokta bulundu "
                           f"({n} bölüm tarandı).**\n")
    report_lines.insert(3, "*Bu bir OTOMATİK ÖNERİ listesidir, kesin doğru "
                           "kabul etmeyin — her maddeyi kaynakla birlikte "
                           "kendiniz kontrol edin. Bazı işaretlemeler yanlış "
                           "pozitif olabilir (bkz. script docstring'i).*\n")

    report_path = os.path.join(output_dir, "qa_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\nRapor yazıldı: {report_path} ({total_issues} şüpheli nokta)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="Kitap slug'ı, örn. knh-11")
    parser.add_argument("--max-chapters", type=int, default=None,
                        help="Test için ilk N bölümle sınırla")
    args = parser.parse_args()
    audit_book(args.slug, args.max_chapters)
