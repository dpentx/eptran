import os
import json
import subprocess
import unicodedata
from datetime import datetime, timezone, timedelta

from groq import Groq, RateLimitError
import time
import re

STATUS_FILE = "status.json"
BRIDGE_OVERLAP = 1800

# Actions'ta bir run crash/timeout olursa bu süreden sonra "running" sayılmaz
STALE_RUNNING_MINUTES = 30

# ── Boilerplate kalıpları (translate.py ile aynı) ─────────────────────────────

_BOILERPLATE_PATTERNS = [
    re.compile(r'©|copyright|\ball rights reserved\b|isbn[\s:]\d', re.IGNORECASE),
    re.compile(r'project gutenberg|gutenberg\.org|www\.gutenberg', re.IGNORECASE),
    re.compile(r'epubbooks?\.com|www\.[a-z0-9\-]+\.[a-z]{2,}', re.IGNORECASE),
    re.compile(r'\bebook\s*#?\d+\b', re.IGNORECASE),
    re.compile(r"^(translator'?s?\s*note|note from the translator|çevirmen\s*notu)\b", re.IGNORECASE),
    re.compile(r'bu (yayın|e[\-\s]?kitap).{0,60}(telif|lisans|hak)', re.IGNORECASE),
    re.compile(r"this e[\-\s]?book is for the use of", re.IGNORECASE),
    re.compile(r'(ilk olarak|first published|originally published).{0,60}\d{4}', re.IGNORECASE),
    re.compile(r'^\s*(the\s+)?full\s+project\s+gutenberg', re.IGNORECASE),
    re.compile(r'(limited warranty|indemnity|disclaimer of|distribution of this)', re.IGNORECASE),
    re.compile(r'(1\.e\.\d|1\.f\.\d|section \d+\.)', re.IGNORECASE),
    # Türkçeye çevrilmiş lisans başlıkları
    re.compile(r'(tam lisans|lisans koşulları|garanti reddi|sorumluluk reddi)', re.IGNORECASE),
    re.compile(r'(bağış|vakf[ıa]|elektronik çalışma).{0,60}(hak|lisans|koşul)', re.IGNORECASE),
]

# Model çıktısı kalıntıları
_JUNK_PATTERNS = [
    re.compile(r'^(?:İşte (?:düzeltilmiş|güncellenmiş|revize edilmiş).*)\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^(?:Düzeltilmiş metin\s*:?)\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^Not\s*:.*\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^(?:Bu metinde|Metinde|Aşağıda).*(?:düzelt|değiştir|güncell).*\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^Açıklama\s*:.*\n?', re.MULTILINE | re.IGNORECASE),
]

_TR_WHITELIST = {
    'olan', 'veya', 'için', 'gibi', 'bile', 'daha', 'kadar', 'beri',
    'önce', 'sonra', 'ancak', 'fakat', 'lakin', 'iken', 'yani', 'hatta',
    'zaten', 'artık', 'ise', 'ama', 'televizyon', 'telefon', 'internet',
    'bilgisayar', 'organizasyon', 'motivasyon', 'pozisyon', 'koleksiyon',
}

_ENG_WORD_RE = re.compile(r'\b[a-zA-Z]{3,}\b')


# ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────────

def is_boilerplate_text(text: str) -> bool:
    for pat in _BOILERPLATE_PATTERNS:
        if pat.search(text):
            return True
    return False


def is_boilerplate_paragraph(paragraph: str) -> bool:
    p = paragraph.strip()
    if not p:
        return True
    return is_boilerplate_text(p)


def clean_boilerplate(text: str) -> str:
    """
    Boilerplate paragrafları kaldır.
    Ayrıca lisans bölümünün başladığı noktadan sonrasını tamamen kes
    — Gutenberg lisansları genellikle metnin sonunda blok halinde gelir.
    """
    # Lisans bloğunun başlangıcını bul ve oradan itibaren kes
    license_block_re = re.compile(
        r'\n\n.*?(tam lisans|full project gutenberg|start:? full license|'
        r'please read this before|1\.e\.\d|garanti reddi).*',
        re.IGNORECASE | re.DOTALL
    )
    text = license_block_re.sub('', text)

    paragraphs = text.split("\n\n")
    cleaned = [p for p in paragraphs if not is_boilerplate_paragraph(p)]
    return "\n\n".join(cleaned).strip()


