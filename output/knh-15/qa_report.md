# QA Raporu — knh-15

**Günlük Gemini kotası tükendiği için durduruldu — 10/24 bölüm tarandı. Script'i tekrar çalıştırınca kaldığı yerden devam edecek (baştan başlamayacak).**

*Bu bir OTOMATİK ÖNERİ listesidir, kesin doğru kabul etmeyin — her maddeyi kaynakla birlikte kendiniz kontrol edin. Bazı işaretlemeler yanlış pozitif olabilir (bkz. script docstring'i).*

## Bölüm 1: Character Profiles — 1 sorun
- **ATLANMIŞ**: Bölümün başlığı olan 'Character Profiles' ifadesi Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Character Profiles"*

## Bölüm 2: Chapter 1: The Selection Exam — 4 sorun
- **ANLAM_KAYMASI**: Kaynak metinde mola odasında et şiş çubukları ve elden ele dolaşan müstehcen bir kitabın bulunduğu belirtilirken, çeviride cümlenin sonuna 'değildi' eklenerek bu nesnelerin orada bulunmadığı söylenmiş ve anlam tamamen tersine çevrilmiştir.
  - Kaynak: *"That was all well and good, but not so much the sticks left over from late-night snacks of meat skewers, or—she couldn’t believe she was finding this—a naughty book that had clearly been passed around."*
  - Çeviri: *"Bu kadarı gayet makuldü, ama gece atıştırmalıklarından kalan et şiş çubukları ya da—bunu gördüğüne inanamıyordu—elden ele dolaşmış açıkça bir “pis kitap” değildi."*
- **ANLAM_KAYMASI**: 'something to tease her about' (onunla uğraşacak/ona takılacak bir şey) ifadesi 'onu taklit edebileceği bir şey' (taklit etmek/imitate) şeklinde yanlış çevrilmiştir.
  - Kaynak: *"He was thrilled to have found something to tease her about, but unfortunately for him, he didn’t realize that Dr. Li was standing right behind him."*
  - Çeviri: *"Onu taklit edebileceği bir şey bulduğu için heyecanlanmıştı, ama ne yazık ki Dr. Li’nin hemen arkasında durduğunu fark etmemişti."*
- **ANLAM_KAYMASI**: 'Are you sure I shouldn't go along?' (Benim de gitmemem gerektiğinden emin misiniz?) sorusu, Türkçe çeviride 'Benimle gelmemem gerektiğinden emin misin?' şeklinde hem anlamsız hem de dil bilgisi açısından hatalı bir şekilde aktarılmıştır.
  - Kaynak: *"“Are you sure I shouldn’t go along?” he asked not Tianyu, but the old physician."*
  - Çeviri: *"“Benimle gelmemem gerektiğinden emin misin?” diye sordu, Tianyu’ya değil, yaşlı hekime."*
- **ANLAM_KAYMASI**: Sarayın bir bölümü olan 'outer court' (dış saray) ifadesi 'dış mahalle' olarak yanlış çevrilmiştir.
  - Kaynak: *"it was located in the outer court, but close to His Majesty’s bedchamber."*
  - Çeviri: *"dış mahalledeydi, ama Majestelerinin yatak odasına yakındı."*

## Bölüm 3: Chapter 2: Smallpox and Chickenpox — 5 sorun
- **ANLAM_KAYMASI**: "handpick" (özenle seçmek) ifadesi yanlış anlaşılarak "eldivenle seçmek" şeklinde çevrilmiştir.
  - Kaynak: *"Why would they handpick people to do drug trials?"*
  - Çeviri: *"İlaç denemeleri için insanları neden eldivenle seçiyorlardı ki?"*
- **ANLAM_KAYMASI**: "frivolous" (ciddiyetsiz, laubali) kelimesi "hafif kanatlı" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"although he acted awfully frivolous, Yo trusted him implicitly."*
  - Çeviri: *"son derece hafif kanatlı davransa da, Yo ona körü körüne güveniyordu."*
- **ANLAM_KAYMASI**: "Let's see" (Bir düşüneyim, bakalım) ifadesi "Görün bakalım" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“Let’s see... I got a pretty serious fever, but the blisters didn’t spread all over my body."*
  - Çeviri: *"“Görün bakalım... Oldukça ciddi bir ateşim çıktı, ama kabarcıklar vücudumun her yerine yayılmadı."*
- **ANLAM_KAYMASI**: "grandfatherly" (büyükbaba gibi, dede gibi) ifadesi "babaanne" (grandmother) olarak yanlış çevrilmiştir.
  - Kaynak: *"He might look like a grandfatherly old man, but he was an experienced hand in this office and was used to things getting a little mean."*
  - Çeviri: *"Dışarıdan babaanne gibi görünebilirdi, ama bu büroda deneyimli bir eldi ve işlerin biraz sertleşmesine alışkındı."*
- **ANLAM_KAYMASI**: Bu diyalog bölümündeki cümlelerin sırası tamamen karışmış, bazı ifadeler mükerrer veya yanlış yerleştirilmiş ve "“İlk” eş, öyle mi?" gibi kaynakta olmayan anlamsız bir ifade eklenmiştir.
  - Kaynak: *"“I have medicines to deliver,” said Maomao, entering the office and taking off her portable medicine cabinet.
“Delivery’s here,” Yo echoed, imitating Maomao.
“Well, well, what a sweet young thing you’ve brought with you today,” said the elderly doctor.
“My name is Yo,” she told him. “I just started this year.” Evidently this was the first time they had met.
“We don’t get a lot of young ladies around here. Too many rough-and-tumble types.”
“I’m here,” Maomao said stiffly.
“You and Miss Chue are special cases. In flower terms, I would say you’re an obako and a dandelion.”"*
  - Çeviri: *"“Teslimat geldi,” diye yankıladı Yo, Maomao’yu taklit ederek.
“Ben buradayım,” dedi Maomao sert bir şekilde.
“İlk” eş, öyle mi?
“İlaç teslimatım var,” dedi Maomao, odaya girip taşınabilir ilaç dolabını omuzlarından indirirken.
“Vay canına, bugün yanına ne tatlı bir kız getirmişsin,” dedi yaşlı doktor.
“Adım Yo,” dedi ona. “Bu yıl yeni başladım.” Görünüşe göre ilk kez tanışıyorlardı.
“Burada pek genç hanımefendi görmüyoruz. Çoğu zaman kaba saba tiplerle uğraşıyoruz.”
“Sen ve Chue Hanım istisnasınız. Çiçeklerle kıyaslayacak olursam, sen bir obako, o da bir karahindiba olursun.”"*

## Bölüm 4: Chapter 3: Reassignment — 5 sorun
- **ANLAM_KAYMASI**: "Not since yesterday" (Dünden beri değil) ifadesi "Hayır, dün değil" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“No, not since yesterday.”"*
  - Çeviri: *"“Hayır, dün değil.”"*
- **ANLAM_KAYMASI**: "What do you think we're making?" (Sizce ne yapıyoruz?) sorusu "Bence ne yapıyoruz?" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“What in the world do you think we’re making?” asked the doctor of average height."*
  - Çeviri: *"“Bence ne yapıyoruz?” diye sordu orta boylu doktor."*
- **ANLAM_KAYMASI**: "Licorice" (meyan kökü) kelimesi uydurma bir kelime olan "Lakübit" olarak, "garden peony" (bahçe şakayığı) ise "bahçe sümbülü" olarak yanlış çevrilmiştir.
  - Kaynak: *"“Licorice and garden peony—it must be a decoction of the two,” answered Tall Senior, the taller of the two seniors."*
  - Çeviri: *"“Lakübit ve bahçe sümbülü—ikisinin bir karışımı olmalı,” diye cevap verdi, iki kıdemliden daha uzun olan Uzun Kıdemli."*
- **ANLAM_KAYMASI**: "thirty minutes" (otuz dakika) ifadesi "Yirmi dakika" olarak yanlış çevrilmiştir.
  - Kaynak: *"They rode along for thirty minutes until they arrived at a mansion on the outskirts of the capital."*
  - Çeviri: *"Yirmi dakika boyunca sürüldüler ve başkentin dışındaki bir konakta indiler."*
- **ANLAM_KAYMASI**: "Don't mind us" (Bize aldırmayın/Kusura bakmayın) ifadesi tam tersi anlama gelecek şekilde "Bizi rahatsız etmeyin" olarak çevrilmiştir.
  - Kaynak: *"Don’t mind us, she thought as she came into the house."*
  - Çeviri: *"Bizi rahatsız etmeyin, diye düşündü evin içine girerken."*

## Bölüm 5: Chapter 4: Drug Trials — 2 sorun
- **ANLAM_KAYMASI**: "constantly staffed" ifadesi klinikte kesintisiz personel/nöbetçi bulundurmak anlamına gelir. Çeviride ise kliniği insanla/hastayla doldurmak anlamındaki "dolu tutmak" ifadesi kullanılarak anlam kaymasına yol açılmıştır.
  - Kaynak: *"Still, the four of them weren’t enough to keep the place constantly staffed."*
  - Çeviri: *"Yine de dört kişilik kadro, mekânı sürekli dolu tutmaya yetmiyordu."*
- **ANLAM_KAYMASI**: "Master Physician" ifadesi hekime yönelik saygılı bir hitap şeklidir (Hekim Efendi/Hekim Üstat). Söz konusu karakter kliniğin veya saray tıp ofisinin idari yöneticisi (başhekimi) olmadığı için "Başhekim" çevirisi yanlış bir unvan kullanımıdır.
  - Kaynak: *"“Master Physician,” she started."*
  - Çeviri: *"“Başhekim,” diye başladı."*

## Bölüm 6: Chapter 5: A Book Restored
*(Denetlenemedi.)*

## Bölüm 7: Chapter 6: The Patient — 6 sorun
- **ANLAM_KAYMASI**: "physicians" (hekimler) kelimesi Türkçe metinde var olmayan "Heimler" şeklinde yanlış yazılmıştır.
  - Kaynak: *"The physicians, chiefly the palace’s own doctors, are actually conducting drug trials."*
  - Çeviri: *"Heimler, özellikle sarayın kendi doktorları, aslında ilaç denemeleri yürütüyor."*
- **ANLAM_KAYMASI**: "Başka kim fark etti?" anlamına gelen soru, "Daha fark eden oldu mu?" şeklinde yanlış çevrilerek anlam kaymasına yol açmıştır.
  - Kaynak: *"Who else has noticed?"*
  - Çeviri: *""Kimse daha fark etti mi?""*
- **ANLAM_KAYMASI**: "even if they did" (fark etseler bile) ifadesi "Yapacak olsalar bile" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"Didn’t you deliberately gather people who would keep their mouths shut even if they did?"*
  - Çeviri: *"Yapacak olsalar bile ağızlarını kapalı tutacak insanları kasıtlı olarak toplamadın mı?"*
- **ANLAM_KAYMASI**: "I thought I told..." (herkese dağılmalarını söylediğimi sanıyordum) ifadesi "Bence herkese dağılmalarını söyledim" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"I thought I told everyone to clear out,"*
  - Çeviri: *""Bence herkese dağılmalarını söyledim,""*
- **ANLAM_KAYMASI**: Gaoshun'un özür dilemesine karşılık Jinshi'nin söylediği "Sorun değil / Önemli değil" anlamındaki ifade "Olur" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"It’s all right."*
  - Çeviri: *""Olur.""*
- **ANLAM_KAYMASI**: "His Majesty" (Majesteleri - İmparator için kullanılır) unvanı, uydurma bir kelime olan "Alteşin" (muhtemelen Altesleri ile karışmış) şeklinde yanlış çevrilmiştir.
  - Kaynak: *"What is His Majesty’s current condition?"*
  - Çeviri: *""Alteşin'in şu anki durumu nedir?""*

## Bölüm 8: Chapter 7: A Man’s Romance — 4 sorun
- **ANLAM_KAYMASI**: Kaynakta 'Princess' (Prenses) olarak geçen unvan Türkçe çeviride 'Prens' olarak yanlış aktarılmıştır.
  - Kaynak: *"For a second, Maomao thought maybe he meant Princess Lingli, but she realized it was probably the adopted daughter Gyoku-ou had sent to the capital."*
  - Çeviri: *"Bir an için Maomao, Prens Lingli'yi kastettiğini düşündü, ama muhtemelen Gyoku-ou'nun başkente gönderdiği evlatlık kızı kastettiğini anladı."*
- **ANLAM_KAYMASI**: Bölümün sonundaki diyaloglar henüz gerçekleşmeden buraya eklenmiş, iki kez tekrarlanmış ve kaynakta hiç olmayan 'Kepek...', 'Sindirim...', 'Demek ki fark etmiş.' gibi ifadeler uydurulmuştur.
  - Kaynak: *"“I did. But since we’ve got the time, how about we do this by question and answer?”"*
  - Çeviri: *""Geldi. Ama vaktimiz varken, bunu soru-cevap şeklinde yapalım mı?"

"Oh, en azından düşünmeye çalış."

"Sana söyledim, bu benim alanım değil."

"Tamam, tamam. İpucu: et."

"Kepek..."

Sindirim...

Demek ki fark etmiş.

"Kıdemlilerine karşı biraz fazla talebeksin, ha? Başka ilginç bir şeyim olup olmadığını bilmiyorum..." Uzun Kıdemli havanını ve havan elini çalıştırırken düşünceli bir ses çıkardı. Alt kademesinden gelen bir isteği yerine getirmek isteyen iyi bir kıdemliydi. "Eh, et ve balıken bahsetmişken..."

"Evet? Aklına bir şey mi geldi?" Maomao'nun gözleri daha da parladı.

"Geldi. Ama vaktimiz varken, bunu soru-cevap şeklinde yapalım mı?"

"Oh, en azından düşünmeye çalış."

"Sana söyledim, bu benim alanım değil."

"Tamam, tamam. İpucu: et."

"Kepek..."

Sindirim...

Demek ki fark etmiş."*
- **ŞAHIS_UYUŞMAZLIĞI**: Kaynakta üçüncü şahıs ('he was so sure') kullanılırken çeviride ikinci şahıs ('eminsen') kullanılmıştır.
  - Kaynak: *"If he was so sure he would win, why did he lose?"*
  - Çeviri: *"Kazanacağından o kadar eminsen, neden kayb_"*
- **ATLANMIŞ**: Metin bu noktada aniden kesilmekte ve bölümün geri kalan kısmı tamamen atlanmaktadır.
  - Kaynak: *"If he was so sure he would win, why did he lose?

"Military matters aren’t really my area of expertise," Maomao said, frowning at what turned out to be quite a different topic from what she had expected. "Help me out."

"Oh, at least 
try
 to think it through."

"I told you, it’s not my field."

The two of them chatted away, their mortars grinding and the powder collecting.

"Okay, okay. Your hint is: meat."

"Meat?" Maomao cocked her head and 
hmm
ed thoughtfully.

Meat, meat, meat... Maybe he means they were caught in some unique trap or something?

It seemed unlikely that actual meat was the issue at hand."*
  - Çeviri: *"Kazanacağından o kadar eminsen, neden kayb_"*

## Bölüm 9: Chapter 8: Anesthesia — 3 sorun
- **ANLAM_KAYMASI**: Jinshi, Hulan'a 'Basen'i gönder, senin yerine geçsin' talimatını vermektedir. Türkçe çeviride ise 'Seni Basen ile değiştirsin' denilerek eylemin yönü ve anlamı yanlış aktarılmıştır.
  - Kaynak: *"“Hulan, you withdraw. Send Basen around to replace you,” Jinshi said."*
  - Çeviri: *""Hulan, çekil. Seni Basen ile değiştirsin," dedi Jinshi."*
- **ANLAM_KAYMASI**: Luomen, Maomao'nun resmi bir ortamda kendisine 'Pops' (Amca) diye hitap etmesini sorgulayarak 'Bana normalde böyle hitap etmezsin/etmemelisin, değil mi?' demek istemektedir. Türkçe çeviri ise bunu yanlış bir ifadeyle aktarmıştır.
  - Kaynak: *"“That’s not what you call me, is it?”"*
  - Çeviri: *""Beni öyle çağırıyorsun, öyle mi?""*
- **ANLAM_KAYMASI**: İngilizcedeki 'appendix' (apandis organı) kelimesi, Türkçe çeviride hastalık adı olan 'apandisit' ile karıştırılmıştır.
  - Kaynak: *"The appendix is that part that looks like a worm, isn’t it?"*
  - Çeviri: *"Apandisit, solucan gibi görünen o kısım değil mi?"*

## Bölüm 10: Chapter 9: To Everyone a Purpose
*(Denetlenemedi.)*

## Bölüm 11: Chapter 10: Gyouyoh
*(Denetlenemedi.)*

## Bölüm 12: Chapter 11: The Special Unit
*(Denetlenemedi.)*

## Bölüm 13: Chapter 12: Explanation and Agreement — 6 sorun
- **ATLANMIŞ**: Kaynak metnin ilk cümlesi çeviride tamamen atlanmıştır.
  - Kaynak: *"They didn’t know where word of the surgery had leaked from."*
- **ANLAM_KAYMASI**: "bride" (gelin) kelimesi "damat adayı" olarak yanlış çevrilmiştir.
  - Kaynak: *"Maomao could only guess how many people had seen those darkened fingers and immediately decided this woman was unfit to be their bride."*
  - Çeviri: *"Maomao, bu kadının damat adayı olmaya uygun olmadığını hemen kararlaştıran kaç kişinin o koyulaşmış parmakları gördüğünü tahmin edebilirdi."*
- **ANLAM_KAYMASI**: "appendix" (apandis) kelimesi "Ekinsoyu" şeklinde anlamsız bir kelimeyle karşılanmıştır.
  - Kaynak: *"If the appendix burst and sent filth throughout the Emperor’s abdomen, the chances of his demise skyrocketed."*
  - Çeviri: *"Ekinsoyu patlar ve İmparator'un karın boşluğuna pislik yayarsa, ölüm olasılığı fırlardı."*
- **ANLAM_KAYMASI**: "she reminded Maomao of Suiren" (Maomao'ya Suiren'i hatırlatıyordu) ifadesi, "Maomao'yu Suiren'e hatırlatıyordu" şeklinde tersine çevrilerek anlam kaymasına yol açmıştır.
  - Kaynak: *"In terms of age, she reminded Maomao of Jinshi’s elderly assistant Suiren, but she was less calculating."*
  - Çeviri: *"Yaş bakımından Maomao'yu, Jinshi'nin yaşlı yardımcısı Suiren'e hatırlatıyordu, ancak daha az hesapçıydı."*
- **ANLAM_KAYMASI**: "what amounted to griping" (sızlanmaktan ibaret olan konuşmalarını) ifadesi "fiyakalı şikayetlerini" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"Maomao sipped her tea and listened to the doctors do what amounted to griping."*
  - Çeviri: *"Maomao çayından bir yudum aldı ve hekimlerin fiyakalı şikayetlerini dinledi."*
- **ANLAM_KAYMASI**: "peony" (şakayık) çiçeği "gelincik" (poppy) olarak yanlış çevrilmiştir.
  - Kaynak: *"“We’d like to ask you to come with us,” one of the men said, showing her a peony crest."*
  - Çeviri: *"“Sizinle gelmenizi rica ediyoruz,” dedi erkeklerden biri, ona bir gelincik arması göstererek."*

## Bölüm 14: Chapter 13: Sowing Seeds — 5 sorun
- **ATLANMIŞ**: Bölümün giriş cümlesi Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Jinshi was getting a headache from having this conversation for the umpteenth time."*
- **ANLAM_KAYMASI**: "This is making me want to hide" (Bu durum bende saklanma isteği uyandırıyor) ifadesi, Türkçe dil bilgisine uymayacak şekilde "Bu beni saklanmak istiyor" olarak yanlış çevrilmiştir.
  - Kaynak: *"“This is making me want to hide,” said Basen, looking just as bothered as Jinshi."*
  - Çeviri: *""Bu beni saklanmak istiyor," dedi Basen, Jinshi kadar rahatsız bir ifadeyle."*
- **ANLAM_KAYMASI**: Jinshi yanağındaki yara izini kaşıyarak "bunlardan (yara izlerinden) birkaç tane daha edinmeliyim" demek isterken, çeviride "birkaç tane daha ekmek yemem gerek" şeklinde tamamen yanlış çevrilmiştir.
  - Kaynak: *"“Perhaps I need a few more of these,” Jinshi said, scratching the scar on his cheek with a finger."*
  - Çeviri: *""Belki birkaç tane daha ekmek yemem gerek," dedi Jinshi, yanağındaki yara izini parmağıyla kaşıyarak."*
- **ANLAM_KAYMASI**: "half-brother" (üvey erkek kardeş) ifadesi "amcasının kızı" olarak, "great-niece" (kız/erkek kardeşinin torunu) ifadesi ise "torunuydu" (granddaughter) olarak yanlış çevrilmiştir.
  - Kaynak: *"She was the grandniece of the Empress Dowager’s half-brother, Hao—and hence also the great-niece of the Empress Dowager herself."*
  - Çeviri: *"Dul İmparatoriçe'nin amcasının kızı Hao'nun torunu ve dolayısıyla Dul İmparatoriçe'nin kendisinin de torunuydu."*
- **ANLAM_KAYMASI**: "middle consort" (orta düzey eş) ifadesi "Üst Düzey Konsort" (upper consort) olarak yanlış çevrilmiştir.
  - Kaynak: *"“A young lady from the Empress’s faction was admitted to the rear palace at the same time and made a middle consort,” Maamei said."*
  - Çeviri: *""İmparatoriçe'nin fraksiyonundan genç bir hanım da aynı anda arka saraya kabul edildi ve Üst Düzey Konsort yapıldı," dedi Maamei."*
