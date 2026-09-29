# QA Raporu — knh-15

**Toplam 43 şüpheli nokta bulundu (17/24 bölüm başarıyla tarandı, 7 bölüm denetlenemedi).**

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

## Bölüm 5: Chapter 4: Drug Trials — 4 sorun
- **ANLAM_KAYMASI**: Metnin geçtiği dönemde telefon olmadığı ve Maomao'nun Lahan'ı telefonla araması değil, yanına çağırması kastedildiği için 'call' kelimesi 'aramak' olarak yanlış çevrilmiştir.
  - Kaynak: *"Which did not mean she was going to call him."*
  - Çeviri: *"Bu, onu araması gerektiği anlamına gelmiyordu."*
- **ANLAM_KAYMASI**: 'Master Physician' ifadesi saygı belirten bir hitap olup 'Hekim Efendi' veya 'Usta Hekim' olarak çevrilmelidir; 'Başhekim' (Chief Physician) unvanı bu karakter için tıbbi hiyerarşi açısından yanlıştır.
  - Kaynak: *"“Master Physician,” she started."*
  - Çeviri: *""Başhekim," diye başladı."*
- **ANLAM_KAYMASI**: 'so they wouldn't get in her way' (elbise kollarının ona engel olmaması için) ifadesi 'kollarının arasına girmemesi için' şeklinde anlamca hatalı çevrilmiştir.
  - Kaynak: *"She’d brought a tie for her sleeves so they wouldn’t get in her way."*
  - Çeviri: *"Kollarının arasına girmemesi için bir bağ getirmişti."*
- **ANLAM_KAYMASI**: İngilizcedeki 'stomach' kelimesi burada karın (abdomen) anlamında kullanılmıştır. Apandisit/kör bağırsak ameliyatında mide organı değil karın açılacağı için 'mide' çevirisi tıbbi açıdan hatalıdır.
  - Kaynak: *"“You could open their stomach and take out the filth,” Short Senior said."*
  - Çeviri: *""Mide açılıp pislik çıkarılabilir," dedi Kısa Kıdemli."*

## Bölüm 6: Chapter 5: A Book Restored — 4 sorun
- **ANLAM_KAYMASI**: 'Just the other day' (daha geçen gün/geçenlerde) ifadesi 'az önce' olarak yanlış çevrilmiştir.
  - Kaynak: *"Just the other day, they had found the book this ancestor had left behind."*
  - Çeviri: *"Az önce, bu atadan geriye kalan kitabı bulmuşlardı."*
- **ANLAM_KAYMASI**: 'Calluses' (nasırlar) kelimesi yanlış bir şekilde 'korkuluklar' olarak çevrilmiştir.
  - Kaynak: *"I see calluses."*
  - Çeviri: *"Korkuluklar görüyorum."*
- **ANLAM_KAYMASI**: Metindeki 'calluses' (nasırlar) kelimesi 'korkuluklar' olarak yanlış çevrilmiştir.
  - Kaynak: *"Just as those who wielded the sword could develop calluses on their hands, so, too, could those who wielded the brush get them on their fingers. Tianyu’s calluses, however, probably came not from a brush but from a scalpel."*
  - Çeviri: *"Tıpkı kılıç kullananların ellerinde korkuluk oluşabileceği gibi, fırça kullananların da parmaklarında korkuluk oluşabilirdi. Ancak Tianyu’nun korkulukları, muhtemelen bir fırçadan değil, bir cerrahi bisturiden geliyordu."*
- **ANLAM_KAYMASI**: 'since I saw you last' (seni son gördüğümden beri) ifadesi 'beni son gördüğümde' şeklinde yanlış çevrilerek anlam kaymasına yol açmıştır.
  - Kaynak: *"“Have you learned to read minds since I saw you last, Niangniang?”"*
  - Çeviri: *"“Beni son gördüğümde telepati mi öğrendin, Niangniang?”"*

## Bölüm 7: Chapter 6: The Patient — 2 sorun
- **ANLAM_KAYMASI**: "on his flank" (vücudunun yan tarafında/böğründe) ifadesi "Yanında" şeklinde yanlış çevrilmiştir. Damga Jinshi'nin vücudundadır, yanında duran bir nesne değildir.
  - Kaynak: *"She was sure the red flower brand must still be on his flank."*
  - Çeviri: *"Yanında o kırmızı çiçek damgasının hâlâ olmasından emindi."*
