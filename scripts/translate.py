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

from lib import boilerplate, groq_client as gc, memory as mem, ner
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

        # Başlık kendisi boilerplate/lisans ifadesi taşıyorsa
        # (örn. "THE FULL PROJECT GUTENBERG™ LICENSE", "Section 1. General Terms")
        # bu item gerçek bir hikaye bölümü değildir — gövde uzun olsa bile atla.
        # Bu kontrol olmadan bu tür bloklar çeviriliyor ve hafızayı
        # (memory.json) kirletip sonraki bölümlerin çevirisini bozuyordu.
        if boilerplate.is_boilerplate_title(raw_title) or boilerplate.is_boilerplate_title(title):
            print(f"  Boilerplate başlık atlandı: {raw_title[:60]!r}")
            continue

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
        f"'[EPUB_IMAGE:...]' etiketlerini olduğu gibi bırak.\n"
    )
    if protected_str:
        system_msg += f"{protected_str}\n"
    system_msg += "Yanıt olarak SADECE çeviriyi yaz, hiçbir açıklama ekleme."
    if memory_ctx:
        system_msg += f"\n\n{memory_ctx}"
    return gc.call(clients, key_index, system_msg, chapter["text"], temperature=0.3)


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

    completed_start = len([f for f in os.listdir(output_dir) if f.endswith(".txt")])
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
        if os.path.exists(out_path):
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
        parts = []

        for j, chunk in enumerate(chunks):
            ch_copy = dict(chapter, text=chunk)
            translated = translate_chapter(ch_copy, clients, key_index,
                                           memory_ctx, protected_str, j, len(chunks))
            parts.append(translated)
            import time; time.sleep(2)

        full_translation = "\n\n".join(parts)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# {chapter['title']}\n\n{full_translation}\n")

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
