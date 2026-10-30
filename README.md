# eptran

İngilizce epub/pdf dosyalarını Türkçeye çeviren, çok modelli (Groq + Gemini)
bir GitHub Actions + Vercel aracı.

## Nasıl Çalışır?

1. Kitabı web arayüzünden yüklersin.
2. Sunucu, `main`'e hiç dokunmadan `main`'in ucundan `queue/<kitap-adı>`
   adında yeni bir dal açar ve dosyayı oraya commit'ler.
3. Bu dal, kitaba özel bir dal olan `book/<kitap-adı>`'na dönüşür; tüm
   çeviri süreci SADECE bu dalda ilerler, `main` süreç boyunca hiç
   etkilenmez.
4. Groq (qwen3.8-27b) her bölümü çevirir, ardından ikinci bir geçişle
   gözden geçirir (İngilizce kalıntı/tutarsız terim kontrolü).
5. Kitap tamamlanınca Gemini tüm kitabı tarayıp bir kalite kontrol
   raporu (`qa_report.md`) çıkarır; Groq bu rapordaki maddeleri otomatik
   düzeltmeye çalışır.
6. Bölümler epub olarak ciltlenir ve `book/<kitap-adı>` dalından `main`'e
   **tek bir pull request** açılır — sen onaylayıp merge edene kadar
   `main` değişmez.
7. Arayüzden ilerlemeyi takip edebilir, tamamlanınca indirebilirsin.

## Mimari Notlar

- **`main` hiçbir zaman otomasyon tarafından doğrudan değiştirilmez.**
  İstersen `main` için branch protection/ruleset kurabilirsin (PR
  zorunluluğu, zorunlu status check vb.) — otomasyon akışı buna göre
  tasarlandı, hiçbir adımı bundan etkilenmez.
- Yükleme, tarayıcıya kalıcı bir GitHub kimlik bilgisi vermez. Sunucu
  (Vercel fonksiyonu) kitap başına, sadece bu repoya ve sadece
  Contents+Actions iznine sahip, ~1 saat sonra kendiliğinden geçersiz
  olan bir GitHub App kurulum token'ı üretir; dosyanın kendisi
  tarayıcıdan doğrudan GitHub'a bu token'la yüklenir (Vercel'in
  fonksiyon başına istek boyutu sınırına takılmamak için).
- Aynı anda yalnızca bir kitap çevrilir, ama kitaplar **sıraya
  eklenebilir**: çevrilen bir kitap (`book/*`) ya da önde bekleyen bir kitap
  varsa yeni yükleme reddedilmez; dosya `queue/<kitap-adı>` dalında bekler
  (arayüzde "sıra" kartında görünür, düğme "Sıraya Ekle" olur, en fazla 10
  kitap). Öndeki kitabın PR'ı merge edilip `book/*` dalı silinince
  `delete-merged-book-branch.yml` sıradaki en eski kitabı otomatik başlatır
  (`scripts/start_next_queue.py`); `translate.yml`'in 6 saatlik cron'u da
  kaçan tetiklemeleri aynı script'le telafi eder.
- `main`'e giden PR, `pr_check.py` (İngilizce kalıntı taraması + Gemini
  raporu özeti) tarafından kontrol edilir; bunu zorunlu bir status
  check olarak ayarlamak istersen workflow adı **"Kitap Bütünlük
  Kontrolü"**.

## Dosya Yapısı

```
eptran/
├── index.html                  # Web arayüzü (yükleme + ilerleme takibi)
├── api/
│   ├── upload.js                 # Yükleme: queue/<kitap> dalı açar, geçici
│   │                              # App token üretir; sistem boşsa workflow'u
│   │                              # tetikler, doluysa kitabı sıraya alır
│   └── status.js                 # Aktif kitabın (book/*) durumu + sıra listesi
├── scripts/
│   ├── translate.py               # Ana çeviri döngüsü (bölüm bölüm)
│   ├── queue_worker.py            # Bir sonraki parçayı işleyip kendini tetikler
│   ├── start_next_queue.py        # Sıradaki (queue/*) kitabı başlatır
│   ├── review.py                  # İkinci geçiş: İngilizce kalıntı/tutarlılık
│   ├── qa_audit.py                # Gemini ile tüm kitabı tarayıp qa_report.md üretir
│   ├── apply_qa_fixes.py          # qa_report.md'deki maddeleri Groq'la düzeltir
│   ├── series_suggest.py          # Karakter/terim sözlüğü için otomatik öneri
│   ├── pr_check.py                # main'e giden PR'ı kontrol eder ("Kitap
│   │                               # Bütünlük Kontrolü" — zorunlu status check)
│   ├── convert.py                 # Bölümleri epub'a ciltler, PR açar
│   └── lib/
│       ├── groq_client.py           # Groq API istemcisi (key rotasyonu, retry)
│       ├── gemini_client.py         # Gemini API istemcisi
│       ├── git_utils.py             # Kitap dalı açma, status.json, push
│       ├── review_fix.py            # review.py'nin whitelist + düzeltme mantığı
│       ├── english_detector.py      # Sözlük destekli İngilizce kalıntı tespiti
│       ├── series.py                # Kitaba özel karakter/terim sözlüğü (series/*.json)
│       ├── memory.py                # Çeviri sırasında öğrenilen isim/terim hafızası
│       ├── dictionary.py            # Öğrenilen kelimeler (dictionary/learned_words.json)
│       ├── ner.py                   # Kaynak metinden isim/terim çıkarımı (çeviri öncesi)
│       ├── boilerplate.py           # Tekrar eden şablon metinleri tanıma
│       ├── unicode_cleaner.py       # Model çıktısındaki bozuk karakterleri temizleme
│       └── pitfalls.py              # common_pitfalls.json'ı sistem prompt'una ekler
├── .github/workflows/
│   ├── translate.yml              # Yükleme sonrası ana çeviri workflow'u
│   ├── queue-worker.yml           # Bölüm/parça bazında devam workflow'u
│   ├── review.yml                 # İkinci geçiş workflow'u
│   ├── qa.yml                     # Gemini denetimi + Qwen düzeltme workflow'u
│   ├── pr-check.yml               # "Kitap Bütünlük Kontrolü"
│   └── convert.yml                # Ciltleme + PR açma workflow'u
├── series/
│   └── <seri-adı>.json            # Kitaba/seriye özel karakter+terim sözlüğü
├── dictionary/
│   └── learned_words.json         # Kitaplar arası öğrenilen kelime hafızası
├── common_pitfalls.json         # Kitap bağımsız, tekrar eden çeviri hataları
├── known_proper_nouns.json      # Kitap bağımsız, İngilizce kalması gereken gerçek isimler
├── status.json                  # main'deki son tamamlanan kitabın durumu
├── requirements.txt
└── vercel.json
```