- **ANLAM_KAYMASI**: "Thinking that I might be more knowledgeable" (kendimin daha bilgili olabileceğimi düşünerek) ifadesi "benden daha bilgili olabileceğimi" şeklinde çevrilerek anlamsız ve hatalı bir anlatım oluşturmuştur.
  - Kaynak: *"“Thinking that I might be more knowledgeable in the matter about which our little cat wishes to learn, I took the liberty of coming here myself.”"*
  - Çeviri: *""Küçük kedimizin öğrenmek istediği konuda benden daha bilgili olabileceğimi düşünerek, buraya kendim gelme cesaretini gösterdim.""*

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

## Bölüm 9: Chapter 8: Anesthesia
*(Denetlenemedi.)*

## Bölüm 10: Chapter 9: To Everyone a Purpose — 4 sorun
- **ANLAM_KAYMASI**: "Chou-u" karakterinin adı yanlışlıkla "Chue" olarak çevrilmiştir. Chue hikayedeki başka bir karakterdir.
  - Kaynak: *"Chou-u, the little troublemaker of the pleasure district, should have been here by all rights as well, but as a side effect of the resurrection drug he had lost his memory, and therefore could walk a different path from these other children."*
  - Çeviri: *"Zevk mahallesinin küçük belası Chue, normal şartlarda burada olmalıydı; ancak diriltme ilacının bir yan etkisi olarak hafızasını kaybetmişti ve bu yüzden diğer çocuklardan farklı bir yol izliyordu."*
- **İNGİLİZCE_KALINTI**: "modest" kelimesi Türkçe çeviride "Modest" olarak İngilizce bırakılmıştır.
  - Kaynak: *"It had a modest table and four chairs; an attendant prepared tea and then promptly left."*
  - Çeviri: *"Modest bir masa ve dört sandalye vardı; bir hizmetli çay hazırladı ve hemen çıktı."*
- **ANLAM_KAYMASI**: "wasn't biting" (ilgilenmedi, yemi yutmadı) deyimi "hiç almadı" şeklinde yanlış ve anlamsız çevrilmiştir.
  - Kaynak: *"“I think this is a road you’d be better off not taking.” Suirei wasn’t biting, not even a little."*
  - Çeviri: *"“Bence bu, gitmemeniz gereken bir yol.” Suirei hiç almadı, en ufak bir şekilde bile."*
- **ANLAM_KAYMASI**: Ameliyat için geliştirilen "anesthetic" (anestezi/anestezik) kelimesi "uyuşturucu" olarak yanlış çevrilmiştir.
  - Kaynak: *"“Who do you propose to use this anesthetic on?”"*
  - Çeviri: *"“Bu uyuşturucuyu kimin üzerinde kullanmayı öneriyorsunuz?”"*

## Bölüm 11: Chapter 10: Gyouyoh
*(Denetlenemedi.)*

## Bölüm 12: Chapter 11: The Special Unit
*(Denetlenemedi.)*

## Bölüm 13: Chapter 12: Explanation and Agreement — 2 sorun
- **ATLANMIŞ**: Bölümün ilk cümlesi Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"They didn’t know where word of the surgery had leaked from."*
- **ANLAM_KAYMASI**: 'Peony' (şakayık) kelimesi 'gelincik' (poppy) olarak yanlış çevrilmiştir. Şakayık, İmparatoriçe Gyokuyou'nun simgesidir.
  - Kaynak: *"“We’d like to ask you to come with us,” one of the men said, showing her a peony crest."*
  - Çeviri: *""Sizinle gelmenizi rica ediyoruz," dedi erkeklerden biri, ona bir gelincik arması göstererek."*

## Bölüm 14: Chapter 13: Sowing Seeds — 3 sorun
- **ANLAM_KAYMASI**: Cümlelerin sırası karıştırılmış ve araya kaynakta olmayan 'İyi, iyi.' ifadesi eklenmiştir. Bu durum, karşılaştırma yapılmadan 'Ana fark şuydu' denilmesine yol açarak mantık akışını bozmuş ve anlam kaymasına sebep olmuştur.
  - Kaynak: *"The former emperor’s reprehensible behavior bore a certain resemblance to something that had led to the rebellion of the Shi clan. That episode had been in some ways a revenge drama staged by Shenmei, whom the former emperor had spurned.

