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
    rapor.
    output/<slug>/.qa_progress.json — checkpoint dosyası (bkz. aşağıdaki
    NOT). Denetim tamamlanınca otomatik silinir.

NOT (Ağustos 2026, CHECKPOINT — gerçek üretim krizi): İlk sürümde bu
script tüm kitabı TEK SEFERDE denetleyip raporu SADECE EN SONDA
yazıyordu. Gerçek üretimde (knh-11) Gemini'nin ücretsiz katmanı
`gemini-3.5-flash` için günde SADECE 20 istekle sınırlı çıktı — 35
bölümlük kitabın 22. bölümünde kota tükendi, script kalan 13 bölüm
için anlamsızca tekrar tekrar denemeye devam etti (her biri 20-40-60
saniye beklemeyle), admin sabrı taşıp çalıştırmayı iptal etti — ve o
ana kadar başarıyla denetlenen 21 bölümün SONUCU DA KAYBOLDU, çünkü
hiçbir ara kayıt yoktu.

Artık her bölümden SONRA (başarılı ya da başarısız) ilerleme
output/<slug>/.qa_progress.json'a yazılıyor. Script tekrar
çalıştırıldığında (aynı gün kota dolmuşsa ertesi gün, ya da farklı bir
key/model ile) KALDIĞI YERDEN devam ediyor, baştan başlamıyor. Ayrıca
GÜNLÜK kota hatası (DailyQuotaExceeded) tespit edilirse script kalan
bölümler için boşuna denemez, hemen durur ve mevcut ilerlemeyi
kaydedip net bir mesajla çıkar.

