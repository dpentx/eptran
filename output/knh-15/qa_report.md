# QA Raporu — knh-15

**Toplam 50 şüpheli nokta bulundu (20/24 bölüm başarıyla tarandı, 4 bölüm denetlenemedi).**

*Bu bir OTOMATİK ÖNERİ listesidir, kesin doğru kabul etmeyin — her maddeyi kaynakla birlikte kendiniz kontrol edin. Bazı işaretlemeler yanlış pozitif olabilir (bkz. script docstring'i).*

## Bölüm 1: Character Profiles — 1 sorun
- **ATLANMIŞ**: Karakter tanıtım bölümünün başlığı olan 'Character Profiles' çeviride atlanmıştır.
  - Kaynak: *"Character Profiles"*

## Bölüm 2: Chapter 1: The Selection Exam
*(Denetlenemedi.)*

## Bölüm 3: Chapter 2: Smallpox and Chickenpox — 2 sorun
- **ANLAM_KAYMASI**: Diyalog sırası tamamen karışmış ve kaynakta hiç olmayan '“İlk” eş, öyle mi?' ifadesi eklenmiştir.
  - Kaynak: *"“I have medicines to deliver,” said Maomao, entering the office and taking off her portable medicine cabinet.

“Delivery’s here,” Yo echoed, imitating Maomao.

“Well, well, what a sweet young thing you’ve brought with you today,” said the elderly doctor.

“My name is Yo,” she told him. “I just started this year.” Evidently this was the first time they had met.

“We don’t get a lot of young ladies around here. Too many rough-and-tumble types.”

“I’m here,” Maomao said stiffly."*
  - Çeviri: *"“Teslimat geldi,” diye yankıladı Yo, Maomao’yu taklit ederek.

“Ben buradayım,” dedi Maomao sert bir şekilde.

“İlk” eş, öyle mi?

“İlaç teslimatım var,” dedi Maomao, odaya girip taşınabilir ilaç dolabını omuzlarından indirirken.

“Vay canına, bugün yanına ne tatlı bir kız getirmişsin,” dedi yaşlı doktor.

“Adım Yo,” dedi ona. “Bu yıl yeni başladım.” Görünüşe göre ilk kez tanışıyorlardı."*
- **ATLANMIŞ**: Kaynakta yer alan 'Too many rough-and-tumble types.' ve 'You and Miss Chue are special cases.' cümleleri Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"“We don’t get a lot of young ladies around here. Too many rough-and-tumble types.”

“I’m here,” Maomao said stiffly.

“You and Miss Chue are special cases. In flower terms, I would say you’re an obako and a dandelion.”"*
  - Çeviri: *"“Burada pek genç hanımefendi görmüyoruz. Çiçeklerle kıyaslayacak olursam, sen bir obako, o da bir karahindiba olursun.”"*

## Bölüm 4: Chapter 3: Reassignment
*(Denetlenemedi.)*

## Bölüm 5: Chapter 4: Drug Trials — 2 sorun
- **TUTARSIZ_TERİM**: "Master Physician" ifadesi burada "Hekim Efendi" olarak çevrilmişken, bir sonraki cümlede "Başhekim" olarak çevrilerek tutarsızlık yaratılmıştır.
  - Kaynak: *"“Master Physician,” she started."*
  - Çeviri: *"Hekim Efendi," diye başladı."*
- **ANLAM_KAYMASI**: "Typhlitis" (tiflitis / kör bağırsak iltihabı) terimi "apandisit" olarak yanlış çevrilmiştir. Metinde hastalığın kör bağırsak (cecum) iltihabı olduğu açıkça belirtilmektedir.
  - Kaynak: *"“Typhlitis, maybe?” Maomao suggested."*
  - Çeviri: *"“Belki apandisit?” diye önerdi Maomao."*

## Bölüm 6: Chapter 5: A Book Restored
*(Denetlenemedi.)*

## Bölüm 7: Chapter 6: The Patient — 3 sorun
- **ANLAM_KAYMASI**: "Man" ifadesi burada "Yahu/Dostum" anlamında bir ünlem olarak kullanılmıştır, "Adam" şeklinde çevrilmesi anlam kaymasına yol açmıştır.
  - Kaynak: *"“Man, I’m hungry too,” Tianyu said as he and Maomao left the room."*
  - Çeviri: *""Adam, ben de açım," dedi Tianyu, Maomao ile birlikte odayı terk ederken."*
- **ANLAM_KAYMASI**: "It's all good" ifadesi "Sorun değil/Gerek yok" anlamına gelir, "Olmaz" şeklinde çevrilmesi anlamı bozmuştur.
  - Kaynak: *"“It’s all good. I’ve been sleeping in the medical office lately anyway.”"*
  - Çeviri: *""Olmaz, son günlerde zaten tıp bürosunda uyuyorum.""*
- **ANLAM_KAYMASI**: "didn't assume ... was an actual answer" ifadesi "kendi görüşünün kesin bir yanıt olduğunu varsaymıyordu" anlamına gelir. Türkçe çevirideki çift olumsuzluk ("olmadığını varsaymadı") tam tersi bir anlam yaratmaktadır.
  - Kaynak: *"Maomao didn’t assume her opinion was an actual answer, however, so what else was she supposed to say?"*
  - Çeviri: *"Maomao, görüşünün gerçek bir cevap olmadığını varsaymadı, peki ne demeliydi?"*

## Bölüm 8: Chapter 7: A Man’s Romance — 2 sorun
- **ANLAM_KAYMASI**: Çeviri metnine kaynakta hiç var olmayan "Kepek...", "Sindirim...", "Demek ki fark etmiş." gibi ilgisiz ifadeler eklenmiş ve metin yapısı ciddi şekilde bozulmuştur.
  - Kaynak: *"“I did. But since we’ve got the time, how about we do this by question and answer?”

“Question and answer, sir?” Maomao nodded; she wasn’t concerned about whether she “won” or “lost” the discussion, so she was more than happy even if it turned out she didn’t know the answers."*
  - Çeviri: *""Kepek..."

Sindirim...

Demek ki fark etmiş."*
- **ATLANMIŞ**: Çeviri metni "neden ka" ifadesiyle yarım kalmış, kaynak metnin sonundaki diyaloglar ve paragraflar tamamen atlanmıştır.
  - Kaynak: *"If he was so sure he would win, why did he lose?”

“Military matters aren’t really my area of expertise,” Maomao said, frowning at what turned out to be quite a different topic from what she had expected. “Help me out.”

“Oh, at least 
try
 to think it through.”

“I told you, it’s not my field.”

The two of them chatted away, their mortars grinding and the powder collecting.

“Okay, okay. Your hint is: meat.”

“Meat?” Maomao cocked her head and 
hmm
ed thoughtfully.

Meat, meat, meat... Maybe he means they were caught in some unique trap or something?

It seemed unlikely that actual meat was the issue at hand."*
  - Çeviri: *"Kazanacağından o kadar eminsen, neden ka"*

## Bölüm 9: Chapter 8: Anesthesia — 2 sorun
- **ANLAM_KAYMASI**: Kaynak metinde Luomen, Maomao'nun kendisine normalde bu şekilde hitap etmediğini belirtirken ('Bana böyle hitap etmiyorsun, değil mi?'), Türkçe çeviride tam tersi bir anlam çıkarılarak 'Beni öyle çağırıyorsun, öyle mi?' denmiştir.
  - Kaynak: *"“That’s not what you call me, is it?”"*
  - Çeviri: *"Beni öyle çağırıyorsun, öyle mi?"*
- **ANLAM_KAYMASI**: Maomao'nun Luomen için kullandığı ve 'İhtiyar' anlamına gelen 'Pops' lakabı 'Amca' olarak yanlış çevrilmiştir.
  - Kaynak: *"“Pops? What are you doing here?” Maomao asked."*
  - Çeviri: *""Amca? Burada ne işin var?" diye sordu Maomao."*

## Bölüm 10: Chapter 9: To Everyone a Purpose
*(Denetlenemedi.)*

## Bölüm 11: Chapter 10: Gyouyoh — 5 sorun
- **ATLANMIŞ**: Bölüm başlığı ve giriş paragrafı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 10: Gyouyoh

From the time he was born, everything had been decided for Gyouyoh: what he would do, what he would be. As the emperor’s only son, that was the position he had been given."*
- **ANLAM_KAYMASI**: Kaynakta 'Anshi'nin ağabeyi/büyük erkek kardeşi' ifadesi geçerken, çeviride 'Anshi'nin büyük oğlu' denilerek amca karakteri Gyouyoh'un kardeşi gibi gösterilmiş ve ciddi bir anlam kayması oluşmuştur.
  - Kaynak: *"His uncle: that was to say, the older brother of Gyouyoh’s mother, Anshi."*
  - Çeviri: *"Amcası: yani Gyouyoh’un annesi Anshi’nin büyük oğlu."*
- **ANLAM_KAYMASI**: Gyouyoh, Hao'ya 'amcam olduğunuz için' demesi gerekirken çeviride 'amcanız olduğunuz için' denilerek anlam bozulmuştur.
  - Kaynak: *"“Mm. So you propose that because you are my uncle, you can interrupt my lunch?”"*
  - Çeviri: *"“Mm. Yani amcanız olduğunuz için öğle yemeğimi bölebileceğinizi mi öneriyorsunuz?”"*
- **ŞAHIS_UYUŞMAZLIĞI**: Gaoshun, Gyouyoh'a ilacı içmesi gerektiğini söylerken (2. tekil/çoğul şahıs), çeviride 1. çoğul şahıs ('zorunluyuz') kullanılarak şahıs uyuşmazlığı yapılmıştır.
  - Kaynak: *"“I’m afraid you must.”"*
  - Çeviri: *"“Maalesef, zorunluyuz.”"*
- **ANLAM_KAYMASI**: Paragrafların sırası karıştığı için İmparator, Hao henüz Lihua'dan bahsetmeden önce Lihua hakkında soru sormakta ve diyalog akışında mantık hatası/anlam kayması oluşmaktadır.
  - Kaynak: *"“Lihua is an upper consort. Is there some sort of problem?” the Emperor asked."*
  - Çeviri: *"“Lihua bir yüksek eş. Bir sorun mu var?” diye sordu İmparator."*

## Bölüm 12: Chapter 11: The Special Unit — 2 sorun
- **ATLANMIŞ**: Bölüm başlığı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 11: The Special Unit"*
- **ANLAM_KAYMASI**: Bu bölümdeki paragraflar ve diyaloglar Türkçe çeviride tamamen birbirine karışmış ve sırası bozulmuştur. Bu durum, henüz yüzde seksen başarı oranı telaffuz edilmeden karakterlerin yüzde yirmilik başarısızlıktan bahsetmesi gibi mantıksal tutarsızlıklara yol açmıştır.
  - Kaynak: *"Kada’s Book, sitting before Dr. Liu, contained detailed drawings of the appendix. The fact that the book was sitting there suggested just how much help it had been.

“Has this surgery been tested?” someone asked.

“Yes, it has. We’ve been watching the patients’ progress, and it appears to have an eighty percent success rate.”

“What happened to the other twenty percent?”

That was the more important subject versus the cases that succeeded.

“In ten percent, the appendix had already burst, causing peritonitis. We removed the appendix and tried to clean out as much of the filth as we could, but the condition ultimately claimed their lives. In the remaining ten percent, toxins entered via the surgical incision and caused infection, and the patient died without ever fully recovering.”

Twenty percent. Were those odds high, or low?

It’s not a very comforting number, that’s for sure. Yet at the same time, it was a far greater success rate than had been possible with the methods available before this."*
  - Çeviri: *""Bu ameliyat test edildi mi?" diye sordu biri.

"Diğer yüzde yirmi ne oldu?"

Yüzde yirmi. Bu olasılık yüksek miydi, yoksa düşük mü?

Dr. Liu'nün önünde duran Kada'nın Kitabı, apendisin detaylı çizimlerini içeriyordu. Kitabın orada durması, ne denli büyük bir yardım olduğunu açıkça ortaya koyuyordu.

"Evet, denendi. Hastaların ilerlemesini izledik ve yüzde seksen başarı oranına ulaştığı görülüyor."

Başarılı vakalarla kıyaslandığında, asıl önemli konu buydu.

"Yüzde onunda apendis zaten patlamıştı ve peritonite yol açmıştı. Apendisi çıkardık ve mümkün olduğunca çok pisliği temizlemeye çalıştık, ancak durum sonunda canlarını aldı. Kalan yüzde onda ise toksinler cerrahi kesiden içeri sızıp enfeksiyona neden oldu ve hasta hiç tam olarak iyileşmeden hayatını kaybetti."

Oldukça teselli edici bir rakam sayılmazdı, bu kesin. Yine de, bundan önceki yöntemlerle elde edilebilecek başarı oranından çok daha yüksekti."*

## Bölüm 13: Chapter 12: Explanation and Agreement — 3 sorun
- **ATLANMIŞ**: Kaynaktaki ilk cümle Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"They didn’t know where word of the surgery had leaked from."*
- **ANLAM_KAYMASI**: 'Your old auntie' ifadesindeki 'old' (yaşlı/ihtiyar) kelimesi yanlış bir şekilde 'eski' (former) olarak çevrilmiştir.
  - Kaynak: *"“Your old auntie has to shepherd her strength in these latter years of her life,” the woman went on."*
  - Çeviri: *"“Eski teyzeniz, hayatının bu son yıllarında gücünü korumak zorunda,” diye devam etti kadın."*
- **İNGİLİZCE_KALINTI**: 'junior' kelimesi Türkçeye çevrilmeden, Türkçe çekim eki alarak 'juniörü' şeklinde İngilizce bırakılmıştır.
  - Kaynak: *"“What do you suppose this is about?” Maomao’s junior, Changsha, asked with a mystified look."*
  - Çeviri: *"“Bu ne hakkında olabilir?” diye sordu Maomao'nun juniörü Changsha, şaşkın bir ifadeyle."*

## Bölüm 14: Chapter 13: Sowing Seeds — 3 sorun
- **ATLANMIŞ**: Bölümün giriş cümlesi Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Jinshi was getting a headache from having this conversation for the umpteenth time."*
- **ANLAM_KAYMASI**: Çeviride bu iki paragrafın sırası tamamen tersine çevrilerek mantık akışı bozulmuş ve araya kaynakta olmayan "İyi, iyi." ifadesi eklenmiştir.
  - Kaynak: *"The former emperor’s reprehensible behavior bore a certain resemblance to something that had led to the rebellion of the Shi clan. That episode had been in some ways a revenge drama staged by Shenmei, whom the former emperor had spurned.

The main difference was that after they learned of Anshi’s pregnancy, her family had swiftly sent her older sister out of the rear palace."*
  - Çeviri: *"Ana fark şuydu: Anshi'nin hamile olduğunu öğrendiklerinde, ailesi ablasını hızla arka saraydan çıkarmıştı.

"İyi, iyi."

Önceki imparatorun kabul edilemez davranışları, Shi Klanı'nın isyanına yol açan olaylara bir benzerlik taşıyordu. O hadise, bir bakıma, önceki imparatorun reddettiği Shenmei'nin sahnelediği bir intikam dramasıydı."*
- **ANLAM_KAYMASI**: Kaynak metinde Jinshi, Basen'in (he) henüz kimseyi yumruklamamış olmasına sevinirken, çeviride 'kimsenin yumruk atmadığına' (yani kimsenin kendilerine vurmadığına) sevindiği şeklinde yanlış aktarılmıştır.
  - Kaynak: *"Jinshi was just happy he hadn’t punched anybody yet."*
  - Çeviri: *"Jinshi, henüz kimsenin yumruk atmadığı için şükrediyordu."*

## Bölüm 15: Chapter 14: The Patient’s Consent — 3 sorun
- **ANLAM_KAYMASI**: "ultimately" (en nihayetinde/sonuç olarak) kelimesi "en son" (lastly) şeklinde yanlış çevrilmiştir.
  - Kaynak: *"It was always ultimately the patient who was least happy to have surgery."*
  - Çeviri: *"Her zaman en son, ameliyat olmaktan en mutsuz olan hastaydı."*
- **ANLAM_KAYMASI**: "shoring up his feelings of vulnerability" (kırılganlık hislerine karşı kendini desteklemek/güçlendirmek) ifadesi, "kırılganlık duygularını pekiştirmek" (kırılganlığını artırmak) şeklinde tam tersi bir anlamda çevrilmiştir.
  - Kaynak: *"Was he thinking of trying to put his personal affairs in order in hopes of shoring up his feelings of vulnerability prior to surgery?"*
  - Çeviri: *"Ameliyat öncesi kırılganlık duygularını pekiştirmek amacıyla kişisel işlerini düzenlemeye mi çalışıyordu?"*
- **ANLAM_KAYMASI**: "might end up with an ulcer of his own" (kendisi de ülser olabilirdi) ifadesi, Türkçe dil bilgisi hatasıyla birleşerek "kendisi de ülser edebilir" (ülsere sebep olabilir) şeklinde yanlış aktarılmıştır.
  - Kaynak: *"If that process included revealing the secret of Jinshi’s birth, Jinshi might end up with an ulcer of his own."*
  - Çeviri: *"Eğer bu süreç, Jinshi’nin doğum sırrını ifşa etmeyi içeriyorsa, Jinshi’nin kendisi de ülser edebilir."*

## Bölüm 16: Chapter 15: Confession—The Surface — 3 sorun
- **ANLAM_KAYMASI**: Chue'nün kayınpederi (father-in-law) olan Gaoshun için 'kayanbiraderim' ve 'kayınbiraderimin' (brother-in-law) ifadeleri kullanılarak yanlış çeviri yapılmıştır.
  - Kaynak: *"“My father-in-law? Not sure. Probably on guard too. But don’t you worry! I’m a good wife who brings her father-in-law’s favorite snacks so that we won’t get bored no matter how long your chat goes on!”"*
  - Çeviri: *"“Kayanbiraderim? Emin değilim. Muhtemelen o da nöbette. Ama merak etmeyin! İyi bir eşim ve kayınbiraderimin en sevdiği atıştırmalıkları getiriyorum, böylece sohbetiniz ne kadar sürerse sürsün sıkılmayız!”"*
- **ANLAM_KAYMASI**: Cümledeki duraksama belirten 'well' ifadesi 'iyi ki' olarak, 'common sense' (sağduyu) ise 'mantıklı olduğunu varsayması' şeklinde tamamen yanlış çevrilmiştir.
  - Kaynak: *"It looked like it was safe to presume he shared the Ma clan’s sense of what was, well, common sense."*
  - Çeviri: *"Görünüşe göre, Ma Klanı'nın neyin, iyi ki, mantıklı olduğunu varsayması güvenle kabul edilebilirdi."*
- **ANLAM_KAYMASI**: Metnin bu bölümünde paragraflar tamamen birbirine karışmış, kaynakta olmayan ve ileriki diyaloglardan kopup gelen alakasız satırlar araya eklenmiştir.
  - Kaynak: *"Right in the middle of the chairs was a round table with two bottles on it. From what Maomao could see of what was in the glass cups that accompanied them, one bottle contained grape juice, the other plain water. There were four cups in total, and two of them were empty. That fact, and the similar number of places to sit, made it clear that only four people were going to take part in what was to follow.

Maomao let her gaze drift to the Emperor. His facial hair was as imposing as ever, and his pallor seemed decent enough.

No, wait...

It was only being made to look decent. She could see traces of brushstrokes on his skin; they’d used whitening powder that matched his skin tone.

You probably wouldn’t spot it from a distance.

Evidently, they were making every effort to ensure that his advisors wouldn’t notice that there was something wrong. She suspected it was Gaoshun doing most of the work.

She was still observing His Majesty when they heard footsteps."*
  - Çeviri: *"Maomao bakışlarını İmparator'a kaydırdı. Yüzündeki tüyler her zamanki kadar heybetliydi ve solgunluğu yeterince iyi görünüyordu.

Hayır, bekle...

Sadece iyi görünmek için yapılıyordu. Cildinde fırça darbelerinin izlerini görebiliyordu; cilt tonuyla eşleşen bir beyazlatıcı toz kullanmışlardı.

Uzaktan fark etmeyebilirdiniz.

“Meyve suyu,” dedi Jinshi.

“Evet, efendim.”

Olmaz.

“Ah-Duo?”

Sandalyelerin tam ortasında, üzerinde iki şişe duran yuvarlak bir masa vardı. Maomao, bu şişelere eşlik eden cam bardakların içindekileri görebildiği kadarıyla, birinin üzüm suyu, diğerinin ise sade su içerdiğini fark etti. Toplamda dört bardak vardı ve ikisi boştu. Bu durum, oturacak yer sayısının da benzer şekilde sınırlı olmasıyla birlikte, devam edecek olan görüşmeye yalnızca dört kişinin katılacağını açıkça ortaya koyuyordu.

Açıkçası, danışmanlarının bir şeylerin ters gittiğini fark etmemesi için her türlü çabayı gösteriyorlardı. Maomao, bu işin büyük kısmını Gaoshun'un üstlendiğini tahmin ediyordu.

Adımlar duyulana kadar Majesteleri'ni gözlemlemeye devam ediyordu."*

## Bölüm 17: Chapter 16: Confession—The Secret — 3 sorun
- **ATLANMIŞ**: Bölümün ilk cümlesinin Türkçe çevirisi metinde tamamen atlanmıştır.
  - Kaynak: *"She’d screwed it all up, thought Ah-Duo."*
- **ANLAM_KAYMASI**: 'Resent' (gücenmek, içerlemek, kırılmak) kelimesi 'nefretle karşılamak' şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“Ah-Duo,” he said. “Do you resent me?”"*
  - Çeviri: *""Ah-Duo," dedi. "Beni nefretle mi karşılıyorsun?""*
- **ANLAM_KAYMASI**: Diyalog sırası tersine dönmüş ve kaynakta olmayan 'Sen bir yük değilsin.' ifadesi eklenerek anlam tamamen bozulmuştur.
  - Kaynak: *"“I suppose you assumed that even if you had set up the Crown Prince instead of Yue, I would be there while he was young.”

“I did. Because you are honest and faithful.”"*
  - Çeviri: *""Evet. Çünkü sen dürüst ve sadıksın."

"Sen bir yük değilsin."

"Sanırım, Yue yerine Veliaht Prens'i tahta çıkarsam, onun gençlik yıllarında da yanında olacağımı varsaydın.""*

## Bölüm 18: Chapter 17: Anxiety — 6 sorun
- **ANLAM_KAYMASI**: Cümlenin anlamı tam tersi şekilde çevrilmiştir. 'Henüz hiçbir şey çözülmemişti' olması gerekirken olumlu fiil kullanılmıştır.
  - Kaynak: *"Nothing had been resolved yet."*
  - Çeviri: *"Henüz hiçbir şey çözülmüştü."*
- **İNGİLİZCE_KALINTI**: İngilizce ifade Türkçe metinde çevrilmeden bırakılmıştır.
  - Kaynak: *"Ah, yes!"*
  - Çeviri: *"Ah, yes!"*
- **ANLAM_KAYMASI**: Paragrafların sırası karıştığı için diyalog akışı tamamen bozulmuş ve anlamsızlaşmıştır. 'Kaygılı mısın?' sorusuna 'Deri grefti mi?' şeklinde alakasız bir cevap verilmektedir.
  - Kaynak: *"“Are you anxious?” She peered at him.

“What else could I possibly be?”"*
  - Çeviri: *"“Kaygılı mısın?” Ona baktı.
“Deri grefti mi?”"*
- **ANLAM_KAYMASI**: Jinshi, bir önceki cümlede başarısız olduğu söylenen yöntem için 'Başarısız olacağı kulağa mantıklı geliyor' (It sounds like it would [fail]) demek isterken, Türkçe çeviride tam tersi şekilde 'İşe yarayacak gibi görünüyor!' denmiştir.
  - Kaynak: *"“It sounds like it would!”"*
  - Çeviri: *"“İşe yarayacak gibi görünüyor!”"*
- **ATLANMIŞ**: Bu iki paragraf Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"You’d think I was on the hunt for his ass!

Other parts would work just as well. She’d just figured the rear was wide enough that it would be easy to harvest from."*
- **ATLANMIŞ**: Bu cümle Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"True, she was probably less worried than Jinshi."*

## Bölüm 19: Chapter 18: Before the Surgery — 2 sorun
- **ATLANMIŞ**: Bölümün en başındaki ilk cümle Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"The procedure would begin at noon."*
- **ANLAM_KAYMASI**: Metnin ilerleyen kısımlarında yer alan 'That's right' (Doğru) ve 'Shortly after?' (Kısa süre sonra mı?) diyalog satırları yanlışlıkla buraya taşınmış ve konuşmanın akışını bozarak anlam kaymasına yol açmıştır.
  - Kaynak: *"“We’re concerned about His Majesty’s status,” Tall Senior said.

“Cut to the chase.”

From the moment he heard the words His Majesty , Dr. Liu was ready to listen."*
  - Çeviri: *"“Majesteleri’nin durumuyla ilgili endişelerimiz var,” dedi Uzun Kıdemli.

“Gelelim asıl meseleye.”

“Doğru.”

“Kısa süre sonra mı?”

Dr. Liu, Majesteleri kelimesini duyduğu anda dinlemeye hazır hale geldi."*

## Bölüm 20: Chapter 19: During the Surgery — 2 sorun
- **ATLANMIŞ**: Bölümün giriş cümlesi olan 'The surgery began.' ifadesi Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"The surgery began."*
- **ANLAM_KAYMASI**: Kaynak metinde 'Luomen c' şeklinde yarım kalan kısım, çeviride kaynakta bu bölümde yer almayan yabancı diyaloglar ve ifadelerle doldurulmuştur.
  - Kaynak: *"Luomen c"*
  - Çeviri: *"Luomen dikkatli ve hassas bir şekilde kesiyordu. Kan silindikçe, ameliyatın hedefi görünüyordu.
İkinci asistan da başını salladı.
“Benim de adım Wang, efendim. Farklı bir karakter.”
Yakışık..."*

## Bölüm 21: Chapter 20: After the Surgery — 5 sorun
- **ATLANMIŞ**: Bölümün girişindeki ilk paragraf Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"After that, the surgery ended uneventfully. It wrapped up so quickly, it was almost as if all the excitement had never happened."*
- **ANLAM_KAYMASI**: 'A row of three cots' (yan yana dizilmiş üç karyola/sedye) ifadesi yanlış bir şekilde 'üç katlı yatak' olarak çevrilmiştir.
  - Kaynak: *"It was a cramped chamber with a row of three cots."*
  - Çeviri: *"Yurt odası olmadığını biliyordu. Üç katlı yatağın sıralandığı daracık bir odaydı."*
- **ANLAM_KAYMASI**: 'nursing consort Lihua' (Lihua Hanım'a bakıcılık/hemşirelik yaptığı zamanlar) ifadesi yanlış anlaşılarak 'süt annesi Lihua' şeklinde çevrilmiştir.
  - Kaynak: *"Every time Maomao saw them at work, she remembered nursing consort Lihua."*
  - Çeviri: *"Maomao onları her çalışırken gördüğünde, süt annesi Lihua’yı hatırlıyordu."*
- **ATLANMIŞ**: Kaynaktaki bu cümle Türkçe çeviride yer almamaktadır; yerine kaynakta olmayan diyaloglar eklenmiş ve metin yarım kalmıştır.
  - Kaynak: *"“I take no responsibility for anything I was too young to remember"*
- **ANLAM_KAYMASI**: Cümlenin sonu 'alıyorm' şeklinde yarım kalmış ve paragrafın ikinci cümlesi tamamen atlanmıştır.
  - Kaynak: *"The Emperor, who just had to lie there with nothing to entertain him, seemed to be enjoying Suiren’s banter. If anything, it seemed like anyone who tried to stop Suiren would be the one who got punished."*
  - Çeviri: *"Ameliyatın ardından hiçbir eğlence kaynağı olmadan sadece yatağa uzanıp kalmak zorunda kalan İmparator, Suiren’in laf atışlarından keyif alıyorm"*

## Bölüm 22: Epilogue — 1 sorun
- **İNGİLİZCE_KALINTI**: İngilizce 'yes' kelimesi Türkçe metinde çevrilmeden bırakılmıştır.
  - Kaynak: *"“Right, yes.” Jinshi clutched a bean bun in one hand and took a bite."*
  - Çeviri: *""Haklısın, yes." Jinshi bir eline fasulye ezmeli bir çörek alıp bir ısırık attı."*
