## Bölüm Özeti

- UART asenkron, iki telli ve saat hattı olmayan bir protokoldür; 8N1 çerçevesi 10 bittir ve alıcı her bit ortasında örnek alır.
- İki saatin toplam sapması kabaca %5'i geçerse, belirli baytlar bozulmaya başlar; bu bir bayt bazında bir sınırdır ve tek bir baytla ölçülmemelidir.
- COBS, çerçeve sınırını kodlu veride sıfır olmayarak çözer; ek yükü her 254 baytta yalnızca bir bayttır.
- CRC-16 bütünlük denetimidir; toplama sağlaması yer değişimini yakalamaz, CRC yakalar. CRC kimlik doğrulama değildir.
- SPI tam çift yönlü bir kaydırma yazmacıdır; CPOL ve CPHA birlikte örnekleme kenarını belirler ve kip uyumsuzluğu bit kaymasına yol açar.
- I2C açık-drenajdır; çekme direnci hız ve kapasitansa göre seçilir. Tahkim, adres ve ACK bitleri protokolün kalbidir; kilitlenme dokuz saat darbesiyle çözülür.
- CAN'de tahkim yıkıcı değildir: en küçük kimlik kazanır. Bit doldurma senkronu korur; CRC-15 bütünlüğü denetler.
- EV Dashboard'da doğrulanmamış Daly yanıtı, 0x95 çözümlemesi, sessiz JSON ve servis çökmesi gibi gerçek sorunlar var; sağlamlaştırılmış çerçeve bunların çoğunu kapatır.

**Sonraki bölümde:** Bölüm 46'da, bu bölümdeki gömülü veri hatlarından çıkıp mikrodenetleyicide çalışan **Edge AI ve TinyML**'e geçeceğiz. Sensörden gelen ham veriyi bu bölümdeki gibi güvenilir biçimde taşımak, orada modelin girdisini oluşturmanın ön koşuludur.

::: mulakat
1. UART'ta iki tarafın saat sapması neden %5 civarında bir sınıra bağlı? Bu sınırı 8N1 çerçevesi üzerinden türet.
2. SPI'de CPOL ve CPHA değiştiğinde hangi bitlerin okunduğu değişir? Neden iki parametreden biri yanlışsa bit kayması oluşabilir?
3. I2C'de çekme direncinin üst ve alt sınırını yazan iki formülü ve hangi fiziksel etkiye dayandıklarını anlat.
4. CAN tahkiminin "yıkıcı olmaması" ne demektir? Düğümler neden kendi mesajlarını bozmadan öncelik belirleyebilir?
5. Toplama sağlaması ile CRC arasındaki farkı, yer değişimi örneğiyle açıkla. Hangisi bir saldırgana karşı işe yarar?
6. Ayraçlı bir çerçevede veriyi kaçışlamak neden gerekir? COBS'un SLIP'e göre avantajı nedir?
7. Kesme ile halka tampon kullanan bir UART alıcısında üretici ve tüketici hangi değişkenleri yazar? Neden bu ayrım kilitsiz çalışmayı mümkün kılar?
8. Bir sensör değerinin ne kadar "taze" olduğunu bilmek neden çerçeve içeriği kadar önemlidir? Bu bilgiyi hangi alanla taşırsın?
