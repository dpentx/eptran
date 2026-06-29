"""
eptran — review.py
Çevrilmiş .txt dosyalarını sliding window ile review eder:
  1. Boilerplate temizle
  2. Sözlük destekli İngilizce kelime düzeltmesi (NER çağrısı YOK,
     hafızadaki whitelist + dictionary.py kullanılır)
  3. Sliding window (chunk + köprü) review
  4. Hafıza context'i her adımda kullanılır
"""
import os

from lib import boilerplate, groq_client as gc, memory as mem, review_fix, sliding_window as sw
from lib.git_utils import read_status, write_status, is_stale_running
from lib import dictionary

STATUS_FILE = "status.json"


def review_file(filepath: str, clients: list, key_index: list,
                memory_ctx: str, memory: dict) -> None:
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

    # Sözlük destekli İngilizce kelime düzeltmesi (NER çağrısı yok)
    print(f"  Paragraf taraması (sözlük destekli)...")
    body = review_fix.fix_text(body, clients, key_index, memory)

    # Sliding window review (hafıza context'li)
    chunks = sw.chunk_text(body)
    corrected = sw.review_chunks(chunks, clients, key_index, memory_ctx)

    final_body = "\n\n".join(corrected)
    final = f"{title_line}\n\n{final_body}\n" if title_line else final_body + "\n"

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

    # Hafızayı yükle
    memory = mem.load(output_dir)
    memory_ctx = mem.build_context(memory)
    if memory_ctx:
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
        review_file(filepath, clients, key_index, memory_ctx, memory)

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
    print("Review tamamlandı.")


if __name__ == "__main__":
    main()