def clean_output(text: str) -> str:
    for pattern in _JUNK_PATTERNS:
        text = pattern.sub('', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── Unicode sanitizer ─────────────────────────────────────────────────────────

def _script_of_char(ch: str) -> str:
    try:
        name = unicodedata.name(ch, '')
        if 'LATIN' in name: return 'latin'
        if 'ARABIC' in name: return 'arabic'
        if 'CYRILLIC' in name: return 'cyrillic'
        if 'GREEK' in name: return 'greek'
        if 'CJK' in name or 'HIRAGANA' in name or 'KATAKANA' in name: return 'cjk'
        return 'other'
    except Exception:
        return 'other'


def sanitize_unicode(text: str) -> str:
    words = text.split(' ')
    cleaned_words = []
    for word in words:
        if len(word) < 2:
            cleaned_words.append(word)
            continue
        scripts = set()
        for ch in word:
            if ch.isalpha():
                scripts.add(_script_of_char(ch))
        if len(scripts) <= 1:
            cleaned_words.append(word)
            continue
        latin_only = ''.join(ch for ch in word if not ch.isalpha() or _script_of_char(ch) == 'latin')
        if latin_only.strip():
            cleaned_words.append(latin_only)
            print(f"    unicode temizlendi: '{word}' → '{latin_only}'")
    return ' '.join(cleaned_words)


# ── İngilizce kelime tespiti ──────────────────────────────────────────────────

def get_english_words(paragraph: str) -> list:
    candidates = _ENG_WORD_RE.findall(paragraph)
    result = []
    for w in candidates:
        wl = w.lower()
        if wl in _TR_WHITELIST:
            continue
        if re.search(r'(ları|leri|ında|inde|dan|den|lar|ler|ını|ini|'
                     r'ına|ine|nın|nin|nun|nün|daki|deki|taki|teki)$', wl):
            continue
        result.append(w)
    return result


# ── Groq ──────────────────────────────────────────────────────────────────────

def get_groq_clients():
    clients = []
    for i in range(1, 5):
        key = os.environ.get(f"GROQ_API_KEY_{i}")
        if key:
            clients.append({"client": Groq(api_key=key), "locked_until": 0, "id": i})
    single_key = os.environ.get("GROQ_API_KEY")
    if single_key and not clients:
        clients.append({"client": Groq(api_key=single_key), "locked_until": 0, "id": "Default"})
    if not clients:
        raise ValueError("Hiçbir GROQ_API_KEY bulunamadı.")
    print(f"Toplam {len(clients)} key aktif.")
    return clients


def parse_retry_seconds(error_message):
    match = re.search(r'try again in ([\dhms .]+)', str(error_message))
    if not match:
        return 3600
    time_str = match.group(1).strip()
    total = 0
    for h in re.findall(r'([\d.]+)h', time_str): total += float(h) * 3600
    for m in re.findall(r'([\d.]+)m', time_str): total += float(m) * 60
    for s in re.findall(r'([\d.]+)s', time_str): total += float(s)
    return int(total) + 5


def call_llm(clients, key_index, system_msg, user_msg):
    while True:
        current_time = time.time()
        available = [c for c in clients if c["locked_until"] <= current_time]
        if not available:
            wait = max(int(min(c["locked_until"] for c in clients) - current_time), 1)
            print(f"Tüm keyler limit dışı. {wait}s bekleniyor...")
            time.sleep(wait)
            continue

        idx = key_index[0] % len(clients)
        if clients[idx]["locked_until"] > current_time:
            for i, c in enumerate(clients):
                if c["locked_until"] <= current_time:
                    idx = i
                    key_index[0] = i
                    break

        info = clients[idx]
        try:
            response = info["client"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
            )
            key_index[0] = (idx + 1) % len(clients)
            return clean_output(response.choices[0].message.content)
        except RateLimitError as e:
            wait = parse_retry_seconds(e)
            print(f"Key {info['id']} rate limit! {wait}s kilitlendi.")
            info["locked_until"] = time.time() + wait
            key_index[0] = (idx + 1) % len(clients)
        except Exception as e:
            print(f"Hata: {e} — 30s sonra tekrar deneniyor...")
            time.sleep(30)


# ── Git ───────────────────────────────────────────────────────────────────────

def git_push(message):
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "pull", "--rebase"], check=True)
        subprocess.run(["git", "push"], check=True)


