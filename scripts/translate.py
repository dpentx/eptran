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

from lib import boilerplate, groq_client as gc, unicode_cleaner, series as series_lib, pitfalls
from lib.git_utils import (
    write_status, trigger_workflow, create_book_branch,
    list_active_book_branches, peek_remote_file, is_stale_running, git_push,
)

STATUS_FILE = "status.json"


# ── Bölüm çıkarma ─────────────────────────────────────────────────────────────

# Bir paragraf içindeki satırların ortalama uzunluğu bu eşiğin
# ÜZERİNDEYSE düzyazı hard-wrap kalıntısı sayılır (kaynağın 70-75
# karakarde sert satır kaydırması, satır sonlarını ANLAMSIZ kılar);
# ALTINDAYSA şiir/dize sayılır (satır sonları KASITLI, korunmalı).
# Gerçek verilerle doğrulandı (pg2147): kırık düzyazı paragrafı ~59
# karakter/satır, "The Raven" epigrafı ~49.5, "Haunted Palace" dizesi
# ~30.5 — 55 eşiği ikisini net ayırıyor.
_HARDWRAP_AVG_LEN_THRESHOLD = 55


def _reflow_hardwrapped(text: str) -> str:
    """
    NOT (Ağustos 2026): Bazı epub'larda (özellikle eski/otomatik
    üretilmiş Gutenberg dönüştürmelerinde) bir alıntı/blok paragraf,
    kaynak düz metnin 70-75 karakterlik sert satır kaydırmasını AYNEN
    koruyan <br/> etiketleriyle işaretleniyor. extract_epub()'daki
    soup.get_text(separator="\\n") bunları TEK satır içi "\\n" olarak
    metne döküyor — ki bu, gerçek bir şiir/dize için doğru davranış
    (convert.py bunları <br/>'a geri çevirip dizeleri korur), ama
    düzyazı için YANLIŞ: model çeviri sırasında bu anlamsız satır
    sonlarını olduğu gibi yansıtabiliyor, convert.py da her birini
    <br/>'a çevirince okuyucuda tek bir cümle sanki birden fazla
    paragrafmış gibi (büyük dikey boşluklarla) görünüyor (gerçek örnek:
    pg2147/003, "Perhaps there is no task more difficult..." paragrafı).

    Burada, çeviriye gitmeden ÖNCE, kaynaktaki her paragrafın satır
    ortalama uzunluğuna bakıp düzyazı-gibi olanları (uzun ortalama) tek
    akan satıra katlıyoruz; şiir-gibi olanları (kısa ortalama) olduğu
    gibi bırakıyoruz. Kusursuz bir sınıflandırıcı değil ama gerçek
    üretim verisiyle doğrulanmış net bir eşiğe dayanıyor.
    """
    paragraphs = text.split("\n\n")
    out = []
    for para in paragraphs:
        lines = [l for l in para.split("\n")]
        non_empty = [l.strip() for l in lines if l.strip()]
        if len(non_empty) >= 2:
            avg_len = sum(len(l) for l in non_empty) / len(non_empty)
            if avg_len > _HARDWRAP_AVG_LEN_THRESHOLD:
                para = " ".join(non_empty)
        out.append(para)
    return "\n\n".join(out)