The main difference was that after they learned of Anshi’s pregnancy, her family had swiftly sent her older sister out of the rear palace."*
  - Çeviri: *"Ana fark şuydu: Anshi'nin hamile olduğunu öğrendiklerinde, ailesi ablasını hızla arka saraydan çıkarmıştı.

"İyi, iyi."

Önceki imparatorun kabul edilemez davranışları, Shi Klanı'nın isyanına yol açan olaylara bir benzerlik taşıyordu. O hadise, bir bakıma, önceki imparatorun reddettiği Shenmei'nin sahnelediği bir intikam dramasıydı."*
- **ANLAM_KAYMASI**: İngilizcedeki 'great-niece' (kız/erkek kardeşin torunu, yeğen torunu) ifadesi 'torun kızı' (granddaughter) olarak çevrilmiştir. Bu durum, karakteri Dul İmparatoriçe'nin öz torunu yaparak soy ağacında ciddi bir anlam hatasına yol açmaktadır.
  - Kaynak: *"She was the grandniece of the Empress Dowager’s half-brother, Hao—and hence also the great-niece of the Empress Dowager herself."*
  - Çeviri: *"Dul İmparatoriçe'nin üvey erkek kardeşi Hao'nun torun kızı ve dolayısıyla Dul İmparatoriçe'nin kendisinin de torun kızıydı."*
- **TUTARSIZ_TERİM**: Metnin önceki kısımlarında 'Pure Consort' terimi 'Saflık Konsortu', 'Precious Consort' terimi ise 'Değerli Konsort' olarak çevrilmişken, burada sırasıyla 'Saf Eş' ve 'Değerli Eş' olarak çevrilerek tutarsızlık yaratılmıştır.
  - Kaynak: *"Which is why we don’t make her the Pure Consort, but the Precious one."*
  - Çeviri: *"Bu yüzden onu Saf Eş değil, Değerli Eş yapıyoruz."*

## Bölüm 15: Chapter 14: The Patient’s Consent
*(Denetlenemedi.)*

## Bölüm 16: Chapter 15: Confession—The Surface
*(Denetlenemedi.)*

## Bölüm 17: Chapter 16: Confession—The Secret — 5 sorun
- **ATLANMIŞ**: Cümlenin Türkçe çevirisi metinde tamamen atlanmıştır.
  - Kaynak: *"She’d screwed it all up, thought Ah-Duo."*
