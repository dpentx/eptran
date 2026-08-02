"""
Review aşaması İngilizce kalıntı düzelticisi.

Önceki tasarımdaki hata: review'da paragraf başına NER LLM çağrısı
yapılıyordu, bu hem yavaş hem de gereksizdi. Bu modül NER çağrısı
YAPMAZ — sadece:
  1. Sözlük destekli english_detector.find() ile gerçek İngilizce
     kelimeleri tespit eder (Türkçe'yi İngilizce sanma sorunu artık
     sözlük katmanıyla çözüldü)
  2. Hafızadaki (memory.json) characters + terms anahtarlarını
     whitelist olarak kullanır (translate aşamasında zaten NER
     yapılmıştı, sonucu hafızada duruyor)
  3. Whitelist dışında kalan gerçek sorunlu kelimeler varsa
     paragrafı LLM'e gönderip düzeltir

Yani review'da hiçbir ekstra NER çağrısı yok — sadece var olan
hafızayı whitelist olarak kullanıp gerekirse fix_paragraph çağırır.

NOT (Temmuz 2026): Büyük bölümler (binlerce kelime, onlarca paragraf)
tek bir job run'ı içinde bitmeyebiliyordu — job 60 dakikada timeout'a
uğrayınca hiçbir paragraf-bazlı ilerleme kaydedilmediği için bir sonraki
run AYNI dosyayı BAŞTAN işliyordu, sonsuza kadar (gerçek bir kitapta 4
gün, ~16 run boyunca aynı dosyada takılı kaldı). Artık fix_text() hem
paragraf bazlı checkpoint tutuyor (job kesilirse kaldığı paragraftan
devam eder) hem de bir zaman bütçesi (deadline) alıp bunu aşarsa
düzgünce erken çıkıyor.
"""
import json
import os
import time

from . import groq_client as gc
from . import boilerplate
from . import unicode_cleaner
from . import english_detector
from . import dictionary
from . import git_utils

_FIX_SYSTEM = (
    "Sen profesyonel bir Türkçe editör ve çevirmensin. "
    "Sana verilen paragrafta bazı kelimeler İngilizce kalmış veya bozuk çevrilmiş. "
    "Korunması gereken özel isimler ayrıca belirtilecek — onlara dokunma. "
    "Paragrafı doğal, akıcı Türkçeye çevir/düzelt. "
    "SADECE düzeltilmiş paragrafı döndür, açıklama ekleme."
)


def _flush_and_commit(paragraph_idx: int) -> None:
    """
    learned_words.json'ı diske yaz VE git'e commit et.
    Sadece flush() yetmez — process timeout'la kesilirse diskte
    duran ama commit edilmemiş değişiklik kaybolur (yeni job
    checkout yapınca eski main'i çeker). Bu yüzden periyodik
    olarak gerçek bir commit atılır.
    """
    dictionary.flush()
    try:
        git_utils.git_push(f"dictionary: learned_words güncellendi (p{paragraph_idx})")
    except Exception as e:
        # git push başarısız olursa akışı durdurma, bir sonraki
        # periyotta tekrar denenecek.
        print(f"    uyarı: dictionary commit başarısız ({e}), devam ediliyor.")


def _build_whitelist(memory: dict) -> set:
    """Hafızadaki karakter ve terim isimlerinden whitelist oluştur (LLM çağrısı yok)."""
    whitelist = set()
    for eng_name, tr_name in memory.get("characters", {}).items():
        whitelist.add(eng_name.lower())
        whitelist.add(tr_name.lower())
        for word in eng_name.split() + tr_name.split():
            if len(word) > 2:
                whitelist.add(word.lower())
    for eng_term, tr_term in memory.get("terms", {}).items():
        whitelist.add(eng_term.lower())
        whitelist.add(tr_term.lower())
        for word in eng_term.split() + tr_term.split():
            if len(word) > 2:
                whitelist.add(word.lower())
    return whitelist


def fix_paragraph(paragraph: str, whitelist: set,
                  bad_words: list, clients: list, key_index: list) -> str:
    """Sorunlu paragrafı LLM'e gönder, düzeltilmiş halini al."""
    protected_str = ", ".join(sorted(whitelist)) if whitelist else "yok"
    user_msg = (
        f"Korunacak isimler ve terimler: {protected_str}\n"
        f"Düzeltilmesi gereken kelimeler: {', '.join(bad_words)}\n\n"
        f"Paragraf:\n{paragraph}"
    )
    result = gc.call(clients, key_index, _FIX_SYSTEM, user_msg)
    time.sleep(1)
    if result is None:
        print("    Uyarı: düzeltme alınamadı (model boş yanıt), paragraf orijinal haliyle korunuyor.")
        return paragraph
    return result


