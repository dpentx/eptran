"""
eptran — review.py
Çevrilmiş .txt dosyalarını review eder:
  1. Boilerplate temizle
  2. Sözlük destekli İngilizce kelime düzeltmesi (NER çağrısı YOK,
     hafızadaki whitelist + dictionary.py kullanılır) — LLM çağrısı
     SADECE gerçek bir sorun (yabancı kelime kalıntısı) bulunursa yapılır

NOT (Temmuz 2026): Eskiden burada bir de sliding_window.review_chunks()
adımı vardı — her chunk'ı (+ chunk sınırlarındaki "köprüleri") koşulsuz
olarak LLM'e tekrar yollayıp "düzelt" diyordu. Bu, translate.py'nin her
chunk'ı birbirinden bağımsız (önceki chunk'ın çevirisini GÖRMEDEN)
çevirmesinin yarattığı üslup/terim dikişlerini SONRADAN yamak içindi.
Artık translate_chapter() bir önceki parçanın çevrilmiş son birkaç
cümlesini bağlam olarak alıyor (bkz. queue_worker.py'deki prev_tail),
yani dikiş sorunu KAYNAĞINDA büyük ölçüde önleniyor. Bu da her bölümü
ikinci kez baştan sona LLM'e sokan (ve review'ı günler sürdüren)
koşulsuz geçişi gereksiz kıldı — kaldırdık. Kalan review_fix.fix_text()
zaten ucuz: sadece gerçek bir İngilizce kalıntı bulursa LLM çağırıyor.
"""
import os

from lib import boilerplate, groq_client as gc, memory as mem, review_fix
from lib.git_utils import read_status, write_status, is_stale_running, trigger_workflow, current_branch
from lib import dictionary

STATUS_FILE = "status.json"


def review_file(filepath: str, clients: list, key_index: list, memory: dict) -> None:
    with open(filepath, encoding="utf-8") as f:
        raw = f.read()

    # Başlık satırını gövdeden ayır
    lines = raw.split("\n", 2)
    if lines[0].startswith("#"):
        title_line = lines[0]
        title_text = title_line.lstrip("#").strip()
        body = lines[2].strip() if len(lines) > 2 else ""

        # Başlık boilerplate VE gövde de boş/kısaysa dosyayı temizle
        if boilerplate.is_boilerplate(title_text) and len(body) < 100:
            print(f"  Boilerplate dosya temizleniyor: {title_text[:60]}")
            open(filepath, "w").close()
            return
    else:
        title_line = None
        body = raw.strip()

    # Boilerplate blokları ve lisans bölümlerini temizle
    body = boilerplate.clean(body)
    if len(body) < 100:
        print(f"  İçerik kalmadı, dosya temizleniyor.")
        open(filepath, "w").close()
        return

    # Sözlük destekli İngilizce kelime düzeltmesi (NER çağrısı yok, LLM
    # çağrısı SADECE gerçek bir yabancı-kelime kalıntısı bulunursa olur)
    print(f"  Paragraf taraması (sözlük destekli)...")
    body = review_fix.fix_text(body, clients, key_index, memory)

    final = f"{title_line}\n\n{body}\n" if title_line else body + "\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final)


def main():
    status = read_status()

    if status.get("status") != "completed":
        print("Çeviri henüz tamamlanmamış.")
        return

    review_status = status.get("review_status")
    if review_status == "running":
        if not is_stale_running(status):
            print("Review zaten aktif çalışıyor.")
            return
        print("Review stale, kaldığı yerden devam ediliyor.")
    elif review_status == "completed":
        print("Review zaten tamamlanmış.")
        return

    book_slug = status.get("book")
    if not book_slug:
        print("status.json'da book bilgisi yok.")
        return

    output_dir = f"output/{book_slug}"
    txt_files = sorted(f for f in os.listdir(output_dir) if f.endswith(".txt"))
    if not txt_files:
        print("Düzeltilecek .txt dosyası bulunamadı.")
        return

    clients = gc.get_clients()
    key_index = [0]

    # Hafızayı yükle (whitelist/sözlük düzeltmesi için)
    memory = mem.load(output_dir)
    print(f"Hafıza yüklendi: {len(memory.get('characters', {}))} karakter, "
          f"{len(memory.get('terms', {}))} terim, "
          f"{len(memory.get('summaries', []))} özet")

    review_done = status.get("review_completed", 0)
    total = len(txt_files)

    status.update({"review_status": "running", "review_total": total,
                   "review_completed": review_done})
    write_status(status, f"review: {review_done}/{total}")

    print(f"Review başlıyor: {book_slug} — {total} dosya ({review_done} tamamlandı)")

    for i, fname in enumerate(txt_files):
        if i < review_done:
            print(f"[{i+1}/{total}] Atlanıyor: {fname}")
            continue

        filepath = os.path.join(output_dir, fname)
        print(f"[{i+1}/{total}] Review: {fname}")
        try:
            review_file(filepath, clients, key_index, memory)
        except gc.AllKeysLockedError as e:
            # review_fix.fix_paragraph() içindeki gc.call() bunu fırlatabilir
            # (bkz. groq_client.py) — eskiden bu, review.py'yi yakalanmamış
            # bir exception olarak ÇÖKERTİYORDU (job kırmızı X ile bitiyordu),
            # ama her çöküşten önce o ana kadarki dosyalar zaten commit'lendiği
            # için ilerleme kayboldu değil, sadece her seferinde gereksiz bir
            # hata + yeniden başlatma döngüsü oluşuyordu. Artık burada
            # yakalayıp run'ı TEMİZ bir şekilde durduruyoruz (review_status
            # "running" kalır) — bir sonraki tetiklemede bu dosyadan devam
            # edilecek. Aşağıdaki "review tamamlandı" finalizasyonuna
            # gitmemesi için doğrudan return ediyoruz.
            print(f"  Tüm keyler kilitli ({e.wait_seconds}s) — bu run burada "
                  f"duruyor, bir sonraki tetiklemede '{fname}'den devam edilecek.")
            return

        status["review_completed"] = i + 1
        status["review_current"] = fname
        write_status(status, f"review: {i+1}/{total}")
        # Not: dictionary.flush() review_fix.fix_text() içinde her dosya
        # sonunda çağrılır, learned_words.json güncellenmiş olur.
        # write_status() -> git_push() "git add -A" kullandığı için
        # learned_words.json değişikliği otomatik commit'e dahil olur.

    # Boş kalan dosyaları sil
    for fname in txt_files:
        fp = os.path.join(output_dir, fname)
        if os.path.exists(fp) and os.path.getsize(fp) == 0:
            os.remove(fp)
            print(f"  Boş dosya silindi: {fname}")

    status.update({"review_status": "completed", "review_current": ""})
    write_status(status, "review: completed")
    print("Review tamamlandı. Ciltleme (convert) tetikleniyor...")
    trigger_workflow("convert.yml", branch=current_branch())


if __name__ == "__main__":
    main()
