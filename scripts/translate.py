"""
eptran — translate.py
epub/pdf → bölüm çıkarma → Groq ile Türkçe çeviri → .txt dosyaları
"""
import os
import re
import json
import shutil
import subprocess
from datetime import datetime, timezone

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from lib import boilerplate, groq_client as gc, memory as mem, ner, unicode_cleaner
from lib.git_utils import git_push, write_status

STATUS_FILE = "status.json"


# ── Bölüm çıkarma ─────────────────────────────────────────────────────────────

def extract_epub(epub_path: str) -> list:
    book = epub.read_epub(epub_path)
    chapters = []
    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for tag in soup(["script", "style", "nav"]):
            tag.decompose()

        heading = soup.find(["h1", "h2", "h3"])

        text = soup.get_text(separator="\n").strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = boilerplate.clean(text)
        if len(text) < 300:
            continue

        # Başlığı ayıkla — "The Project Gutenberg eBook of X" → "X"
        raw_title = heading.get_text().strip() if heading else item.get_name()
        title = re.sub(
            r'^the\s+project\s+gutenberg\s+e[\-\s]?book\s+of\s+',
            '', raw_title, flags=re.IGNORECASE
        ).strip() or raw_title
        chapters.append({"name": item.get_name(), "title": title, "text": text})
    return chapters


