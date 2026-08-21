# QA Raporu — knh-11

**Toplam 106 şüpheli nokta bulundu (26/27 bölüm başarıyla tarandı, 1 bölüm denetlenemedi).**

*Bu bir OTOMATİK ÖNERİ listesidir, kesin doğru kabul etmeyin — her maddeyi kaynakla birlikte kendiniz kontrol edin. Bazı işaretlemeler yanlış pozitif olabilir (bkz. script docstring'i).*

## Bölüm 1: Character Profiles — 5 sorun
- **ANLAM_KAYMASI**: "down to earth" (mütevazı, gerçekçi) deyimi kelimesi kelimesine "toprağa yakın" olarak yanlış çevrilmiştir.
  - Kaynak: *"He’s remarkably down to earth for someone so gorgeous"*
  - Çeviri: *"O kadar yakışıklı biri için son derece toprağa yakın bir duruşu var"*
- **ANLAM_KAYMASI**: "let oneself go" (kendini koyuvermek, kontrolünü kaybetmek) ifadesi "kendine gelip gitmek" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"if he lets himself go"*
  - Çeviri: *"kendine gelip gitmesine izin verirse"*
- **ANLAM_KAYMASI**: Saray kadın hizmetçisi/nedime anlamına gelen "lady-in-waiting" terimi, "hanımefendi" olarak yanlış çevrilmiştir.
  - Kaynak: *"Jinshi’s lady-in-waiting"*
  - Çeviri: *"Jinshi'nin hanımefendisi"*
- **ANLAM_KAYMASI**: "Frivolous" (ciddiyetsiz, havai) kelimesi "geçici" (temporary) olarak yanlış çevrilmiştir.
  - Kaynak: *"He can seem frivolous"*
  - Çeviri: *"Geçici görünebilir"*
- **ANLAM_KAYMASI**: "Quip" (hazırcevaplık, espri, nükte) kelimesi "fıkra" olarak ve "offering quips" ifadesi "fıkralar atmak" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"shines when offering quips"*
  - Çeviri: *"Fıkralar atarken parlayan"*

## Bölüm 2: Prologue — 2 sorun
- **ANLAM_KAYMASI**: 'neighing' (kişneme) kelimesi 'nallar' (at nalı) olarak yanlış çevrilmiştir.
  - Kaynak: *"the neighing of the horses"*
  - Çeviri: *"atların nalları"*
- **ANLAM_KAYMASI**: 'richer than anywhere else' (her yerden daha zengin) ifadesi, Türkçe mantığına uymayacak şekilde 'başka hiçbir yerden daha zengin' olarak çevrilerek anlam karmaşası yaratılmıştır.
  - Kaynak: *"richer and more beautiful than anywhere else"*
  - Çeviri: *"başka hiçbir yerden daha zengin ve güzel"*

## Bölüm 3: Chapter 1: Dried Fruit — 6 sorun
- **ANLAM_KAYMASI**: "Cleaver" (satır) kelimesi "balta" (axe) olarak yanlış çevrilmiştir.
  - Kaynak: *"Maomao chopped some of the herbs in question with a cleaver"*
  - Çeviri: *"Maomao, söz konusu otlardan bazılarını bir balta ile doğrayıp"*
- **ANLAM_KAYMASI**: "Pestle" (havan eli/tokmak) kelimesi "örs" (anvil) olarak yanlış çevrilmiştir.
  - Kaynak: *"Maomao passed Chue a mortar and pestle"*
  - Çeviri: *"Maomao, Chue’ye bir havan ve örs vererek"*
- **ANLAM_KAYMASI**: "Jinshi" ismi çeviride atlanıp yerine "onu" zamiri kullanıldığı için cümlenin anlamı tamamen bozulmuş ve Gyoku-ou'ya kötü davranılıyormuş gibi bir anlam ortaya çıkmıştır.
  - Kaynak: *"how he had used Jinshi as a convenient foil, hardly treating him like a real Imperial relative."*
  - Çeviri: *"onu nasıl bir araç olarak kullandığını biliyordu, neredeyse gerçek bir imparatorluk ailesi üyesi gibi davranmıyordu."*
- **ANLAM_KAYMASI**: "Extermination" (yok etme/itlaf) kelimesi "yoklama" (inspection) olarak yanlış çevrilmiştir.
  - Kaynak: *"getting the freak strategist to form a bug-extermination team."*
  - Çeviri: *"o garip stratejistin bir böcek yoklama ekibi kurmasını sağlamak"*
- **ANLAM_KAYMASI**: "Eunuch" (hadım) kelimesi metin genelinde (birden fazla yerde) yanlış bir şekilde "sağır" (deaf) olarak çevrilmiştir.
  - Kaynak: *"He’d been as busy as he’d been during his time as a “eunuch”"*
  - Çeviri: *"“Sağır” olduğu zamanlarda olduğu kadar meşguldü"*
- **ANLAM_KAYMASI**: "Boy" ünlemi "Erkek" olarak, "get an earful" (azar işitmek) deyimi ise "kulaklarına bir şeyler dolacak" şeklinde tamamen yanlış çevrilmiştir.
  - Kaynak: *"Boy, was she going to get an earful about this"*
  - Çeviri: *"Erkek, bir dahaki sefere birbirlerini gördüklerinde kulaklarına bir şeyler dolacak."*

## Bölüm 4: Chapter 2: The Strategist Strikes! — 6 sorun
- **ATLANMIŞ**: Bölüm başlığı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 2: The Strategist Strikes!"*
- **ANLAM_KAYMASI**: Hadım anlamına gelen 'eunuch' kelimesi 'cübbeli' olarak yanlış çevrilmiştir.
  - Kaynak: *"pretending to be a eunuch"*
  - Çeviri: *"bir cübbeli gibi davranmış"*
- **ANLAM_KAYMASI**: Maomao'nun 'Pek öyle demezdim' anlamındaki sözü, 'Bunu söylemem gerekmez sanırım' şeklinde yanlış aktarılmıştır.
  - Kaynak: *"“I’m not sure I’d say that, sir,”"*
  - Çeviri: *"“Bunu söylemem gerekmez sanırım, efendim,”"*
- **ANLAM_KAYMASI**: Öfkeyle/dik dik bakmak anlamına gelen 'glared' eylemi, 'gözlerini kırptı' şeklinde yanlış çevrilmiştir.
  - Kaynak: *"Maomao glared at him."*
  - Çeviri: *"Maomao ona gözlerini kırptı."*
- **ATLANMIŞ**: Maomao'nun konuyu değiştirmek için ameliyatın başarısını bildirdiği ve periyodik kontroller için izin istediği paragraf çeviride tamamen atlanmıştır.
  - Kaynak: *"In a bid to change the subject, Maomao decided to make the report she had come here expecting to make. “The surgery on Master Gyoku-ou’s granddaughter was a success. However, I’d like to continue doing periodic exams to check the progress of her recovery. I assume that will be all right?”"*
- **ANLAM_KAYMASI**: İstekli/gönüllü olmayı belirten 'willing' ifadesi, tam tersi anlamda 'istemeden de olsa' şeklinde çevrilmiştir.
  - Kaynak: *"“I would have been willing.”"*
  - Çeviri: *"“İstemeden de olsa yapmaya hazırdım.”"*

## Bölüm 5: Chapter 3: Big Lin — 4 sorun
- **ANLAM_KAYMASI**: "thrown out on their ears" deyimi yaka paça/apar topar dışarı atılmak anlamına gelirken, çeviride "kulakları çınlayana kadar dışarı atılmak" şeklinde yanlış aktarılmıştır.
  - Kaynak: *"thrown out on their ears by the menservants."*
  - Çeviri: *"erkek hizmetkarlar tarafından kulakları çınlayana kadar dışarı atılabilirdi."*
- **ANLAM_KAYMASI**: "Brothel" (genelev) kelimesi yanlış bir şekilde soyut bir kavram olan "fahişelik" olarak çevrilmiştir.
  - Kaynak: *"Being the official apologizer for a brothel"*
  - Çeviri: *"Bir fahişelik için resmi özür dilemek"*
- **ANLAM_KAYMASI**: "pay attention" (dikkatini vermek/odaklanmak) ifadesi, "dikkat çekmek" (attract attention) şeklinde yanlış çevrilmiştir.
  - Kaynak: *"get the freak strategist to pay that much attention"*
  - Çeviri: *"Tuhaf stratejisti Shogi oyununa o kadar dikkat çekmeye ikna eden"*
- **ANLAM_KAYMASI**: "I'm not sure he can offer" (sunabileceğinden emin değilim) ifadesi, "sunamayacağını düşünmüyorum" denilerek tam tersi bir anlama büründürülmüştür.
  - Kaynak: *"I’m not sure he can offer the kind of information"*
  - Çeviri: *"bilgiler sunamayacağını düşünmüyorum."*

## Bölüm 6: Chapter 4: Small Lin — 5 sorun
- **ANLAM_KAYMASI**: "Man" ünlemi "Yaşasın" (hooray) olarak, "what's keeping that guy" (o adam nerede kaldı) ifadesi ise "o adam ne yapıyor" olarak tamamen yanlış çevrilmiştir.
  - Kaynak: *"Man, what’s keeping that guy?"*
  - Çeviri: *"Yaşasın, o adam ne yapıyor?"*
- **ANLAM_KAYMASI**: "stole a glance" (göz ucuyla/gizlice bakmak) ifadesi "fısıltıyla bakış atmak" şeklinde yanlış ve anlamsız bir şekilde çevrilmiştir.
  - Kaynak: *"stole a glance"*
  - Çeviri: *"fısıltıyla bir bakış attı"*
- **ANLAM_KAYMASI**: "causing" (sebep olmak/yol açmak) fiili "zorlamak" (forced) olarak yanlış çevrilmiştir.
  - Kaynak: *"causing everyone to look at her in surprise"*
  - Çeviri: *"herkesi şaşkınlıkla ona bakmaya zorladı"*
- **ANLAM_KAYMASI**: "Ona bu yüzden mi öyle [Küçük Lin] diyorsun?" anlamına gelen soru, "Ona bunu neden söylüyorsun?" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"Is that why you call him that?"*
  - Çeviri: *"Ona bunu neden söylüyorsun?"*
- **ANLAM_KAYMASI**: Diyalog sırası karıştırılmış ve kaynağın bu kısmında olmayan "But artık eğlence bitti, efendim?" şeklinde uydurma bir satır eklenerek konuşmanın anlamı tamamen kaydırılmıştır.
  - Kaynak: *"“Why didn’t you say that?”
“Well, what’s it got to do with me?”"*
  - Çeviri: *"“Neden bunu söylemedin?”
“But artık eğlence bitti, efendim?”"*

## Bölüm 7: Chapter 5: A Brother’s Return — 3 sorun
- **ANLAM_KAYMASI**: 'Tramp' (hırpani/evsiz kimse) kelimesi yanlış anlaşılarak 'sokak ağzı' (argo/şive) şeklinde çevrilmiştir.
  - Kaynak: *"Maomao stared at the tramp. Tramp might not seem like a very polite word"*
  - Çeviri: *"Maomao, sokak ağzına baktı. Sokak ağzı çok kibar bir kelime gibi görünmeyebilirdi"*
- **ATLANMIŞ**: Chue'nun bu ünlem cümlesi Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"“You look like death!” Chue exclaimed."*
- **ANLAM_KAYMASI**: Bir travma veya yorgunluk belirtisi olan 'thousand-yard stare' (boş/sabit bakış) ifadesi, kelimesi kelimesine çevrilerek anlamsız bir hal almıştır.
  - Kaynak: *"judging by the thousand-yard stare on his face."*
  - Çeviri: *"Yüzündeki bin yardalığına bakılırsa"*

## Bölüm 8: Chapter 6: From the Capital — 5 sorun
- **ANLAM_KAYMASI**: "had in his sights" (gözüne kestirdiği/hedeflediği) ifadesi "nişanlandığı" (engaged to) olarak yanlış çevrilmiştir.
  - Kaynak: *"the next lady this colleague had in his sights"*
  - Çeviri: *"bu meslektaşının nişanlandığı sonraki hanımın"*
- **ANLAM_KAYMASI**: "in question" (söz konusu) ifadesi "soru işaretli olan" (suspicious/questionable) şeklinde yanlış çevrilmiştir.
  - Kaynak: *"The particular official in question"*
  - Çeviri: *"Soru işaretli olan belirli yetkili"*
- **ANLAM_KAYMASI**: Lahan'ın yardımcılarından hiçbirinin üç aydan fazla dayandığını görmediği anlamı, Lahan'ın o yetkilinin kendisinin üç aydan fazla dayanmadığını bilmediği şeklinde tamamen yanlış çevrilmiştir.
  - Kaynak: *"Lahan had never known one of his adjuncts to last longer than three months"*
  - Çeviri: *"Lahan, bu adamın üç aydan fazla dayanmadığını hiç bilmiyordu"*
- **ANLAM_KAYMASI**: "perfectly welcome to be upset" (öfkelenmekte serbestti / öfkelenebilirdi) ifadesi "öfkeli olmaya tamamen haklıydı" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"The man was perfectly welcome to be upset"*
  - Çeviri: *"Adam öfkeli olmaya tamamen haklıydı"*
- **ANLAM_KAYMASI**: "per ticket" (bilet başına) ifadesi "gümüş başına" olarak yanlış çevrilmiştir.
  - Kaynak: *"at two silver per ticket"*
  - Çeviri: *"gümüş başına iki gümüşe"*

## Bölüm 9: Chapter 7: The Letters That Arrived — 4 sorun
- **ANLAM_KAYMASI**: 'Mung beans' (maş fasulyesi) terimi hatalı bir şekilde 'Mısır' (corn) olarak çevrilmiştir.
  - Kaynak: *"Mung beans, in addition to producing sprouts, could be used to make noodles"*
  - Çeviri: *"Mısır, fasulye filizlerinin yanı sıra noodle yapımında ve tıbbi amaçlarla da kullanılabilir."*
- **ANLAM_KAYMASI**: Saygı unvanı olan 'Master' (Efendi), yanlış anlaşılarak 'Ustası' şeklinde çevrilmiştir.
  - Kaynak: *"Not many people know Master Baryou personally."*
  - Çeviri: *"Çok az insan Ustası Baryou’yu kişisel olarak tanır."*
- **ATLANMIŞ**: İngilizce replik Türkçe metinde çevrilmeden aynen bırakılmış ve devamındaki diyalog sırası tamamen karıştırılmıştır.
  - Kaynak: *"“By the way, Lahan’s Little Sister...”"*
  - Çeviri: *"“By the way, Lahan’s Little Sister...”"*
- **ATLANMIŞ**: Metnin sonundaki cümle yarım bırakılmış, kelime 'tıbbi uygulamala' şeklinde kesilmiştir.
  - Kaynak: *"The region around the western capital was..."*
  - Çeviri: *"tıbbi uygulamala"*

## Bölüm 10: Chapter 8: The Letters That Didn’t — 5 sorun
- **ANLAM_KAYMASI**: "damage to the harvest" (hasat hasarı) ifadesi, "hasar gören hasar" şeklinde anlamsız ve hatalı çevrilmiştir.
  - Kaynak: *"trying to make up for the damage to the harvest"*
  - Çeviri: *"Hasar gören hasarı telafi etmeye tamamen odaklanmışlardı"*
- **ANLAM_KAYMASI**: Kaynakta karakterin matematik yapamadığı için değil, sorumluluk ağır olduğu için zorlandığı belirtilirken, çeviride hesap yapamadığı söylenerek tam tersi bir anlam verilmiştir.
  - Kaynak: *"It wasn’t that he couldn’t do the math"*
  - Çeviri: *"Hesap yapamıyordu ki"*
- **ANLAM_KAYMASI**: "never averse to" (bu tür bilgilere karşı olmadığını/açık olduğunu) ifadesi, "hiç hoşlanmadığını" şeklinde tam tersi anlamda çevrilmiştir.
  - Kaynak: *"he knew the other man was never averse to information of this variety."*
  - Çeviri: *"diğer adamın bu tür bilgilerden hiç hoşlanmadığını biliyordu."*
- **ATLANMIŞ**: Lahan'ın meraklı yapısından ve I-sei eyaletindeki böcek salgınından haberdar olmamasının imkansızlığından bahseden paragraf tamamen atlanmıştır.
  - Kaynak: *"Lahan being who he was, there was no way he didn’t know about the plague of insects..."*
- **ANLAM_KAYMASI**: "Restless" (huzursuz/tedirgin) kelimesi, Türkçe "restleşmek" (meydan okumak) kelimesiyle karıştırılarak yanlış çevrilmiştir.
  - Kaynak: *"the people were restless after the major disaster"*
  - Çeviri: *"halk yeni gerçekleşen büyük felaketin ardından restleşmişti"*

## Bölüm 11: Chapter 9: The Meeting — 2 sorun
- **ANLAM_KAYMASI**: Kaynaktaki 'Jinshi ile birlikte başkentten gelenler' ifadesi, çeviride 'Başkente gelen' şeklinde yanlış yön bildirecek şekilde çevrilmiş ve Jinshi'nin adı atlanmıştır.
  - Kaynak: *"Those who had come with Jinshi from the capital"*
  - Çeviri: *"Başkente gelen ve gerçeği bilenler"*
- **ANLAM_KAYMASI**: Geminin limana yanaşma/demirleme izni (permission to dock), 'dolaşma izni' olarak tamamen yanlış çevrilmiştir.
  - Kaynak: *"the supply ship might even have been refused permission to dock."*
  - Çeviri: *"tedarik gemisinin dolaşma izni bile reddedilebilirdi."*

## Bölüm 12: Chapter 10: The Golden Ratio — 3 sorun
- **ANLAM_KAYMASI**: Kaynak metindeki 'tens of thousands' (on binlerce) ifadesi çeviride 'yüz binlerce' (hundreds of thousands) olarak yanlış aktarılmıştır.
  - Kaynak: *"His actions might have saved tens of thousands of lives"*
  - Çeviri: *"Eylemleri böcek salgınından yüz binlerce hayatı kurtarmış olabilir"*
- **ANLAM_KAYMASI**: Kaynak metindeki 'see him recognized' (onun takdir edildiğini/tanındığını görmek) ifadesi, 'onu görmeye yemin etti' şeklinde yanlış çevrilerek anlam kaymasına yol açmıştır.
  - Kaynak: *"Maomao vowed afresh that she would see him recognized for his contributions"*
  - Çeviri: *"Maomao, bu sefer en azından katkıları tanınana kadar onu görmeye yemin etti"*
- **TUTARSIZ_TERİM**: Metin boyunca 'quack' veya 'quack doctor' terimi 'şarlatan doktor' olarak çevrilmişken, bu cümlede 'sahte' olarak çevrilerek terim tutarsızlığı yaratılmıştır.
  - Kaynak: *"Lahan’s Brother wasn’t looking for Maomao and the quack’s input"*
  - Çeviri: *"Lahan’ın Kardeşi, Maomao ve sahtenin girdisinden çok"*

## Bölüm 13: Chapter 11: The Coal Mine — 2 sorun
- **ANLAM_KAYMASI**: "Tickle" kelimesi gıdıklamak anlamına gelir, kaşımak (scratch) değil. Cümledeki eylem yanlış çevrilmiştir.
  - Kaynak: *"Chue grinned and tickled her."*
  - Çeviri: *"Chue gülümsedi ve onu kaşıdı."*
- **ANLAM_KAYMASI**: "On edge" ifadesi gergin, huzursuz veya tetikte olmak anlamına gelir. "Geride" olarak çevrilmesi tamamen yanlış bir anlam vermiştir.
  - Kaynak: *"Everyone’s on edge right now"*
  - Çeviri: *"Şu anda herkes geride"*

## Bölüm 14: Chapter 12: Mother versus Son — 7 sorun
- **ATLANMIŞ**: Suiren, Chue ve Baryou'nun tepkilerini ve eylemlerini anlatan paragraf Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"“My goodness!” Suiren put her hands to her cheeks and laughed, while Chue was uncharacteristically silent"*
- **ANLAM_KAYMASI**: "quack" (vaklama) kelimesi yanlış anlaşılarak "kükürt" (sulfur) olarak çevrilmiştir.
  - Kaynak: *"The duck gave a sympathetic quack and flapped her wings."*
  - Çeviri: *"Ördek, empati dolu bir kükürt sesi çıkardı ve kanatlarını çırptı."*
- **ANLAM_KAYMASI**: "Who are you calling Mother?" (Kime anne diyorsun?) ifadesi, "Kimin annesini çağırıyorsun?" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“Who are you calling Mother? We’re at work, here!”"*
  - Çeviri: *"“Kimin annesini çağırıyorsun? Burada çalışıyoruz!”"*
- **ANLAM_KAYMASI**: "her disgust" (tiksintisi/iğrenmesi) ifadesi, "kendi iğrençliği" (kendisinin iğrenç olması) şeklinde yanlış çevrilmiştir.
  - Kaynak: *"Jinshi could tell Taomei was barely holding back her disgust herself."*
  - Çeviri: *"Jinshi, Taomei’nin kendi iğrençliğini nasıl zorla tuttuğunu anlayabiliyordu."*
- **ANLAM_KAYMASI**: Jinshi'nin kendisini kastettiği "gain me" (bana kazandıracağını) ifadesi, çeviride "size" şeklinde yanlış bir şahsa yöneltilmiştir.
  - Kaynak: *"“Do you think that would gain me anything?”"*
  - Çeviri: *"“Bunun size bir şey kazandıracağını mı düşünüyorsunuz?”"*
- **ANLAM_KAYMASI**: "How about this?" (Buna ne dersiniz? / Şöyle yapsak nasıl olur?) önerisi, "Nasıl olsa şöyle?" şeklinde yanlış ve anlamsız çevrilmiştir.
  - Kaynak: *"At length, Chue ventured, “How about this?”"*
  - Çeviri: *"Sonunda Chue cesaret etti, “Nasıl olsa şöyle?” dedi."*
- **ANLAM_KAYMASI**: "in my stead" (benim yerime) ifadesi "benim adımıma" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"“I grant you that belt. Put it on and go to work in my stead.”"*
  - Çeviri: *"“Bu kuşağı sana veriyorum. Giy ve benim adımıma işe git.”"*

## Bölüm 15: Chapter 13: A Visit to the Ill — 5 sorun
- **ANLAM_KAYMASI**: "Dandelions" (karahindiba) kelimesi "papatyalar" (daisies) olarak yanlış çevrilmiştir.
  - Kaynak: *"We’re also out of the dandelions that were filling in for tea leaves."*
  - Çeviri: *"Ayrıca çay yaprağı yerine kullanılan papatyalar da bitti."*
- **ANLAM_KAYMASI**: "My old man" (babam/ihtiyar) ifadesi "eski babam", "body double" (benzeri/dublörü) ise "ikizi" olarak yanlış çevrilmiştir.
  - Kaynak: *"Even if he is here as a body double for my old man."*
  - Çeviri: *"Eski babamın ikizi olarak burada olsa da."*
- **ANLAM_KAYMASI**: "Brother-in-law" (kayınbirader) kelimesi "kayınpeder" (father-in-law) olarak yanlış çevrilmiştir.
  - Kaynak: *"Even she saw fit to refer to her brother-in-law as “Master”"*
  - Çeviri: *"O bile o anda kayınpederine “Usta” hitap etmeye uygun gördü."*
- **ANLAM_KAYMASI**: "Attending Dr. You" (Dr. You'ya eşlik ediyor/yardımcı oluyor) ifadesi, Dr. You'yu tedavi ediyorlarmış gibi "Dr. You'ya bakıyoruz" şeklinde yanlış çevrilmiştir.
  - Kaynak: *"Attending Dr. You today."*
  - Çeviri: *"Bugün Dr. You’ya bakıyoruz."*
- **ŞAHIS_UYUŞMAZLIĞI**: Kaynakta üçüncü tekil şahıs ("he") kullanılırken, çeviride ikinci çoğul şahıs ("başladığınızda") kullanılmıştır.
  - Kaynak: *"Once he seemed to be getting the hang of it"*
  - Çeviri: *"İşin püf noktasını kavramaya başladığınızda"*

## Bölüm 16: Chapter 14: Tianyu — 5 sorun
- **ATLANMIŞ**: Bölümün en başındaki ilk paragraf Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"After some discussion of how to handle Dr. You’s shy streak, it was determined"*
- **ANLAM_KAYMASI**: Kaynak metindeki 'tekrar takılabileceğini sanmıyorum' ifadesi, çeviride çift olumsuzluk yapılarak 'takılamayacağını düşünmüyorum' (yani takılabileceğini düşünüyorum) şeklinde ters anlamda çevrilmiştir.
  - Kaynak: *"I don’t think it can be reattached"*
  - Çeviri: *"tekrar takılamayacağını düşünmüyorum"*
- **ANLAM_KAYMASI**: 'Glowered' (öfkeyle/ters ters bakmak) kelimesi 'kıskançlıkla baktı' şeklinde yanlış çevrilmiştir.
  - Kaynak: *"glowered at Dr. Li’s back"*
  - Çeviri: *"Dr. Li’nin arkasına kıskançlıkla baktı"*
- **ANLAM_KAYMASI**: 'Young man' (genç adam) ifadesi 'yaşlı bir adam' olarak tamamen zıt anlamda çevrilmiştir.
  - Kaynak: *"maybe you could call him a young man"*
  - Çeviri: *"yaşlı bir adam da diyebilirsin"*
- **ANLAM_KAYMASI**: Bu paragraf ve takip eden birkaç paragraf çeviride tamamen yer değiştirmiş, sırası bozulmuş ve araya kaynakta olmayan 'Evet, efendim.' ifadesi eklenerek konuşmanın mantık akışı bozulmuştur.
  - Kaynak: *"It was his connections, in a way. I said to his father..."*
  - Çeviri: *"Bir bakıma, bağlantıları sayesindeydi. Babasına, avcıya..."*

## Bölüm 17: Chapter 15: Violence
*(Denetlenemedi.)*

## Bölüm 18: Chapter 16: Gyokuen’s Children — 3 sorun
- **ANLAM_KAYMASI**: Kaynakta Jinshi, İmparatoriçe'nin Gyoku-ou ile başa çıkabilecek iyi bir konumda olmadığını belirtirken, çeviride çift olumsuzluk kullanılarak tam tersi bir anlam verilmiştir.
  - Kaynak: *"But I don’t think she’s in a good position to deal with Sir Gyoku-ou."*
  - Çeviri: *"Ama İmparatoriçe’nin Sir Gyoku-ou ile başa çıkacak durumda olmadığını düşünmüyorum."*
- **TUTARSIZ_TERİM**: Aynı unvan (Emperor) metnin farklı yerlerinde hem 'İmparator' hem de 'Padişah' olarak tutarsız bir şekilde çevrilmiştir.
  - Kaynak: *"Emperor's younger brother / His Majesty the Emperor"*
  - Çeviri: *"İmparator’un küçük kardeşinden / Padişah’ın ataları"*
- **ANLAM_KAYMASI**: Maomao'nun Jinshi'nin yanındaki hizmetçi/nedime rolünü belirten 'lady-in-waiting' ifadesi 'hanımefendi' olarak yanlış çevrilmiştir.
  - Kaynak: *"during her time as Jinshi’s lady-in-waiting"*
  - Çeviri: *"Jinshi’nin hanımefendisi olarak geçirdiği süre boyunca"*

## Bölüm 19: Chapter 17: In the Shadow of the Ritual — 3 sorun
- **ATLANMIŞ**: Bölüm başlığı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 17: In the Shadow of the Ritual"*
- **ANLAM_KAYMASI**: Karakterin tıraş olamadığı için çenesinde kirli sakal çıkmaya başladığı belirtilirken, çeviride 'sakal tıraşı olmaya başlayan' denilerek tam tersi bir anlam verilmiştir.
  - Kaynak: *"stroking his chin, which was gradually acquiring a stubble"*
  - Çeviri: *"yavaşça sakal tıraşı olmaya başlayan çenesini okşayarak"*
- **ANLAM_KAYMASI**: Lihaku'nun diğer muhafızlardan artık ses çıkmadığını/alay edilmediğini belirttiği cümle, kendisinin kimseyle konuşmadığı şeklinde yanlış çevrilmiştir.
  - Kaynak: *"since that mob the other night, I haven’t heard a word from anyone."*
  - Çeviri: *"o geceki kalabalıktan beri kimseyle bir kelime bile konuşmadım."*

## Bölüm 20: Chapter 18: The Siblings’ Conference — 4 sorun
- **ANLAM_KAYMASI**: 'three faces' (üç çehre/yüz) ifadesi, Türkçe sayı olan 'üç yüz' (300) şeklinde çevrilerek anlam karmaşasına yol açmıştır.
  - Kaynak: *"There were also three faces that Rikuson didn’t recognize."*
  - Çeviri: *"Ayrıca Rikuson’un tanımadığı üç yüz daha vardı."*
- **ANLAM_KAYMASI**: 'outtalking' (laf dalaşında bastırmak/susturmak) kelimesi tam tersi anlamda 'konuşturma' olarak çevrilmiştir.
  - Kaynak: *"it almost seemed the younger sister had succeeded in outtalking her elder brother"*
  - Çeviri: *"küçük kız kardeşinin büyük abisini konuşturma konusunda başarılı olduğu gibi göründü"*
- **ANLAM_KAYMASI**: 'I've been entrusted with...' (Tekstil sanayisi bana emanet edildi) ifadesi, özne ve nesne ilişkisi karıştırılarak 'Ben sanayiye emanet edildim' şeklinde yanlış çevrilmiştir.
  - Kaynak: *"I’ve been entrusted with the western capital’s whole textile industry."*
  - Çeviri: *"Batı başkentinin tüm tekstil sanayisine emanet edildim."*
- **ANLAM_KAYMASI**: 'By all rights' (Aslında, normal şartlarda) kalıbı, 'sahip olduğu haklar uyarınca' anlamına gelecek şekilde 'Hakları gereği' olarak yanlış çevrilmiştir.
  - Kaynak: *"By all rights, Rikuson should have been in the plaza, observing the ritual."*
  - Çeviri: *"Hakları gereği Rikuson, ritüeli gözlemlemek için meydanda olmalıydı."*

## Bölüm 21: Chapter 19: The Weeping Wind (Part One) — 4 sorun
- **ANLAM_KAYMASI**: Kaynakta Gyoku-ou'nun bülbül yerine kartal gibi güçlü bir isim dilediği belirtilirken, çeviride tam tersi şekilde kartal yerine zayıf bir kuşun adını dilediği söylenerek anlam tersine çevrilmiştir.
  - Kaynak: *"He wished, though, that she had named him after the eagle instead."*
  - Çeviri: *"Oysa Gyoku-ou, annesinin onu kartal yerine sığırtikan gibi zayıf bir kuştan sonra adlandırmasını diledi."*
- **ANLAM_KAYMASI**: Bu diyalog satırı Türkçe çeviride kronolojik olarak çok daha erken ve alakasız bir yere yerleştirilerek metnin akışını ve anlamını bozmuştur.
  - Kaynak: *"“Of course it’s my concern. I’m your older brother.”"*
  - Çeviri: *"“Tabii ki benim işim. Ben senin büyük kardeşin.”"*
- **ANLAM_KAYMASI**: Kaynakta annenin kendisinin eski bir Rüzgar Okuyucu olduğu belirtilirken, çeviride onun soyundan geldiği ifade edilmiştir.
  - Kaynak: *"Takubatsu’s mother had been an enslaved former Windreader."*
  - Çeviri: *"Takubatsu’nun annesi, köleleştirilmiş eski bir Rüzgar Okuyucu’dan geliyordu."*
- **TUTARSIZ_TERİM**: Kaynakta geçen 'hawk' (şahin/atmaca) ve 'eagle' (kartal) kelimelerinin her ikisi de çeviride 'kartal' olarak karşılanmıştır.
  - Kaynak: *"hawk"*
  - Çeviri: *"kartal"*

## Bölüm 22: Chapter 20: The Weeping Wind (Part Two) — 5 sorun
- **ATLANMIŞ**: Bölüm başlığı ve ilk paragraf Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 20: The Weeping Wind (Part Two)

His mother had often said to him, “When you grow up, you’ll become the wind.”"*
- **ANLAM_KAYMASI**: İngilizce cümledeki 'görüyorum ki yanında...' anlamı kaybolmuş ve 'Seninle küçük bir Piyonun var' şeklinde bozuk ve yanlış bir anlamla çevrilmiştir.
  - Kaynak: *"“I see you have a little Pawn with you,” the man said"*
  - Çeviri: *"“Seninle küçük bir Piyonun var,” dedi adam"*
- **ANLAM_KAYMASI**: 'holding him to fifty-fifty' (başa baş gitmek, yarı yarıya berabere kalmak) ifadesi Türkçe karşılığı olmayan 'beşeride tutuyordu' şeklinde yanlış çevrilmiştir.
  - Kaynak: *"But this visitor seemed to be holding him to fifty-fifty in their games."*
  - Çeviri: *"Ama bu ziyaretçi, oyunlarında onu beşeride tutuyordu."*
- **ANLAM_KAYMASI**: 'No one would have dared' (kimse cesaret edemezdi) ifadesi tam tersi anlam verecek şekilde 'cesaret ederdi' olarak çevrilmiştir.
  - Kaynak: *"No one would have dared to say such a thing"*
  - Çeviri: *"kimse böyle bir şey söylemeye cesaret ederdi"*
- **ANLAM_KAYMASI**: 'What's to get?' (Anlaşılmayacak ne var?) sorusu, 'get' kelimesinin yanlış anlamlandırılmasıyla 'Ne kazanacaksın ki?' şeklinde hatalı çevrilmiş ve diyalog sırası karıştırılmıştır.
  - Kaynak: *"“What’s to get? You see them a few times, you remember them, right?”"*
  - Çeviri: *"“Ne kazanacaksın ki? Birkaç kez görürsün, hatırlarsın, değil mi?”"*

## Bölüm 23: Chapter 21: The Strategist Takes Command — 4 sorun
- **ATLANMIŞ**: Bölüm başlığı Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Chapter 21: The Strategist Takes Command"*
- **ANLAM_KAYMASI**: "Lady-in-waiting" (nedime) ifadesi metin genelinde hatalı bir şekilde "hazinedar" olarak çevrilmiştir.
  - Kaynak: *"lady-in-waiting"*
  - Çeviri: *"hazinedar"*
- **ANLAM_KAYMASI**: Bu diyalog satırı Türkçe çeviride yanlış bir yere (metnin yukarısına) yerleştirilmiş, asıl bulunması gereken yerde ise "Ne demek?" şeklinde hatalı çevrilmiştir.
  - Kaynak: *"“I certainly will. Might I make one request in exchange?”"*
  - Çeviri: *"“Kesinlikle yapacağım. Bir teklifim olabilir mi karşılığında?”"*
- **ATLANMIŞ**: Chue'nun "What would that be?" şeklindeki sorusu Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"“What would that be?”"*

## Bölüm 24: Chapter 22: The Imperial Younger Brother’s Complaint — 5 sorun
- **ANLAM_KAYMASI**: "drifted down" (üzerlerine düşene/konana kadar) ifadesi "düne kadar" (until yesterday) şeklinde tamamen yanlış çevrilerek anlamsız bir cümle oluşturmuştur.
  - Kaynak: *"until the sparks drifted down on their own heads."*
  - Çeviri: *"kıvılcımlar kendi başlarına düne kadar."*
- **ANLAM_KAYMASI**: "lady-in-waiting" (nedime/saray görevlisi) terimi yanlış bir şekilde "hazinedar" (treasurer) olarak çevrilmiştir.
  - Kaynak: *"she was also a capable lady-in-waiting"*
  - Çeviri: *"aynı zamanda yetenekli bir hazinedardı"*
- **ATLANMIŞ**: Maomao'nun sorduğu "Can't one of them do it?" (Onlardan biri yapamaz mı?) sorusu çeviride tamamen atlanmıştır.
  - Kaynak: *"“Can’t one of them do it?”"*
- **ANLAM_KAYMASI**: "a thorn in someone's side" (birinin ayağına batan diken/baş belası) deyimi, "yanaklarını kaşıyan bir diken" şeklinde son derece hatalı ve gerçek dışı bir şekilde kelimesi kelimesine çevrilmiştir.
  - Kaynak: *"Gyoku-ou had been a thorn in Jinshi’s side"*
  - Çeviri: *"Jinshi’nin yanaklarını kaşıyan bir diken olmuştu"*
- **ANLAM_KAYMASI**: "Do you think..." (Sence ... mi?) sorusu, anlamı tamamen değiştirecek şekilde "Sanıyorsun ki..." (You think that...) olarak çevrilmiştir.
  - Kaynak: *"Do you think the family was able to get away?"*
  - Çeviri: *"Sanıyorsun ki aile kaçabildi mi?"*

## Bölüm 25: Epilogue — 4 sorun
- **ATLANMIŞ**: Bu cümle Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Suddenly, he thought he heard a voice: 'No, you can’t!'"*
- **ANLAM_KAYMASI**: Kaynaktaki 'he' zamiri Gyokuen'i kastederken, çeviride bu kişi yanlış bir şekilde 'Gyoku-ou' olarak aktarılmıştır.
  - Kaynak: *"and he had changed her name to Gyokuyou."*
  - Çeviri: *"ve Gyoku-ou onun adını Gyokuyou olarak değiştirdi."*
- **ANLAM_KAYMASI**: Saray nedimeleri anlamına gelen 'ladies-in-waiting' terimi yanlış bir şekilde 'hazinedar' olarak çevrilmiştir.
  - Kaynak: *"ladies-in-waiting"*
  - Çeviri: *"hazinedarları"*
- **ANLAM_KAYMASI**: Kaynaktaki 'As you will' ifadesi başlangıçta çevrilmemiş, bunun yerine metnin alakasız bir yerine 'İstediğin gibi. “Kuşlar...”' şeklinde hatalı bir ekleme yapılmıştır.
  - Kaynak: *"As you will."*
  - Çeviri: *"İstediğin gibi. “Kuşlar...”"*

## Bölüm 26: Translator’s Notes – The Apothecary Diaries vol. 11 — 3 sorun
- **ATLANMIŞ**: Metnin en başındaki ana başlık Türkçe çeviride tamamen atlanmıştır.
  - Kaynak: *"Translator’s Notes – The Apothecary Diaries vol. 11"*
- **ANLAM_KAYMASI**: Shogi ve satrançta yer alan 'Bishop' (Fil) taşı, Türkçe çeviride uydurma bir kelime olan 'Buşep' olarak çevrilmiştir.
  - Kaynak: *"promoted form of the Bishop (kakugyou)"*
  - Çeviri: *"Buşepin (kakugyou) taşının yükseltilmiş halidir"*
- **ATLANMIŞ**: Kaynak metindeki '二歩' kanji karakterleri Türkçe çeviride yazılmamış, bu yüzden cümle 'notasyonundaki 'dur' şeklinde eksik ve bozuk kalmıştır.
  - Kaynak: *"The word “nifu” is the Shogi notation 二歩, or a kanji 2"*
  - Çeviri: *"“Nifu” kelimesi, Shogi notasyonundaki ’dur, yani bir kanji 2"*

## Bölüm 27: Copyright — 2 sorun
- **ATLANMIŞ**: Kitabın adı ve cilt numarası Türkçe çeviride yer almamaktadır.
  - Kaynak: *"The Apothecary Diaries: Volume 11"*
- **ATLANMIŞ**: İngilizce çevirmenin adı Türkçe metinde atlanmıştır.
  - Kaynak: *"Translated by Kevin Steinbach"*