- **ANLAM_KAYMASI**: "if Maomao would be hemmed in" (Maomao'nun da köşeye sıkışıp sıkışmayacağını) ifadesi "Maomao sıkışıp kaldığında" şeklinde yanlış çevrilerek kesinlik bildiren bir zaman zarfına dönüştürülmüştür.
  - Kaynak: *"She wanted to know what choice Yue would make, if Maomao would be hemmed in, entrapped as Ah-Duo had been."*
  - Çeviri: *"Maomao sıkışıp kaldığında, tıpkı Ah-Duo'nun sıkışıp kaldığı gibi, Yue'nin ne seçim yapacağını bilmek istiyordu."*
- **ANLAM_KAYMASI**: "Excuse myself" (müsaade istemek, ayrılmak) ifadesi kelimesi kelimesine "kendimi dışarıda bırakmak" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“I suppose I should excuse myself, then.”"*
  - Çeviri: *""Sanırım kendimi dışarıda bırakmalıyım.""*
- **ANLAM_KAYMASI**: "Take dictation" (söylenenleri yazmak/not etmek) ifadesi, tarihsel bağlama uymayacak şekilde "daktilo tutmak" olarak son derece hatalı çevrilmiştir.
  - Kaynak: *"“Don’t ask me to take dictation on your will."*
  - Çeviri: *""Vasiyetin için bana daktilo tutmamı isteme."*
- **ANLAM_KAYMASI**: Diyalog sırası tersine dönmüş ve araya kaynakta olmayan "Sen bir yük değilsin." şeklinde uydurma bir cümle eklenmiştir.
  - Kaynak: *"“I suppose you assumed that even if you had set up the Crown Prince instead of Yue, I would be there while he was young.”

“I did. Because you are honest and faithful.”"*
  - Çeviri: *""Evet. Çünkü sen dürüst ve sadıksın."

"Sen bir yük değilsin."

"Sanırım, Yue yerine Veliaht Prens'i tahta çıkarsam, onun gençlik yıllarında da yanında olacağımı varsaydın.""*

## Bölüm 18: Chapter 17: Anxiety
*(Denetlenemedi.)*

## Bölüm 19: Chapter 18: Before the Surgery — 2 sorun
- **ATLANMIŞ**: Bölümün ilk cümlesi olan 'The procedure would begin at noon.' Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"The procedure would begin at noon."*
- **ANLAM_KAYMASI**: Metindeki 'will' kelimesi İmparator'un arkasında bıraktığı 'vasiyet' anlamında kullanılmışken, çeviride 'irade' (istek/kararlılık) olarak yanlış aktarılmıştır.
  - Kaynak: *"She didn’t know what kind of will he had left, but she was determined that it wouldn’t be necessary."*
  - Çeviri: *"Ne tür bir iradeye sahip olduğunu bilmiyordu, ama buna ihtiyaç duyulmaması gerektiğine kararlıydı."*

## Bölüm 20: Chapter 19: During the Surgery — 3 sorun
- **ATLANMIŞ**: Ameliyatın başladığını belirten bu giriş cümlesi Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"The surgery began."*
- **ANLAM_KAYMASI**: 'must have overwhelmed him' (onu sarsmış/bunalıma sokmuş olmalıydı) şeklindeki çıkarım ifadesi, çeviride 'onu ezmeliydi' denilerek bir gereklilik/zorunluluk gibi yanlış aktarılmıştır.
  - Kaynak: *"He’d stuck a scalpel into Dr. Liu’s dominant hand, even if he hadn’t meant to, and the shock of doing something so awful must have overwhelmed him."*
  - Çeviri: *"Ameliyat odasındaki yere yığılan adam, birinci asistandı; üst düzey hekimlerden biriydi. İstese de istemese de bistürüyü Dr. Liu’nun baskın eline saplamıştı ve bu kadar korkunç bir şey yaptığı şoku onu ezmeliydi."*
- **ANLAM_KAYMASI**: Buradaki 'nerves' (heyecan, gerginlik, korku) kelimesi 'sinir' (öfke, hiddet) olarak yanlış çevrilmiştir.
  - Kaynak: *"His hand never shook from nerves."*
  - Çeviri: *"Eli sinirinden titremiyordu."*

## Bölüm 21: Chapter 20: After the Surgery
*(Denetlenemedi.)*

## Bölüm 22: Epilogue — 4 sorun
- **ATLANMIŞ**: Bölüm başlığı olan 'Epilogue' (Sonsöz) çeviride atlanmıştır.
  - Kaynak: *"Epilogue"*
- **ANLAM_KAYMASI**: 'He said to just leave him' (onu kendi haline bırakmamızı söyledi) ifadesi, 'Bırakın gitsin, dedi' şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“I’m very sorry. He said to just leave him—that he couldn’t afford to sleep yet,” Basen said apologetically."*
  - Çeviri: *"“Çok özür dilerim. Bırakın gitsin, dedi — henüz uyuyamayacağını söyledi,” dedi Basen özür dileyerek."*
- **ANLAM_KAYMASI**: 'leave enough for her' (kendisine de kalacak kadar bırakmanızı) ifadesi, çeviride 'size yetecek kadar' şeklinde yanlış aktarılmıştır.
  - Kaynak: *"“Miss Maomao, Miss Chue hopes you’ll leave enough for her,” Chue said—she was even hungrier than Maomao."*
  - Çeviri: *"“Maomao Hanım, Chue Hanım'ın size yetecek kadar bırakmanızı umuyor,” dedi Chue — Maomao'dan bile daha açtı."*
- **ANLAM_KAYMASI**: 'slurped' (höpürdeterek yedi) kelimesi 'emerek yedi' şeklinde yanlış ve tuhaf bir şekilde çevrilmiştir.
  - Kaynak: *"“I see. I’m not suited to be emperor, you say?” Jinshi slurped some noodles, looking oddly happy."*
  - Çeviri: *"“Anlıyorum. İmparator olmaya uygun değilim, öyle mi?” Jinshi, garip bir mutlulukla noodle'ları emerek yedi."*