def extract_epub(epub_path: str) -> tuple:
    """
    NOT (Temmuz 2026): Eskiden bu fonksiyon SADECE metni çıkarıyordu
    (soup.get_text()) — epub içindeki <img> etiketleri sessizce
    kayboluyordu, çünkü [EPUB_IMAGE:...] yer tutucu mekanizması sadece
    extract_pdf()'te vardı. Epub kaynaklı kitaplarda (çoğu light novel
    gibi) illüstrasyonlar bu yüzden hiç çıkarılmıyordu. Artık <img>
    etiketleri metne dönüştürülmeden ÖNCE bulunup BELLEKTE tutuluyor
    (diske YAZILMIYOR — bu fonksiyon main dalındayken, kitap dalı henüz
    oluşturulmadan önce çağrılıyor; diske yazsaydık bir sonraki
    git_push()'un 'git add -A'sı bu resimleri main'e commit'leyebilirdi).
    Görüntüler, main() içinde kitap dalına geçildikten SONRA diske
    yazılıyor. Yerlerine aynı [EPUB_IMAGE:...] yer tutucusu konuyor —
    chunking ve çeviri bunu olduğu gibi bırakıyor, convert.py da geri
    <img>'e çeviriyor (zaten vardı).

    Döner: (chapters, images) — images = {dosya_adı: bytes}
    """
    book = epub.read_epub(epub_path)

    # Kitabın başlık/yazar metadata'sı — seri otomatik tanıma için
    # (bkz. lib/series.py: detect_from_metadata). DC metadata yoksa
    # (bazı ham/eksik epub'larda olabilir) sessizce boş kalır.
    def _dc(name):
        vals = book.get_metadata("DC", name)
        return vals[0][0] if vals else ""
    book_meta = {"title": _dc("title"), "author": _dc("creator")}
    images = {}
    saved_names = {}  # epub-içi href -> atanan dosya adı
    img_counter = [0]

    def _capture_image(href: str):
        if href in saved_names:
            return saved_names[href]
        item = book.get_item_with_href(href)
        if item is None:
            return None
        ext = os.path.splitext(href)[1] or ".jpg"
        img_counter[0] += 1
        name = f"img_{img_counter[0]:03d}{ext}"
        images[name] = item.get_content()
        saved_names[href] = name
        return name

    # NOT (Ağustos 2026): Eskiden burada book.get_items() ile TÜM
    # ITEM_DOCUMENT'lar dolaşılıyordu — ama bu, epub'ın gerçek okuma
    # sırasını (<spine>) DEĞİL, ebooklib'in dahili/manifest sırasını
    # verir; çoğu epub'da bu iki sıra birbirinden tamamen farklıdır
    # (özellikle bölümü ikiye bölen resim ekleri olan kitaplarda, örn.
    # "chapterN.xhtml" + "chapterN_1.xhtml"). Gerçek üretimde
    # (knh-10) bu, "Bölüm 20'den sonra Bölüm 1 gelmesi" ve "(2. Bölüm)
    # önce (1. Bölüm) sonra" gibi ciddi bir bölüm karışıklığına yol
    # açtı — kitabın TAMAMI çevrildi ama İçindekiler'de doğru sırada
    # değildi. Artık book.spine'ı (idref, linear) kullanıp gerçek
    # okuma sırasını izliyoruz; spine'da olmayan (ör. bozuk/eksik
    # referanslı) itemlar için eskisi gibi get_items() sırasına
    # (spine'dan SONRA) düşüyoruz, hiçbir içerik kaybolmasın diye.
    spine_ids = [idref for idref, _ in book.spine]
    ordered_items = []
    seen_ids = set()
    for idref in spine_ids:
        item = book.get_item_with_id(idref)
        if item is not None and item.get_type() == ebooklib.ITEM_DOCUMENT:
            ordered_items.append(item)
            seen_ids.add(id(item))
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT and id(item) not in seen_ids:
            ordered_items.append(item)

    chapters = []
    last_chapter_base = None  # örn. 'chapter2' — son EKLENEN gerçek bölümün taban adı
    for item in ordered_items:
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        # Bazı epub'larda gerçek (ebooklib'in ürettiği) nav.xhtml'e ek
        # olarak, düz metin bir "İçindekiler" kopyası da AYRI bir sayfa
        # olarak bulunuyor (örn. "toc.xhtml") — sadece bölüm başlıklarının
        # alt alta dizildiği, 300+ karaktere kolayca ulaşan ama gerçek
        # anlatı içermeyen bir liste. Bu yüzden hem eski hem yeni mantıkta
        # "gerçek bölüm" sanılıp gereksiz yere çevriliyordu (knh-10'da bu
        # yüzden TÜM bölüm numaraları bir kayıyordu — gerçek kaynak: bu
        # sayfa chapters[] listesinin başında fazladan bir slot açıyordu).
        # Dosya adı "toc"/"contents" içeriyorsa atla.
        base_lower = os.path.basename(item.get_name()).lower()
        if re.search(r"\btoc\b|contents", base_lower):
            continue

        # NOT (Ağustos 2026, İKİNCİ bir gerçek üretim hatası — knh-11):
        # Bazı bölümler ortadaki bir resim eki yüzünden epub'da İKİ ayrı
        # dosyaya bölünüyor (örn. "chapter2.xhtml" + [resim] +
        # "chapter2_1.xhtml" — ikisi de AYNI hikâye bölümünün parçası).
        # convert.py bunu render sırasında zaten fark edip tek sayfa
        # olarak birleştiriyordu, AMA extract_epub() burada hâlâ bunları
        # İKİ AYRI "bölüm" olarak çeviriyordu — 35 bölümlük knh-11'de bu
        # yüzden 8 çift oluştu, çeviri BİTTİ ama convert.py bu 8 "fazladan"
        # çeviriyi hiçbir spine slotuna eşleştiremedi ve epub'a hiç
        # koyamadı ("Uyarı: 8 bölüm eşleştirilemedi" — aslında 8 bölümün
        # TAMAMI sessizce kitaptan düşmüştü). Kökten çözüm: birleştirmeyi
        # convert.py'de değil, BURADA (çeviriye gitmeden önce) yapmak —
        # böylece hem tek bir çeviri birimi olarak (daha tutarlı) çevrilir
        # hem de convert.py'nin zaten bildiği mantıkla birebir örtüşür.
        base_noext = os.path.splitext(os.path.basename(item.get_name()))[0]
        is_continuation = bool(
            last_chapter_base
            and re.match(rf'^{re.escape(last_chapter_base)}_\d+$', base_noext)
        )

        soup = BeautifulSoup(item.get_content(), "html.parser")
        for tag in soup(["script", "style", "nav"]):
            tag.decompose()

        # <img> etiketlerini metin-içi yer tutucuyla değiştir — get_text()
        # çağrılmadan ÖNCE yapılmalı ki placeholder doğru paragraf
        # konumunda kalsın (chunking paragraf sınırlarını koruyor, bu
        # yüzden resim, metinde neredeyse olduğu yerde kalır).
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("xlink:href") or ""
            if not src:
                img.decompose()
                continue
            href = os.path.normpath(
                os.path.join(os.path.dirname(item.get_name()), src)
            ).replace("\\", "/")
            saved_name = _capture_image(href)
            if saved_name:
                img.replace_with(f"\n[EPUB_IMAGE:{saved_name}]\n")
            else:
                img.decompose()

        heading = soup.find(["h1", "h2", "h3"])

        text = soup.get_text(separator="\n").strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = _reflow_hardwrapped(text)
        text = boilerplate.clean(text)
        if len(text) < 300:
            continue

        if is_continuation:
            # Yeni bir chapters[] girdisi AÇMIYORUZ — bir öncekinin
            # gövdesine ekliyoruz. Başlık zaten önceki girdiden geliyor,
            # burada başlık belirleme mantığına hiç girmiyoruz.
            chapters[-1]["text"] = chapters[-1]["text"].rstrip() + "\n\n" + text
            continue

        if heading:
            raw_title = heading.get_text().strip()
        else:
            # Bazı epub'larda bölüm başlıkları <h1-h3> değil, düz bir
            # paragraf olarak biçimlendiriliyor. Eskiden bu durumda
            # item.get_name() (ham epub iç dosya yolu, örn.
            # "Text/chapter1_1.xhtml") kullanılıyordu — bu, kullanıcıya
            # başlık olarak AYNEN böyle çirkin bir haliyle görünüyordu.
            # Onun yerine: metnin ilk satırı "Chapter N" gibi tanıdık bir
            # kalıba uyuyorsa ya da kısa/başlık-gibi görünüyorsa onu
            # başlık olarak kullan (ve gövdeden çıkar, tekrar etmesin);
            # hiçbiri uymuyorsa ham dosya adı yerine nötr, sıralı bir
            # "Bölüm N" kullan.
            first_line = text.split("\n", 1)[0].strip()
            chapter_pattern = re.compile(
                r'^(chapter\s+\w+|prologue|epilogue|interlude|afterword|'
                r'foreword|preface)\b', re.IGNORECASE
            )
            looks_like_title = len(first_line) < 100 and not first_line.endswith(
                (".", "!", "?", "…", ":", ",")
            )
            if chapter_pattern.match(first_line) or looks_like_title:
                raw_title = first_line
                text = text.split("\n", 1)[1].strip() if "\n" in text else text
            else:
                # NOT (Ağustos 2026): Eskiden burada f"Bölüm {len(chapters)+1}"
                # kullanılıyordu — yani listedeki HAM SIRA numarası. Bu,
                # kaynakta gerçek başlığı olmayan (numarasız kısa ara
                # sahne/interlude) bölümler için YANILTICI: hikâyenin
                # kendi numaralandırmasıyla hiç alakası yok. Gerçek
                # üretimde (knh-11) "Bölüm 15: Şiddet" hemen ardından
                # "Bölüm 23" geliyordu, sonra "Bölüm 16" ile devam
                # ediyordu — okuyucuya sanki 16-22 arası bölümler
                # silinmiş/kayıp gibi görünüyordu, oysa hiçbir şey eksik
                # değildi, sadece bu ara sahnenin numarası anlamsızdı.
                # Artık numaralı bir bölümmüş GİBİ görünen hiçbir şey
                # üretmiyoruz — nötr bir sahne-arası işareti kullanıyoruz.
                raw_title = "* * *"

        # Başlığı ayıkla — "The Project Gutenberg eBook of X" → "X"
        title = re.sub(
            r'^the\s+project\s+gutenberg\s+e[\-\s]?book\s+of\s+',
            '', raw_title, flags=re.IGNORECASE
        ).strip() or raw_title
        chapters.append({"name": item.get_name(), "title": title, "text": text})
        last_chapter_base = base_noext
    return chapters, images, book_meta