Neden Gemini (Qwen değil): Aynı modelin kendi çıktısını kendi
denetlemesi, aynı kör noktaları paylaşma riski taşır. Farklı bir model
ailesi, farklı hatalara farklı şekilde "takılır" — iki modelin ortak
kaçırdığı şeyler daha az olur.
"""
import argparse
import json
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
- İNGİLİZCE_KALINTI: Türkçe çeviri metninde, ÇEVRİLMESİ GEREKİRKEN
  İngilizce bırakılmış tek bir kelime ya da kısa bir ifade (örn. bir
  fiil, sıfat ya da bağlaç İngilizce kalmış). Aşağıda "SABİTLENMİŞ
  İSİM/TERİM SÖZLÜĞÜ" verilmişse oradaki isimleri ya da bilinçli olarak
  Latin harfleriyle bırakılan özel isimleri/başlıkları BUNA DAHIL ETME
  — sadece gerçekten çevrilmesi unutulmuş sıradan kelimeleri işaretle.

Emin olmadığın, sadece ÜSLUP tercihi olabilecek (örn. "ne yapıyorsun"
vs "ne halt ediyorsun" gibi ton farkları) şeyleri RAPORLAMA — bunlar
gerçek hata değil. Sadece gerçekten emin olduğun, somut sorunları bildir.

SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{"issues": [{"type": "ATLANMIŞ|ANLAM_KAYMASI|TUTARSIZ_TERİM|ŞAHIS_UYUŞMAZLIĞI|İNGİLİZCE_KALINTI",
"source_quote": "kaynaktan, harfi harfine KOPYALANMIŞ bir alıntı",
"translation_quote": "çeviriden, harfi harfine KOPYALANMIŞ bir alıntı (yoksa boş) — KISALTMA, ÖZETLEME ya da PARAFRAZ ETME; metinde birebir NASIL geçiyorsa (noktalama, tırnak işaretleri, büyük/küçük harf dahil) AYNEN öyle aktar. Sorunlu ifade uzun bir cümlenin ortasındaysa bile TAM CÜMLEYİ (nokta/virgülüyle) ver — kısa bir parça değil. Bu alan daha sonra dosyada BİREBİR ARANACAK; tek bir karakter bile farklıysa eşleşme başarısız olur ve düzeltme uygulanamaz.",
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


def _progress_path(output_dir: str) -> str:
    return os.path.join(output_dir, ".qa_progress.json")


def _load_progress(output_dir: str) -> dict:
    path = _progress_path(output_dir)
    if not os.path.exists(path):
        return {"completed": {}, "failed": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_progress(output_dir: str, progress: dict) -> None:
    with open(_progress_path(output_dir), "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def _write_report(output_dir: str, slug: str, chapters: list, progress: dict,
                   n: int, note: str = "") -> int:
    """Checkpoint'teki mevcut sonuçlardan raporu (yeniden) üretir."""
    report_lines = [f"# QA Raporu — {slug}", ""]
    total_issues = 0
    completed = progress["completed"]
    failed = set(progress["failed"])

    for i in range(1, n + 1):
        key = str(i)
        if key in completed:
            issues = completed[key]
            if issues:
                title = chapters[i - 1]["title"] if i <= len(chapters) else f"#{i}"
                report_lines.append(f"## Bölüm {i}: {title} — {len(issues)} sorun")
                for issue in issues:
                    report_lines.append(f"- **{issue.get('type', '?')}**: {issue.get('description', '')}")
                    if issue.get("source_quote"):
                        report_lines.append(f"  - Kaynak: *\"{issue['source_quote']}\"*")
                    if issue.get("translation_quote"):
                        report_lines.append(f"  - Çeviri: *\"{issue['translation_quote']}\"*")
                report_lines.append("")
                total_issues += len(issues)
        elif i in failed or key in [str(x) for x in failed]:
            title = chapters[i - 1]["title"] if i <= len(chapters) else f"#{i}"
            report_lines.append(f"## Bölüm {i}: {title}")
            report_lines.append("*(Denetlenemedi.)*\n")

    checked = len(completed)
    failed_n = len(progress["failed"])
    remaining = n - checked - failed_n

    if note:
        header = note
    elif remaining > 0:
        header = (f"**KISMİ RAPOR: {checked}/{n} bölüm tarandı, {remaining} bölüm "
                   f"henüz denetlenmedi (muhtemelen kota/kesinti). Script'i "
                   f"tekrar çalıştırınca kaldığı yerden devam edecek.**\n")
    elif failed_n > 0 and checked < n * 0.5:
        header = (f"**UYARI: {failed_n}/{n} bölüm denetlenemedi (Gemini hatası) "
                   f"— bu rapor GÜVENİLİR DEĞİL. Yukarıdaki log'ları kontrol "
                   f"edip tekrar çalıştırın.**\n")
    else:
        header = (f"**Toplam {total_issues} şüpheli nokta bulundu "
                   f"({checked}/{n} bölüm başarıyla tarandı"
                   + (f", {failed_n} bölüm denetlenemedi" if failed_n else "")
                   + ").**\n")

    report_lines.insert(2, header)
    report_lines.insert(3, "*Bu bir OTOMATİK ÖNERİ listesidir, kesin doğru "
                           "kabul etmeyin — her maddeyi kaynakla birlikte "
                           "kendiniz kontrol edin. Bazı işaretlemeler yanlış "
                           "pozitif olabilir (bkz. script docstring'i).*\n")

    report_path = os.path.join(output_dir, "qa_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    return total_issues


def _load_series_glossary(slug: str) -> str:
    """
    Bu kitabın ait olduğu serinin karakter/terim sözlüğünü (series/<seri
    slug>.json) okuyup Gemini'nin denetim prompt'una eklenecek bir blok
    olarak döner. Sözlük yoksa ya da boşsa "" döner.

    NEDEN GEREKLİ: Gemini'ye şimdiye kadar SADECE tek bir bölümün kaynak+
    çeviri metni veriliyordu — kitabın/serinin kendi karakter isimleri ve
    terim kararları hakkında HİÇBİR BAĞLAM yoktu. Bu yüzden:
      1) Doğru ve KASITLI çevrilmiş isimler/terimler bazen yanlışlıkla
         ANLAM_KAYMASI ya da TUTARSIZ_TERİM diye işaretlenebiliyordu —
         Gemini'nin "doğru" kabul edeceği bir referansı yoktu.
      2) TUTARSIZ_TERİM kontrolü SADECE o bölümün İÇİNDE tutarlılığa
         bakabiliyordu — bölümler arası (örn. 3. bölümde "Gyoku-ou",
         20. bölümde "Gyokuou" gibi) tutarsızlıkları YAKALAYAMIYORDU,
         çünkü Gemini her bölümü birbirinden habersiz, izole
         görüyordu.
    Bu sözlük artık her bölüm isteğine ekleniyor — Gemini artık hem
    "bu isim burada neden böyle" diye tahmin etmek zorunda kalmıyor
    hem de kitabın GENELİNDE sabitlenmiş isimlerle bu bölümü
    karşılaştırabiliyor.
    """
    status_path = "status.json"
    series_slug = None
    if os.path.exists(status_path):
        with open(status_path, encoding="utf-8") as f:
            series_slug = json.load(f).get("series")
    if not series_slug:
        return ""

    data = series_lib.load(series_slug)
    characters = data.get("characters", {})
    terms = data.get("terms", {})
    if not characters and not terms:
        return ""

    lines = [
        "\n\nBU SERİ İÇİN SABİTLENMİŞ İSİM/TERİM SÖZLÜĞÜ (bunlar KASITLI "
        "kararlardır — aşağıdaki eşleşmelerden biri bölümde doğru "
        "kullanılmışsa bunu ASLA ANLAM_KAYMASI ya da TUTARSIZ_TERİM diye "
        "işaretleme; ama bölüm bu eşleşmelerden FARKLI bir çeviri "
        "kullanıyorsa bu GERÇEK bir TUTARSIZ_TERİM sorunudur):"
    ]
    for eng, tr in characters.items():
        lines.append(f"- {eng} → {tr}")
    for eng, tr in terms.items():
        lines.append(f"- {eng} → {tr}")
    return "\n".join(lines)


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

    glossary_block = _load_series_glossary(slug)
    audit_system = _AUDIT_SYSTEM + glossary_block
    if glossary_block:
        print(f"  Seri sözlüğü yüklendi ({glossary_block.count(chr(10)) - 1} "
              f"madde) — denetim buna göre karşılaştıracak.")

    clients = gem.get_clients()
    key_index = [0]
    progress = _load_progress(output_dir)
    n = len(chapters) if max_chapters is None else min(max_chapters, len(chapters))

    already_done = len(progress["completed"]) + len(progress["failed"])
    if already_done:
        print(f"Devam ediliyor: {already_done}/{n} bölüm daha önce işlenmiş "
              f"(checkpoint bulundu), kalan {n - already_done} bölümden devam.")

    stopped_early = False
    for i in range(1, n + 1):
        key = str(i)
        if key in progress["completed"] or i in progress["failed"]:
            continue  # zaten checkpoint'te var, atla

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
        try:
            raw = gem.call(clients, key_index, audit_system, user_msg, temperature=0.1)
        except gem.AllKeysExhausted:
            print(f"\n  Elimizdeki tüm Gemini key'lerinin günlük kotası tükendi "
                  f"({i}/{n}. bölümde). Kalan bölümler için boşuna denenmiyor — "
                  f"ilerleme kaydedildi, script'i yarın (ya da yeni bir key "
                  f"eklendiğinde) tekrar çalıştırınca kaldığı yerden devam edecek.")
            stopped_early = True
            break
            stopped_early = True
            break

        if raw is None:
            progress["failed"].append(i)
            _save_progress(output_dir, progress)
            continue

        try:
            data = gem.extract_json(raw)
            issues = data.get("issues", [])
        except Exception as e:
            print(f"    Yanıt ayrıştırılamadı: {e}")
            progress["failed"].append(i)
            _save_progress(output_dir, progress)
            continue

        progress["completed"][key] = issues
        _save_progress(output_dir, progress)  # HER bölümden sonra checkpoint

    note = ""
    if stopped_early:
        checked = len(progress["completed"])
        note = (f"**Günlük Gemini kotası tükendiği için durduruldu — "
                f"{checked}/{n} bölüm tarandı. Script'i tekrar çalıştırınca "
                f"kaldığı yerden devam edecek (baştan başlamayacak).**\n")

    total_issues = _write_report(output_dir, slug, chapters, progress, n, note)

    # Denetim (bu run'ın erişebildiği kadarıyla) tamamlandıysa checkpoint'i
    # temizle — bir sonraki tam taramanın sıfırdan başlaması için.
    if not stopped_early and len(progress["completed"]) + len(progress["failed"]) >= n:
        prog_path = _progress_path(output_dir)
        if os.path.exists(prog_path):
            os.remove(prog_path)
        print(f"\nDenetim tamamlandı. Rapor: output/{slug}/qa_report.md "
              f"({total_issues} şüpheli nokta)")
    else:
        print(f"\nKısmi rapor yazıldı: output/{slug}/qa_report.md "
              f"({total_issues} şüpheli nokta, checkpoint korunuyor)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="Kitap slug'ı, örn. knh-11")
    parser.add_argument("--max-chapters", type=int, default=None,
                        help="Test için ilk N bölümle sınırla")
    args = parser.parse_args()
    audit_book(args.slug, args.max_chapters)
