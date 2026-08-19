"""
eptran — scripts/pr_check.py

Bir kitap dalının (book/<slug>) main'e açtığı "tamamlandı" PR'ını,
GERÇEK MERGE'DEN ÖNCE otomatik denetler. Amaç: bu projede zaten canlıda
yaşanmış hata sınıflarının hiçbirinin fark edilmeden main'e girmemesi —
şu ana kadar bunların hepsini BEN (Claude) elle, log inceleyerek
buluyordum; bu script aynı kontrolleri PR açıldığı anda otomatik yapıp
kırmızı/yeşil bir GitHub check olarak gösteriyor.

KAPSAM — geçmişte gerçekten yaşanmış, somut hata sınıfları:
1. "Bölüm eşleştirilemedi" (knh-11, 18 Ağustos) — bölünmüş bölümler
   çeviride birleşmemişti, 8 bölüm epub'a hiç girmemişti. convert.py'yi
   gerçekten çalıştırıp bu uyarıyı arıyoruz.
2. İngilizce başlık sızıntısı (knh-11) — Türkçe başlık satırı ünlem/
   soru işaretiyle bittiği için tespit edilemeyip İngilizcesi kalmıştı.
3. Kalıntı İngilizce kelime (pg2147, tekrar tekrar) — review'dan
   kaçmış, whitelist'te olmayan gerçek İngilizce kalıntılar.
4. Eksik/boş bölüm dosyaları — status.json'daki sayı ile gerçek dosya
   sayısı tutmuyorsa.

BU SCRIPT HİÇBİR ŞEYİ DÜZELTMEZ, sadece bulur ve raporlar (projenin
genel ilkesi — bkz. qa_audit.py, series.py docstring'leri). Sorun
bulunursa exit code 1 ile çıkar; bu, GitHub Actions'ta job'ı
"failed" (kırmızı X) yapar. PR'da görünür ama branch protection
kurulmadıkça merge'i FİZİKSEL OLARAK ENGELLEMEZ — sadece uyarır. Sert
engel istenirse repo Settings > Branches'te bu check "required" olarak
işaretlenmeli.

Kullanım:
    python scripts/pr_check.py <kitap-slug>
"""
import argparse
import io
import json
import os
import re
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(__file__))
from convert import load_txt_chapters, build_epub, find_original_epub  # noqa: E402
from lib import english_detector, boilerplate  # noqa: E402
from lib import memory as mem  # noqa: E402
from lib.review_fix import _build_whitelist  # noqa: E402


def _english_looking_title(title: str) -> bool:
    """
    Başlık satırının hâlâ İngilizce kalmış olma ihtimalini kaba bir
    şekilde yoklar: yaygın İngilizce başlık kelimeleriyle başlıyor ve
    hiç Türkçe'ye özgü karakter (ç,ğ,ı,ö,ş,ü) içermiyorsa şüpheli say.
    Kusursuz değil ama ucuz ve gerçek üretim hatasını (knh-11) doğrudan
    yakalıyor.
    """
    if re.match(r'^(chapter|prologue|epilogue|part|volume)\b', title, re.IGNORECASE):
        return True
    has_tr_chars = bool(re.search(r'[çğıöşüÇĞİÖŞÜ]', title))
    has_common_en_words = bool(re.search(
        r'\b(the|and|of|to|in|with|his|her)\b', title, re.IGNORECASE))
    return has_common_en_words and not has_tr_chars


def check_book(slug: str) -> list:
    """Sorun listesini döner — boşsa kitap temiz demektir."""
    problems = []
    output_dir = f"output/{slug}"
    status_path = "status.json"

    if not os.path.isdir(output_dir):
        return [f"output/{slug}/ klasörü hiç yok."]

    # 1) status.json tutarlılığı
    if os.path.exists(status_path):
        status = json.load(open(status_path, encoding="utf-8"))
        if status.get("convert_status") != "completed":
            problems.append(f"status.json: convert_status={status.get('convert_status')!r} (completed değil).")
        if status.get("review_status") != "completed":
            problems.append(f"status.json: review_status={status.get('review_status')!r} (completed değil).")

    txt_files = sorted(f for f in os.listdir(output_dir) if re.match(r"^\d{3}_.+\.txt$", f))
    if not txt_files:
        problems.append("Hiç çeviri (.txt) dosyası bulunamadı.")
        return problems

    # 2) convert.py'yi GERÇEKTEN çalıştırıp "eşleştirilemedi" uyarısını yakala
    #    (bkz. docstring madde 1 — knh-11'de 8 bölüm böyle kaybolmuştu)
    chapters = load_txt_chapters(output_dir)
    orig_path = find_original_epub(slug)
    if orig_path:
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                build_epub(slug, chapters, orig_path, "/tmp/_pr_check_build.epub")
        except Exception as e:
            problems.append(f"convert.py çalıştırılırken hata: {e}")
        output = buf.getvalue()
        m = re.search(r"Uyarı: (\d+) bölüm eşleştirilemedi", output)
        if m:
            problems.append(
                f"{m.group(1)} bölüm epub'a eşleştirilemedi — bunlar epub'a hiç "
                f"girmemiş olabilir (bkz. translate.py'nin bölünmüş-bölüm "
                f"birleştirme mantığı)."
            )
    else:
        problems.append(f"input/.originals/{slug}.epub|.pdf bulunamadı — "
                        f"epub yeniden derlenip doğrulanamadı.")

    # 3) Her dosyanın başlığını ve gövdesini kontrol et
    memory = mem.load(output_dir)
    whitelist = _build_whitelist(memory)
    suspicious_titles = []
    english_residue_files = []

    for fname in txt_files:
        path = os.path.join(output_dir, fname)
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        parts = raw.split("\n\n", 2)
        if len(parts) < 3 or not parts[0].startswith("#"):
            continue
        tr_title, body = parts[1].strip(), parts[2].strip()

        if _english_looking_title(tr_title):
            suspicious_titles.append((fname, tr_title))

        if not body:
            problems.append(f"{fname}: gövde tamamen boş.")
            continue

        cleaned = boilerplate.clean(body)
        eng_words = english_detector.find(cleaned)
        truly_bad = [w for w in eng_words if w.lower() not in whitelist]
        if truly_bad:
            english_residue_files.append((fname, truly_bad[:5]))

    if suspicious_titles:
        problems.append(
            f"{len(suspicious_titles)} dosyanın başlığı İngilizce kalmış "
            f"olabilir: " + ", ".join(f"{f} ({t[:30]!r})" for f, t in suspicious_titles[:5])
            + (" ..." if len(suspicious_titles) > 5 else "")
        )

    if english_residue_files:
        problems.append(
            f"{len(english_residue_files)} dosyada whitelist dışı İngilizce "
            f"kalıntı kelime var: " + ", ".join(
                f"{f} {words}" for f, words in english_residue_files[:5])
            + (" ..." if len(english_residue_files) > 5 else "")
        )

    return problems


