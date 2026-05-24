import os
import json
import subprocess
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime, timezone
import time
import re

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
STATUS_FILE = "status.json"


def git_push(message):
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push"], check=True)


def write_status(data):
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    git_push(f"status: {data.get('completed', 0)}/{data.get('total', '?')}")


def extract_chapters(epub_path):
    book = epub.read_epub(epub_path)
    chapters = []

    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        soup = BeautifulSoup(item.get_content(), "html.parser")

        # Remove script/style tags
        for tag in soup(["script", "style", "nav"]):
            tag.decompose()

        text = soup.get_text(separator="\n").strip()
        text = re.sub(r"\n{3,}", "\n\n", text)

        if len(text) < 300:
            continue

        title = item.get_name()
        # Try to find a heading
        heading = soup.find(["h1", "h2", "h3"])
        if heading:
            title = heading.get_text().strip()

        chapters.append({"name": item.get_name(), "title": title, "text": text})

    return chapters


def chunk_text(text, max_chars=12000):
    """Split text into chunks at paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current += "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def translate_chunk(model, text, chapter_title, chunk_index, total_chunks):
    context = f" (Parça {chunk_index + 1}/{total_chunks})" if total_chunks > 1 else ""
    prompt = (
        f"Aşağıdaki İngilizce metni Türkçeye çevir. "
        f"Çeviriyi doğal, akıcı ve edebi tut. "
        f"Karakterlerin sesini, tonunu ve yazı stilini koru. "
        f"Sadece çeviriyi döndür, başka hiçbir şey ekleme.\n\n"
        f"Bölüm: {chapter_title}{context}\n\n"
        f"{text}"
    )

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt + 1}/3 after error: {e}")
            time.sleep(5 * (attempt + 1))


def main():
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    # Find epub
    input_files = [f for f in os.listdir("input") if f.endswith(".epub")]
    if not input_files:
        print("input/ klasöründe epub bulunamadı.")
        return

    epub_file = input_files[0]
    epub_path = f"input/{epub_file}"
    book_slug = re.sub(r"[^\w\-]", "_", epub_file.replace(".epub", ""))

    print(f"Kitap: {epub_file}")

    # Extract
    chapters = extract_chapters(epub_path)
    total = len(chapters)
    print(f"Toplam bölüm: {total}")

    output_dir = f"output/{book_slug}"
    os.makedirs(output_dir, exist_ok=True)

    status = {
        "status": "running",
        "book": book_slug,
        "epub_file": epub_file,
        "total": total,
        "completed": 0,
        "current_chapter": "",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    write_status(status)

    # Translate
    for i, chapter in enumerate(chapters):
        print(f"[{i+1}/{total}] {chapter['title']}")
        status["current_chapter"] = chapter["title"]
        write_status(status)

        chunks = chunk_text(chapter["text"])
        translated_parts = []

        for j, chunk in enumerate(chunks):
            translated = translate_chunk(model, chunk, chapter["title"], j, len(chunks))
            translated_parts.append(translated)
            time.sleep(1)  # rate limit buffer

        full_translation = "\n\n".join(translated_parts)
        out_path = f"{output_dir}/{i+1:03d}_{book_slug}.txt"

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# {chapter['title']}\n\n{full_translation}\n")

        status["completed"] = i + 1
        subprocess.run(["git", "add", out_path])
        write_status(status)

    # Cleanup input
    os.remove(epub_path)
    subprocess.run(["git", "rm", epub_path], check=True)

    status["status"] = "completed"
    status["current_chapter"] = ""
    write_status(status)

    print("Çeviri tamamlandı.")


if __name__ == "__main__":
    main()
