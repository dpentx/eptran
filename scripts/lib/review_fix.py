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
    """
    Hafızadaki karakter ve terim isimlerinden whitelist oluştur (LLM
    çağrısı yok).

    NOT (Ağustos 2026): `characters` (Maomao, Jinshi gibi özel isimler)
    ile `terms` (Red Plum Village -> Kızıl Erik Köyü gibi Türkçe
    karşılığı OLAN yer/unvan/terim çiftleri) birbirinden farklı amaçlar
    taşıyor — characters İngilizce KALMALI, terms ise ÇEVRİLMİŞ olmalı.
    Eskiden ikisi de aynı şekilde işleniyordu: terms'in İNGİLİZCE
    tarafındaki her kelime de (örn. "Village") tek tek whitelist'e
    ekleniyordu. Sonuç: "Red Plum Village" bir paragrafta HİÇ
    çevrilmeden kalsa bile, "Village" kelimesi whitelist'te "tanıdık"
    sayıldığı için review bunu hiç fark etmiyordu — gerçek üretimde
    (knh-10/010) tam olarak bu oldu, aynı kitapta üç farklı hal bir
    arada kaldı: çevrilmemiş "Red Plum Village", tutarsız "Kırmızı Erik
    Köyü" ve resmi "Kızıl Erik Köyü". Artık terms'in İNGİLİZCE
    tarafından kelime çıkarmıyoruz — böylece çevrilmemiş bir terim
    gerçekten "sorunlu kelime" olarak tespit edilip fix_paragraph'a
    gidiyor (ki fix_paragraph da artık aşağıda doğru karşılığı
    biliyor, bkz. _relevant_term_map).
    """
    whitelist = set()
    for eng_name, tr_name in memory.get("characters", {}).items():
        whitelist.add(eng_name.lower())
        whitelist.add(tr_name.lower())
        for word in eng_name.split() + tr_name.split():
            if len(word) > 2:
                whitelist.add(word.lower())
    for eng_term, tr_term in memory.get("terms", {}).items():
        # Türkçe karşılığın kelimelerini whitelist'e ekliyoruz (yanlışlıkla
        # "İngilizce" sanılmasınlar diye) — ama eng_term'ün kelimelerini
        # EKLEMİYORUZ, çünkü bunlar tam da review'ın YAKALAMASI gereken,
        # henüz çevrilmemiş kalıntılar olabilir.
        whitelist.add(tr_term.lower())
        for word in tr_term.split():
            if len(word) > 2:
                whitelist.add(word.lower())
    return whitelist


def _relevant_term_map(paragraph: str, memory: dict) -> dict:
    """
    Paragrafta (İngilizce hâliyle) geçen terim/karakter isimlerinin
    daha önce belirlenmiş RESMİ Türkçe karşılığını çıkarır. fix_paragraph
    bunu modele vererek "Village"i kendi seçtiği bir kelimeyle (örn.
    "Kırmızı Erik Köyü") değil, kitap boyunca zaten kullanılan resmi
    karşılıkla (örn. "Kızıl Erik Köyü") değiştirmesini sağlar — aksi
    halde her fix_paragraph çağrısı aynı terimi farklı çevirebiliyordu.
    """
    low = paragraph.lower()
    out = {}
    for eng_term, tr_term in memory.get("terms", {}).items():
        if eng_term.lower() in low:
            out[eng_term] = tr_term
    for eng_name, tr_name in memory.get("characters", {}).items():
        if eng_name.lower() in low:
            out[eng_name] = tr_name
    return out


def _term_consistency_issues(paragraph: str, memory: dict) -> dict:
    """
    ZATEN Türkçeye çevrilmiş ama resmi terimden FARKLI bir varyantla
    yazılmış yerleri yakalar (örn. paragrafta "Kırmızı Erik Köyü"
    geçiyor, oysa hafızadaki resmi karşılık "Kızıl Erik Köyü" —
    ikisi de İngilizce değil, o yüzden english_detector/whitelist
    mekanizması bunu HİÇ göremiyordu; gerçek üretimde knh-10/010'da
    tam olarak bu oldu).

    Yöntem: 3+ kelimelik her terimin son 2 kelimesini ("çapa" —
    genelde baş isim, örn. "Erik Köyü") ara. Çapa paragrafta geçiyor
    ama TERİMİN TAMAMI geçmiyorsa, muhtemelen ilk kelime(ler) farklı
    yazılmış demektir → tutarsızlık şüphesi.

    2 kelimelik terimler (örn. "Çiftlik Köyü") BİLEREK dışarıda
    bırakıldı: son kelimeyi tek başına çapa yapmak ("Köyü" gibi) çok
    jenerik olur ve alakasız yer adlarını (örn. "Kızıl Erik Köyü")
    yanlış pozitif olarak tutsak eder.
    """
    low = paragraph.lower()
    issues = {}
    for eng_term, tr_term in memory.get("terms", {}).items():
        words = tr_term.split()
        if len(words) < 3:
            continue
        anchor = " ".join(words[-2:]).lower()
        if anchor in low and tr_term.lower() not in low:
            issues[tr_term] = eng_term
    return issues


