# QA Raporu — knh-12

**Günlük Gemini kotası tükendiği için durduruldu — 12/35 bölüm tarandı. Script'i tekrar çalıştırınca kaldığı yerden devam edecek (baştan başlamayacak).**

*Bu bir OTOMATİK ÖNERİ listesidir, kesin doğru kabul etmeyin — her maddeyi kaynakla birlikte kendiniz kontrol edin. Bazı işaretlemeler yanlış pozitif olabilir (bkz. script docstring'i).*

## Bölüm 1: Character Profiles — 3 sorun
- **ANLAM_KAYMASI**: "imperial court" (imparatorluk sarayı/saray çevresi) ifadesi, hukuki bir terim olan "imparatorluk mahkemesi" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"After a stint in the rear palace and then the imperial court, she now finds herself as an assistant to the physicians in the western capital."*
  - Çeviri: *"Arka sarayda ve ardından imparatorluk mahkemesinde kısa bir süre görev yaptıktan sonra, şimdi kendini batı başkentindeki hekimlerin yardımcısı olarak buluyor."*
- **ANLAM_KAYMASI**: "foists a lot of work on him" (ona çok fazla iş yıkıyor/yüklüyor) ifadesi "ona çok fazla iş yükleniyor" şeklinde çevrilmiştir. "Yüklenmek" fiili dönüşlü/edilgen anlam taşıdığı için işi Rikuson'un üstlendiği veya Rikuson'a iş yüklendiği anlamı oluşarak kaynağın tersi bir durum yaratmıştır.
  - Kaynak: *"Rikuson in particular foists a lot of work on him, and Jinshi is eager to get back at him someday."*
  - Çeviri: *"Özellikle Rikuson ona çok fazla iş yükleniyor ve Jinshi bir gün ona misilleme yapmayı sabırsızlıkla bekliyor."*
- **ANLAM_KAYMASI**: "tormenting" (uğraşmak, canını sıkmak, eziyet etmek) kelimesi "ezmekle" şeklinde çevrilerek bağlama uymayan, aşırı sert ve yanlış bir anlam kazanmıştır.
  - Kaynak: *"Completing his life’s work seems to have helped him relax, and he now spends his time tormenting the Emperor’s younger brother."*
  - Çeviri: *"Hayatının işini tamamlamış gibi görünmesi onu rahatlatmışa benziyor ve şimdi zamanını İmparator’un küçük kardeşini ezmekle geçiriyor."*

## Bölüm 2: Prologue — 1 sorun
- **ATLANMIŞ**: Metnin başındaki 'Prologue' (Prolog/Giriş) başlığı Türkçe çeviride atlanmıştır.
  - Kaynak: *"Prologue"*

## Bölüm 3: Chapter 1: The Princeling of the Main House — 2 sorun
- **ANLAM_KAYMASI**: 'Here I thought...' kalıbı 'Ben de ... sanmıştım' anlamına gelirken, çeviride 'Keşke ... öğrense' şeklinde bir temenni olarak yanlış aktarılmıştır.
  - Kaynak: *"Here I thought he’d learned to step back just a little bit."*
  - Çeviri: *"Keşke biraz geri çekilmeyi öğrense, diye geçirdi aklından."*
- **TUTARSIZ_TERİM**: Kaynak metindeki 'quack doctor' ifadesi bir önceki cümlede 'Şarlatan doktor' olarak çevrilmişken, burada 'Doktor Kralı' şeklinde farklı ve tutarsız bir şekilde çevrilmiştir.
  - Kaynak: *"“All right, young lady. I leave the rest in your hands!” The quack doctor departed and Maomao, basically trading off with him, went into Jinshi’s bedroom."*
  - Çeviri: *"“Tamam, genç hanım. Geri kalanını senin ellerine bırakıyorum!” Doktor Kralı ayrıldı ve Maomao, temelde onunla nöbet değişimi yaparcasına Jinshi’nin yatak odasına girdi."*

## Bölüm 4: Chapter 2: The Greenhouse and the Chapel — 1 sorun
- **ŞAHIS_UYUŞMAZLIĞI**: Kaynak metinde birinci çoğul şahıs ("we") kullanılırken, çeviride ikinci çoğul şahıs ("sökerseniz") kullanılarak şahıs uyuşmazlığı yapılmıştır.
  - Kaynak: *"Maybe if we tear up that other cucumber plot too."*
  - Çeviri: *"Belki o diğer salatalık tarlasını da sökerseniz."*

## Bölüm 5: Chapter 3: Gyoku-ou’s Children — 2 sorun
- **ANLAM_KAYMASI**: "Who the heck is this guy?" sorusu "Bu adam da kim?" anlamına gelir, karakterin kimin oğlu olduğunu sormamaktadır.
  - Kaynak: *"Who the heck is this guy?"*
  - Çeviri: *"Bu adam kimin oğlu acaba?"*
- **ANLAM_KAYMASI**: "quack doctor" (şarlatan hekim) ifadesi yanlış bir şekilde "Doktor Kralı" olarak çevrilmiştir.
  - Kaynak: *"He was sipping tea with the quack doctor—a eunuch—and didn’t hesitate to act polite to Maomao."*
  - Çeviri: *"Doktor Kralı ile—bir hadım olan—çay içiyor ve Maomao’ya kibar davranmaktan çekinmiyordu."*

## Bölüm 6: Chapter 4: The Sheltered Wife — 3 sorun
- **ATLANMIŞ**: Bölüm başlığı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 4: The Sheltered Wife"*
- **ANLAM_KAYMASI**: Fiziksel bir eylem olan 'bowing' (eğilerek selam verme) ifadesi, soyut anlamdaki 'eğilim' (tendency/inclination) sözcüğüyle karıştırılarak 'derin bir eğilimle' şeklinde hatalı çevrilmiştir.
  - Kaynak: *"“Thank you so much,” Hu’s Sis said, bowing deeply."*
  - Çeviri: *"“Çok teşekkür ederim,” dedi Hu’nun Ablası, derin bir eğilimle."*
- **ANLAM_KAYMASI**: 'anyway' (zaten, nasıl olsa) kelimesi 'Neyse ki' (iyi ki, şans eseri) şeklinde çevrilerek anlam kaymasına yol açmıştır.
  - Kaynak: *"“Hulan isn’t back yet, anyway. Why don’t we take it easy?”"*
  - Çeviri: *"“Neyse ki Hulan henüz dönmedi. Neden biraz rahatlamayalım?”"*

## Bölüm 7: Chapter 5: Third Son, Second Son, Eldest Son — 2 sorun
- **ATLANMIŞ**: Bölüm başlığı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 5: Third Son, Second Son, Eldest Son"*
- **ANLAM_KAYMASI**: İngilizce metindeki 'snorting with certainty' (emin bir şekilde burnundan ses çıkarmak/hınçla onaylamak) ifadesi, Türkçe'ye öfkeden deliye dönmek anlamına gelen 'burnundan solumaktaydı' şeklinde yanlış çevrilmiştir.
  - Kaynak: *"Hulan was practically snorting with certainty, and his eyes were truly shining; if this was an act, he was doing a very good job."*
  - Çeviri: *"Hulan, neredeyse kesinlikle burnundan solumaktaydı ve gözleri gerçekten parlıyordu; eğer bu bir oyunduysa, çok iyi oynuyordu."*

## Bölüm 8: Chapter 6: The Winery — 2 sorun
- **ANLAM_KAYMASI**: Maomao'nun kabullenme/onay belirten 'Sure. Right.' (Peki, tamam) ifadesi 'Eminim' şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“Sure. Right. Off I go,” Maomao said, then she stuffed some tools into a bag and left the office."*
  - Çeviri: *"“Eminim. Tamam. Gidiyorum,” dedi Maomao, ardından bazı aletleri bir çantaya doldurdu ve ofisten ayrıldı."*
- **ANLAM_KAYMASI**: Karakterin babasının kız kardeşi (halası) olduğu açıkça belirtilen kişi için Türkçe çeviride 'teyze' kelimesi kullanılmıştır.
  - Kaynak: *"“Your aunt? Meaning...”

“My father’s younger sister,” Hulan explained."*
  - Çeviri: *"“Teyzen? Yani...”

“Babamın küçük kız kardeşi,” açıkladı Hulan."*

## Bölüm 9: Chapter 7: The Inheritance — 1 sorun
- **ANLAM_KAYMASI**: Çeviride 'mushrooms that make you super drunk' (insanı aşırı sarhoş eden mantarlar) kısmı tamamen atlanmış ve 'winery' kelimesi aynı cümle içinde hem 'şarap evi' hem 'şarap imalathanesi' olarak mükerrer çevrilerek anlam tamamen bozulmuştur.
  - Kaynak: *"“So, getting back to the mushrooms, the question is why a winery would even have mushrooms that make you super drunk, right?”"*
  - Çeviri: *"“Peki, mantarlara dönersek, soru şu: Bir şarap evinin neden bir şarap imalathanesinin mantarları bile olabileceği, değil mi?”"*

## Bölüm 10: Chapter 8: Junjie — 2 sorun
- **ANLAM_KAYMASI**: 'root-y' (kök gibi, cılız) ifadesi 'kökleri olanlar' şeklinde yanlış çevrilmiştir. Ayrıca 'Even' kelimesinin 'Bile' olarak cümlenin başında doğrudan çevrilmesi Türkçe dil bilgisine aykırıdır.
  - Kaynak: *"“Even...root-y ones like these?”"*
  - Çeviri: *"“Bile... bunlar gibi kökleri olanlar mı?”"*
- **ANLAM_KAYMASI**: 'forget it’s mine' (benim adım olduğunu unutun) ifadesi 'istediğiniz gibi unutun' şeklinde yanlış çevrilerek anlam kaymasına yol açmıştır.
  - Kaynak: *"“Oh, but if anyone else here already has my name, please, by all means, forget it’s mine."*
  - Çeviri: *"“Ah, ama eğer burada benim adımı taşıyan başka biri varsa, lütfen, istediğiniz gibi unutun."*

## Bölüm 11: Chapter 9: The Foreign Girl
*(Denetlenemedi.)*

## Bölüm 12: Chapter 10: Emergency Patient, Emergency Situation — 2 sorun
- **ATLANMIŞ**: Bu cümle Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"That was as conciliatory as Maomao could be."*
- **ANLAM_KAYMASI**: Paragrafların ve diyalogların sırası tamamen karışmış, bu yüzden Maomao henüz 'öldürülmekten' bahsedilmeden 'Öldürüldü mü?' diye tepki vermekte ve konuşma mantıksız bir hal almaktadır.
  - Kaynak: *"“Please help him. Uncle Shikyou, he’s dying.” Xiaohong was struggling not to cry. She was too meek for this to be an act; she seemed to be in earnest.

Maomao wondered what to do. This didn’t strike her as a childish prank. If Shikyou, Gyoku-ou’s eldest son, was indeed on death’s doorstep, Maomao couldn’t possibly just ignore him. But then, someone as important as Shikyou would obviously have a doctor already attending him.

“Tell me something. Why did you come to me? There are plenty of other doctors, right?”

The confusion of the days immediately after the swarm was long since settled. Reprehensible though his behavior might be, there was no way a physician would refuse to see the son of the late governor. And Maomao couldn’t imagine any reason a female attendant would be required in this instance.

Most of all, though, she wondered why it was Xiaohong who had come to call her.

“Uncle... Uncle says that if a doctor sees him...he’ll be killed.”

“Killed?”

Now, that got her attention."*
  - Çeviri: *"“Bana bir şey söyleyin. Neden bana geldiniz? Başka doktorlar var, değil mi?”
Öldürüldü mü?
Şimdi, bu dikkatini çekti.
“Lütfen ona yardım edin. Amca Shikyou, ölüyor.” Xiaohong ağlamamak için kendini zorluyordu. Bu kadar utangaç bir kız için bu bir oyundu olamazdı; samimi görünüyordu.
Maomao ne yapacağını düşünüyordu. Bu, çocukça bir şaka gibi gelmiyordu ona. Eğer Shikyou, yani Gyoku-ou’nun en büyük oğlu gerçekten ölümün eşiğindeyse, Maomao onu görmezden gelemeyecekti. Ama Shikyou gibi önemli birinin yanında zaten bir doktor olmalıydı.
Sürü olayının hemen ardından yaşanan kargaşa çoktan yatışmıştı. Davranışı ne kadar kınanmaya değer olursa olsun, merhum valinin oğluna bakmayı reddeden bir hekim çıkamazdı. Üstelik Maomao, bu durumda bir kadın hizmetçinin neden gerekeceğini hayal bile edemiyordu.
Ama en çok merak ettiği şey, onu çağırmaya gelenin neden Xiaohong olmasıydı.
“Amca... Amca, bir doktor onu görürse... öldürüleceğini söylüyor.”"*

## Bölüm 13: Chapter 11: The Southern Inn Town — 2 sorun
- **ANLAM_KAYMASI**: Kaynak metindeki diyalog sırası ve paragraflar tamamen karıştırılmış; Maomao'nun cevabı ve düşüncelerini içeren paragraf aradan çıkarılarak Shikyou'nun sözleri doğrudan birbirine bağlanmış ve anlam bütünlüğü bozulmuştur.
  - Kaynak: *"“I take it from the look on your face that you’d like me to explain how I know where we are.”

“If you’d be so kind.” Shikyou had barely been conscious when they were brought here; he should be even less sure of their location than Maomao was. How could he be so certain she was right? “Did you and Miss Chue agree ahead of time that this was where you would come?”

“Chue and I want the same thing.”"*
  - Çeviri: *"“Yüzündeki ifadeye bakılırsa açıklamamı istediğinizi anlıyorum”

"Chue ile aynı şeyi istiyoruz.""*
- **ANLAM_KAYMASI**: Kaynak metin yarım bir cümleyle biterken, çeviride bu ifadeden sonra kaynakta hiç bulunmayan diyaloglar, paragraflar ve yarım kalmış ifadeler eklenmiş, ayrıca önceki paragraflar buraya taşınarak metin yapısı tamamen bozulmuştur.
  - Kaynak: *"“Why did you drag me"*
  - Çeviri: *""Neden beni de sürüklediniz?"

"Gyokujun'un annesi ne olacak?"

"He he!"

"Buyur, rica ederim." Shikyou, buraya getirildiğinde neredeyse bilincini yitirmişti; Maomao'dan bile daha az emin olmalıydı konumları hakkında. Nasıl bu kadar kesin bir şekilde haklı olduğunu biliyordu? "Sen ve Bayan Chue, buraya geleceğinizi önceden mi kararlaştırdınız?"

Maomao, bir şeyler sakladığından emindi — ama bunun Shikyou ile bir bağlantı olduğunu asla tahmin etmemişti. En azından, onu kendisine bakması için neden istediğini açıklıyordu bu.

*Yalan kokusu alıyorum*, diye düşündü Maomao — her ne kadar bu, Chue'nin sesinde bir şaka tonu taşıyarak söyleyebileceği türden bir şey olsa da.

"Bu eyaleti yönetmekten bu kadar kaçınan birinden gelen ilginç bir arzu."

"Herkesin en iyi olduğu bir işi olduğunu duymadın mı? Doğru kişiyi doğru yere koy; işlerin düzgün yürümesini sağlayan şey budur."

Bu, Shikyou'nun I-sei Eyaleti'ni yönetecek kapasiteye sahip olmadığını düşündüğünü söyleme biçimiydi.

Neden böyle düşündüğünü anlamamak için bir sebep yoktu.
Maomao'nun *anlayamadığı* şey ise...

"Eh. Bana ait bir konu değil. Bunu Chue'ye kendin sormalısın." Shikyou bir yudum daha su içti, ardından kepçeyi bir kenara bıraktı. Yatakta yatan Gyokujun'un ve Xiaohong'un başını okşadı. "Bu çocuklara kötü bir şey yaptım," dedi. "Yinxing şimdiye kadar çıldırmış olmalı."

Yinxing. Adını anış şeklinden, Maomao onun Xiaohong'un annesi olduğunu tahmin etti — bu da onu Shikyou'nun küçük kız kardeşi yapardı.

"Şaşıraca"*
