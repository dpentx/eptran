"""
Sliding window review mekanizması.

N chunk → 2N-1 pencere:
  Çift indexler  (0,2,4,...) → chunk'ların kendisi
  Tek indexler   (1,3,5,...) → köprü pencereleri (A sonu + B başı)
"""
import time

from . import groq_client as gc

BRIDGE_OVERLAP = 1800  # her iki taraftan alınan karakter (~270 kelime)

CHUNK_SYSTEM = (
    "Sen bir Türkçe metin editörüsün. "
    "Sana verilen metin daha önce İngilizceden Türkçeye çevrilmiş bir bölümdür.\n"
    "Görevin:\n"
    "1. PARAGRAF DÜZEYİ: Yazım hatalarını düzelt, İngilizce kalmış kelimeleri "
    "Türkçeye çevir, anlamsız kelime seçimlerini düzelt.\n"
    "2. BÖLÜM DÜZEYİ: Paragraflar arası anlam akışını ve tutarlılığı koru, "
    "aynı kavram için farklı kelimeler kullanılmışsa birleştir, "
    "bozuk cümle yapılarını yeniden yaz.\n"
    "ZORUNLU KURALLAR:\n"
    "- '[EPUB_IMAGE:...]' etiketlerine kesinlikle dokunma.\n"
    "- '# ' ile başlayan başlık satırını olduğu gibi koru.\n"
    "- Yanıt olarak SADECE düzeltilmiş metni yaz, hiçbir açıklama ekleme."
)

BRIDGE_SYSTEM = (
    "Sen bir Türkçe metin editörüsün. "
    "Sana verilen metin iki parçanın birleşim noktasından alınmış köprü bölümüdür. "
    "'---' işareti iki parça arasındaki sınırı gösterir. "
    "Bu geçiş noktasında anlam sürekliliğini ve kelime tutarlılığını kontrol et.\n"
    "ZORUNLU KURALLAR:\n"
    "- '[EPUB_IMAGE:...]' etiketlerine dokunma.\n"
    "- '---' ayırıcısını olduğu gibi koru.\n"
    "- Yanıt olarak SADECE düzeltilmiş köprü metnini yaz, hiçbir açıklama ekleme."
)


def chunk_text(text: str, max_chars: int = 12000) -> list:
    """Metni paragraf sınırlarına göre chunk'lara böl."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    current = ""
    for para in text.split("\n\n"):
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current += "\n\n" + para if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks


def build_windows(chunks: list, overlap: int = BRIDGE_OVERLAP) -> list:
    """Chunk listesinden sliding window listesi oluştur."""
    if len(chunks) == 1:
        return [{"text": chunks[0], "is_bridge": False, "index": 0}]

    windows = []
    for i, chunk in enumerate(chunks):
        windows.append({"text": chunk, "is_bridge": False, "index": i})
        if i < len(chunks) - 1:
            bridge = chunk[-overlap:] + "\n\n---\n\n" + chunks[i + 1][:overlap]
            windows.append({"text": bridge, "is_bridge": True, "index": i})
    return windows


def apply_bridge_corrections(chunks: list, bridge_results: dict) -> list:
    """Köprü düzeltmelerini ilgili chunk'ların sınır bölgelerine yansıt."""
    corrected = list(chunks)

    for bridge_idx, bridge_text in bridge_results.items():
        parts = bridge_text.split("\n\n---\n\n", 1)
        if len(parts) != 2:
            print(f"    uyarı: köprü {bridge_idx} ayırıcısı kaybolmuş, atlanıyor.")
            continue

        left, right = parts[0].strip(), parts[1].strip()

        # Sol chunk'ın sonu
        lc = corrected[bridge_idx]
        split = max(0, len(lc) - BRIDGE_OVERLAP)
        corrected[bridge_idx] = (lc[:split] + "\n\n" + left) if split > 0 else left

        # Sağ chunk'ın başı
        rc = corrected[bridge_idx + 1]
        end = min(len(rc), BRIDGE_OVERLAP)
        corrected[bridge_idx + 1] = (right + "\n\n" + rc[end:]) if end < len(rc) else right

    return corrected


def review_chunks(chunks: list, clients: list, key_index: list,
                  memory_context: str = "") -> list:
    """
    Chunk listesini sliding window ile review et.
    memory_context varsa her sistem mesajına eklenir.
    """
    windows = build_windows(chunks)
    print(f"  {len(chunks)} chunk → {len(windows)} pencere")

    corrected = list(chunks)
    bridge_results = {}

    for win in windows:
        # Memory context'i system mesajına ekle
        if memory_context:
            sys_chunk = CHUNK_SYSTEM + "\n\n" + memory_context
            sys_bridge = BRIDGE_SYSTEM + "\n\n" + memory_context
        else:
            sys_chunk = CHUNK_SYSTEM
            sys_bridge = BRIDGE_SYSTEM

        if win["is_bridge"]:
            result = gc.call(clients, key_index, sys_bridge, win["text"])
            bridge_results[win["index"]] = result
            print(f"    köprü {win['index']}↔{win['index']+1} ✓")
        else:
            result = gc.call(clients, key_index, sys_chunk, win["text"])
            corrected[win["index"]] = result
            print(f"    chunk {win['index']+1}/{len(chunks)} ✓")
        time.sleep(2)

    if bridge_results:
        corrected = apply_bridge_corrections(corrected, bridge_results)

    return corrected
