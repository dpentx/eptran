# QA Raporu — knh-15

**Günlük Gemini kotası tükendiği için durduruldu — 8/24 bölüm tarandı. Script'i tekrar çalıştırınca kaldığı yerden devam edecek (baştan başlamayacak).**

*Bu bir OTOMATİK ÖNERİ listesidir, kesin doğru kabul etmeyin — her maddeyi kaynakla birlikte kendiniz kontrol edin. Bazı işaretlemeler yanlış pozitif olabilir (bkz. script docstring'i).*

## Bölüm 1: Character Profiles — 2 sorun
- **ATLANMIŞ**: Bölümün başlığı olan 'Character Profiles' ifadesi Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Character Profiles"*
- **ANLAM_KAYMASI**: 'Hen-pecked' (kılıbık, karı sözünden çıkmayan) ifadesi 'eşine bağımlı' şeklinde çevrilerek yanlış bir anlam verilmiştir.
  - Kaynak: *"He’s hen-pecked and long-suffering, but he knows a side of the Emperor that few people see."*
  - Çeviri: *"Eşine bağımlı ve sabırlı bir adam, ama İmparator'un az insanın gördüğü bir yönünü biliyor."*

## Bölüm 2: Chapter 1: The Selection Exam — 1 sorun
- **ANLAM_KAYMASI**: Kaynaktaki 'not so much' ifadesi, mola odasında şekerleme yapılmasının hoş karşılandığını ancak et şişlerinin ve müstehcen kitabın o kadar da hoş karşılanmadığını belirtmektedir. Çeviri ise 'müstehcen bir kitap değildi' diyerek orada bulunan şeylerin bunlar olmadığını iddia etmekte ve anlamı tamamen tersine çevirmektedir.
  - Kaynak: *"That was all well and good, but not so much the sticks left over from late-night snacks of meat skewers, or—she couldn’t believe she was finding this—a naughty book that had clearly been passed around."*
  - Çeviri: *"Bu kadarı gayet makuldü, ama gece atıştırmalıklarından kalan et şiş çubukları ya da—bunu gördüğüne inanamıyordu—elden ele dolaşmış açıkça müstehcen bir kitap değildi."*

## Bölüm 3: Chapter 2: Smallpox and Chickenpox — 3 sorun
- **ANLAM_KAYMASI**: "may I make a request of you?" (senden bir ricada bulunabilir miyim?) ifadesi yanlış anlaşılarak "senden bir ricam var mı?" şeklinde soruya dönüştürülmüştür.
  - Kaynak: *"“I realize this isn’t very polite, but may I make a request of you?” she said."*
  - Çeviri: *"“Bunun pek kibarca bir istek olmadığını biliyorum, ama senden bir ricam var mı?” dedi."*
- **ANLAM_KAYMASI**: Diyalogdaki cümlelerin sırası tamamen karışmış, konuşmanın akışı bozulmuş ve kaynağı belirsiz bir şekilde "“İlk” eş, öyle mi?" ifadesi eklenmiştir.
  - Kaynak: *"“I have medicines to deliver,” said Maomao, entering the office and taking off her portable medicine cabinet.

“Delivery’s here,” Yo echoed, imitating Maomao.

“Well, well, what a sweet young thing you’ve brought with you today,” said the elderly doctor.

“My name is Yo,” she told him. “I just started this year.” Evidently this was the first time they had met.

“We don’t get a lot of young ladies around here. Too many rough-and-tumble types.”

“I’m here,” Maomao said stiffly.

“You and Miss Chue are special cases. In flower terms, I would say you’re an obako and a dandelion.”

So she was in the same category as Chue now?"*
  - Çeviri: *"“Teslimat geldi,” diye yankıladı Yo, Maomao’yu taklit ederek.

“Ben buradayım,” dedi Maomao sert bir şekilde.

“İlk” eş, öyle mi?

“İlaç teslimatım var,” dedi Maomao, odaya girip taşınabilir ilaç dolabını omuzlarından indirirken.

“Vay canına, bugün yanına ne tatlı bir kız getirmişsin,” dedi yaşlı doktor.

“Adım Yo,” dedi ona. “Bu yıl yeni başladım.” Görünüşe göre ilk kez tanışıyorlardı.

“Burada pek genç hanımefendi görmüyoruz. Çoğu zaman kaba saba tiplerle uğraşıyoruz.”

“Sen ve Chue Hanım istisnasınız. Çiçeklerle kıyaslayacak olursam, sen bir obako, o da bir karahindiba olursun.”

Yani artık Chue ile aynı kategoride miydi?"*
- **ANLAM_KAYMASI**: Rahatlama belirten "Phew" (Of, şükür) ünlemi, "İyi ki" (neyse ki) şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“Phew... Sorry about that. Thanks for the help,” Maomao said."*
  - Çeviri: *"“İyiki... Özür dilerim. Yardımın için teşekkürler,” dedi Maomao."*

## Bölüm 4: Chapter 3: Reassignment — 2 sorun
- **ANLAM_KAYMASI**: "I haven't seen you since..." ifadesindeki "you" (seni) nesnesi yanlış anlaşılarak "senden beri" şeklinde çevrilmiş ve ortaya anlamsız bir Türkçe cümle çıkmıştır. Doğrusu "Seni... dünden beri görmemiştim" olmalıdır.
  - Kaynak: *"“I haven’t seen you since...yesterday,” she said."*
  - Çeviri: *"“Dün... senden beri görmedim,” dedi."*
- **ANLAM_KAYMASI**: "They rode along" (yol aldılar/arabayla gittiler) ifadesi, sürgün edilmek veya zorla götürülmek anlamına gelen "sürüldüler" kelimesiyle yanlış çevrilmiştir.
  - Kaynak: *"They rode along for thirty minutes until they arrived at a mansion on the outskirts of the capital."*
  - Çeviri: *"Otuz dakika boyunca sürüldüler ve başkentin dışındaki bir konakta indiler."*

## Bölüm 8: Chapter 7: A Man’s Romance — 2 sorun
- **ANLAM_KAYMASI**: Çevirinin bu kısmında ciddi bir teknik bozulma gerçekleşmiş; diyaloglar birbirine girmiş, kaynakta olmayan kelimeler eklenmiş, metin mükerrer şekilde tekrarlanmış ve en sonunda yarım kalmıştır.
  - Kaynak: *"“Military matters aren’t really my area of expertise,” Maomao said, frowning at what turned out to be quite a different topic from what she had expected. “Help me out.”
“Oh, at least try to think it through.”
“I told you, it’s not my field.”
The two of them chatted away, their mortars grinding and the powder collecting.
“Okay, okay. Your hint is: meat.”"*
  - Çeviri: *"“Oh, en azından düşünmeye çalış.”
“Sana söyledim, bu benim alanım değil.”
“Tamam, tamam. İpucu: et.”
“Kepek...”
“Sindirim...”
“Demek ki fark etmiş.”
“Kıdemlilerine karşı biraz fazla talebeksin, ha? Başka ilginç bir şeyim olup olmadığını bilmiyorum...” Uzun Kıdemli havanını ve havan elini çalıştırırken düşünceli bir ses çıkardı. Alt kademesinden gelen bir isteği yerine getirmek isteyen iyi bir kıdemliydi. “Eh, et ve balıken bahsetmişken...”
“Evet? Aklına bir şey mi geldi?” Maomao'nun gözleri daha da parladı.
“Geldi. Ama vaktimiz varken, bunu soru-cevap şeklinde yapalım mı?”
“Oh, en azından düşünmeye çalış.”
“Sana söyledim, bu benim alanım değil.”
“Tamam, tamam. İpucu: et.”
“Kepek...”
“Sindirim...”
“Demek ki fark etmiş.”
“Soru-cevap, efendim?” Maomao başını salladı; tartışmada “kazandığına” ya da “kaybettiğine” dair endişesi yoktu, bu yüzden cevapları bilmediği ortaya çıksa bile gayet memnundu.
“Tamam, başlayalım. Çok uzun zaman önce, topraklarımız başka bir ülkeye karşı savaştı ve berbat bir şekilde yenildi. Orduyu komuta eden asker, son derece keskin zekâlı, stratejik durumu her zaman kavrayıp akıllıca kararlar veren bir adamdı. Keşifçiler göndererek düşman kampını inceletti ve zafer şansının yüksek olduğunu belirledi, bu temele dayanarak savaşa girdi. Kazanacağından o kadar eminsen, neden ka"*
- **ATLANMIŞ**: Kaynak metnin sonundaki Maomao'nun et ipucu üzerine düşündüğü paragraflar Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"“Meat?” Maomao cocked her head and hmmed thoughtfully.
Meat, meat, meat... Maybe he means they were caught in some unique trap or something?
It seemed unlikely that actual meat was the issue at hand."*
