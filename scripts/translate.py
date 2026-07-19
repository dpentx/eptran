"""
eptran — translate.py

Artık çeviri yapmıyor: epub/pdf'ten bölümleri çıkarır, kelime-hedefli
parçalara böler ve output/<slug>/.originals/ altına yazar ("ön-bölme").
Gerçek çeviriyi parça parça yapan queue_worker.py'yi tetikleyip çıkar.
Ayrıca kuyrukta iş varken bir güvenlik ağı görevi de görür (bkz. main()).
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

from lib import boilerplate, groq_client as gc, unicode_cleaner
from lib.git_utils import (
    write_status, trigger_workflow, create_book_branch,
    list_active_book_branches, peek_remote_file, is_stale_running, git_push,
)

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

def _chunk(text: str, target_words: int = 4500) -> list:
    """
    Metni paragraf sınırlarını koruyarak parçalara böler.

    Sabit bir parça SAYISI değil, parça başına HEDEF KELİME SAYISI
    (~4500, yani 4-5k aralığının ortası) kullanılıyor. Bu sayede kısa
    bölümler tek parça kalırken, çok uzun bölümler (23-24k kelime gibi)
    gerektiği kadar (5-6+) parçaya bölünüyor — sabit bir üst sınır yok.
    NER taraması zaten bölümün TAMAMI üzerinde (parçalardan önce, ayrıca)
    çalıştığı için isim/terim tutarlılığı parça sayısından bağımsız olarak
    korunuyor.
    """
    total_words = len(text.split())
    # %15 tolerans: hedefi az aşan bölümler için anlamsızca küçük bir
    # son parça oluşturmaktansa tek parça bırakmak daha iyi.
    if total_words <= target_words * 1.15:
        return [text]

    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    num_parts = max(2, round(total_words / target_words))
    target_words_per_part = total_words / num_parts

    chunks, current, current_words = [], "", 0
    for para in paragraphs:
        para_words = len(para.split())
        if (current and len(chunks) < num_parts - 1
                and current_words + para_words > target_words_per_part):
            chunks.append(current.strip())
            current, current_words = para, para_words
        else:
            current = f"{current}\n\n{para}" if current else para
            current_words += para_words
    if current.strip():
        chunks.append(current.strip())
    return chunks


def translate_chapter(chapter: dict, clients: list, key_index: list,
                       memory_ctx: str, protected_str: str,
                       chunk_idx: int, total_chunks: int,
                       prev_tail: str = "") -> str:
    """
    prev_tail: bu bölümün BİR ÖNCEKİ parçasının çevrilmiş (Türkçe) son
    birkaç cümlesi. Chunk'lar birbirinden bağımsız çevrildiği için
    (her API çağrısı sadece kendi chunk'ını görür), parça sınırlarında
    üslup/terim dikişi atlayabiliyordu — review'daki sliding_window
    "köprü" adımı bunu SONRADAN yamıyordu. Bunun yerine artık dikişi
    KAYNAĞINDA önlüyoruz: modele "buradan devam et" diye önceki parçanın
    nasıl bittiğini gösteriyoruz. Bu, review'ı hafifletmeyi güvenli hale
    getiren asıl değişiklik.
    """
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
    if prev_tail:
        system_msg += (
            f"\nBu bölümün bir önceki parçası şöyle bitmişti (SADECE bağlam "
            f"için veriliyor — bunu TEKRAR ÇEVİRME, üslup ve terimleri "
            f"koruyarak doğal bir şekilde devam et):\n"
            f"\"...{prev_tail}\"\n"
        )
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


# ── Ana akış ───────────────────────────────────────────────────────────────────
# NOT: Bu script artık ÇEVİRİ YAPMIYOR — sadece kitabı bölüp
# output/<slug>/.originals/ altına parça parça yazıyor ("ön-bölme"), sonra
# gerçek çeviriyi parça parça yapan queue_worker.py'yi tetikliyor. Bu,
# Hydra'daki build kuyruğuna benzer bir tasarım: her worker run'ı kısa
# ömürlü (tek parça), zincirleme kendini tetikliyor. Eskiden tek bir dev
# run 360 dakikaya kadar sürebiliyor, timeout'a uğradığında o ana kadarki
# ilerleme (chunk checkpoint'i olsa bile) riske giriyordu; artık her run
# birkaç dakika sürüyor, kaybedilecek en fazla şey TEK bir parça.

def _scan_and_nudge_active_books() -> None:
    """
    main'de dururken tüm 'book/*' dallarını (checkout ETMEDEN) tarar,
    her birinin status.json'una bakar ve hangi aşamada bekliyorsa o
    workflow'u ilgili dal adıyla tetikler. Kuyruk/review/convert
    zincirinin bir yerde kopması (rate limit, geçici hata) durumunda
    devreye giren TEK merkezi güvenlik ağı — translate.yml zaten
    periyodik (cron) çalıştığı için bu taramayı her tetiklenişinde yapar.
    """
    try:
        branches = list_active_book_branches()
    except subprocess.CalledProcessError:
        return

    for branch in branches:
        raw = peek_remote_file(branch, STATUS_FILE)
        if raw is None:
            continue
        try:
            status = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if status.get("status") == "running" and status.get("queue_mode"):
            print(f"[{branch}] çeviri kuyruğu sürüyor — queue-worker dürtülüyor.")
            trigger_workflow("queue-worker.yml", branch=branch)
            continue

        review_status = status.get("review_status")
        if status.get("status") == "completed" and review_status != "completed":
            if review_status == "running" and not is_stale_running(status):
                continue  # aktif çalışıyor, dokunma
            print(f"[{branch}] review bekliyor/durmuş — review dürtülüyor.")
            trigger_workflow("review.yml", branch=branch)
            continue

        if review_status == "completed" and status.get("convert_status") != "completed":
            print(f"[{branch}] ciltleme (epub) bekliyor — convert dürtülüyor.")
            trigger_workflow("convert.yml", branch=branch)


def main():
    _scan_and_nudge_active_books()

    input_files = [f for f in os.listdir("input")
                   if f.endswith(".epub") or f.endswith(".pdf")]
    if not input_files:
        print("input/ klasöründe yeni epub/pdf yok.")
        return

    input_file = input_files[0]
    file_path = f"input/{input_file}"
    book_slug = re.sub(r"[^\w\-]", "_",
                       re.sub(r'\.(epub|pdf)$', '', input_file, flags=re.IGNORECASE))
    file_ext = os.path.splitext(input_file)[1].lower()
    branch = f"book/{book_slug}"

    print(f"Dosya: {input_file}")
    chapters = (extract_epub(file_path) if file_ext == ".epub"
                else extract_pdf(file_path, book_slug))
    total = len(chapters)
    print(f"Toplam bölüm: {total}")
    if total == 0:
        print("Hiç bölüm çıkarılamadı.")
        return

    # Orijinal dosyanın baytlarını sil MEDEN önce belleğe al — az sonra
    # kitap dalına yedek olarak yazılacak.
    with open(file_path, "rb") as f:
        original_bytes = f.read()

    # input/, henüz işlenmemiş kitapların kuyruğu — main dalında yaşıyor.
    # Bir kitap işlenmeye alınır alınmaz kuyruktan (main'den) hemen
    # ÇIKARILIP push'lanmalı; yoksa bir sonraki cron tetiklemesi aynı
    # dosyayı TEKRAR bulur ve book/<slug> dalı zaten var olduğu için
    # `git checkout -b` çakışmasına yol açar.
    os.remove(file_path)
    subprocess.run(["git", "rm", file_path], check=True)
    git_push(f"input'tan alındı: {input_file}")

    # Bu kitap için main'den ayrı, kendine ait bir dal oluştur. Tüm ara
    # ilerleme (çeviri, review, ciltleme) bundan sonra SADECE bu dala
    # yazılır — main hiç etkilenmez. Kitap tamamen bitince tek bir PR
    # açılır (bkz. convert.py), sen onaylayıp merge edene kadar main'e
    # hiçbir şey yansımaz.
    create_book_branch(branch)

    output_dir = f"output/{book_slug}"
    originals_dir = f"{output_dir}/.originals"
    os.makedirs(originals_dir, exist_ok=True)

    # Orijinali (bellekte tuttuğumuz baytlardan) bu dala yedekle —
    # convert.py bu dosyayı find_original_epub() ile burada arayacak.
    backup_dir = "input/.originals"
    os.makedirs(backup_dir, exist_ok=True)
    with open(f"{backup_dir}/{book_slug}{file_ext}", "wb") as f:
        f.write(original_bytes)

    # Ön-bölme: her bölümü kelime-hedefli parçalara ayır, .originals/'a yaz.
    # NER/hafıza context'i BURADA hesaplanmıyor — queue_worker.py, her
    # bölümün ilk parçasını işlerken (o anki güncel hafıza durumuyla)
    # hesaplayıp bölümün meta dosyasına önbelleğe alacak. Böylece hafıza,
    # önceki bölümler işlendikçe birikmeye devam ediyor (tek seferde tüm
    # kitabı önceden bölmek bunu bozmaz, çünkü context hesaplama işlemi
    # zaman içinde, sırayla, worker tarafından yapılıyor).
    total_parts_all = 0
    for i, chapter in enumerate(chapters):
        chunks = _chunk(chapter["text"])
        total_parts_all += len(chunks)
        for j, chunk_text in enumerate(chunks):
            part_path = f"{originals_dir}/{i:03d}_{j:02d}.txt"
            with open(part_path, "w", encoding="utf-8") as f:
                f.write(chunk_text)
        meta_path = f"{originals_dir}/{i:03d}_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "title": chapter["title"],
                "total_parts": len(chunks),
                "protected_str": None,
                "memory_ctx": None,
            }, f, ensure_ascii=False)
    print(f"Ön-bölme tamamlandı: {total} bölüm, {total_parts_all} parça.")

    status = {
        "status": "running", "book": book_slug, "epub_file": input_file,
        "branch": branch, "source_type": file_ext.lstrip("."), "total": total,
        "completed": 0, "current_chapter": "",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "queue_mode": True,
    }
    subprocess.run(["git", "add", originals_dir])

    # Bu dalın ilk push'u — git_utils.git_push() remote'ta bu dal henüz
    # yokken otomatik '-u origin <branch>' ile push eder.
    write_status(status, f"kuyruğa alındı: {total} bölüm, {total_parts_all} parça")
    print(f"Queue-worker tetikleniyor (dal: {branch})...")
    trigger_workflow("queue-worker.yml", branch=branch)


if __name__ == "__main__":
    main()
