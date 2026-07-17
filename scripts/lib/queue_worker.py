"""
eptran — queue_worker.py

Hydra tarzı kuyruk işleyicisi: output/<kitap>/.originals/ altındaki
parçaları SIRAYLA, HER ÇALIŞTIRMADA TEK BİR TANESİNİ işler, commit'ler
ve sırada başka parça varsa kendini yeniden tetikler (gh workflow run).

Bir bölümün TÜM parçaları çevrildiğinde, onları birleştirip normal
output/<kitap>/NNN_<slug>.txt dosyasını yazar (review.py/convert.py bu
dosyaları eskisi gibi, hiçbir değişiklik gerekmeden kullanır).

Neden bu tasarım: eskiden tek bir run bir kitabın TÜMÜNÜ (360 dakikaya
kadar) işlemeye çalışıyordu. Chunk checkpoint'i olsa bile bu, uzun
job'ları concurrency/timeout risklerine açık bırakıyordu. Artık her run
sadece birkaç dakika sürüyor — kaybedilebilecek en fazla şey tek bir
parçanın o anki denemesi, hiçbir zaman saatlerce ilerleme değil.

Rate limit / kalıcı hata durumunda: bu run'da hiçbir şey commit'lenmez
VE self-trigger YAPILMAZ — zincir orada durur, translate.yml'in periyodik
"güvenlik ağı" tetiklemesi bir sonraki denemeyi başlatır.
"""
import glob
import json
import os
import re
import subprocess
from datetime import datetime, timezone

from lib import groq_client as gc, memory as mem, ner
from lib.git_utils import write_status, trigger_workflow
from translate import translate_chapter

STATUS_FILE = "status.json"
PART_RE = re.compile(r"^(\d{3})_(\d{2})\.txt$")


def _load_status():
    if not os.path.exists(STATUS_FILE):
        return None
    with open(STATUS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _originals_dir(output_dir: str) -> str:
    return f"{output_dir}/.originals"


def _translated_dir(output_dir: str) -> str:
    return f"{output_dir}/.translated"


def _next_part(originals_dir: str, translated_dir: str):
    """Sırada bekleyen ilk (chapter_idx, part_idx, dosya_yolu) üçlüsünü bulur."""
    for path in sorted(glob.glob(f"{originals_dir}/*_*.txt")):
        name = os.path.basename(path)
        m = PART_RE.match(name)
        if not m:
            continue
        translated_path = os.path.join(translated_dir, name)
        if not os.path.exists(translated_path):
            return int(m.group(1)), int(m.group(2)), path
    return None


def _chapter_meta_path(originals_dir: str, chapter_idx: int) -> str:
    return f"{originals_dir}/{chapter_idx:03d}_meta.json"


def _load_chapter_meta(originals_dir: str, chapter_idx: int) -> dict:
    with open(_chapter_meta_path(originals_dir, chapter_idx), encoding="utf-8") as f:
        return json.load(f)


def _save_chapter_meta(originals_dir: str, chapter_idx: int, meta: dict) -> None:
    path = _chapter_meta_path(originals_dir, chapter_idx)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)


def _reconstruct_source(originals_dir: str, chapter_idx: int, total_parts: int) -> str:
    """Bir bölümün TÜM kaynak parçalarını birleştirir (NER/hafıza taraması için)."""
    parts = []
    for p in range(total_parts):
        path = f"{originals_dir}/{chapter_idx:03d}_{p:02d}.txt"
        with open(path, encoding="utf-8") as f:
            parts.append(f.read())
    return "\n\n".join(parts)


