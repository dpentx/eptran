# eval — çeviri kalitesini ölçme

Amaç: prompt, model, QA kuralı ya da few-shot değiştirdiğinde çevirinin
gerçekten iyileşip iyileşmediğini "galiba" yerine sayıyla görmek.

```
eval/
├── gold/            # lisansı temiz kaynak+referans çiftleri (public, JSONL)
├── private/         # kendi testin için telifli veri (git'e GİRMEZ)
├── results/         # koşu çıktıları (git'e girmez; workflow artifact yükler)
├── baseline.json    # (isteğe bağlı) beğendiğin bir sonucun kopyası
├── run_eval.py      # altın seti hattan geçirip puanlar
└── add_pair.py      # çift ekle / listele / few-shot'a kopyala
```

## Akış

1. **Veri topla** — `DATA_SOURCES.md`'deki kaynak ve lisans kurallarına uy.
   Paragraf düzeyinde (20–2500 karakter) çiftler; farklı türlerden karışık
   (diyalog, anlatım, deyim, olumsuzlama, özel isim) olsun. Hedef: 30–50 çift.
2. **Ekle:**
   ```
   python eval/add_pair.py add --id gutenberg-pp-001 \
     --source @kaynak.txt --reference @ceviri.txt \
     --origin "Pride and Prejudice, Böl. 1" --license public-domain \
     --source-url https://www.gutenberg.org/ebooks/1342 --translator "Ad (öl. 19xx)"
   python eval/add_pair.py list
   ```
3. **Sına (API'siz):** `python eval/run_eval.py --dry-run` — veri ve puanlama
   çalışıyor mu (referans kendisiyle karşılaştırılır, chrF = 100 çıkmalı).
4. **Baseline al:** Actions → "Eval (altın set)" → Run workflow (dal: main).
   Beğendiğin sonucu `eval/baseline.json` olarak kopyalayıp commit'le.
5. **Değişikliği ölç:** değişikliği bir dalda yap, workflow'u O dalı seçerek
   çalıştır — özet, baseline'a göre farkı gösterir. Few-shot etkisi için aynı
   dalda `fewshot` kutusunu açıp kapatarak iki koşu yap.

Groq kotası çeviriyle ortak olduğu için workflow aktif kitap (`book/*`) ya da
bekleyen yükleme (`queue/*`) varken çalışmaz (`force` ile aşılabilir).

## Metrikler

| metrik | anlamı |
|---|---|
| `chrF` | karakter n-gram benzerliği (0–100, yüksek iyi) |
| `repeat_gap` | yakın mesafeli kelime tekrarı, referansa göre fark (0'a yakın iyi; "var" tekrarı sorununu yakalar) |
| `en_residue` | çevrilmemiş İngilizce kalıntı oranı |
| `len_ratio` | çeviri/referans uzunluğu (çok düşük = içerik atlama şüphesi) |

Sınırlar (dürüst olalım): chrF tek bir referansa bakar; iyi ama farklı bir
çeviriyi cezalandırabilir. 30'dan az çiftte farklar gürültüdür. Anlam kayması
(olumsuzlamanın tersine dönmesi gibi) bu sayılarla yakalanmaz — onu
Gemini QA denetimi yakalıyor. Sonraki adım olarak LLM-hakem ya da COMET
eklenebilir; önce veri lazım.

## Few-shot

`fewshot.json` boşken hiçbir şey değişmez. İyi bir çifti eklemek için:
`python eval/add_pair.py fewshot <id>` (her yanı ≤600 karakter). Prompt'a en
fazla 3 örnek / 1200 karakter girer (Groq free TPM tavanı ~8000 yüzünden).
`EPTRAN_FEWSHOT=0` ile kapatılır. Üretimde açmadan önce eval'de baseline'dan
iyi çıktığını gör; few-shot review/refine çağrılarının prompt'una da girer,
bu yüzden büyük chunk'larda 413 riskini de gözle.