def read_status():
    if not os.path.exists(STATUS_FILE):
        return {}
    with open(STATUS_FILE, encoding="utf-8") as f:
        return json.load(f)


def write_status(data):
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    git_push(f"review: {data.get('review_completed', 0)}/{data.get('review_total', '?')}")


def is_stale_running(status: dict) -> bool:
    """
    review_status == 'running' ama updated_at STALE_RUNNING_MINUTES'tan eskiyse
    önceki run crash/timeout olmuş demektir — kaldığı yerden devam et.
    """
    updated_at_str = status.get("updated_at")
    if not updated_at_str:
        return True
    try:
        updated_at = datetime.fromisoformat(updated_at_str)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - updated_at
        return age > timedelta(minutes=STALE_RUNNING_MINUTES)
    except Exception:
        return True


# ── Named Entity tespiti ──────────────────────────────────────────────────────

_NER_SYSTEM = (
    "Sana verilen metindeki özel isimleri listele: kişi adları, yer adları, "
    "kurum/marka adları, kitap/eser adları. "
    "Her ismi yeni satıra yaz. Sadece listeyi döndür, açıklama ekleme. "
    "Eğer özel isim yoksa boş satır döndür."
)


def get_named_entities(paragraph: str, clients, key_index) -> set:
    result = call_llm(clients, key_index, _NER_SYSTEM, paragraph)
    time.sleep(1)
    entities = set()
    for line in result.splitlines():
        name = line.strip().strip('-').strip('•').strip()
        if name:
            entities.add(name.lower())
            for word in name.split():
                if len(word) > 2:
                    entities.add(word.lower())
    return entities


# ── Sorunlu paragraf düzeltici ────────────────────────────────────────────────

_FIX_SYSTEM = (
    "Sen profesyonel bir Türkçe editör ve çevirmensin. "
    "Sana verilen paragrafta bazı kelimeler İngilizce kalmış veya bozuk çevrilmiş. "
    "Korunması gereken özel isimler ayrıca belirtilecek — onlara dokunma. "
    "Paragrafı doğal, akıcı Türkçeye çevir/düzelt. "
    "SADECE düzeltilmiş paragrafı döndür, açıklama ekleme."
)


def fix_paragraph(paragraph: str, protected_names: set,
                  bad_words: list, clients, key_index) -> str:
    protected_str = ", ".join(sorted(protected_names)) if protected_names else "yok"
    user_msg = (
        f"Korunacak özel isimler: {protected_str}\n"
        f"Düzeltilmesi gereken kelimeler: {', '.join(bad_words)}\n\n"
        f"Paragraf:\n{paragraph}"
    )
    result = call_llm(clients, key_index, _FIX_SYSTEM, user_msg)
    time.sleep(1)
    return result


def fix_bad_paragraphs(text: str, clients, key_index) -> str:
    paragraphs = text.split("\n\n")
    fixed_paragraphs = []
    fixed_count = 0

    for para in paragraphs:
        if para.strip().startswith("[EPUB_IMAGE:") or para.strip().startswith("#"):
            fixed_paragraphs.append(para)
            continue

        if is_boilerplate_paragraph(para):
            print(f"    boilerplate atlandı: {para[:60]}...")
            continue

        cleaned = sanitize_unicode(para)
        eng_words = get_english_words(cleaned)

        if not eng_words:
            fixed_paragraphs.append(cleaned)
            continue

        entities = get_named_entities(cleaned, clients, key_index)
        truly_bad = [w for w in eng_words if w.lower() not in entities]

        if not truly_bad:
            fixed_paragraphs.append(cleaned)
            continue

        print(f"    düzeltiliyor: {truly_bad[:5]}{'...' if len(truly_bad) > 5 else ''}")
        fixed = fix_paragraph(cleaned, entities, truly_bad, clients, key_index)
        fixed_paragraphs.append(fixed)
        fixed_count += 1

    if fixed_count:
        print(f"  {fixed_count} paragraf düzeltildi.")

    return "\n\n".join(fixed_paragraphs)


