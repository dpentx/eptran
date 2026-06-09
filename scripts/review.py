import os
import json
import subprocess
import unicodedata
from datetime import datetime, timezone

from groq import Groq, RateLimitError
import time
import re

STATUS_FILE = "status.json"
BRIDGE_OVERLAP = 1800

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
]

# Model çıktısı kalıntıları
_JUNK_PATTERNS = [
    re.compile(r'^(?:İşte (?:düzeltilmiş|güncellenmiş|revize edilmiş).*)\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^(?:Düzeltilmiş metin\s*:?)\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^Not\s*:.*\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^(?:Bu metinde|Metinde|Aşağıda).*(?:düzelt|değiştir|güncell).*\n?', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^Açıklama\s*:.*\n?', re.MULTILINE | re.IGNORECASE),
]

# İngilizce suffix'ler — Türkçede bu soneklerle biten kelimeler genellikle çevrilmemiş
_ENG_SUFFIXES = re.compile(
    r'\b\w+(?:lessly|fulness|iveness|ingness|ously|ously|ingly|lessly|'
    r'ment|ness|tion|sion|ity|ful|less|ish|ize|ise|ify|ous|ive|ary|ery|'
    r'ory|ward|wards|wise|like|some|hood|ship|dom|ling)\b',
    re.IGNORECASE
)

# Türkçede normal olan ve false positive oluşturan İngilizce görünümlü kelimeler
_TR_WHITELIST = {
    'olan', 'veya', 'için', 'olan', 'gibi', 'bile', 'daha', 'olan',
    'kadar', 'beri', 'önce', 'sonra', 'ancak', 'fakat', 'lakin',
    'iken', 'yani', 'hatta', 'zaten', 'artık', 'ise', 'ama',
    # Türkçede kullanılan yabancı kökenli ama kabul görmüş kelimeler
    'televizyon', 'telefon', 'internet', 'bilgisayar', 'organizasyon',
    'motivasyon', 'pozisyon', 'prodüksiyon', 'koleksiyon', 'üniversite',
}


def is_boilerplate(paragraph: str) -> bool:
    p = paragraph.strip()
    if not p:
        return True
    for pat in _BOILERPLATE_PATTERNS:
        if pat.search(p):
            return True
    return False


def clean_boilerplate(text: str) -> str:
    paragraphs = text.split("\n\n")
    cleaned = [p for p in paragraphs if not is_boilerplate(p)]
    return "\n\n".join(cleaned).strip()


# ── Unicode sanitizer ─────────────────────────────────────────────────────────

def _script_of_char(ch: str) -> str:
    """Karakterin unicode script kategorisini döndür."""
    try:
        name = unicodedata.name(ch, '')
        if 'LATIN' in name:
            return 'latin'
        if 'ARABIC' in name:
            return 'arabic'
        if 'CYRILLIC' in name:
            return 'cyrillic'
        if 'GREEK' in name:
            return 'greek'
        if 'CJK' in name or 'HIRAGANA' in name or 'KATAKANA' in name:
            return 'cjk'
        return 'other'
    except Exception:
        return 'other'


def sanitize_unicode(text: str) -> str:
    """
    Kelime içi script karışımlarını temizle.
    Örn: 'unutسام' → 'unut' (arapça kısım kaldırılır, kelime işaretlenir)
    Bozuk token sonucu oluşan mixed-script kelimeleri boşlukla ayır.
    """
    words = text.split(' ')
    cleaned_words = []

    for word in words:
        if len(word) < 2:
            cleaned_words.append(word)
            continue

        # Kelimede birden fazla script var mı?
        scripts = set()
        for ch in word:
            if ch.isalpha():
                scripts.add(_script_of_char(ch))

        if len(scripts) <= 1:
            cleaned_words.append(word)
            continue

        # Mixed script: latin olmayan kısımları at
        latin_only = ''.join(ch for ch in word if not ch.isalpha() or _script_of_char(ch) == 'latin')
        if latin_only.strip():
            cleaned_words.append(latin_only)
            print(f"    unicode temizlendi: '{word}' → '{latin_only}'")
        # Latin hiç yoksa tüm kelimeyi at (tamamen yabancı script bozukluğu)

    return ' '.join(cleaned_words)


# ── İngilizce kelime tespiti ──────────────────────────────────────────────────

_ENG_WORD_RE = re.compile(r'\b[a-zA-Z]{3,}\b')

# Kesinlikle İngilizce olan suffix kalıpları
_HARD_ENG_SUFFIX = re.compile(
    r'\b\w+(?:lessly|iveness|ingness|fulness|ously|ingly|ment|tion|sion|'
    r'ness|ify|ize|ise|ary|ery|ward|wards|wise|hood|ship)\b',
    re.IGNORECASE
)


def get_english_words(paragraph: str) -> list[str]:
    """Paragraftaki İngilizce kalmış kelimeleri döndür."""
    candidates = _ENG_WORD_RE.findall(paragraph)
    result = []
    for w in candidates:
        wl = w.lower()
        if wl in _TR_WHITELIST:
            continue
        # Türkçe eklerle bitiyorsa muhtemelen Türkçe kelime
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
            raw = response.choices[0].message.content
            return clean_output(raw)
        except RateLimitError as e:
            wait = parse_retry_seconds(e)
            print(f"Key {info['id']} rate limit! {wait}s kilitlendi.")
            info["locked_until"] = time.time() + wait
            key_index[0] = (idx + 1) % len(clients)
        except Exception as e:
            print(f"Hata: {e} — 30s sonra tekrar deneniyor...")
            time.sleep(30)


def clean_output(text: str) -> str:
    for pattern in _JUNK_PATTERNS:
        text = pattern.sub('', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


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


# ── Named Entity tespiti ──────────────────────────────────────────────────────

_NER_SYSTEM = (
    "Sana verilen metindeki özel isimleri listele: kişi adları, yer adları, "
    "kurum/marka adları, kitap/eser adları. "
    "Her ismi yeni satıra yaz. Sadece listeyi döndür, açıklama ekleme. "
    "Eğer özel isim yoksa boş satır döndür."
)


def get_named_entities(paragraph: str, clients, key_index) -> set[str]:
    """Paragraftaki özel isimleri LLM ile tespit et, whitelist olarak döndür."""
    result = call_llm(clients, key_index, _NER_SYSTEM, paragraph)
    time.sleep(1)
    entities = set()
    for line in result.splitlines():
        name = line.strip().strip('-').strip('•').strip()
        if name:
            entities.add(name.lower())
            # Çok kelimeli isimlerin her kelimesini de ekle
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


def fix_paragraph(paragraph: str, protected_names: set[str],
                  bad_words: list[str], clients, key_index) -> str:
    """Sorunlu paragrafı LLM'e gönder, düzeltilmiş halini al."""
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
    """
    Metindeki tüm paragrafları tara:
    1. Unicode temizle
    2. İngilizce kelime tespit et
    3. NER ile özel isimleri whitelist'e al
    4. Whitelist dışında sorun varsa paragrafı yeniden düzelt
    """
    paragraphs = text.split("\n\n")
    fixed_paragraphs = []
    fixed_count = 0

    for para in paragraphs:
        # [EPUB_IMAGE:...] etiketleri ve başlık satırlarına dokunma
        if para.strip().startswith("[EPUB_IMAGE:") or para.strip().startswith("#"):
            fixed_paragraphs.append(para)
            continue

        # Boilerplate kontrolü
        if is_boilerplate(para):
            print(f"    boilerplate atlandı: {para[:60]}...")
            continue

        # Unicode temizle
        cleaned = sanitize_unicode(para)

        # İngilizce kelime tespiti
        eng_words = get_english_words(cleaned)

        if not eng_words:
            fixed_paragraphs.append(cleaned)
            continue

        # NER — özel isimleri whitelist'e al
        entities = get_named_entities(cleaned, clients, key_index)

        # Whitelist dışında İngilizce kelime var mı?
        truly_bad = [w for w in eng_words if w.lower() not in entities]

        if not truly_bad:
            # Hepsi özel isim, sorun yok
            fixed_paragraphs.append(cleaned)
            continue

        # Sorunlu paragraf → LLM ile düzelt
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


# ── System mesajları ──────────────────────────────────────────────────────────

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


# ── Köprü entegrasyonu ────────────────────────────────────────────────────────

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
        body = lines[2].strip() if len(lines) > 2 else ""
    else:
        title_line = None
        body = raw.strip()

    # 1. Boilerplate temizle (zaten çevrilmiş dosyalar için)
    body = clean_boilerplate(body)

    # 2. Sorunlu paragrafları tespit et ve düzelt (NER + fix)
    print(f"  paragraf taraması başlıyor...")
    body = fix_bad_paragraphs(body, clients, key_index)

    # 3. Sliding window review
    chunks = chunk_text(body)
    windows = build_windows(chunks)
    print(f"  {len(chunks)} chunk → {len(windows)} pencere (sliding window)")

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

    if status.get("review_status") in ("running", "completed"):
        print(f"Review zaten: {status.get('review_status')}")
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

    review_done = status.get("review_completed", 0)
    total = len(txt_files)

    status["review_status"] = "running"
    status["review_total"] = total
    status["review_completed"] = review_done
    write_status(status)

    print(f"Review başlıyor: {book_slug} — {total} dosya ({review_done} zaten tamamlandı)")

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

    status["review_status"] = "completed"
    status["review_current"] = ""
    write_status(status)

    print("Review tamamlandı.")


if __name__ == "__main__":
    main()
