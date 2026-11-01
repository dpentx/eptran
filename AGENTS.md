# AGENTS.md — eptran'da çalışan yapay zekâ ajanları için notlar

Bu dosya, repoda araçla (GitHub MCP, sandbox) çalışan ajanlar içindir. Kısa tut,
yeni bir dersi bulunca buraya ekle.

## 1. ÖNCE BUNU OKU: repo şişkin, timeout buradan çıkıyor

- `output/` (~206 MB) ve `input/` (~101 MB) git'te duruyor: 20-30 MB'lık epub'lar,
  yüzlerce görsel. `.git` ~228 MB. Tam (sığ) klon ~20 sn ve ~300 MB; sandbox'ta
  ve araç çağrılarında zaman aşımına yol açıyor.
- YAPMA:
  - `get_file_contents` ile `output/`, `input/` ya da `output/<kitap>/`
    klasörlerini listeleme (yüzlerce kayıt), epub/jpg okuma.
  - Düz `git clone` (tam içerik).
  - Büyük araç çıktılarını bağlama dökme. `| head`, `cut -c1-200`, `max_chars` kullan.
- YAP: sparse + partial klon (≈1 sn, <1 MB):
  ```
  git clone --depth 1 --filter=blob:none --sparse https://github.com/dpentx/eptran.git
  cd eptran && git sparse-checkout set scripts .github api eval series dictionary
  ```
  Kitap verisinden tek dosya lazımsa `git show origin/main:output/<slug>/001_x.txt`
  (yalnızca o blob inen) ya da `get_file_contents` ile TEK dosya yolu. Bir kitabın
  klasörünü `sparse-checkout add` ile açma: epub ve görseller de iner.
- Kalıcı çözüm henüz yapılmadı: epub/görselleri git'ten çıkarıp Releases/
  eptran-library'ye taşımak ve geçmişi temizlemek (`git filter-repo` TÜM dalların
  geçmişini yeniden yazar → yalnızca İbo açıkça isterse).

## 2. Çalışma biçimi

- `main` korumalı: doğrudan push yok, her konu için dal + PR. Zorunlu check:
  "Kitap Bütünlük Kontrolü" (sadece `book/*` PR'larında gerçekten çalışır, diğerlerinde
  atlanır ama kaydı birkaç sn gecikebilir). Merge "405 … expected" verirse ~30 sn
  bekleyip tekrar dene.
- PR'ı İbo istemeden merge etme (istediğinde et). Canlı siteye giden repolarda
  (eptran-web) önce Vercel preview READY mi diye bak.
- `push_files` (GitHub MCP) TAM dosya içeriği ister, satır içi düzenleme yok.
  Büyük bir dosyayı baştan yazmak yazım hatası riski taşır (özellikle Türkçe
  `ı/i`, `İ`). Mümkünse yeni dosya ekle. Mutlaka doğrula:
  `git hash-object <yerel-dosya>` ile push edilen dosyanın sha'sını karşılaştır
  (`get_file_contents` dizin listesi `ref` parametresiyle sha verir) ya da public
  repoda `raw.githubusercontent.com/<owner>/<repo>/<COMMIT_SHA>/<path>` ile diff
  al. Dal adıyla raw URL ~5 dk önbellekli, bayat içerik gösterir; commit SHA kullan.
- MCP araçları `tool_search` ile yüklenir; çoğunda `owner`/`repo` parametresi var
  (varsayılan `dpentx/eptran`). PR kapatma aracı yok: dalı silmek PR'ı kapatır.
- Test et ve PR'a yaz neyi test ettiğini: `py_compile`, YAML yükleme, JS için jsdom,
  `gh` çağıran script'ler için sahte `gh`. Gerçek Actions çalıştırması çoğu zaman
  mümkün değil; bunu açıkça belirt.
- Hafızadaki/eski notlar ile repo birbirini tutmayabilir. Kod gerçeğe tek kaynaktır;
  önce `main`'e bak.

## 3. Mimari (bozma)

- Hiçbir otomasyon `main`'e doğrudan yazmaz. Yükleme: `api/upload.js` →
  `queue/<slug>` → `translate.py` kitabı `book/<slug>` dalına taşır → çeviri,
  review, QA, ciltleme hepsi o dalda → `convert.py` tek bir PR açar.
- Kuyruk: sistem doluyken yüklenen kitaplar `queue/<slug>` dalında bekler;
  `scripts/start_next_queue.py` aktif kitap yoksa en eskisini başlatır.
- `book/*` PR'ı kapanınca (merge edilsin ya da edilmesin) dal otomatik silinir ve
  sıradaki kitap başlar (`delete-merged-book-branch.yml`). Merge'siz kapatılan
  kitabın dosyaları dalla birlikte gider.
- Okuyucu sitesine (eptran-web) gönderim PR MERGE EDİLİNCE yapılır
  (`web-ingest-on-merge.yml` → `scripts/web_ingest_book.py`). `convert.py`
  içindeki `push_book()` `book/*` dalındayken bilerek hiçbir şey göndermez.
- Siteden kitap silmek: `web-purge.yml` workflow'unu `source_keys` (virgüllü slug'lar,
  hepsi için `ALL`) ile tetikle. Sır (`WEB_INGEST_SECRET`) yalnızca Actions'ta.
- Groq: `qwen/qwen3.8-27b` (preview), free planda TPM tavanı ~8K (prompt+completion).
  `GROQ_API_KEY_1..4` dört AYRI hesaptır. Few-shot/prompt eklerken token bütçesine dikkat.
- Kalite ölçümü: `eval/` (altın set şu an boş). Prompt/model değiştirmeden önce ölç.

## 4. İlgili repolar ve Vercel projeleri

- `dpentx/eptran-web` — okuyucu sitesi (Astro + Turso). Vercel: `eptran-web`
  (https://eptran-web-virid.vercel.app). `/api/ingest`, `/api/purge`, `/api/suggestions`.
- `dpentx/web-writer-dpentx` — Kehribar Writer (Vercel: `web-writer-dpentx`);
  `/eptran.html` eptran depolarını mobilden düzenler. Aynı origin'de `gh_token` kullanır.
- `dpentx/eptran-library` — halka açık kütüphane (staging/ana dal + Releases).
- `dpentx/eptran-mcp` — "M mcp" GitHub MCP sunucusu (private).

## 5. Dikkat edilecekler

- Yorumlar ve commit mesajları Türkçe. Sır/token yazma, loglama.
- Telifli metni halka açık repoya koyma (`DATA_SOURCES.md`).
- Çözümü kodun yanına yorum olarak "neden"ini yaz; bu repoda çoğu hata sessiz
  bozulmaydı (bkz. yorumlardaki "gerçek üretim hatası" notları).
