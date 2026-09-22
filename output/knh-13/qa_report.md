# QA Raporu — knh-13

**Toplam 23 şüpheli nokta bulundu (16/19 bölüm başarıyla tarandı, 3 bölüm denetlenemedi).**

*Bu bir OTOMATİK ÖNERİ listesidir, kesin doğru kabul etmeyin — her maddeyi kaynakla birlikte kendiniz kontrol edin. Bazı işaretlemeler yanlış pozitif olabilir (bkz. script docstring'i).*

## Bölüm 1: Character Profiles — 2 sorun
- **ANLAM_KAYMASI**: 'Rikuson'dan intikamını alamadan' yerine 'Rikuson'a intikamını alamadan' denilerek yönelme eki yanlış kullanılmış ve anlam bozulmuştur.
  - Kaynak: *"In the end, he has to go back to the royal capital without ever having gotten his revenge on Rikuson."*
  - Çeviri: *"Sonuçta, Rikuson'a intikamını alamadan imparatorluk başkentine geri dönmek zorunda kalmıştır."*
- **ANLAM_KAYMASI**: 'a survivor' ifadesi 'bir hayatta kalmıştır' şeklinde dil bilgisi açısından hatalı ve anlamsız bir şekilde çevrilmiştir. 'hayatta kalan biridir' şeklinde çevrilmeliydi.
  - Kaynak: *"In truth, he’s a survivor of the otherwise exterminated Yi clan, and has secretly exacted revenge for his family."*
  - Çeviri: *"Aslında, yok edilen Yi klanından bir hayatta kalmıştır ve ailesi için gizlice intikamını almıştır."*

## Bölüm 2: Chapter 1: Lahan and Sanfan — 3 sorun
- **ANLAM_KAYMASI**: "got one in the oven" hamile olmak anlamına gelen bir deyimdir. Çevirmen bunu kelimesi kelimesine "karnında bir şey olmak" şeklinde çevirerek anlamı tamamen bozmuştur.
  - Kaynak: *"“A whole year... I wonder if Maomao’s at least got one in the oven,” he mumbled."*
  - Çeviri: *"“Tam bir yıl... Umarım Maomao’nun en azından bir şeyi karnında olmuştur,” diye mırıldandı."*
- **ANLAM_KAYMASI**: "it was only when..." (sadece ... olduğunda gerçekleşiyordu) ifadesi, "sadece Lahan'a özgüydü" (it was unique only to Lahan) şeklinde yanlış çevrilmiştir.
  - Kaynak: *"Somehow it was only when he made a request of Sanfan that no drivers were available and she came instead."*
  - Çeviri: *"Sanfan’dan bir istekte bulunduğu zamanlarda şoför bulunamaması ve onun gelmesi, bir şekilde sadece Lahan’a özgüydü."*
- **ANLAM_KAYMASI**: "I wonder if she will" (Acaba gelir mi/geleceğinden şüpheliyim) ifadesi, "Umarım gelir" (I hope she comes) şeklinde yanlış bir anlam ve tonla çevrilmiştir.
  - Kaynak: *"“I wonder if she will.”"*
  - Çeviri: *"“Umarım gelir.”"*

## Bölüm 3: Chapter 2: Lahan and the Dangling Corpse (Part One)
*(Denetlenemedi.)*

## Bölüm 4: Chapter 3: Lahan and the Dangling Corpse (Part Two)
*(Denetlenemedi.)*

## Bölüm 5: Chapter 4: Lahan and the Dangling Corpse (Part Three) — 3 sorun
- **ATLANMIŞ**: Kaynağın en başında yer alan bu paragraf Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"The three women Onsou brought were all new palace ladies who had just passed the examinations this year. They were of reasonably respectable backgrounds; two of them were officials’ daughters while the other came from a merchant family. Each of them, Lahan thought, was notably beautiful."*
- **ANLAM_KAYMASI**: Cümledeki 'bizi öldürdüğümüzü' ifadesi anlamı bozmaktadır; doğrusu 'onu bizim öldürdüğümüzü' olmalıdır.
  - Kaynak: *"Why in the world would you say we killed him?"*
  - Çeviri: *"Neden dünyada bizi öldürdüğümüzü söylersiniz?"*
- **ANLAM_KAYMASI**: Buradaki 'tell' fiili 'kokuyu ayırt etmek/fark etmek' anlamındadır. 'Kendine itiraf edememişti' çevirisi tamamen farklı ve hatalı bir anlam vermektedir.
  - Kaynak: *"Lahan hadn’t been able to tell himself"*
  - Çeviri: *"Lahan kendine itiraf edememişti"*

## Bölüm 6: Chapter 5: Jinshi and the Report — 4 sorun
- **ANLAM_KAYMASI**: Cümledeki 'yanığın bir sızı hissettiğini sandı' ifadesi dil bilgisel olarak hatalıdır ve yanığın kendisinin sızı hissettiği anlamını taşımaktadır. Doğrusu 'yanığında bir sızı hissettiğini sandı' olmalıdır.
  - Kaynak: *"Jinshi thought he felt a throb from the burn on his flank, which should have healed long ago."*
  - Çeviri: *"Jinshi, çoktan iyileşmiş olması gereken böğründeki yanığın bir sızı hissettiğini sandı."*
- **ANLAM_KAYMASI**: 'that reminds me' kalıbı 'aklıma gelmişken' veya 'bu bana ... hatırlattı' anlamına gelir. 'bu beni hatırlattı' şeklinde çevrilmesi anlam kaymasına yol açmıştır.
  - Kaynak: *"Ah, yes, Zuigetsu, that reminds me,” the Emperor said when Jinshi had finished his report."*
  - Çeviri: *"Evet, evet, Zuigetsu, bu beni hatırlattı," dedi İmparator, Jinshi raporunu bitirdiğinde."*
- **ANLAM_KAYMASI**: 'Empress Dowager' (Ana İmparatoriçe) unvanı 'İmparatoriçe Dowa' şeklinde yanlış ve anlamsız bir kelimeyle çevrilmiştir.
  - Kaynak: *"After I’ve greeted the Empress Dowager and the Empress. Er... If I could ask you to carry a summons?"*
  - Çeviri: *"İmparatoriçe Dowa'ya ve İmparatoriçe'ye selam verdikten sonra. Eee... Bir çağrıyı taşımanı rica edebilir miyim?""*
- **ANLAM_KAYMASI**: Kaynak metinde Gaoshun'un, Jinshi'nin Maomao'yu çağırabileceği konusunda Basen'i uyardığı belirtilmektedir ('you might call'). Çeviride ise 'Maomao'yu çağırabileceğimi' denilerek eylemi yapacak kişi Basen olarak aktarılmıştır.
  - Kaynak: *"My father cautioned me you might call Maomao before he went."*
  - Çeviri: *"Babam, gitmeden önce Maomao'yu çağırabileceğimi uyardı.""*

## Bölüm 9: Chapter 8: True Records of an Elder Brother — 1 sorun
- **ATLANMIŞ**: Bölüm başlığı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 8: True Records of an Elder Brother"*

## Bölüm 10: Chapter 9: En’en’s Day Off — 1 sorun
- **ATLANMIŞ**: Bölüm başlığı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 9: En’en’s Day Off"*

## Bölüm 11: Chapter 10: En’en and the Love Chat — 2 sorun
- **ANLAM_KAYMASI**: "aren't we suspicious?" ifadesi burada "ne kadar da şüpheciyiz/güvensiziz" (başkalarından şüphelenen anlamında) demektir. Çeviride ise "şüpheli (zan altında olan) değil miyiz?" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“Well, aren’t we suspicious? I’m only suggesting that people may look askance at a young lady of fine breeding taking up residence in a man’s house for so long.”"*
  - Çeviri: *"“İyi de, şüpheli değil miyiz? Sadece, iyi bir soylu aileden gelen genç bir hanımın bir erkeğin evinde bu kadar uzun süre ikamet etmesinin insanların gözünde şüpheli görünebileceğini öne sürüyorum.”"*
- **ANLAM_KAYMASI**: Bölümün sonundaki paragraflar Türkçe çeviride tamamen birbirine karışmış ve yanlış bir sırayla verilmiştir. Bu durum diyalog akışını bozarak anlamı tamamen anlaşılmaz hale getirmiştir.
  - Kaynak: *"Sanfan said, “To be quite honest, I’d be curious to know how a young woman of marriageable age justifies moving into a young man’s house, no matter how much she may resent her uncle’s attempts to arrange a match. Particularly considering that that meddlesome uncle is currently far away to the west, with no indication of when he will return. I simply don’t know where she finds the nerve to stick around.”

Just as En’en began to really bristle, Maomao nudged her again. “En’en, is it possible that you actually agree with Sanfan’s suggestion as such, but because it comes from Sanfan, you can’t bring yourself to simply say yes?”

“No. Nothing of the sort,” En’en said—but it took her a long moment to say it. Maomao could be remarkably perceptive about what other people were thinking and feeling. En’en just wished she would have picked a different time to activate that ability. Where was it when En’en needed it?

“You’re frowning very, very hard right now, En’en. And your face is twitching.” Maomao was giving En’en a scowl of her own.

“You’re imagining things,” En’en said. “I don’t have any particular objections to her i"*
  - Çeviri: *"En'en gerçekten diken diken olmaya başladığında, Maomao tekrar ona dokundu. “En'en, Sanfan'ın önerisini kendi içinde aslında kabul ediyorsun ama Sanfan'dan geldiği için basitçe evet diyemiyor olabilir misin?”

“Şu an çok, çok sert kaşlarını çatıyorsun, En'en. Ve yüzün titriyor.” Maomao, En'en'e kendi kaşlarını çatarak baktı.

“Pbbbbt!”

Sanfan, “Açıkçası, evlenme çağındaki genç bir kadının, amcasının kendisi için yaptığı eş arama girişimlerinden ne kadar nefret ederse etsin, neden bir gencin evine taşınmayı meşru gördüğünü bilmek isterdim. Özellikle de o müdahaleci amcanın şu an batıda, ne zaman döneceği belli olmayan bir yerde olduğunu düşününce. Nereden cesaret alıp burada kalmaya devam ettiğini gerçekten anlamıyorum.

“Yok. Hiçbir şey değil,” dedi En'en, ama bunu söylemek uzun bir anını aldı. Maomao, diğer insanların ne düşündüğünü ve hissettiğini son derece keskin bir şekilde sezebiliyordu. En'en, o yeteneğini kullanması için daha farklı bir zaman seçmesini isterdi. En'en'in buna ihtiyacı olan anda o yetenek neredeydi?

“Sen hayal görüyorsun,” dedi En'en. “Onun fikrine karşı özel bir itirazım yok.”"*

## Bölüm 12: Chapter 11: A Flower Called Joka — 1 sorun
- **ATLANMIŞ**: Bölüm başlığı ve giriş paragrafı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 11: A Flower Called Joka

Joka, facing a pile of books, recited the words of the venerated text as if she were singing. It might be called reading aloud, except she never opened a book. She knew the Four Books and Five Classics by heart, every one. If someone named one of the books and a page, she could recite it from memory."*

## Bölüm 13: Chapter 12: Joka and Her Little Sister — 2 sorun
- **ANLAM_KAYMASI**: Çeviride paragrafların sırası tamamen karışmış, bu durum diyalogların mantığını ve anlam akışını bozmuştur.
  - Kaynak: *"“Believe me, it wasn’t easy.” Maomao gazed into the middle distance. Her stay in the western capital, which she had initially told them should be just a few months, had turned into an entire year—one that had included an insect swarm. Things had been tough, all right.

“What about me? What do you have for me?” Pairin asked, her eyes shining.

“This is for you, Pairin.” Maomao handed her a piece of what appeared to be silk worked with delicate embroidery. What could this be?

“What have we here?” asked Pairin.

“Underwear from an exotic land.”

“Oh, boy!”

This evidently met with Pairin’s approval. Her eyes sparkled even more brightly.

Maomao sipped her tea, but she seemed to be looking everywhere at once.

“What’s wrong? You look restless,” said Pairin."*
  - Çeviri: *"“Peki ya ben? Bana ne var?” diye sordu Pairin, gözleri parlayarak.

“Burada ne var?” diye sordu Pairin.

“Yabancı bir topraktan iç çamaşırı.”

“Vay canına!”

“Ne oluyor? Huzursuz görünüyorsun,” dedi Pairin.

“İnan bana, hiç kolay değildi.” Maomao, gözlerini uzaklara daldırdı. Batı başkentindeki kalışını onlara başta birkaç ay süreceğini söylemişti, ama bu süre tam bir yıla uzamıştı; üstelik bu yılın içine bir böcek istilası da sığmıştı. Şeyler gerçekten zordu, evet.

“Bu sana, Pairin.” Maomao, üzerinde ince işçilikle dokunmuş gibi görünen ipek bir parça uzattı. Bu neydi acaba?

Pairin bu hediyeyle açıkça memnun olmuştu. Gözleri daha da parladı.

Maomao çayından bir yudum aldı, ama sanki aynı anda her yere bakıyordu."*
- **ANLAM_KAYMASI**: Çevirinin sonuna kaynak metinde yer almayan, yarım kalmış fazladan bir paragraf/cümle eklenmiştir.
  - Kaynak: *"“Ah, yes,” Pairin said. “Your daddy—er, I mean Master Lakan brought the Sage here"*
  - Çeviri: *""Aa, evet," dedi Pairin. "Baban—yani, demek istediğim Lakan Efendi, batı başkentine gitmeden önce Bilge'yi buraya getirmişti."

Go oyunundaki ustalığıyla tanınan Bilge, Lakan'a kendisine uygun rakipler olup olmadığını sormuştu; bunun"*

## Bölüm 14: Chapter 13: Yao and the Return of Lahan’s Brother — 2 sorun
- **ATLANMIŞ**: Cümlenin Türkçe çevirisi metinde tamamen atlanmıştır.
  - Kaynak: *"Yao had learned quite a few skills while Maomao was in the western capital."*
- **İNGİLİZCE_KALINTI**: İngilizce 'and' bağlacı Türkçe çeviride unutularak aynen bırakılmıştır.
  - Kaynak: *"an exam and some medicine"*
  - Çeviri: *"Bir muayene and biraz ilaç istemek isterdim"*

## Bölüm 15: Chapter 14: Ah-Duo’s Truth — 1 sorun
- **ATLANMIŞ**: Kaynağın girişindeki ilk paragraf Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"The voice of a rambunctious boy echoed around Ah-Duo’s palace. A lady-in-waiting chased him as he raced back and forth around the huge pavilion."*

## Bölüm 16: Chapter 15: Jinshi’s Shock, Maomao’s Resolution — 1 sorun
- **ATLANMIŞ**: Bölümün en başındaki bu cümle Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"The incense worked its way into Jinshi’s nose."*

## Bölüm 17: Chapter 16: Maomao and the Late Dinner
*(Denetlenemedi.)*
