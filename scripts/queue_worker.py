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

from lib import groq_client as gc, memory as mem, ner, series as series_lib
from lib.git_utils import write_status, trigger_workflow, current_branch
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


MIN_SPLIT_WORDS = 500  # bunun altına inersek daha fazla bölmenin faydası yok


def _split_and_requeue(originals_dir: str, chapter_idx: int, part_idx: int,
                        total_parts: int, chunk_text: str, meta: dict) -> bool:
    """
    Bir parça, gc.call()'ın kendi retry/küçültme mekanizmasına rağmen
    ISRARLA başarısız oluyorsa, bunun sebebi genelde ARTIK reasoning
    token'ları değil — parçanın kendisi (girdi + gereken çıktı) hesabın
    TPM tavanı için tek başına fazla büyük demektir. Bu durumda parçayı
    paragraf sınırında ikiye bölüp kuyruğa GERİ KOYUYORUZ.

    Sıradaki (part_idx'ten sonraki) parçalar henüz hiç işlenmediği için
    (kuyruk her zaman sırayla ilerliyor) numaralarını 1 kaydırmak
    güvenlidir — hiçbir çevrilmiş içerik kaybolmaz, sadece yeniden
    numaralandırılır.

    Böler ve kuyruğa koyarsa True, (kelime sayısı zaten düşükse, bölmenin
    faydası olmayacağı için) bölmeden False döner.
    """
    words = chunk_text.split()
    if len(words) < MIN_SPLIT_WORDS * 2:
        print(f"  Parça zaten küçük ({len(words)} kelime) — bölmenin faydası "
              f"yok, sorun büyüklükten kaynaklanmıyor olabilir.")
        return False

    paragraphs = [p for p in chunk_text.split("\n\n") if p.strip()]
    half_words = len(words) / 2

    if len(paragraphs) < 2:
        # Tek bir devasa paragraf (bkz. Poe'nun "Marie Rogêt" gibi
        # bölümleri — bazı paragrafları tek başına 700+ kelime). Doğal
        # bir paragraf sınırı yoksa cümle sınırında bölmeyi dene.
        sentences = re.split(r'(?<=[.!?”"\'])\s+(?=[A-ZÀ-Ý])', paragraphs[0]) if paragraphs else []
        if len(sentences) < 2:
            print("  Parça tek bir paragraf/cümle — doğal bir bölme sınırı yok.")
            return False
        first, second, running = [], [], 0
        for sent in sentences:
            sent_words = len(sent.split())
            if not first or running + sent_words <= half_words:
                first.append(sent)
                running += sent_words
            else:
                second.append(sent)
        if not second:
            print("  Cümle bazlı bölme de ikinci yarıyı boş bıraktı — bölünemedi.")
            return False
        first_text = " ".join(first)
        second_text = " ".join(second)
    else:
        # Paragrafları BİRİKTİREREK ikiye ayır. NOT: eskiden burada
        # "running < half_words ise ekle" mantığı vardı — ama bir paragraf
        # TEK BAŞINA yarıdan büyükse (örn. 723 kelimelik bir paragraf),
        # bu paragraf eklendiğinde running yarıyı çoktan geçmiş oluyor
        # ANCAK zaten "içeri alınmış" oluyordu, ondan sonra eklenecek
        # paragraf kalmıyordu — "second" boş kalıp SESSİZCE False
        # dönüyordu (bu bug'ı gerçek bir Poe bölümünde yakaladık: 5
        # paragraf, biri 723 kelime, hepsi "first"e gitmişti). Artık her
        # paragraf eklenmeden ÖNCE "eklersem yarıyı aşar mıyım" diye
        # kontrol ediyoruz — aşıyorsa (ve "first" zaten boş değilse) bu
        # paragrafı ve sonrasını "second"e bırakıyoruz.
        first, second, running = [], [], 0
        for para in paragraphs:
            para_words = len(para.split())
            if not first or running + para_words <= half_words:
                first.append(para)
                running += para_words
            else:
                second.append(para)
        if not second:
            print("  Paragraf bazlı bölme ikinci yarıyı boş bıraktı — "
                  "bölünemedi (tüm paragraflar tek yarıya sığdı).")
            return False
        first_text = "\n\n".join(first)
        second_text = "\n\n".join(second)

    # Sonraki (henüz işlenmemiş) parçaların dosya adlarını SONDAN BAŞA
    # doğru 1 kaydır (üzerine yazmayı önlemek için ters sırayla).
    for p in range(total_parts - 1, part_idx, -1):
        old = f"{originals_dir}/{chapter_idx:03d}_{p:02d}.txt"
        new = f"{originals_dir}/{chapter_idx:03d}_{p+1:02d}.txt"
        if os.path.exists(old):
            os.rename(old, new)
            subprocess.run(["git", "add", new])
            subprocess.run(["git", "rm", "--cached", "--ignore-unmatch", old])

    with open(f"{originals_dir}/{chapter_idx:03d}_{part_idx:02d}.txt",
              "w", encoding="utf-8") as f:
        f.write(first_text)
    with open(f"{originals_dir}/{chapter_idx:03d}_{part_idx+1:02d}.txt",
              "w", encoding="utf-8") as f:
        f.write(second_text)
    subprocess.run(["git", "add", originals_dir])

    meta["total_parts"] = total_parts + 1
    _save_chapter_meta(originals_dir, chapter_idx, meta)
    subprocess.run(["git", "add", _chapter_meta_path(originals_dir, chapter_idx)])

    print(f"  Parça {part_idx+1}/{total_parts} ısrarla başarısız oldu "
          f"({len(words)} kelime) — muhtemelen hesabın TPM tavanı için tek "
          f"başına çok büyük. İkiye bölünüp kuyruğa geri konuldu "
          f"(bölüm artık {total_parts + 1} parça).")
    return True


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
    if memory.get("characters") and not memory.get("_book_memory_seeded"):
        # Bu özellikten ÖNCE başlamış eski bir kitap: hafıza zaten dolu,
        # sıfırdan çıkarmaya gerek yok — sadece bayrağı işaretle.
        memory["_book_memory_seeded"] = True

    # Seri geneli hafıza (bkz. lib/series.py): bu kitap bir seriye
    # bağlıysa (status.json'da "series"), admin'in elle yazdığı
    # series/<slug>.json'ı hafızaya işle. BİR KEZE MAHSUS değil — her
    # run'da (ucuz, LLM çağrısı yok) tekrar uygulanıyor ki kitabın
    # kendi öğrenme süreci (extract_from_source/update_from_translation)
    # seri düzeyinde zaten doğrulanmış bir değeri YANLIŞLIKLA ezemesin
    # (knh-10'da "Lahan'ın Kardeşi"nin "Lakan'ın Kardeşi"ye dönüşüp 10
    # bölüme yayılması tam olarak böyle önlenmek isteniyor).
    series_data = series_lib.load(status["series"]) if status.get("series") else {}
    if series_data:
        memory = series_lib.apply_overlay(memory, series_data)

    # Kitabın ilk bölümünün ilk parçasıysa ve hafıza boşsa, hafızayı
    # kaynak metinden çıkar (bir kereye mahsus). Seri glossary'si zaten
    # bazı karakterleri doldurmuş olabilir — extract_from_source yine de
    # çalışır, çünkü amaç SADECE seride olmayan, bu kitaba özel yeni
    # karakter/terimleri bulmak; overlay az önce uygulandığı ve aşağıda
    # tekrar uygulanacağı için seriden gelenler ezilemez.
    if chapter_idx == 0 and part_idx == 0 and not memory.get("_book_memory_seeded"):
        print("Çeviri hafızası çıkarılıyor...")
        full_source = _reconstruct_source(originals_dir, chapter_idx, total_parts)
        try:
            memory = mem.extract_from_source(full_source, clients, key_index)
        except gc.AllKeysLockedError as e:
            print(f"Tüm keyler kilitli ({e.wait_seconds}s) — hafıza çıkarılamadı, "
                  f"bu run'da self-trigger yapılmıyor.")
            return
        memory = series_lib.apply_overlay(memory, series_data)  # seri her zaman kazanır
        memory["_book_memory_seeded"] = True
        mem.save(output_dir, memory)
        print(f"  Hafıza: {len(memory['characters'])} karakter, "
              f"{len(memory['terms'])} terim"
              + (f" (+ seri: {status['series']})" if series_data else ""))

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

    # Bir önceki parçanın çevirisinin son ~600 karakterini bağlam olarak
    # al — bu, chunk sınırlarında üslup/terim dikişini KAYNAĞINDA önlüyor
    # (bkz. translate_chapter'daki prev_tail açıklaması). İlk parça için
    # (part_idx==0) doğal olarak önceki parça yok.
    prev_tail = ""
    if part_idx > 0:
        prev_path = f"{translated_dir}/{chapter_idx:03d}_{part_idx-1:02d}.txt"
        if os.path.exists(prev_path):
            with open(prev_path, encoding="utf-8") as f:
                prev_text = f.read().strip()
            prev_tail = prev_text[-600:]

    print(f"[{chapter_idx+1}/{total}] Çevriliyor: {title} "
          f"— parça {part_idx+1}/{total_parts}")
    status["current_chapter"] = title
    try:
        translated = translate_chapter(
            {"title": title, "text": chunk_text}, clients, key_index,
            memory_ctx, protected_str, part_idx, total_parts,
            prev_tail=prev_tail,
        )
    except gc.AllKeysLockedError as e:
        print(f"Tüm keyler kilitli ({e.wait_seconds}s) — bu parça bu run'da "
              f"çevrilemedi, self-trigger yapılmıyor (güvenlik ağı devralacak).")
        return

    if translated is None:
        print("Hata: parça çevrilemedi (model ısrarla boş/kesik yanıt döndürdü).")
        split_ok = _split_and_requeue(originals_dir, chapter_idx, part_idx,
                                       total_parts, chunk_text, meta)
        if split_ok:
            write_status(status, f"parça bölündü: bölüm {chapter_idx+1}/{total} "
                                  f"({total_parts}→{total_parts + 1} parça)")
            print("Bölünen (artık daha küçük) parça için hemen tekrar deneniyor...")
            trigger_workflow("queue-worker.yml", branch=current_branch())
        else:
            print("Self-trigger yapılmıyor — bir sonraki tetiklemede aynı "
                  "parça tekrar denenecek.")
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
            # update_from_translation artık KAYNAK (İngilizce) metni
            # bekliyor (bkz. memory.py'deki açıklama) — originals henüz
            # silinmedi (temizlik aşağıda), o yüzden burada güvenle
            # yeniden okunabilir.
            full_source = _reconstruct_source(originals_dir, chapter_idx, total_parts)
            memory = mem.update_from_translation(memory, full_source,
                                                  clients, key_index)
            memory = mem.add_summary(memory, title, full_translation,
                                      clients, key_index)
        except gc.AllKeysLockedError:
            print("Uyarı: hafıza güncellenemedi (tüm keyler kilitli), "
                  "mevcut hafıza korunuyor.")
        # Seri her zaman kazanır: update_from_translation modelin kendi
        # LLM çağrısıyla hafızayı yeniden yazabiliyor — teorik olarak
        # seriden gelen bir değeri (örn. "Lahan'ın Kardeşi") yanlışlıkla
        # değiştirebilirdi. Bu yüzden bölüm sonunda overlay'i her zaman
        # tekrar (ucuza, LLM çağrısı olmadan) uyguluyoruz.
        memory = series_lib.apply_overlay(memory, series_data)
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

    # Sırada başka parça var mı? Varsa kendimi tetikle, yoksa kitap bitti
    # — review.yml'e açıkça devrediyoruz (workflow_run zincirlemesi yerine
    # açık tetikleme kullanıyoruz, geçmişte çift-tetiklenme sorunlarına yol
    # açmıştı).
    branch = current_branch()
    if _next_part(originals_dir, translated_dir) is not None:
        print("Sıradaki parça için kendimi tetikliyorum...")
        trigger_workflow("queue-worker.yml", branch=branch)
    else:
        status["status"] = "completed"
        status["current_chapter"] = ""
        write_status(status, "status: completed")
        print("Kitabın çevirisi tamamlandı! Review'e devrediliyor...")
        trigger_workflow("review.yml", branch=branch)


if __name__ == "__main__":
    main()
