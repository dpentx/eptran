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
- Aynı anda yalnızca bir kitap işlenir — `book/*` ya da `queue/*` önekli
  bir dal var olduğu sürece yeni yükleme reddedilir.
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
│   │                              # App token üretir, workflow'u tetikler
│   └── status.js                 # Arayüzün ilerleme durumunu okuduğu endpoint
├── scripts/
│   ├── translate.py               # Ana çeviri döngüsü (bölüm bölüm)
│   ├── queue_worker.py            # Bir sonraki parçayı işleyip kendini tetikler
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
│       ├── git_utils.py             # Dal açma/yeniden adlandırma, status.json, push
│       ├── review_fix.py            # review.py'nin whitelist + düzeltme mantığı
│       ├── english_detector.py      # Sözlük destekli İngilizce kalıntı tespiti
│       ├── series.py                # Kitaba özel karakter/terim sözlüğü (series/*.json)
│       ├── memory.py                # Çeviri sırasında öğrenilen isim/terim hafızası
│       ├── dictionary.py            # Öğrenilen kelimeler (dictionary/learned_words.json)
│       ├── ner.py                   # Bölüm başına isim/terim çıkarımı
│       ├── boilerplate.py           # Tekrar eden şablon metinleri tanıma
│       ├── unicode_cleaner.py       # Model çıktısındaki bozuk karakterleri temizleme
│       ├── sliding_window.py        # Uzun bölümleri parçalara ayırma
│       └── pitfalls.py              # common_pitfalls.json'ı sistem prompt'una ekler
├── .github/workflows/
│   ├── translate.yml              # Yükleme sonrası ana çeviri workflow'u
│   ├── queue-worker.yml           # Bölüm/parça bazlı devam workflow'u
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



### 1. Repoyu Fork'la

Sağ üstten **Fork** butonuna bas.

### 2. GitHub Actions'ı Etkinleştir

Fork'ladıktan sonra **Actions** sekmesine gidip etkinleştir.

### 3. Bir GitHub App Oluştur

Otomasyon, kalıcı bir kişisel token yerine bir GitHub App üzerinden
çalışır (hem GitHub Actions hem Vercel tarafında).

[github.com/settings/apps/new](https://github.com/settings/apps/new)
adresinden:
- **Repository permissions:** `Contents` (Read and Write), `Pull
  requests` (Read and Write), `Actions` (Read and Write)
- Oluşturduktan sonra **App ID**'yi not al, bir **private key** üret ve
  indir (`.pem` dosyası)
- App'i fork'ladığın repoya kur (Install App)

### 4. GitHub Actions Secret'larını Ekle

Repo → **Settings → Secrets and variables → Actions**:

| İsim | Açıklama |
|---|---|
| `APP_ID` | 3. adımdaki App ID |
| `APP_PRIVATE_KEY` | İndirdiğin `.pem` dosyasının tam içeriği |
| `GROQ_API_KEY_1..4` | Groq API key'leri (bkz. aşağıdaki not) — tek key de yeterli, o zaman sadece `GROQ_API_KEY` kullan |
| `GEMINI_API_KEY`, `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3` | Gemini API key'leri (birden fazlası isteğe bağlı, rate limit rotasyonu için) |

> **Not — birden fazla Groq/Gemini key'i:** Rotasyonun gerçekten işe
> yaraması için her key'in **ayrı bir hesaptan** gelmesi gerekir.
> Groq'un (ve çoğu sağlayıcının) rate limit'leri hesap/organizasyon
> başınadır — aynı hesaptan üretilmiş birden fazla key toplam
> kapasiteyi ARTIRMAZ, hepsi aynı havuzu paylaşır.

Ayrıca **Settings → Secrets and variables → Actions → Variables**
kısmına `GEMINI_MODEL` (örn. güncel bir Gemini model adı) eklemen
gerekir.

### 5. Vercel'e Deploy Et

[vercel.com](https://vercel.com) üzerinden repoyu import et ve şu ortam
değişkenlerini gir:

| Değişken | Açıklama |
|---|---|
| `GH_PAT` | Sunucu tarafı işlemler (dal açma, workflow tetikleme) için bir GitHub token — repo'ya `Contents` + `Actions` yazma izni yeterli |
| `GH_REPO` | `kullaniciadi/eptran` formatında fork'un adı |
| `GH_BRANCH` | Ana dal adı (genellikle `main`) |
| `APP_ID` | 3. adımdaki App ID — GitHub Actions'takiyle AYNI değer |
| `APP_PRIVATE_KEY` | 3. adımdaki private key — GitHub Actions'takiyle AYNI değer |

## Limitler

Groq'un güncel rate limit'lerini kendi hesabından doğrula:
[console.groq.com/settings/limits](https://console.groq.com/settings/limits)
(model, plan tipine göre değişir — ücretsiz planda dakikalık token
tavanı düşük olabilir, çok bölümlü kitaplarda çeviri birden fazla
çalıştırmaya yayılabilir).

## Çıktı Formatı

Çeviri tamamlanınca `output/<kitap-adı>/<kitap-adı>_tr.epub` olarak
üretilir. Bölümler ayrıca `output/<kitap-adı>/001_<kitap-adı>.txt`
şeklinde de mevcuttur.

## Bilinen İstisna Listeleri

- `common_pitfalls.json` — kitap bağımsız, tekrar eden genel çeviri
  hataları (yanlış kelime seçimleri vb.)
- `known_proper_nouns.json` — kitap bağımsız, gerçek dünyaya ait ve
  İngilizce bırakılması gereken özel isimler (bir çevirmen notunda
  anılan gerçek bir eser adı gibi)

Her ikisi de elle güncellenir — yeni bir örüntü/isim keşfedilince
ilgili dosyaya bir satır eklemek yeterli, kod değişikliği gerekmez.

---

*Groq (qwen3.8-27b) · Gemini · GitHub Actions · Vercel*