def extract_pdf(pdf_path: str, book_slug: str) -> tuple:
    """
    Döner: (chapters, images) — images = {dosya_adı: bytes}. Aynı
    extract_epub() gibi, main dalındayken diske YAZMIYORUZ (bkz. o
    fonksiyonun docstring'i) — main() kitap dalına geçtikten sonra yazar.
    """
    import pdfplumber, fitz

    patterns = [
        re.compile(r'^(chapter\s+\w+[\s:\-–—]?.*)$', re.IGNORECASE),
        re.compile(r'^(prologue|epilogue|interlude|afterword|foreword|preface)$', re.IGNORECASE),
        re.compile(r'^(\d+\.\s+.{3,60})$'),
        re.compile(r'^([IVX]+\.\s+.{3,60})$'),
    ]
    images = {}
    all_lines, doc = [], fitz.open(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        for pi, page in enumerate(pdf.pages):
            if page.extract_text():
                all_lines.extend(page.extract_text().split("\n"))
            for ii, img in enumerate(doc[pi].get_images(full=True)):
                base = doc.extract_image(img[0])
                name = f"page_{pi+1}_img_{ii+1}.{base['ext']}"
                images[name] = base["image"]
                all_lines.append(f"[EPUB_IMAGE:{name}]")
            all_lines.append("")

    starts = []
    for i, line in enumerate(all_lines):
        s = line.strip()
        if s and any(p.match(s) for p in patterns):
            starts.append((i, s))

    if not starts:
        text = boilerplate.clean(_reflow_hardwrapped(
            re.sub(r"\n{3,}", "\n\n", "\n".join(all_lines).strip())))
        chapters = [{"name": "chapter_001",
                 "title": os.path.splitext(os.path.basename(pdf_path))[0],
                 "text": text}] if len(text) >= 300 else []
        return chapters, images, {}

    starts.append((len(all_lines), None))
    chapters = []
    for idx in range(len(starts) - 1):
        sl, title = starts[idx]
        body = boilerplate.clean(_reflow_hardwrapped(re.sub(r"\n{3,}", "\n\n",
                                        "\n".join(all_lines[sl+1:starts[idx+1][0]]).strip())))
        if len(body) >= 300:
            chapters.append({"name": f"chapter_{idx+1:03d}", "title": title, "text": body})
    # PDF'lerde güvenilir DC metadata genelde yok — seri otomatik
    # tanıma için boş dönüyoruz, dosya adı üzerinden .series eşlik
    # dosyası ya da elle status.json düzenlemesi hâlâ çalışır.
    return chapters, images, {}


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
        f"\n"
        # NOT (Ağustos 2026, gerçek üretim geri bildirimi — knh-11, iki
        # ayrı bulgu turu): Model dilbilgisi olarak doğru ama üslup
        # olarak "İngilizce'yi birebir Türkçe kelimelerle yazmış" gibi
        # duran çeviriler üretiyordu (1. tur — kullanıcının elle bulduğu
        # örnekler: "var" tekrarı, "kıyafet"/"kostüm" tutarsızlığı, "bu
        # tarla yasak" gibi eksiltili çeviri). Gemini'nin bağımsız
        # denetimi (2. tur — bkz. qa_audit.py) AYNI kök sorunun çok daha
        # geniş ve TEHLİKELİ bir versiyonunu ortaya çıkardı: 84 anlam
        # kayması arasında EN ciddi alt küme, İngilizce'deki OLUMSUZLAMA
        # kalıplarının (çift olumsuzlama, "never averse to" gibi zıt-
        # anlamlı ifadeler) çeviride YANLIŞLIKLA TERS ANLAMA dönüşmesiydi
        # — örn. "willing" (istekli) → "istemeden de olsa"; "a young man"
        # → "yaşlı bir adam"; "no one would have dared" → olumsuzlama
        # düşürülüp "kimse ... ederdi". Bunlar YÜZEYDE gayet akıcı/doğru
        # görünen Türkçe cümleler — review.py'nin İngilizce-kalıntı
        # denetimi bunları HİÇ YAKALAYAMAZ. Aşağıdaki kurallar hem 1.
        # hem 2. tur bulgularını kapsayacak şekilde genişletildi.
        f"ÇEVİRİ TARZI — aşağıdakilere özellikle dikkat et:\n"
        f"1. Kelime kelime çevirme; ANLAMI al, Türkçenin kendi doğal cümle "
        f"kalıbıyla yeniden kur. İngilizce cümle yapısını (kelime sırasını, "
        f"kısalığını/eksiltili yapısını) birebir taşımaya çalışma. Örnek: "
        f"\"this field is forbidden\" → kelime kelime \"bu tarla yasak\" DEĞİL, "
        f"\"bu tarlaya ekim yapmak yasak\" gibi anlamı tamamlayan doğal bir "
        f"Türkçe ifade kullan.\n"
        f"2. Yan yana ya da yakın cümlelerde AYNI kelimeyi (özellikle \"var\", "
        f"\"oldu\", \"gibi\" gibi sık kullanılan kelimeleri) tekrar etmekten "
        f"kaçın — cümle yapısını çeşitlendirerek aynı anlamı ver, okurken "
        f"tekrar yüzünden anlam bulanıklaşmasın.\n"
        f"3. Aynı bölüm/sahne içinde aynı nesne/kavramı HER ZAMAN aynı "
        f"kelimeyle adlandır. Örnek: bir karakterin üzerindeki aynı giysiyi "
        f"bir cümlede \"kıyafet\" diğerinde \"kostüm\" diye farklı "
        f"kelimelerle çevirme — hangisini seçersen o bölüm boyunca ona sadık "
        f"kal.\n"
        f"4. OLUMSUZLAMA/ZIT-ANLAM ÇOK TEHLİKELİ: İngilizce'de çift "
        f"olumsuzlama ya da \"never averse to\", \"willing\", \"no one would "
        f"have dared\" gibi olumsuzlama/zıt-anlam içeren kalıpları çevirirken, "
        f"ANLAMIN YANLIŞLIKLA TERSİNE dönmesi çok kolay ve fark edilmesi çok "
        f"zor bir hata (çünkü ortaya çıkan Türkçe cümle gayet akıcı görünür). "
        f"Her böyle bir cümlede, çevirmeden ÖNCE kaynağın GERÇEKTE olumlu mu "
        f"olumsuz mu dediğini kendine sor, sonra o anlamı Türkçeye AÇIK ve "
        f"NET şekilde aktar.\n"
        f"5. Kaynakta bir karakterin adı AÇIKÇA belirtilmişse, bu adı "
        f"çeviride düşürüp belirsiz bir zamire (\"o\", \"onu\") çevirme — "
        f"hangi karaktere atıf yapıldığı belirsizleşebilir ya da yanlış "
        f"karaktere atfedilebilir.\n"
        f"6. Bir İngilizce kelime, Türkçede FARKLI bir anlama gelen "
        f"benzer-görünümlü bir kelimeye (\"yanlış dost\") benziyorsa, bu "
        f"benzerliğe kanıp yanlış çevirme — emin olmadığın bir kelimenin "
        f"GERÇEK anlamını düşün.\n"
        f"7. Diyalog sırasını ve içeriğini kaynağa sadık tut — kaynakta "
        f"olmayan hiçbir cümle/diyalog ekleme, kaynaktaki sırayı değiştirme.\n"
        f"8. Doğallık okunabilirlikten önemli değil: bir çeviri dilbilgisi "
        f"olarak doğru ama \"çevrilmiş gibi\" okunuyorsa, o cümleyi bir "
        f"Türk yazarın nasıl kurardığını düşünüp yeniden yaz.\n"
    )
    pitfalls_ctx = pitfalls.build_context()
    if pitfalls_ctx:
        system_msg += f"\n{pitfalls_ctx}\n"
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