# ── Sliding window ────────────────────────────────────────────────────────────

def chunk_text(text, max_chars=12000):
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


def build_windows(chunks, overlap=BRIDGE_OVERLAP):
    if len(chunks) == 1:
        return [{"text": chunks[0], "is_bridge": False, "index": 0}]
    windows = []
    for i, chunk in enumerate(chunks):
        windows.append({"text": chunk, "is_bridge": False, "index": i})
        if i < len(chunks) - 1:
            bridge_text = chunk[-overlap:] + "\n\n---\n\n" + chunks[i + 1][:overlap]
            windows.append({"text": bridge_text, "is_bridge": True, "index": i})
    return windows


CHUNK_SYSTEM = (
    "Sen bir Türkçe metin editörüsün. "
    "Sana verilen metin daha önce İngilizceden Türkçeye çevrilmiş bir bölümdür. "
    "Görevin şu iki adımı sırayla uygulamak:\n"
    "1. PARAGRAF DÜZEYİ: Her paragrafı ayrı incele — yazım hatalarını düzelt, "
    "İngilizce kalmış kelimeleri Türkçeye çevir, anlamsız kelime seçimlerini düzelt.\n"
    "2. BÖLÜM DÜZEYİ: Tüm metni bir bütün olarak değerlendir — paragraflar arası "
    "anlam akışını ve tutarlılığı koru, aynı kavram için farklı kelimeler "
    "kullanılmışsa birleştir, bozuk cümle yapılarını yeniden yaz.\n"
    "ZORUNLU KURALLAR:\n"
    "- '[EPUB_IMAGE:...]' etiketlerine kesinlikle dokunma.\n"
    "- '# ' ile başlayan başlık satırını olduğu gibi koru.\n"
    "- Yanıt olarak SADECE düzeltilmiş metni yaz. "
    "Hiçbir açıklama, yorum, giriş veya kapanış cümlesi ekleme."
)

BRIDGE_SYSTEM = (
    "Sen bir Türkçe metin editörüsün. "
    "Sana verilen metin, iki parçanın birleşim noktasından alınmış bir köprü bölümüdür. "
    "'---' işareti iki parça arasındaki sınırı gösterir. "
    "Görevin: bu geçiş noktasında anlam sürekliliğini ve kelime tutarlılığını kontrol et. "
    "ZORUNLU KURALLAR:\n"
    "- '[EPUB_IMAGE:...]' etiketlerine kesinlikle dokunma.\n"
    "- '---' ayırıcısını olduğu gibi koru.\n"
    "- Yanıt olarak SADECE düzeltilmiş köprü metnini yaz. "
    "Hiçbir açıklama veya yorum ekleme."
)


def apply_bridge_corrections(corrected_chunks, bridge_results):
    for bridge_idx, bridge_text in bridge_results.items():
        parts = bridge_text.split("\n\n---\n\n", 1)
        if len(parts) != 2:
            print(f"    uyarı: köprü {bridge_idx} ayırıcısı kaybolmuş, atlanıyor.")
            continue

        left_correction = parts[0].strip()
        right_correction = parts[1].strip()

        left_chunk = corrected_chunks[bridge_idx]
        left_overlap_start = max(0, len(left_chunk) - BRIDGE_OVERLAP)
        corrected_chunks[bridge_idx] = (
            left_chunk[:left_overlap_start] + "\n\n" + left_correction
            if left_overlap_start > 0 else left_correction
        )

        right_chunk = corrected_chunks[bridge_idx + 1]
        right_overlap_end = min(len(right_chunk), BRIDGE_OVERLAP)
        corrected_chunks[bridge_idx + 1] = (
            right_correction + "\n\n" + right_chunk[right_overlap_end:]
            if right_overlap_end < len(right_chunk) else right_correction
        )

    return corrected_chunks


