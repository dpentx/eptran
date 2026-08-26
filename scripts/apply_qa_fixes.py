"""
eptran — scripts/apply_qa_fixes.py

qa_audit.py'nin ürettiği qa_report.md'deki (Gemini'nin bulduğu) somut
çeviri hatalarını Qwen'e (Groq) TEK TEK, HEDEFLİ şekilde düzelttirir.

NEDEN GÜVENLİ (önceki hatalardan ders): Bu projede daha önce iki kez
"otomatik düzeltme" gerçek zarar vermişti — review_fix.py'deki ilk
tutarlılık kontrolü (knh-10, "İmparator'un küçük kardeşi" örneği) ve
seri-geneli genişletme denemesi. İkisi de HEURISTIC'e (tahmine)
dayanıyordu: "bu kelime böyle geçiyor, muhtemelen yanlış" diyip
körlemesine düzeltiyordu. BU script farklı — Gemini'nin raporu zaten
KAYNAK ALINTI + HATALI ÇEVİRİ ALINTISI çiftini somut olarak veriyor,
tahmin yok. Yine de iki güvenlik katmanı var:
  1. Düzeltme SADECE `translation_quote` dosyada TAM/BİREBİR bulunursa
     uygulanır — bulunamazsa (rapor yazıldıktan sonra dosya değiştiyse,
     ya da alıntı ufak bir noktalama farkıyla kayıtlıysa) o madde
     ATLANIR, ASLA tahminle en yakın yere yapıştırılmaz.
  2. Qwen'e SADECE o tek cümle/ifade + kaynak + sorun açıklaması
     veriliyor, bütün bölüm yeniden çevrilmiyor — bu hem ucuz hem de
     "düzeltirken başka bir şeyi bozma" riskini en aza indiriyor.

Bu script hiçbir zaman "TUTARSIZ_TERİM" gibi translation_quote'u boş
olan (yani somut bir yer işaretlenmemiş) maddelere dokunmaz — onlar
hâlâ elle incelenmeli.

Kullanım:
    python scripts/apply_qa_fixes.py <kitap-slug>
"""
import argparse
import os
import re

from lib import groq_client as gc


_FIX_SYSTEM = """Sen profesyonel bir çevirmensin. Sana bir çeviri hatası
bildirilecek: kaynak (İngilizce) metin, mevcut (hatalı) Türkçe çeviri, ve
sorunun açıklaması. Görevin: SADECE o cümle/ifadeyi düzeltip doğru,
doğal Türkçe çevirisini vermek. Cümlenin geri kalanına (bağlama) sadık
kal, sadece belirtilen hatayı düzelt. Çıktı olarak YALNIZCA düzeltilmiş
Türkçe metni yaz — tırnak işareti, açıklama, ek yorum EKLEME."""


def _parse_report(path: str) -> dict:
    """
    qa_report.md'yi ayrıştırır.
    Döner: {bölüm_no: [{"type","desc","source","translation"}, ...]}
    Sadece `translation` alanı DOLU olan maddeler alınır — boşsa (somut
    bir yer işaretlenmemişse) bu script'in güvenle dokunacağı bir şey
    yok demektir.
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()

    chapters = {}
    sections = re.split(r"^## Bölüm (\d+):.*$", content, flags=re.MULTILINE)
    for i in range(1, len(sections), 2):
        chapter_num = int(sections[i])
        body = sections[i + 1]
        issues = []
        for m in re.finditer(
            r'- \*\*(?P<type>[A-ZÇĞİÖŞÜ_]+)\*\*: (?P<desc>.+?)\n'
            r'(?:  - Kaynak: \*"(?P<source>.*?)"\*\n)?'
            r'(?:  - Çeviri: \*"(?P<translation>.*?)"\*\n)?',
            body,
        ):
            d = m.groupdict()
            if d.get("translation"):
                issues.append(d)
        if issues:
            chapters[chapter_num] = issues
    return chapters


def apply_fixes(slug: str, report_path: str, clients: list, key_index: list,
                 dry_run: bool = False):
    chapters_issues = _parse_report(report_path)
    output_dir = f"output/{slug}"
    total_fixed, total_skipped = 0, 0
    skipped_log = []

    for chapter_num, issues in sorted(chapters_issues.items()):
        path = os.path.join(output_dir, f"{chapter_num:03d}_{slug}.txt")
        if not os.path.exists(path):
            print(f"  Bölüm {chapter_num}: dosya bulunamadı, atlanıyor.")
            continue

        with open(path, encoding="utf-8") as f:
            raw = f.read()
        parts = raw.split("\n\n", 2)
        if len(parts) < 3:
            continue
        header = parts[0] + "\n\n" + parts[1]
        body = parts[2]
        changed = False

        for issue in issues:
            tq = issue["translation"]
            sq = issue.get("source", "")
            desc = issue["desc"]

            if tq not in body:
                total_skipped += 1
                skipped_log.append((chapter_num, tq[:60]))
                continue

            print(f"  [Bölüm {chapter_num}] düzeltiliyor: {tq[:50]!r}...")
            if dry_run:
                total_fixed += 1
                continue

            user_msg = (
                f"KAYNAK: \"{sq}\"\n"
                f"MEVCUT (HATALI) ÇEVİRİ: \"{tq}\"\n"
                f"SORUN: {desc}\n\n"
                f"Yukarıdaki hatalı çeviriyi düzelt."
            )
            fixed = gc.call(clients, key_index, _FIX_SYSTEM, user_msg, temperature=0.1)
            if not fixed:
                total_skipped += 1
                skipped_log.append((chapter_num, tq[:60]))
                continue

            fixed = fixed.strip().strip('"').strip()
            if tq in body:
                body = body.replace(tq, fixed, 1)
                changed = True
                total_fixed += 1
                print(f"    -> {fixed[:60]!r}")
            else:
                # Aynı bölümde önceki bir düzeltme bu alıntıyı da
                # değiştirmiş olabilir (nadir çakışma) — atla.
                total_skipped += 1
                skipped_log.append((chapter_num, tq[:60]))

        if changed and not dry_run:
            new_raw = header + "\n\n" + body
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_raw)

    print(f"\n{'[KURU ÇALIŞTIRMA] ' if dry_run else ''}"
          f"Toplam: {total_fixed} düzeltme {'uygulanacaktı' if dry_run else 'uygulandı'}, "
          f"{total_skipped} madde atlandı (metin tam eşleşmedi).")
    if skipped_log:
        print("Atlanan örnekler (ilk 10):")
        for ch, snippet in skipped_log[:10]:
            print(f"  Bölüm {ch}: {snippet!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="Kitap slug'ı, örn. knh-11")
    parser.add_argument("--report", default=None,
                        help="qa_report.md yolu (varsayılan: output/<slug>/qa_report.md)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Hiçbir şeyi Groq'a göndermeden/yazmadan sadece neyin "
                             "eşleştiğini göster")
    args = parser.parse_args()

    report_path = args.report or f"output/{args.slug}/qa_report.md"
    if not os.path.exists(report_path):
        print(f"Hata: {report_path} bulunamadı.")
    else:
        if args.dry_run:
            clients, key_index = None, None
        else:
            clients = gc.get_clients()
            key_index = [0]
        apply_fixes(args.slug, report_path, clients, key_index, dry_run=args.dry_run)