def refine_translation(source_text: str, translation: str, clients: list,
                       key_index: list, chapter_title: str,
                       memory_ctx: str = "", protected_str: str = "") -> str:
    """
    İlk çeviriyi kaynakla KARŞILAŞTIRIP gözden geçiren, AYRI ve ODAKLI
    bir ikinci geçiş. translate_chapter()'ın hemen ardından çağrılır.

    NEDEN AYRI BİR GEÇİŞ (tek seferde değil): Bir model aynı anda hem
    akıcı/yaratıcı metin ÜRETMEK hem de o metni SIKI şekilde DENETLEMEK
    arasında geçiş yapmakta zorlanır — bunlar farklı bilişsel modlar.
    Gerçek üretim kanıtı (knh-11'in Gemini denetimi, bkz. qa_audit.py)
    bunu doğruluyor: review.py'nin İngilizce-kalıntı denetimi hiçbirini
    YAKALAYAMADIĞI 84 anlam kayması bulundu — çünkü hepsi YÜZEYDE akıcı,
    "doğru görünen" Türkçe cümlelerdi (olumsuzlamanın tersine dönmesi,
    atlanmış cümleler, karakter adının belirsiz zamire dönüşmesi, hatta
    bazı yerlerde kaynakta OLMAYAN uydurma diyalog satırları). Bunların
    HİÇBİRİ kelime bazlı bir kontrolle yakalanamaz — sadece kaynakla
    KARŞILAŞTIRMALI bir okuma yakalayabilir. Bu fonksiyon tam olarak
    bunu yapıyor: modele üretmek değil, SADECE karşılaştırıp gerekirse
    düzeltmek görevi veriyor.

    reasoning_effort="low" kullanılıyor (varsayılan "none" değil) —
    bu, gc.call()'ın kendi belgelediği "nadiren daha derin akıl
    yürütme gerektiren çağrılar" durumu; karşılaştırma/analiz görevi
    ham üretimden farklı, gerçek adım-adım muhakeme faydalı olabilir.

    GÜVENLİK (bu geçiş ASLA çeviriyi kötüleştirmemeli):
    - API başarısız olursa (None, ya da tüm key'ler kilitliyse) ORİJİNAL
      çeviri hiç dokunulmadan döner — bu adım tamamen OPSİYONEL bir
      iyileştirme, ana çeviriyi ASLA riske atmaz.
    - Gözden geçirilmiş metin, orijinalin %50'sinden kısa ya da %160'ından
      uzunsa (modelin bir şeyi bozduğunun/kısalttığının/tekrarladığının
      işareti), ORİJİNAL çeviri korunur, şüpheli sonuç ASLA kullanılmaz.
    """
    system_msg = (
        f"Sen titiz bir çeviri editörüsün. \"{chapter_title}\" bölümünün "
        f"İngilizce kaynağı ile ilk Türkçe çevirisi verilecek. Görevin "
        f"ÜRETMEK değil, KARŞILAŞTIRIP DÜZELTMEK.\n\n"
        f"Özellikle şunları dikkatlice kontrol et:\n"
        f"1. OLUMSUZLAMA/TERS ANLAM: İngilizce'de çift olumsuzlama ya da "
        f"\"never averse to\", \"willing\", \"no one would have dared\" gibi "
        f"olumsuzlama/zıt-anlam içeren kalıplar, çeviride YANLIŞLIKLA "
        f"TERSİNE dönmüş olabilir (örn. \"istekli\" iken \"istemeden\" "
        f"çıkmış olabilir) — bu tip bir ters anlam var mı dikkatlice "
        f"karşılaştır.\n"
        f"2. ATLANMIŞ/DEĞİŞTİRİLMİŞ İÇERİK: kaynaktaki bir cümle "
        f"çeviride hiç yok mu, ya da anlamı tamamen değişmiş mi?\n"
        f"3. KARAKTER/ZAMİR KARIŞIKLIĞI: kaynakta açıkça adı geçen bir "
        f"karakter, çeviride belirsiz bir zamire dönüşüp yanlış kişiye "
        f"atıf yapar hale gelmiş mi?\n"
        f"4. UYDURMA/SIRASI KARIŞMIŞ DİYALOG: çeviride kaynakta olmayan "
        f"bir cümle eklenmiş mi, diyalog sırası kaynakla uyuşmuyor mu?\n\n"
        f"Gerçek bir sorun BULAMAZSAN çeviriyi OLDUĞU GİBİ, HİÇ "
        f"DEĞİŞTİRMEDEN geri ver — küçük üslup tercihlerine DOKUNMA, "
        f"sadece yukarıdaki türden SOMUT hataları düzelt. Yanıt olarak "
        f"SADECE (düzeltilmiş ya da değiştirilmemiş) TAM çeviriyi yaz, "
        f"hiçbir açıklama/yorum ekleme."
    )
    pitfalls_ctx = pitfalls.build_context()
    if pitfalls_ctx:
        system_msg += f"\n\n{pitfalls_ctx}"
    if protected_str:
        system_msg += f"\n{protected_str}"
    if memory_ctx:
        system_msg += f"\n\n{memory_ctx}"

    user_msg = f"KAYNAK:\n{source_text}\n\nİLK ÇEVİRİ:\n{translation}"

    try:
        refined = gc.call(clients, key_index, system_msg, user_msg,
                          temperature=0.1, reasoning_effort="low")
    except gc.AllKeysLockedError:
        # Bu adım opsiyonel bir İYİLEŞTİRME — ana çeviri zaten başarıyla
        # tamamlanmıştı, keyler kilitliyse burada run'ı durdurmuyoruz,
        # sadece gözden geçirmeden vazgeçip orijinali koruyoruz.
        print("    Gözden geçirme atlandı (tüm keyler kilitli), orijinal çeviri korunuyor.")
        return translation

    if not refined:
        print("    Gözden geçirmeden yanıt alınamadı, orijinal çeviri korunuyor.")
        return translation

    orig_len, new_len = len(translation), len(refined)
    if orig_len > 200 and not (0.5 * orig_len <= new_len <= 1.6 * orig_len):
        print(f"    Uyarı: gözden geçirme çıktısı beklenmedik uzunlukta "
              f"({orig_len}->{new_len} karakter), orijinal çeviri korunuyor.")
        return translation

    if refined.strip() != translation.strip():
        print("    Gözden geçirme bir düzeltme uyguladı.")

    return refined


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

    # Seri geneli hafıza (bkz. lib/series.py): admin, epub ile AYNI
    # isimde bir .series dosyası bırakırsa (örn. input/knh-11.epub +
    # input/knh-11.series, içinde tek satır "kusuriya" yazan), bu kitap
    # o seriye bağlanır — queue_worker.py, çeviriye başlamadan önce
    # series/kusuriya.json'daki karakter/terim/notları hafızaya
    # otomatik işler. Dosya yoksa hiçbir şey değişmez (eski davranış).
    series_slug = None
    series_companion = f"input/{os.path.splitext(input_file)[0]}.series"
    if os.path.exists(series_companion):
        with open(series_companion, encoding="utf-8") as f:
            series_slug = f.read().strip()
        os.remove(series_companion)
        subprocess.run(["git", "rm", "-f", series_companion], check=False)
        print(f"Seri tespit edildi: {series_slug}")

    print(f"Dosya: {input_file}")
    if file_ext == ".epub":
        chapters, images, book_meta = extract_epub(file_path)
    else:
        chapters, images = extract_pdf(file_path, book_slug)
        book_meta = {}

    # Eşlik dosyası verilmediyse, epub'ın kendi başlık/yazar
    # metadata'sından (+ dosya adından) otomatik seri tanımayı dene.
    # Tek ve NET bir eşleşme yoksa dokunmuyoruz (bkz. detect_from_metadata
    # docstring'i) — knh-11'de series/kusuriya.json'ın hiç uygulanmamış
    # olması, admin'in .series eşlik dosyası oluşturmayı unutmasından
    # kaynaklanmıştı (GitHub web'den tek dosya sürüklerken bu pratik
    # değil); bu otomatik tanıma ile normal şartlarda hiç gerekmiyor.
    if not series_slug:
        guess = series_lib.detect_from_metadata(
            book_meta.get("title", ""), book_meta.get("author", ""), input_file
        )
        if guess:
            series_slug = guess
            print(f"Seri otomatik tespit edildi (epub metadata): {series_slug}")

    total = len(chapters)
    print(f"Toplam bölüm: {total}, {len(images)} görsel bulundu.")
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

    # Görselleri ANCAK ŞİMDİ (kitap dalındayken) diske yaz — extract_epub/
    # extract_pdf bunları bilerek diske yazmadı (bkz. o fonksiyonların
    # docstring'i): main dalındayken yazılsaydı, az önceki git_push()'un
    # 'git add -A'sı bunları main'e commit'leyebilirdi.
    if images:
        images_dir = f"{output_dir}/images"
        os.makedirs(images_dir, exist_ok=True)
        for name, data in images.items():
            with open(os.path.join(images_dir, name), "wb") as f:
                f.write(data)

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
    if series_slug:
        status["series"] = series_slug
    subprocess.run(["git", "add", originals_dir])

    # Bu dalın ilk push'u — git_utils.git_push() remote'ta bu dal henüz
    # yokken otomatik '-u origin <branch>' ile push eder.
    write_status(status, f"kuyruğa alındı: {total} bölüm, {total_parts_all} parça")
    print(f"Queue-worker tetikleniyor (dal: {branch})...")
    trigger_workflow("queue-worker.yml", branch=branch)


if __name__ == "__main__":
    main()
