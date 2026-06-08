import os
import json
import subprocess
from datetime import datetime, timezone

from groq import Groq, RateLimitError
import time
import re

STATUS_FILE = "status.json"
BRIDGE_OVERLAP = 1800  # her iki taraftan alınacak karakter (~270 kelime)


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
    for h in re.findall(r'([\d.]+)h', time_str):
        total += float(h) * 3600
    for m in re.findall(r'([\d.]+)m', time_str):
        total += float(m) * 60
    for s in re.findall(r'([\d.]+)s', time_str):
        total += float(s)
    return int(total) + 5


def call_llm(clients, key_index, prompt):
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
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            key_index[0] = (idx + 1) % len(clients)
            return response.choices[0].message.content.strip()
        except RateLimitError as e:
            wait = parse_retry_seconds(e)
            print(f"Key {info['id']} rate limit! {wait}s kilitlendi.")
            clients[idx]["locked_until"] = time.time() + wait
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


# ── Sliding window ────────────────────────────────────────────────────────────

def chunk_text(text, max_chars=12000):
    """translate.py ile aynı mantık — tutarlılık için birebir kopya."""
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
    """
    N chunk → 2N-1 pencere.
    Tek chunk ise sadece kendisi döner.
    Çift indexler (0,2,4...) chunk'ların kendisi,
    tek indexler (1,3,5...) köprü pencereleri.
    """
    if len(chunks) == 1:
        return [{"text": chunks[0], "is_bridge": False, "index": 0}]

    windows = []
    for i, chunk in enumerate(chunks):
        windows.append({"text": chunk, "is_bridge": False, "index": i})
        if i < len(chunks) - 1:
            bridge_text = chunk[-overlap:] + "\n\n---\n\n" + chunks[i + 1][:overlap]
            windows.append({"text": bridge_text, "is_bridge": True, "index": i})
    return windows


# ── Prompt'lar ────────────────────────────────────────────────────────────────

CHUNK_PROMPT = """Aşağıdaki metin bir Türkçe çevirinin bir bölümüdür.

Görevin şu iki adımı sırayla uygulamak:

1. PARAGRAF DÜZEYİ — Her paragrafı ayrı ayrı incele:
   - Yazım hatalarını (typo) düzelt
   - İngilizce kalmış kelimeleri Türkçeye çevir (örn. "shield" → "kalkan", "raid" → "baskın")
   - Garip veya anlamsız kelime seçimlerini düzelt

2. BÖLÜM DÜZEYİ — Tüm metni bir bütün olarak değerlendir:
   - Paragraflar arası anlam akışını ve tutarlılığı koru
   - Aynı kavram için farklı kelimeler kullanılmışsa birleştir
   - Cümle yapısı bozuksa yeniden yaz, ama anlamı değiştirme

KURALLAR:
- [EPUB_IMAGE:...] etiketlerini KESİNLİKLE olduğu gibi bırak, taşıma, silme, değiştirme
- Başlık satırını (# ile başlayan) olduğu gibi koru
- Sadece düzeltilmiş metni döndür, açıklama ekleme
- Metnin uzunluğunu korumaya çalış

METİN:
{text}"""

BRIDGE_PROMPT = """Aşağıdaki metin iki chunk'ın birleşim noktasından alınan bir köprü parçasıdır.
"---" işareti iki chunk arasındaki sınırı gösterir.

Görevin:
- Bu geçiş noktasında anlam sürekliliğini kontrol et
- Sınır boyunca tutarsız kelime veya kavram kullanımı varsa not et
- Düzeltilmiş köprü metnini döndür (aynı uzunlukta)

KURALLAR:
- [EPUB_IMAGE:...] etiketlerine dokunma
- Sadece düzeltilmiş metni döndür
- "---" ayırıcısını koru

METİN:
{text}"""


# ── Köprü geri bildirimi entegrasyonu ────────────────────────────────────────

def apply_bridge_corrections(original_chunks, bridge_results):
    """
    Köprü pencerelerinden gelen düzeltmeleri ilgili chunk'lara yansıt.
    Köprünün ilk yarısı → önceki chunk'ın sonu
    Köprünün ikinci yarısı → sonraki chunk'ın başı
    """
    corrected = list(original_chunks)

    for bridge_idx, bridge_text in bridge_results.items():
        # bridge_idx: köprünün solundaki chunk'ın index'i
        parts = bridge_text.split("\n\n---\n\n", 1)
        if len(parts) != 2:
            continue

        left_correction, right_correction = parts[0].strip(), parts[1].strip()

        # Sol chunk'ın sonunu güncelle
        left_chunk = corrected[bridge_idx]
        left_overlap_start = max(0, len(left_chunk) - BRIDGE_OVERLAP)
        corrected[bridge_idx] = left_chunk[:left_overlap_start] + "\n\n" + left_correction if left_overlap_start > 0 else left_correction

        # Sağ chunk'ın başını güncelle
        right_chunk = corrected[bridge_idx + 1]
        right_overlap_end = min(len(right_chunk), BRIDGE_OVERLAP)
        corrected[bridge_idx + 1] = right_correction + "\n\n" + right_chunk[right_overlap_end:] if right_overlap_end < len(right_chunk) else right_correction

    return corrected


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

    chunks = chunk_text(body)
    windows = build_windows(chunks)

    print(f"  {len(chunks)} chunk → {len(windows)} pencere")

    corrected_chunks = list(chunks)
    bridge_results = {}

    for win in windows:
        if win["is_bridge"]:
            prompt = BRIDGE_PROMPT.format(text=win["text"])
            result = call_llm(clients, key_index, prompt)
            bridge_results[win["index"]] = result
            print(f"    köprü {win['index']}↔{win['index']+1} ✓")
        else:
            prompt = CHUNK_PROMPT.format(text=win["text"])
            result = call_llm(clients, key_index, prompt)
            corrected_chunks[win["index"]] = result
            print(f"    chunk {win['index']+1}/{len(chunks)} ✓")
        time.sleep(2)

    # Köprü düzeltmelerini chunk'lara yansıt
    if bridge_results:
        corrected_chunks = apply_bridge_corrections(corrected_chunks, bridge_results)

    final_body = "\n\n".join(corrected_chunks)
    if title_line:
        final_content = f"{title_line}\n\n{final_body}\n"
    else:
        final_content = final_body + "\n"

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

    # Kaldığı yerden devam
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