def fix_paragraph(paragraph: str, whitelist: set,
                  bad_words: list, clients: list, key_index: list,
                  term_map: dict = None, consistency_issues: dict = None) -> str:
    """Sorunlu paragrafı LLM'e gönder, düzeltilmiş halini al."""
    protected_str = ", ".join(sorted(whitelist)) if whitelist else "yok"
    user_msg = f"Korunacak isimler ve terimler: {protected_str}\n"
    if bad_words:
        user_msg += f"Düzeltilmesi gereken (İngilizce kalmış) kelimeler: {', '.join(bad_words)}\n"
    if term_map:
        # Bu kitapta bu terimler için ZATEN belirlenmiş resmi karşılıklar
        # var — modelin kendi ad-hoc çevirisini uydurup tutarsızlık
        # yaratmasını (örn. "Kırmızı Erik Köyü" vs resmi "Kızıl Erik
        # Köyü") önlemek için bunları açıkça veriyoruz.
        mapping_str = "; ".join(f'"{k}" = "{v}"' for k, v in term_map.items())
        user_msg += (
            f"Bu kitapta bu terimler için ZATEN belirlenmiş resmi "
            f"karşılıklar var, başka bir çeviri UYDURMA, AYNEN kullan: "
            f"{mapping_str}\n"
        )
    if consistency_issues:
        # Paragraf zaten tamamen Türkçe ama muhtemelen bir terimin
        # FARKLI bir varyantı kullanılmış (bkz. _term_consistency_issues
        # docstring'i). LLM'e "hangi kelimeyi ara" değil "hangi ifadenin
        # resmi karşılığı bu" diye söylüyoruz — kendisi bulup değiştirsin.
        cons_str = "; ".join(f'"{tr}" (kaynak: "{eng}")'
                              for tr, eng in consistency_issues.items())
        user_msg += (
            f"UYARI: Bu paragrafta, aşağıdaki terimlerin RESMİ karşılığından "
            f"FARKLI bir varyantı (örn. farklı bir sıfat/kelimeyle) "
            f"kullanılmış olabilir. Eğer öyleyse, o ifadeyi resmi karşılıkla "
            f"DEĞİŞTİR (anlamı aynı ama farklı yazılmış bir yer/terim adı "
            f"arıyorsun): {cons_str}\n"
        )
    user_msg += f"\nParagraf:\n{paragraph}"
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
    # terms'in İngilizce tarafına ait kelimeler — bunlar mark_known ile
    # KALICI olarak "İngilizce değil" diye işaretlenmemeli, çünkü bunlar
    # çevrilmesi GEREKEN kelimeler (örn. "Village"); bir defalık gözden
    # kaçma başka bir yerdeki gerçek çeviri ihtiyacını da köreltmemeli.
    term_eng_words = set()
    for eng_term in memory.get("terms", {}).keys():
        for word in eng_term.split():
            if len(word) > 2:
                term_eng_words.add(word.lower())
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
            truly_bad = [w for w in eng_words if w.lower() not in whitelist] if eng_words else []
            # Paragrafta İngilizce kalıntı olmasa BİLE, zaten Türkçeye
            # çevrilmiş bir terimin farklı bir varyantı kullanılmış
            # olabilir (bkz. _term_consistency_issues) — bunu da ayrıca
            # kontrol ediyoruz, çünkü english_detector bunu hiç göremez.
            consistency_issues = _term_consistency_issues(cleaned, memory)

            if not truly_bad and not consistency_issues:
                result.append(cleaned)
            else:
                if truly_bad:
                    print(f"    düzeltiliyor (İngilizce kalıntı): {truly_bad[:5]}"
                          f"{'...' if len(truly_bad) > 5 else ''}")
                if consistency_issues:
                    print(f"    düzeltiliyor (tutarsız terim varyantı): "
                          f"{list(consistency_issues.keys())[:3]}")
                term_map = _relevant_term_map(cleaned, memory)
                fixed = fix_paragraph(cleaned, whitelist, truly_bad,
                                      clients, key_index, term_map,
                                      consistency_issues)
                result.append(fixed)
                fixed_count += 1

                # KRİTİK: LLM'e "düzelt" diye gönderdiğimiz kelimelerden
                # düzeltilmiş metinde HÂLÂ duran varsa (örn. "Jupiter",
                # "massa" gibi özel isim/lehçe kelimesi — model bilerek
                # dokunmamış demektir), bunu mini sözlüğe "İngilizce
                # DEĞİL" diye işaretle. dictionary.py'de bunun için
                # mark_known() zaten vardı ama hiçbir yerden
                # çağrılmıyordu — bu yüzden aynı isim, bir hikâyede
                # onlarca kez geçtiğinde HER paragrafta yeniden
                # "sorunlu" sanılıp LLM'e yollanıyor, birkaç dakikada
                # 4 Groq key'in de rate limitini tüketip run'ı
                # kilitliyordu (bkz. pg2147/007 — Jupiter/massa/
                # Charleston tekrar tekrar "düzeltiliyor"). mark_known
                # zaten mini sözlüğe yazıyor, _flush_and_commit ile de
                # (aşağıda periyodik olarak) diske/git'e işleniyor —
                # yani hem bu dosyanın kalanında hem sonraki
                # dosyalarda/kitaplarda bir daha flag'lenmeyecek.
                fixed_lower = fixed.lower()
                for w in truly_bad:
                    if w.lower() in fixed_lower and w.lower() not in term_eng_words:
                        dictionary.mark_known(w, is_english=False)

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