def _check_gemini_report(output_dir: str) -> tuple:
    """
    Daha önce (qa_audit.py ile) üretilmiş bir Gemini denetim raporu
    varsa, bulgularını bu kontrole dahil eder.

    NEDEN SENKRON ÇALIŞTIRMIYORUZ: Gemini'nin ücretsiz katmanı günde
    ~20 istekle sınırlı (proje başına, key sayısı fark etmiyor — bkz.
    gemini_client.py). Bunu PR check'in İÇİNE senkron koysaydık, büyük
    bir kitapta check günlerce "beklemede" kalır, merge'i pratikte
    süresiz bekletirdi. Bunun yerine: admin "QA Audit (Gemini)"
    workflow'unu ayrı, kendi hızında (checkpoint'li, günler sürebilen)
    çalıştırır; BU fonksiyon sadece o ÇALIŞMANIN ÇIKTISINI (varsa)
    okuyup PR check'e dahil eder. Rapor yoksa/eskiyse bunu SORUN değil,
    sadece BİLGİ notu sayıyoruz — Gemini denetimi opsiyonel bir katman,
    deterministik kontroller (bölüm kaybı, kalıntı kelime vb.) kadar
    "zorunlu" değil.

    Döner: (problems, info_notes) — problems exit code'u etkiler,
    info_notes sadece bilgilendirme amaçlı.
    """
    problems, info = [], []
    report_path = os.path.join(output_dir, "qa_report.md")
    progress_path = os.path.join(output_dir, ".qa_progress.json")

    if os.path.exists(progress_path):
        info.append(
            "Gemini denetimi yarım kalmış (checkpoint mevcut) — muhtemelen "
            "günlük kota yüzünden duraklamış. 'QA Audit (Gemini)' workflow'unu "
            "tekrar çalıştırınca kaldığı yerden devam edecek."
        )

    if not os.path.exists(report_path):
        info.append(
            "Henüz bir Gemini denetim raporu yok. İsteğe bağlı: Actions'tan "
            "'QA Audit (Gemini)' çalıştırıp kaynakla karşılaştırmalı ek bir "
            "denetim yaptırabilirsin."
        )
        return problems, info

    with open(report_path, encoding="utf-8") as f:
        report = f.read()

    m = re.search(r"\*\*(.+?)\*\*", report)
    summary = m.group(1) if m else ""

    if "KISMİ RAPOR" in summary or "UYARI" in summary:
        info.append(f"Gemini raporu tam/güvenilir değil: {summary}")
    else:
        m2 = re.search(r"Toplam (\d+) şüpheli nokta", summary)
        n_issues = int(m2.group(1)) if m2 else 0
        if n_issues > 0:
            problems.append(
                f"Gemini denetimi {n_issues} şüpheli nokta buldu (bkz. "
                f"output/{os.path.basename(output_dir)}/qa_report.md). "
                f"BU BİR ÖNERİ LİSTESİ, kesin hata anlamına gelmez — her "
                f"maddeyi kaynakla birlikte kendin kontrol et."
            )
        else:
            info.append("Gemini denetimi tamamlanmış, şüpheli nokta bulunamamış.")

    return problems, info


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="Kitap slug'ı, örn. knh-11")
    parser.add_argument("--skip-gemini-report", action="store_true",
                        help="Var olan qa_report.md'yi bile kontrole dahil etme")
    args = parser.parse_args()

    problems = check_book(args.slug)
    info = []

    if not args.skip_gemini_report:
        gemini_problems, gemini_info = _check_gemini_report(f"output/{args.slug}")
        problems += gemini_problems
        info += gemini_info

    if info:
        print("ℹ️  Bilgi:")
        for note in info:
            print(f"  - {note}")
        print()

    if problems:
        print(f"❌ {args.slug}: {len(problems)} sorun bulundu:\n")
        for p in problems:
            print(f"  - {p}")
        print("\nBu sorunlar merge'i FİZİKSEL OLARAK engellemiyor (branch "
              "protection kurulmadıysa) ama önce kontrol edilmeli.")
        sys.exit(1)
    else:
        print(f"✅ {args.slug}: bilinen hata sınıflarından hiçbiri bulunamadı.")
        sys.exit(0)
