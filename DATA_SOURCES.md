# Veri Kaynakları

Altın test setine (`eval/gold/`) ve few-shot örneklerine (`fewshot.json`) giren
HER veri burada kayıt altına alınır: nereden, hangi lisansla, ne zaman. Kayıt
olmayan ya da lisansı belirsiz veri repoya girmez.

> Bu dosya hukuki tavsiye değildir. Bir kaynağın lisansından emin değilsen
> kullanma — ya da `eval/private/` altında (git'e girmez) sadece kendi
> testin için tut.

## Kabul edilen lisanslar (public repo)

| Kod | Anlamı |
|---|---|
| `public-domain` | Telifi sona ermiş. Türkiye'de süre, yazarın ve ÇEVİRMENİN vefatından itibaren 70 yıl; çevirmenin ölüm tarihini mutlaka kontrol et — eski bir çeviri otomatik olarak serbest değildir. |
| `CC0` | Hakları tamamen serbest bırakılmış. |
| `CC-BY` / `CC-BY-SA` | Atıf (ve SA'da aynı lisansla paylaşım) şartıyla serbest. Atfı aşağıdaki tabloya yaz. |
| `own` | Senin kendi çevirin/düzeltmen (kaynak metin de serbestse). |
| `permission` | Çevirmenden açık YAZILI izin. İzni nasıl aldığını `Not` sütununa yaz. |

## Kullanma

- Basılı roman, yayınevi çevirisi, hayran çevirisi vb. telifli metinleri public
  repoya koyma (`eptran-library` dahil). Sadece kendi testin için gerekiyorsa
  `python eval/add_pair.py add ... --private`.
- Lisansı "sanırım serbest" olanlar.

## Nereden bulunur

- **Kaynak (İngilizce) metin:** Project Gutenberg (gutenberg.org) — telifi bitmiş romanlar.
- **Referans (Türkçe) çeviri:** Vikikaynak (tr.wikisource.org) üzerindeki telifi bitmiş
  çeviriler; çevirmenin vefat tarihini doğrula.
- **Genel paralel derlemler:** OPUS (opus.nlpl.eu) üzerinden Tatoeba (CC BY),
  WikiMatrix (CC BY-SA). Çoğu kısa cümle/ansiklopedi dili; light novel üslubuna
  uzak, terim ve cümle doğruluğu için iyi.
- **Kendi verin:** insan gözünden geçip düzelttiğin bölümler (`own`). Okuyucu
  önerisi PR akışı kurarsan katkı şartlarını (örn. CC BY-SA) açıkça yaz.

## Kayıt

`eval/add_pair.py add` bir çift eklediğinde buraya bir satır ekle:

| Tarih | Kaynak / eser | Çevirmen | Lisans | URL | Çift sayısı | Not |
|---|---|---|---|---|---|---|
| _(henüz yok)_ | | | | | | |