def extract_pdf(pdf_path: str, book_slug: str) -> list:
    import pdfplumber, fitz

    patterns = [
        re.compile(r'^(chapter\s+\w+[\s:\-–—]?.*)$', re.IGNORECASE),
        re.compile(r'^(prologue|epilogue|interlude|afterword|foreword|preface)$', re.IGNORECASE),
        re.compile(r'^(\d+\.\s+.{3,60})$'),
        re.compile(r'^([IVX]+\.\s+.{3,60})$'),
    ]
    images_dir = f"output/{book_slug}/images"
    os.makedirs(images_dir, exist_ok=True)
    all_lines, doc = [], fitz.open(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        for pi, page in enumerate(pdf.pages):
            if page.extract_text():
                all_lines.extend(page.extract_text().split("\n"))
            for ii, img in enumerate(doc[pi].get_images(full=True)):
                base = doc.extract_image(img[0])
                name = f"page_{pi+1}_img_{ii+1}.{base['ext']}"
                with open(os.path.join(images_dir, name), "wb") as f:
                    f.write(base["image"])
                all_lines.append(f"[EPUB_IMAGE:{name}]")
            all_lines.append("")

    starts = []
    for i, line in enumerate(all_lines):
        s = line.strip()
        if s and any(p.match(s) for p in patterns):
            starts.append((i, s))

    if not starts:
        text = boilerplate.clean(re.sub(r"\n{3,}", "\n\n", "\n".join(all_lines).strip()))
        return [{"name": "chapter_001",
                 "title": os.path.splitext(os.path.basename(pdf_path))[0],
                 "text": text}] if len(text) >= 300 else []

    starts.append((len(all_lines), None))
    chapters = []
    for idx in range(len(starts) - 1):
        sl, title = starts[idx]
        body = boilerplate.clean(re.sub(r"\n{3,}", "\n\n",
                                        "\n".join(all_lines[sl+1:starts[idx+1][0]]).strip()))
        if len(body) >= 300:
            chapters.append({"name": f"chapter_{idx+1:03d}", "title": title, "text": body})
    return chapters


# ── Çeviri ─────────────────────────────────────────────────────────────────────

def _chunk(text: str, max_chars: int = 12000) -> list:
    if len(text) <= max_chars:
        return [text]
    chunks, current = [], ""
    for para in text.split("\n\n"):
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current += "\n\n" + para if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks


def translate_chapter(chapter: dict, clients: list, key_index: list,
                       memory_ctx: str, protected_str: str,
                       chunk_idx: int, total_chunks: int) -> str:
    part_info = f", Parça {chunk_idx + 1}/{total_chunks}" if total_chunks > 1 else ""
    system_msg = (
        f"Sen profesyonel bir çevirmensin. "
        f"Şu an \"{chapter['title']}\"{part_info} başlıklı bölümü çeviriyorsun.\n"
        f"Görevin yalnızca verilen İngilizce metni Türkçeye çevirmek. "
        f"Çeviriyi doğal, akıcı ve edebi tut; karakterlerin sesini ve tonunu koru. "
        f"Çıktının TAMAMI sadece Türkçe olmalı — başka hiçbir dilden "
        f"(Arapça, Fransızca, İngilizce vb.) tek bir kelime bile karışmamalı. "
        f"'[EPUB_IMAGE:...]' etiketlerini olduğu gibi bırak.\n"
    )
    if protected_str:
        system_msg += f"{protected_str}\n"
    system_msg += "Yanıt olarak SADECE çeviriyi yaz, hiçbir açıklama ekleme."
    if memory_ctx:
        system_msg += f"\n\n{memory_ctx}"

    result = gc.call(clients, key_index, system_msg, chapter["text"], temperature=0.3)
    if result is None:
        # gc.call zaten MAX_EMPTY_RETRIES kez denedi, hâlâ boş — burada
        # zorlamıyoruz, çağıran (main) bu bölümü bu çalıştırmada
        # tamamlanmış saymayıp bir sonraki run'da yeniden deneyecek.
        return None

    # Çıktıda Arapça/Kiril/Yunan gibi beklenmeyen script varsa bir kez retry et
    foreign = unicode_cleaner.find_foreign_words(result)
    if foreign:
        print(f"  Uyarı: çıktıda yabancı script tespit edildi {foreign[:5]} — yeniden deneniyor.")
        retry_msg = system_msg + (
            "\n\nÖNEMLİ: Önceki yanıtında Türkçe olmayan kelimeler vardı. "
            "Bu sefer çıktının HER kelimesi Türkçe olmalı."
        )
        retry_result = gc.call(clients, key_index, retry_msg, chapter["text"], temperature=0.2)
        if retry_result is None:
            # Retry boş döndüyse ilk (yabancı kelimeli) sonucu koru — en
            # azından içerik var, hiç içerik olmamasından daha iyidir.
            print("  Uyarı: yabancı-kelime retry'ı boş yanıt döndürdü, ilk sonuç korunuyor.")
        else:
            result = retry_result
            still_foreign = unicode_cleaner.find_foreign_words(result)
            if still_foreign:
                print(f"  Uyarı: retry sonrası hâlâ yabancı kelime var {still_foreign[:5]} — "
                      f"elle kontrol gerekebilir.")

    return result


# ── Chunk checkpoint (parça bazlı ara kayıt) ────────────────────────────────
# Büyük bölümler (çok chunk'lı) bir run içinde bitmeyip timeout'a uğrarsa,
# o ana kadar çevrilen chunk'lar burada saklanır. Bir sonraki run, bölümü
# baştan değil KALDIĞI CHUNK'TAN devam ettirir — hem zaman kazandırır hem
# de her chunk kendi başına diske/commit'e yazıldığı için run yarıda
# kesilse bile o parçalar kaybolmaz.

def _checkpoint_path(output_dir: str, i: int, book_slug: str) -> str:
    return f"{output_dir}/.checkpoints/{i+1:03d}_{book_slug}.json"


def _load_checkpoint(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("parts", [])
    except (json.JSONDecodeError, OSError):
        print(f"  Uyarı: checkpoint okunamadı ({path}), sıfırdan başlanıyor.")
        return []


def _save_checkpoint(path: str, parts: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"parts": parts}, f, ensure_ascii=False)


def _remove_checkpoint(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
        subprocess.run(["git", "rm", "-f", "--ignore-unmatch", path])


# ── Ana akış ───────────────────────────────────────────────────────────────────

def main():
    clients = gc.get_clients()
    key_index = [0]

    input_files = [f for f in os.listdir("input")
                   if f.endswith(".epub") or f.endswith(".pdf")]

    if not input_files:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE) as f:
                prev = json.load(f)
            if prev.get("status") == "running":
                print("Status running ama input'ta dosya yok.")
                return
        print("input/ klasöründe epub/pdf bulunamadı.")
        return

    input_file = input_files[0]
    file_path = f"input/{input_file}"
    book_slug = re.sub(r"[^\w\-]", "_",
                       re.sub(r'\.(epub|pdf)$', '', input_file, flags=re.IGNORECASE))
    file_ext = os.path.splitext(input_file)[1].lower()

    print(f"Dosya: {input_file}")
    chapters = (extract_epub(file_path) if file_ext == ".epub"
                else extract_pdf(file_path, book_slug))
    total = len(chapters)
    print(f"Toplam bölüm: {total}")
    if total == 0:
        print("Hiç bölüm çıkarılamadı.")
        return

    output_dir = f"output/{book_slug}"
    os.makedirs(output_dir, exist_ok=True)

    # Orijinali yedekle
    backup_dir = "input/.originals"
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy2(file_path, f"{backup_dir}/{book_slug}{file_ext}")

    completed_start = len([
        f for f in os.listdir(output_dir)
        if f.endswith(".txt") and
        os.path.getsize(os.path.join(output_dir, f)) > 500
    ])
    if completed_start > 0:
        print(f"Kaldığı yerden devam: {completed_start}/{total}")

    status = {
        "status": "running", "book": book_slug, "epub_file": input_file,
        "source_type": file_ext.lstrip("."), "total": total,
        "completed": completed_start, "current_chapter": "",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    write_status(status, f"status: {completed_start}/{total}")

    # Hafızayı yükle veya ilk bölümden çıkar
    memory = mem.load(output_dir)
    if completed_start == 0 and not memory.get("characters"):
        print("Çeviri hafızası çıkarılıyor...")
        memory = mem.extract_from_source(chapters[0]["text"], clients, key_index)
        mem.save(output_dir, memory)
        print(f"  Hafıza: {len(memory['characters'])} karakter, "
              f"{len(memory['terms'])} terim")

    for i, chapter in enumerate(chapters):
        out_path = f"{output_dir}/{i+1:03d}_{book_slug}.txt"
        # Bölümün Türkçe çevirisi orijinalin en az %30'u kadar olmalı.
        # Sabit 500 byte eşiği yarım çevirileri "tamamlanmış" sayıyordu.
        min_expected = max(500, len(chapter["text"]) * 0.30)
        if os.path.exists(out_path) and os.path.getsize(out_path) > min_expected:
            print(f"[{i+1}/{total}] Atlanıyor: {chapter['title']}")
            continue

        print(f"[{i+1}/{total}] Çevriliyor: {chapter['title']}")
        status["current_chapter"] = chapter["title"]
        write_status(status, f"status: {i}/{total}")

        # Bölüm başına NER — kaynak metinden özel isimleri çıkar
        print(f"  NER taraması...")
        chapter_entities = ner.extract_from_source(chapter["text"], clients, key_index)
        protected_str = ner.build_protected_str(memory, chapter_entities)
        if protected_str:
            print(f"  Korunan: {len(chapter_entities)} isim/terim")

        memory_ctx = mem.build_context(memory)
        chunks = _chunk(chapter["text"])
        checkpoint_path = _checkpoint_path(output_dir, i, book_slug)
        parts = _load_checkpoint(checkpoint_path)
        if parts:
            print(f"  Checkpoint bulundu: {len(parts)}/{len(chunks)} parça zaten "
                  f"çevrilmiş, kaldığı chunk'tan devam ediliyor.")

        chapter_failed = False
        for j in range(len(parts), len(chunks)):
            chunk = chunks[j]
            ch_copy = dict(chapter, text=chunk)
            translated = translate_chapter(ch_copy, clients, key_index,
                                           memory_ctx, protected_str, j, len(chunks))
            if translated is None:
                print(f"  Hata: parça {j+1}/{len(chunks)} çevrilemedi (model ısrarla "
                      f"boş yanıt döndürdü). Bu bölüm bu çalıştırmada atlanıyor, "
                      f"bir sonraki run'da (şimdiye kadar çevrilen "
                      f"{len(parts)}/{len(chunks)} parçadan devam ederek) "
                      f"yeniden denenecek.")
                chapter_failed = True
                break
            parts.append(translated)
            # Her chunk'ı hemen diske + git'e yaz — run burada kesilse bile
            # bu parça kaybolmaz, bir sonraki run j+1'den devam eder.
            _save_checkpoint(checkpoint_path, parts)
            subprocess.run(["git", "add", checkpoint_path])
            write_status(status, f"status: {i}/{total} (parça {j+1}/{len(chunks)})")
            import time; time.sleep(2)

        if chapter_failed:
            # status'u ilerletme — bir sonraki run bu bölümü, checkpoint'te
            # kayıtlı olan yerden devam ettirir. Var olan (varsa) çıktı
            # dosyasına dokunulmadı.
            continue

        full_translation = "\n\n".join(parts)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# {chapter['title']}\n\n{full_translation}\n")
        _remove_checkpoint(checkpoint_path)

        # Hafızayı çeviriyle güncelle + özet ekle
        memory = mem.update_from_translation(memory, full_translation, clients, key_index)
        memory = mem.add_summary(memory, chapter["title"], full_translation, clients, key_index)
        mem.save(output_dir, memory)

        status["completed"] = i + 1
        subprocess.run(["git", "add", out_path,
                        os.path.join(output_dir, mem.MEMORY_FILE)])
        write_status(status, f"status: {i+1}/{total}")

    if os.path.exists(file_path):
        os.remove(file_path)
        subprocess.run(["git", "rm", file_path], check=True)

    status["status"] = "completed"
    status["current_chapter"] = ""
    write_status(status, "status: completed")
    print("Çeviri başarıyla tamamlandı.")


if __name__ == "__main__":
    main()