def main():
    status = _load_status()
    if status is None or status.get("status") != "running" or not status.get("queue_mode"):
        print("Aktif bir kuyruk yok, çıkılıyor.")
        return

    book_slug = status["book"]
    total = status["total"]
    output_dir = f"output/{book_slug}"
    originals_dir = _originals_dir(output_dir)
    translated_dir = _translated_dir(output_dir)
    os.makedirs(translated_dir, exist_ok=True)

    next_part = _next_part(originals_dir, translated_dir)
    if next_part is None:
        print("Kuyrukta bekleyen parça yok — kitap tamamlanmış olmalı.")
        status["status"] = "completed"
        status["current_chapter"] = ""
        write_status(status, "status: completed")
        return

    chapter_idx, part_idx, part_path = next_part
    with open(part_path, encoding="utf-8") as f:
        chunk_text = f.read()

    meta = _load_chapter_meta(originals_dir, chapter_idx)
    total_parts = meta["total_parts"]
    title = meta["title"]

    clients = gc.get_clients()
    key_index = [0]

    memory = mem.load(output_dir)

    # Kitabın ilk bölümünün ilk parçasıysa ve hafıza boşsa, hafızayı
    # kaynak metinden çıkar (bir kereye mahsus).
    if chapter_idx == 0 and part_idx == 0 and not memory.get("characters"):
        print("Çeviri hafızası çıkarılıyor...")
        full_source = _reconstruct_source(originals_dir, chapter_idx, total_parts)
        try:
            memory = mem.extract_from_source(full_source, clients, key_index)
        except gc.AllKeysLockedError as e:
            print(f"Tüm keyler kilitli ({e.wait_seconds}s) — hafıza çıkarılamadı, "
                  f"bu run'da self-trigger yapılmıyor.")
            return
        mem.save(output_dir, memory)
        print(f"  Hafıza: {len(memory['characters'])} karakter, "
              f"{len(memory['terms'])} terim")

    # Bu bölümün ilk parçasıysa NER + hafıza context'ini hesaplayıp
    # bölümün meta dosyasına önbelleğe al — diğer parçalar bunu tekrar
    # hesaplamadan aynen kullanacak (tutarlılık + gereksiz API çağrısını
    # önlemek için).
    if part_idx == 0 and meta.get("protected_str") is None:
        print(f"[{chapter_idx+1}/{total}] NER taraması: {title}")
        full_source = _reconstruct_source(originals_dir, chapter_idx, total_parts)
        try:
            chapter_entities = ner.extract_from_source(full_source, clients, key_index)
        except gc.AllKeysLockedError as e:
            print(f"Tüm keyler kilitli ({e.wait_seconds}s) — NER yapılamadı, "
                  f"bu run'da self-trigger yapılmıyor.")
            return
        protected_str = ner.build_protected_str(memory, chapter_entities)
        if protected_str:
            print(f"  Korunan: {len(chapter_entities)} isim/terim")
        meta["protected_str"] = protected_str
        meta["memory_ctx"] = mem.build_context(memory)
        _save_chapter_meta(originals_dir, chapter_idx, meta)
        subprocess.run(["git", "add", _chapter_meta_path(originals_dir, chapter_idx)])

    protected_str = meta.get("protected_str") or ""
    memory_ctx = meta.get("memory_ctx") or ""

    print(f"[{chapter_idx+1}/{total}] Çevriliyor: {title} "
          f"— parça {part_idx+1}/{total_parts}")
    status["current_chapter"] = title
    try:
        translated = translate_chapter(
            {"title": title, "text": chunk_text}, clients, key_index,
            memory_ctx, protected_str, part_idx, total_parts,
        )
    except gc.AllKeysLockedError as e:
        print(f"Tüm keyler kilitli ({e.wait_seconds}s) — bu parça bu run'da "
              f"çevrilemedi, self-trigger yapılmıyor (güvenlik ağı devralacak).")
        return

    if translated is None:
        print("Hata: parça çevrilemedi (model ısrarla boş/kesik yanıt döndürdü). "
              "Self-trigger yapılmıyor — bir sonraki tetiklemede aynı parça "
              "tekrar denenecek.")
        return

    translated_path = f"{translated_dir}/{chapter_idx:03d}_{part_idx:02d}.txt"
    with open(translated_path, "w", encoding="utf-8") as f:
        f.write(translated)
    subprocess.run(["git", "add", translated_path])
    write_status(status, f"parça: bölüm {chapter_idx+1}/{total} "
                          f"- {part_idx+1}/{total_parts}")

    # Bölümün tüm parçaları bitti mi?
    all_done = all(
        os.path.exists(f"{translated_dir}/{chapter_idx:03d}_{p:02d}.txt")
        for p in range(total_parts)
    )
    if all_done:
        pieces = []
        for p in range(total_parts):
            with open(f"{translated_dir}/{chapter_idx:03d}_{p:02d}.txt",
                      encoding="utf-8") as f:
                pieces.append(f.read())
        full_translation = "\n\n".join(pieces)
        out_path = f"{output_dir}/{chapter_idx+1:03d}_{book_slug}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{full_translation}\n")

        try:
            memory = mem.update_from_translation(memory, full_translation,
                                                  clients, key_index)
            memory = mem.add_summary(memory, title, full_translation,
                                      clients, key_index)
        except gc.AllKeysLockedError:
            print("Uyarı: hafıza güncellenemedi (tüm keyler kilitli), "
                  "mevcut hafıza korunuyor.")
        mem.save(output_dir, memory)

        # Bu bölümün kuyruk dosyalarını temizle (artık gerekmiyorlar)
        for p in range(total_parts):
            for d in (originals_dir, translated_dir):
                fp = f"{d}/{chapter_idx:03d}_{p:02d}.txt"
                if os.path.exists(fp):
                    os.remove(fp)
                    subprocess.run(["git", "rm", "-f", "--ignore-unmatch", fp])
        meta_path = _chapter_meta_path(originals_dir, chapter_idx)
        if os.path.exists(meta_path):
            os.remove(meta_path)
            subprocess.run(["git", "rm", "-f", "--ignore-unmatch", meta_path])

        status["completed"] = chapter_idx + 1
        subprocess.run(["git", "add", out_path,
                        os.path.join(output_dir, mem.MEMORY_FILE)])
        write_status(status, f"status: {chapter_idx+1}/{total}")
        print(f"[{chapter_idx+1}/{total}] Bölüm tamamlandı: {title}")

    # Sırada başka parça var mı? Varsa kendimi tetikle, yoksa kitap bitti.
    if _next_part(originals_dir, translated_dir) is not None:
        print("Sıradaki parça için kendimi tetikliyorum...")
        trigger_workflow("queue-worker.yml")
    else:
        status["status"] = "completed"
        status["current_chapter"] = ""
        write_status(status, "status: completed")
        print("Kitap tamamlandı!")


if __name__ == "__main__":
    main()