# ── Ana review fonksiyonu ─────────────────────────────────────────────────────

def review_file(filepath, clients, key_index):
    with open(filepath, encoding="utf-8") as f:
        raw = f.read()

    # Başlık satırını ayır
    lines = raw.split("\n", 2)
    if lines[0].startswith("#"):
        title_line = lines[0]
        title_text = title_line.lstrip("#").strip()
        body = lines[2].strip() if len(lines) > 2 else ""

        # Başlık boilerplate ise dosyanın tamamı boilerplate — temizle ve çık
        if is_boilerplate_text(title_text):
            print(f"  Boilerplate dosya temizleniyor: {title_text[:60]}")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("")
            return
    else:
        title_line = None
        body = raw.strip()

    # Boilerplate blokları temizle
    body = clean_boilerplate(body)

    if len(body) < 100:
        print(f"  İçerik kalmadı (boilerplate temizlendi), dosya siliniyor.")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("")
        return

    # Sorunlu paragrafları tespit et ve düzelt
    print(f"  Paragraf taraması...")
    body = fix_bad_paragraphs(body, clients, key_index)

    # Sliding window review
    chunks = chunk_text(body)
    windows = build_windows(chunks)
    print(f"  {len(chunks)} chunk → {len(windows)} pencere")

    corrected_chunks = list(chunks)
    bridge_results = {}

    for win in windows:
        if win["is_bridge"]:
            result = call_llm(clients, key_index, BRIDGE_SYSTEM, win["text"])
            bridge_results[win["index"]] = result
            print(f"    köprü {win['index']}↔{win['index']+1} ✓")
        else:
            result = call_llm(clients, key_index, CHUNK_SYSTEM, win["text"])
            corrected_chunks[win["index"]] = result
            print(f"    chunk {win['index']+1}/{len(chunks)} ✓")
        time.sleep(2)

    if bridge_results:
        corrected_chunks = apply_bridge_corrections(corrected_chunks, bridge_results)

    final_body = "\n\n".join(corrected_chunks)
    final_content = f"{title_line}\n\n{final_body}\n" if title_line else final_body + "\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_content)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    status = read_status()

    if status.get("status") != "completed":
        print("Çeviri henüz tamamlanmamış, review bekliyor.")
        return

    review_status = status.get("review_status")

    # running ama eski → crash/timeout olmuş, kaldığı yerden devam et
    if review_status == "running":
        if is_stale_running(status):
            print(f"Review 'running' ama {STALE_RUNNING_MINUTES}dk+ güncellenmemiş — "
                  f"kaldığı yerden devam ediliyor.")
        else:
            print("Review zaten aktif olarak çalışıyor, çıkılıyor.")
            return

    if review_status == "completed":
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

    clients = get_groq_clients()
    key_index = [0]

    # Kaldığı yerden devam — boş dosyaları da tamamlanmış say
    review_done = status.get("review_completed", 0)
    total = len(txt_files)

    status["review_status"] = "running"
    status["review_total"] = total
    status["review_completed"] = review_done
    write_status(status)

    print(f"Review başlıyor: {book_slug} — {total} dosya ({review_done} tamamlandı)")

    for i, fname in enumerate(txt_files):
        if i < review_done:
            print(f"[{i+1}/{total}] Atlanıyor: {fname}")
            continue

        filepath = os.path.join(output_dir, fname)
        print(f"[{i+1}/{total}] Review: {fname}")

        review_file(filepath, clients, key_index)

        status["review_completed"] = i + 1
        status["review_current"] = fname
        write_status(status)

    # Boş bırakılan dosyaları (tamamen boilerplate olanları) sil
    for fname in txt_files:
        filepath = os.path.join(output_dir, fname)
        if os.path.exists(filepath) and os.path.getsize(filepath) == 0:
            os.remove(filepath)
            print(f"  Boş dosya silindi: {fname}")

    status["review_status"] = "completed"
    status["review_current"] = ""
    write_status(status)

    print("Review tamamlandı.")


if __name__ == "__main__":
    main()