def _load_checkpoint(checkpoint_path: str):
    if not checkpoint_path or not os.path.exists(checkpoint_path):
        return 0, []
    try:
        with open(checkpoint_path, encoding="utf-8") as f:
            ckpt = json.load(f)
        return ckpt.get("done_idx", 0), ckpt.get("result", [])
    except (json.JSONDecodeError, OSError):
        return 0, []


def _save_checkpoint(checkpoint_path: str, done_idx: int, result: list) -> None:
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump({"done_idx": done_idx, "result": result}, f, ensure_ascii=False)


def fix_text(text: str, clients: list, key_index: list, memory: dict,
             checkpoint_path: str = None, deadline: float = None) -> tuple:
    """
    Review aşamasında çevrilmiş metni tara:
    1. Unicode temizle (mixed-script bozuk tokenlar)
    2. Sözlük destekli İngilizce kelime tespiti (heuristic + dictionary)
    3. Hafızadaki whitelist ile karşılaştır (NER çağrısı YOK)
    4. Whitelist dışında sorun varsa paragrafı fix_paragraph ile düzelt

    Döner: (metin, tamamlandı_mı)
    - tamamlandı_mı=True ise `metin` nihai, kullanıma hazır sonuçtur.
    - tamamlandı_mı=False ise (deadline aşıldığı için erken çıkıldı)
      `metin` None'dur — checkpoint_path'e kaydedilen paragraf-bazlı
      ilerlemeden bir sonraki çağrıda otomatik devam edilir (aynı
      checkpoint_path ile tekrar çağırman yeterli).

    Not: dictionary.flush() periyodik olarak (her 5 paragrafta bir) ve
    fonksiyon sonunda çağrılır. Rate limit nedeniyle uzun süren
    çalışmalarda job timeout'a uğrarsa bile o ana kadar öğrenilen
    kelimeler kaybolmaz — periyodik flush bunu garanti eder.
    """
    whitelist = _build_whitelist(memory)
    paragraphs = text.split("\n\n")

    start_idx, result = _load_checkpoint(checkpoint_path)
    if start_idx > 0:
        print(f"    Checkpoint bulundu: {start_idx}/{len(paragraphs)} paragraf "
              f"zaten işlenmiş, kaldığı yerden devam ediliyor.")

    fixed_count = 0

    for idx in range(start_idx, len(paragraphs)):
        para = paragraphs[idx]
        stripped = para.strip()

        if stripped.startswith("[EPUB_IMAGE:") or stripped.startswith("#"):
            result.append(para)
        elif boilerplate.is_boilerplate(stripped):
            print(f"    boilerplate atlandı: {stripped[:60]}...")
        else:
            cleaned = unicode_cleaner.clean(para)
            eng_words = english_detector.find(cleaned)
            if not eng_words:
                result.append(cleaned)
            else:
                truly_bad = [w for w in eng_words if w.lower() not in whitelist]
                if not truly_bad:
                    result.append(cleaned)
                else:
                    print(f"    düzeltiliyor: {truly_bad[:5]}"
                          f"{'...' if len(truly_bad) > 5 else ''}")
                    fixed = fix_paragraph(cleaned, whitelist, truly_bad,
                                          clients, key_index)
                    result.append(fixed)
                    fixed_count += 1

        # Periyodik flush + commit — rate limit beklerken kesinti olsa
        # bile bu ana kadar öğrenilen kelimeler git'e işlenmiş olur.
        if idx % 5 == 0:
            _flush_and_commit(idx)

        if deadline is not None and time.time() > deadline and idx < len(paragraphs) - 1:
            # Zaman bütçesi doldu — dosyayı BAŞTAN değil, TAM BURADAN
            # devam edecek şekilde checkpoint'e kaydedip erken çık.
            # Eskiden checkpoint hiç yoktu; job timeout'a uğradığında
            # bir sonraki run aynı büyük dosyayı sıfırdan deniyor, asla
            # bitiremiyordu (gerçek bir kitapta 4 gün/~16 run böyle
            # takılı kaldı).
            if checkpoint_path:
                _save_checkpoint(checkpoint_path, idx + 1, result)
                import subprocess
                subprocess.run(["git", "add", checkpoint_path])
            print(f"    Zaman bütçesi doldu ({idx+1}/{len(paragraphs)} paragraf "
                  f"işlendi) — checkpoint kaydedildi, bir sonraki run'da "
                  f"kaldığı yerden devam edilecek.")
            return None, False

    if fixed_count:
        print(f"  {fixed_count} paragraf düzeltildi.")

    # Bu dosyanın taraması bitti — kalan öğrenilen kelimeleri diske/git'e yaz
    _flush_and_commit(len(paragraphs))

    if checkpoint_path and os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        import subprocess
        subprocess.run(["git", "rm", "-f", "--ignore-unmatch", checkpoint_path])

    return "\n\n".join(result), True
