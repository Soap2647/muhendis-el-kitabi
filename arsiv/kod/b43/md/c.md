
## Çözümlü Örnekler

Her örnek bölümdeki kavramları bir soruyu adım adım çözerek sınar. Altı adımı izle: Anla, Örnekle, Kaba çöz, Örüntü, İyileştir, Doğrula. Adım 6'da her zaman elle iz sürme tablosu bulunur; bu tablo kendi bilgisayarında kontrol edebileceğin bir kanıttır.

### Örnek 1 (★): PD12'nin modunu bit maskesiyle değiştirmek

**Soru.** GPIOD `MODER` yazmacının değeri `0x26000000` ve pin 12 şu anda alternatif işlev modunda (`10`). Pin 12'yi genel çıkış (`01`) yap; diğer pinlere dokunma.

**Adım 1 — Anla.** `MODER`'de her pin iki bittir. Pin `n` için bitler `[2n+1 : 2n]` aralığındadır. Pin 12 için bu `[25:24]`tür. Değişecek yalnızca bu iki bit; diğer 30 bit aynı kalmalıdır.

**Adım 2 — Örnekle.** Değerin ikili hâli pin 15'ten pin 12'ye doğru `00 10 01 10`dur. Pin 14 `10`, pin 13 `01` olarak yanında duruyor; bunların değişmemesi gerekiyor.

**Adım 3 — Kaba çöz.** Önce pin 12'nin iki bitini sıfırla, sonra `01` değerini yaz. Sıfırlamak için bir maske gerekir: `3u << 24` değeri `0x03000000`dır ve bu iki biti seçer. Ters maske `~(3u << 24)` diğer tüm bitleri 1 yapar.

**Adım 4 — Örüntü.** Her "bit alanı değiştirme" işlemi aynı üç adımdan oluşur: (1) alanı temizle (`&= ~maske`), (2) yeni değeri alan konumuna kaydırarak yaz (`|= deger << konum`). Bölüm 43.5'teki okuma-değiştirme-yazma tehlikesi de burada geçerlidir: bu işlem yazmaç üzerinde tek bir RMW'dir.

**Adım 5 — İyileştir.** Tek satırda yaz ve yorum ekle:

```c
GPIOD->MODER = (GPIOD->MODER & ~(3u << 24)) | (1u << 24);
```

Bu ifadede `1u << 24` değeri `01` modunu, `3u << 24` maskesi iki biti temsil eder. Konumu sabit yazmak yerine `2u * LED_PIN` gibi bir ifade kullanırsan kod pin değiştikçe de doğru kalır. Yine de bu bir RMW olduğundan, aynı yazmaca bir kesmeden erişiliyorsa kritik bölgede kesmeleri kapatmak gerekir (Bölüm 27).

**Adım 6 — Doğrula.** Aşağıdaki iz tablosunda her adımın yazmaç değerini ikili olarak yazdık. Bunu bir C programında da test ettik (`host/ornek_dogrula.c`, derleme: WSL gcc `-O2 -Wall -Wextra -std=c11`). Çıktı tablodakiyle aynı:

| Adım | İşlem | Pin 15 | Pin 14 | Pin 13 | Pin 12 | `MODER` (hex) |
|---|---|---|---|---|---|---|
| 0 | Başlangıç | 00 | 10 | 01 | 10 | `0x26000000` |
| 1 | `&= ~(3u << 24)` | 00 | 10 | 01 | 00 | `0x24000000` |
| 2 | `\|= (1u << 24)` | 00 | 10 | 01 | 01 | `0x25000000` |

Pin 14 ve pin 13 üç adımda da aynıdır; yalnızca pin 12 iki bitinin değiştiği görülür. Son satır, `01`in gerçekten pin 12'de olduğunu gösterir.

**Bunu AI'sız yazabilir misin?** Pin 5'in `MODER` alanını `10` (alternatif işlev) yapan bir ifade yaz. Başlangıç değeri `0x00000C00` olsun (pin 5 şu anda `11`). Sonucu önce ikili olarak elle hesapla, sonra ifadeyi bir C programında çalıştırıp `0x00000800` çıkıp çıkmadığını kontrol et.

### Örnek 2 (★★): Bit-band takma adresini elle hesaplamak

**Soru.** SRAM'de `0x20000004` adresindeki kelimenin 3. bitinin bit-band takma adresi nedir? Ayrıca GPIOD ODR'nin bit 31 ve bit 0 takma adreslerini bul.

**Adım 1 — Anla.** Bit-band'in iki bölgesi vardır: çevre birimi (`0x40000000`, takma taban `0x42000000`) ve SRAM (`0x20000000`, takma taban `0x22000000`). Formül her iki bölge için aynıdır, yalnızca taban değişir.

**Adım 2 — Örnekle.** `0x20000004` SRAM bölgesinin 4. baytıdır. Bu, bölge başından 4 bayt uzaklıkta demektir. Bit 3 ise kelimenin içindeki 3. bittir.

**Adım 3 — Kaba çöz.** Önce bayt ofsetini bulursun: `0x20000004 - 0x20000000 = 4`. Her bayt 8 bit içerir, dolayısıyla her bit için 32 takma kelime ayrılır: `4 * 32 = 128`. Sonra bit konumu için `3 * 4 = 12` eklenir. Toplam ofset `128 + 12 = 140`, yani `0x8C`; taban `0x22000000` ile birleşince `0x2200008C` çıkar.

**Adım 4 — Örüntü.** Her iki bölgede de alias adresi `taban + (ofset) * 32 + bit * 4` biçimindedir. Ofsetin `32` ile çarpılması, bayt başına 8 bit ve her bit için 4 bayt takma kelime düşünüldüğünde ortaya çıkar. Bu örüntü, bir yazmacın değişen bir bitine tek yazma ile erişmeyi sağlar.

**Adım 5 — İyileştir.** Formülü bir makroya koy ama adresleri elle hesaplamadan doğrulamak için bir fonksiyon yaz:

```c
static uint32_t bitband(uint32_t taban, uint32_t bolge,
                        unsigned b)
{
    return taban + (bolge - 0x40000000u) * 32u + b * 4u;
}
```

Yalnızca çevre birimi bölgesi için kullanıyor; SRAM için `bolge` yerine `0x20000000` ve taban olarak `0x22000000` verilmelidir. Bu basit ayrıntıyı unutmak, çevre birimi taban adresinin SRAM için kullanılması demektir.

**Adım 6 — Doğrula.** Bu hesabı, adres değerlerini çalıştırarak sınadık. Program Örnek 1 ve Örnek 2'yi birlikte sınar; tam kodu ve çıktısı aşağıda.

```c
{{KOD:host/ornek_dogrula.c}}
```

```term
$ gcc -O2 -Wall -Wextra -std=c11 ornek_dogrula.c -o ornek_dogrula
$ ./ornek_dogrula
{{CIKTI:cikti/ornek_dogrula_temiz.txt}}
```

Çıktının ilk üç satırı Örnek 1'in sonuçlarıdır; dördüncü satır elle hesabımızı doğruluyor: SRAM için `0x2200008C`. Son iki satır GPIOD ODR için bit 31 (`0x424182FC`) ve bit 0 (`0x42418280`) değerleridir. Bit 12 değeri Bölüm 43.5'teki `0x424182B0` ile aynı hesap yolundan gelir.

**Bunu AI'sız yazabilir misin?** `0x40020C18` (GPIOD BSRR) yazmacunun bit 16 takma adresini hesapla. Sonucu bu bölümdeki formül ile elle doğrula, ardından bu adrese yazmanın ODR'nin hangi bitini değiştireceğini (ve neden değiştirmeyeceğini) açıkla.

### Örnek 3 (★★): Bir programın flash ve RAM bütçesini çıkarmak

**Soru.** Bir kart 16 KB flash ve 4 KB RAM içeriyor (bu bir varsayımdır; kendi kartının değerlerini kullan). Aşağıdaki programın üç sürümü bu karta sığar mı? Sürümler: (a) printf'li program, (b) (a) + 2 KB UART alım tamponu, (c) (b) + 1 KB ek tampon. Yığın için 1 KB ayır.

**Adım 1 — Anla.** Flash kullanımı `text + data`, RAM kullanımı `data + bss` ile hesaplanır (Bölüm 43.7). Yığın bu toplamın üstüne eklenir, çünkü yığın yalnızca çalışma zamanında belli olur; yani bütçede ayrıca rezerv edilir.

**Adım 2 — Örnekle.** Önceki ölçümde printf'li programın `size` çıktısı `text 5688`, `data 92`, `bss 344` idi (Bölüm 43.10). Flash: `5688 + 92 = 5780`. RAM: `92 + 344 = 436`.

**Adım 3 — Kaba çöz.** (a) için RAM `436 + 1024 (yığın) = 1460`. Bu 4096'dan küçük. (b) için RAM `436 + 2048 = 2484`, yığınla birlikte `3508`. Yine 4096 içinde. (c) için `2484 + 1024 = 3508`, yığınla `4532`. Bu 4096'dan büyük.

**Adım 4 — Örüntü.** Her tampon eklendiğinde RAM kullanımı tampon boyutu kadar artar. Yığın sabit bir rezervdir. Bütçe denetimi her eklemeden sonra aynı üç sayıyı karşılaştırmaktır: flash toplamı, RAM toplamı, RAM toplamı artı yığın. Bu örüntü Bölüm 43.7'deki `ASSERT` satırının elle yapılmış hâlidir.

**Adım 5 — İyileştir.** Tabloyu bir betik yerine bağlayıcının kendi denetimine bırak: bağlayıcı betiğindeki `RAM` uzunluğunu 4 KB yap ve `ASSERT` satırını koru. Beklenen davranış, sürüm (c)'yi derlediğinde bağlayıcının taşmayı hata olarak bildirmesidir; bu, elle yapılan hesabın bir makine denetimidir. (Bu deneyi kitap kapsamında çalıştırmadık; kendin dene.) Ayrıca yığını `-fstack-usage` ile gerçek değerlerle doğrula (Bölüm 43.9).

**Adım 6 — Doğrula.** Aşağıdaki tabloda her aşamanın değerleri, kenar durumu dahil yer alıyor. Tamponlar sayısal değerler olarak yazıldı; asıl ölçüm sürümlerin kendilerinde yapılmalıdır.

| Aşama | Flash (text + data) | RAM (data + bss + tampon) | RAM + yığın (1024) | 4096 içinde mi? |
|---|---|---|---|---|
| (a) printf'li program | 5780 | 436 | 1460 | evet |
| (b) + 2048 UART tamponu | 5780 | 2484 | 3508 | evet |
| (c) + 1024 ek tampon | 5780 | 3508 | 4532 | **hayır, 436 bayt fazla** |

Flash her aşamada 16384 içinde kalır; darboğaz RAM'dir. Bu, gömülü tasarımda sık görülen bir durumdur: flash genellikle RAM'den bol olur, bu yüzden tampon boyutları bütçenin asıl belirleyicisidir.

Yığın tahmini için `-fstack-usage` ürettiği dosyayı okuyalım. Bu örnekte bir çağrı zinciri (`main` → `dis` → `orta` → `ic_fonk`) var; bu programın `.su` dosyası şöyle:

```term
$ cat yigin.su
{{CIKTI:cikti/yigin_su.txt}}
```

Zincirin toplamı `8 + 8 + 16 + 64 = 96` bayttır. Bu bir **alt sınırdır**: dönüş adresleri, kesme çerçeveleri ve derleyicinin ekleyebileceği kaydetme alanları bu sayıya dahil olmayabilir. Gerçek bütçe, en derin yolun en kötü durum toplamı artı kesmelerin payıdır (Bölüm 44).

**Bunu AI'sız yazabilir misin?** Bu programa 2 KB'lık bir ikinci UART alıcı tamponu ekledin, RAM bütçesi 4096 içinde mi? Yığını 1 KB yerine 1536 bayt rezerv edersen sonuç ne olur? Tabloyu iki sütunla yeniden kur.

### Örnek 4 (★★★): C ile yazılmış başlangıç kodunun .data ve .bss işini izlemek

**Soru.** Bölüm 43.6'daki `Reset_Handler`, `.data` ve `.bss` bölümlerini hangi komutlarla ve hangi yazmaç değerleriyle hazırlıyor? İzi bir emulatörde kaydet ve her adımı yorumla.

**Adım 1 — Anla.** `Reset_Handler` iki döngü çalıştırır: birincisi `.data`yı flash'tan RAM'e kopyalar (`_sidata` → `_sdata`, uzunluk `_edata - _sdata`), ikincisi `.bss`yi sıfırlar (`_sbss` → `_ebss`). Döngülerin kaç kez döneceğini hedef ve bitiş adresleri belirler.

**Adım 2 — Örnekle.** Bu programda `.data` 4 bayttır (`acilis_degeri`), `.bss` 8 bayttır (`sonuc_menzil` ve `dongu_sayaci`). Dolayısıyla `.data` döngüsü bir, `.bss` döngüsü iki kez dönmelidir.

**Adım 3 — Kaba çöz.** İzi emulatörde almak için harness'a her komutun adresini ve R1-R3 yazmaçlarının komuttan önceki değerini kaydetmesini söyledik (Bölüm 43.8). Sonuçlar `startup_iz.csv` dosyasına yazıldı ve tablo oradan üretildi.

**Adım 4 — Örüntü.** İzde iki döngünün başı ve sonu şöyle görünür: `cmp` ile bitiş adresi karşılaştırılır, `bne` ile geri dönülür. `.data` döngüsünde R1 bitiş adresini (`0x08000168`) tutar, R3 kaynak işaretçisidir ve `ldr.w r0, [r3], #4` ile `str.w r0, [r2], #4` komut çiftini kullanır. `.bss` döngüsünde ise R2 bitiş adresini (`0x2000000C`), R3 hedef işaretçisini tutar ve `str.w r1, [r3], #4` ile sıfır yazılır.

**Adım 5 — İyileştir.** Bu izden iki gözlem çıkarırsın: (1) `.data` ve `.bss` döngüleri için adres aralığının bitiş değerleri doğru hesaplanmıştır, çünkü bağlayıcı sembolleri (`_edata`, `_ebss`) RAM sınırlarını gösterir; (2) toplam komut sayısı 36'dır ve bu, startup'ın gecikmeye ihtiyaç duymadığını gösterir. Eğer `.bss` çok büyük olsaydı bu döngü de uzardı; bu nedenle `.bss` boyutu da ölçülmelidir.

**Adım 6 — Doğrula.** Aşağıdaki tablo, emulatörün kaydettiği 36 komutun tamamıdır. Her satır, komut çalıştırılmadan önceki yazmaç değerlerini gösterir. Okurken `.data` döngüsünün satır 9-15, `.bss` döngüsünün satır 25-31 arasında olduğuna dikkat et.

{{TABLO:cikti/iz_tablo.md}}

Tablo emulatörde elde edilmiştir; bu bir donanım ölçümü değildir. Ama aynı kodun ARM komutlarını işlediğini ve adreslerin bağlayıcı sembolleriyle tutarlı olduğunu gösterir: 0x08000164 `_sidata`, 0x20000004 `_sbss`, 0x2000000C `_ebss` (bkz. Bölüm 43.7'deki `nm` çıktısı).

**Bunu AI'sız yazabilir misin?** Aynı startup'ı `.data` iki kelime (8 bayt) ve `.bss` üç kelime (12 bayt) olacak şekilde değiştir. Döngülerin kaç kez döneceğini ve tablonun kaç satır uzayacağını önceden tahmin et; sonra emulatörde ölçerek kontrol et.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, bağlayıcı betiğini ve testleri kendin yaz. Derleyici uyarılarını ve `objdump`, `size` çıktılarını kendin oku. Takıldığında yalnızca bu bölümdeki ilgili kısma dön; cevabı kopyalama.
:::

### Proje 1 (★★): Sıfırdan Cortex-M4 iskeleti ve bütçe raporu

**Amaç.** Bu bölümdeki dosyalara bakmadan, bir Cortex-M4 hedefi için minimal bir iskelet kur: vektör tablosu, C ile yazılmış reset işleyicisi, bağlayıcı betiği, bir GPIO sürücüsü ve bir derleme betiği. Sonra ürettiğin ikilinin bölüm ve bütçe analizini yap.

**Beklenen davranış.** Derleme uyarısız tamamlanır. `arm-none-eabi-size` çıktısından flash ve RAM kullanımını hesaplayabilirsin. Emulatörde (Unicorn) reset'ten `main`'e ulaşan programın `.data` değerini RAM'de doğru buluyor ve `.bss`'yi sıfırlanmış görüyorsun. Bağlayıcı betiğinde RAM'i bilerek küçültüp taşma yaptığında derleme hata veriyor.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Önce vektör tablosunu tek bir dizi olarak yaz ve `.isr_vector` bölümüne koy. Sonra bağlayıcı betiğinde `.data` için `> RAM AT> FLASH` ve `.bss` için `(NOLOAD)` yazmanın gerektirdiği sembolleri (`_sidata`, `_sdata`, `_edata`, `_sbss`, `_ebss`) tanımla. Reset işleyicisinde bu sembollerle iki döngü yaz. GPIO sürücüsünü bir `struct` ile modelle ve ofsetleri `_Static_assert` ile denetle. Derleme betiğinde `-nostdlib -nostartfiles -T` bayraklarını ve `-Wl,-Map=` seçeneğini kullan. Emulatör harness'ını bu bölümden alıp kendi ikilin için uyarla.

**Başarı kriterleri.** (1) Derleme `-Wall -Wextra` ile uyarısız. (2) Emulatör raporunda `.data` değeri ve `.bss` sıfırlığı doğru. (3) Flash ve RAM kullanımını `size` çıktısından hesaplayıp bir tabloda gösterdin. (4) Bilerek bir taşma yaptığında bağlayıcı hata veriyor ve hata mesajını anlıyorsun. (5) Yığın tahminini `-fstack-usage` ile yaptın ve bir çağrı zinciri için toplamı açıkladın.

### Proje 2 (★★★): EV Dashboard'un UART sürücüsünü çıplak yazmaçla yeniden yazmak

**Amaç.** EV Dashboard'daki `Daly_VeriOku` fonksiyonunun iki HAL çağrısını (`HAL_UART_Transmit` ve `HAL_UART_Receive`) yoklamaya dayalı bir çıplak yazmaç sürücüsüyle değiştir. Zaman aşımını HAL'in yaptığı gibi bir sayaçla kendin yönet. Sonra iki sürümün kod boyutunu ve en kötü durum süresini karşılaştır.

**Beklenen davranış.** Sürücü 13 baytlık bir isteği USART'a gönderir ve 13 baytlık bir yanıt bekler. Her bekleme, bir zaman aşımı değerine bağlanır ve aşılırsa hata döndürür. Donanım yerine bir sahte yazmaç yapısı (host üzerinde `struct` ile) kullanarak sürücünün bayt sırasını ve zaman aşımını test edebilmelisin.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** USART yazmaçlarını bir `struct` olarak tanımla (SR, DR ve diğerleri; ofsetleri resmi aygıt başlığından, `stm32f407xx.h` v2.6.10 içinden, doğrula). Gönderme için SR'deki TXE bayrağını (bit 7) yokla, sonra DR'ye bir bayt yaz; hepsi bittikten sonra TC bayrağını (bit 6) bekle. Alma için RXNE bayrağını (bit 5) yokla. Zaman aşımını, bir sayaç ya da bir zaman damgası ile uygula; fonksiyonun her çağrısında süre sınırını bir parametre olarak al. Host testinde sahte yazmaç yapısında bayrakları sen değiştir.

**Başarı kriterleri.** (1) Host testinde 13 bayt doğru sırayla DR'ye yazılıyor. (2) Yanıt gelmediğinde sürücü, belirlediğin süreden sonra hata döndürüyor ve bunu bir testle gösterdin. (3) Yeni sürücünün `size` çıktısını HAL'li sürümle karşılaştırdın; HAL kaynağını ve derleme bayraklarını birlikte yazdın (HAL tarafı için kendi projendeki sürümü kullan). (4) Daly_BataryaGuncelle'nin en kötü durum süresini, bu bölümdeki tabloya benzer biçimde, kendi zaman aşımlarınla yeniden hesapladın ve 200 ms hedefiyle karşılaştırdın. (5) Kart üzerinde ölçüm yapmadıysan bunu raporda açıkça yazdın.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümleri bölümde yok. Her birini önce kâğıtta düşün, sonra yalnızca derleyici ve emulatörle doğrula.

1. (★) `GPIOx->ODR` yerine `GPIOx->BSRR` kullanarak bir pini set eden bir makro yaz. Neden kesme içinde daha güvenlidir? (Mülakat)
2. (★) Bir yazmacın bitlerini "1 yazarak temizle" (write-1-to-clear) olarak tanımlayan bir bayrak için okuma-değiştirme-yazma neden tehlikelidir? Bir örnekle açıkla. (Mülakat)
3. (★) `const uint8_t tablo[16]` dizisinin flash'ta olduğunu hangi iki komutla kanıtlarsın? Çıktıda hangi sütuna bakarsın?
4. (★) Bağlayıcı betiğinde `AT> FLASH` yazmasaydın `.data`nın davranışı ne olurdu? Reset işleyicisi hangi sembolleri kullanamazdı?
5. (★★) `volatile` bir döngüde `gecikme(n)` çağrısı `n = 0` için ne yapar? Döngünün bitiş koşulunu neden sıfır kontrolüyle yazdığımızı açıkla.
6. (★★) Yığın taşmasını çalışma zamanında yakalamak için bir yöntem öner (ipucu: yığın tepesine bir sınır deseni yazmak). Bu yöntemin kaçırabileceği bir durum var mı? (Mülakat)
7. (★) `-Os` ile `-O2` arasında boyut farkını hangi tür kod (döngü, tablo, çağrı) daha çok etkiler? Bu bölümdeki `app.c` ile ölçerek karşılaştır.
8. (★★) `offsetof` ile bir yapının dolgusunu (padding) bulan bir program yaz. Hangi alanın önünde dolgu olduğunu nasıl anlarsın? (Mülakat)
9. (★★) Thumb biti 0 olan bir vektör tablosu girişinin reset sonrası ne yaptığını, kendi kelimelerinle açıkla. (Mülakat)
10. (★★) `printf` yerine yalnızca bir karakter yazan bir `put_char` fonksiyonu koysan, `printf_yok` ile `printf_deney` arasındaki boyut farkı ne kadar kapanır? Ölç ve raporla.
11. (★★★) Bir kesme işleyicisi içinde `malloc` çağırmanın neden sorun olduğunu, Bölüm 25'teki ayırıcı kavramlarıyla açıkla. (Mülakat)
12. (★★★) Cortex-M'de `_estack` sembolünü bağlayıcıdan almak yerine sabit bir sayı yazsaydın, hangi durumda programın yanlış yığın tepesi ile çalışırdı? Bir RAM düzeni değişikliği senaryosu kur.

## Kod Okuma Egzersizi

Bu bölümde kullandığımız ARM çekirdek başlığını ARM'ın kendi açık kaynak CMSIS paketinden okuyacağız. Kaynak: `ARM-software/CMSIS_5`, etiket **5.9.0**, dosya `CMSIS/Core/Include/core_cm4.h`. Dosyanın başlığı kendi sürümünü `@version V5.1.2` olarak veriyor; bu, dosyanın paket etiketinden farklı bir sürüm numarası taşıdığı anlamına gelir ve paket sürümü ile dosya sürümünü ayırt etmek gerekir. Aşağıdaki kesitlerde alan adları, tipler, ofsetler ve koşullar kaynakla aynıdır. SCB kesitinde yorumlar kitap sayfasına sığsın diye çıkarıldı; NVIC kesitinde ise yalnızca satır sonları değiştirildi, token dizisi aynıdır. Kaynak satırları aşağıda belirtilmiştir.

İlk kesit, SCB (System Control Block) yapısı. Bu yapı, Reset_Handler'da kullandığımız CPACR yazmacını ve Bölüm 43.11'deki HardFault yazmaçlarını içerir:

```c
{{KOD:cikti/scb_sade.h}}
```

İkinci kesit, NVIC öncelik ayarlama fonksiyonu. Bu fonksiyonun kendisi Bölüm 44'ün konusudur, ama kodu şimdiden okuyabilirsin:

```c
{{KOD:cikti/nvic_sade.c}}
```

Bu fonksiyonun adı dosyada `__NVIC_SetPriority`dir; kullanıcı kodu genellikle `NVIC_SetPriority` adını kullanır ve dosyadaki `#define NVIC_SetPriority __NVIC_SetPriority` satırı bu adı buna bağlar (1617. satır).

**Sorular — cevaplamadan geçme:**

1. `SCB_Type` içinde `CPACR` alanının ofseti `0x088`dir. SCB tabanı `0xE000ED00` olduğuna göre CPACR'nin mutlak adresi nedir ve bu, Reset_Handler'daki `0xE000ED88` ile nasıl eşleşir?
2. `__NVIC_SetPriority` içinde `IRQn >= 0` ve negatif IRQn için iki farklı yazma yolu var. Hangisi dış kesmeler (`NVIC->IP`), hangisi sistem istisnaları (`SCB->SHP`) için kullanılır? Bu ayrımın neden gerekli olduğunu açıkla.
3. `(priority << (8U - __NVIC_PRIO_BITS)) & 0xFFUL` ifadesinde sol kaydırma neden yapılıyor? STM32F4 için `__NVIC_PRIO_BITS` değeri 4'tür (bkz. `stm32f407xx.h`); bu durumda öncelik değerinin hangi bitleri kullanılır?
4. `SCB_Type` alanlarının bir kısmı `__IM` (salt okunur), bir kısmı `__IOM` ile tanımlı. Bu nitelikler C'de hangi `volatile` ve `const` kombinasyonlarına karşılık gelir? Bir `__IM` alanına yazmanın derleyiciye göre ne anlama geldiğini düşün.
5. Fonksiyonlar `__STATIC_INLINE` ile tanımlanıyor. `static` ve `inline` anahtar kelimelerinin birlikte kullanılmasının, başlık dosyasının birden çok çeviri biriminde dahil edilmesi için neden önemli olduğunu açıkla.
6. Dosyanın başlığındaki `@version V5.1.2` ile etiket `5.9.0` arasındaki fark, bir CMSIS güncellemesinin hangi kısmını etkiler? Bir projede bu iki sürümü ayırt etmek için hangi bilgiyi kontrol edersin?

## Bölüm Özeti

- Gömülü sistemde işletim sistemi, sanal bellek ve dinamik bellek yoktur; her adres fiziksel, her bayt bütçeye tabidir.
- Mikrodenetleyici bir çipe işlemci, flash, SRAM, çevre birimleri, bus matrisi ve saat ağacı koyar. Çevre birimine saat vermeden yazmaca yazmak genellikle etkisizdir.
- Bellek eşlemeli G/Ç'de her yazmaç sabit bir adrestir ve her erişim `volatile` olmalıdır. `volatile`, derleyiciye erişimi atlamamasını ve silmemesini söyler; senkronizasyon sağlamaz.
- Okuma-değiştirme-yazma yarışları yazmaca bağlıdır; BSRR gibi yazma-yalnız yazmaçlar bu riski azaltır. Bit alanları taşınabilir değildir ve RMW'den kaçmaz.
- Vektör tablosunun ilk iki kelimesi başlangıç MSP ve reset adresidir; reset adresindeki Thumb biti 1'dir.
- Reset işleyicisi `.data`yı flash'tan RAM'e (LMA'dan VMA'ya) kopyalar, `.bss`yi sıfırlar ve `main`e geçer. Bağlayıcı betiği bu sembolleri ve bölge kurallarını tanımlar.
- Bütçe iki formülle çıkar: flash = text + data, RAM = data + bss; yığın ayrıca rezerv edilir. Bağlayıcının `ASSERT` denetimi taşmayı derleme zamanında yakalar.
- Yazmaç yapıları (`struct`) ofsetleriyle birlikte `_Static_assert` ile doğrulanır; CMSIS ve aygıt başlıkları aynı yöntemle kurulur.
- Derleme seçenekleri (`-Os`, `-ffunction-sections`, `--gc-sections`) ve printf'in maliyeti ölçülmeden tahmin edilmez.

**Sonraki bölümde:** Bölüm 44 — Kesme ve Zamanlayıcı. Bu bölümde yazdığımız busy-wait gecikmesi işlemciyi meşgul ediyordu ve zamanlaması komut sayısına bağlıydı. Bölüm 44'te NVIC ile kesmeleri, öncelikleri, SysTick zamanlayıcısını, timer, PWM ve watchdog'u göreceğiz; EV Dashboard'daki 200 ms döngünün de gerçek zamanlayıcıya nasıl bağlanacağını göstereceğiz.

::: mulakat
1. `volatile` tam olarak neyi garanti eder, neyi garanti etmez? Bir donanım yazmacı ile kesmeyle paylaşılan bir değişken için farkı açıkla.
2. Bir GPIO pinini `ODR |= ...` ile set etmek ile `BSRR` kullanmak arasındaki fark nedir? Hangisi kesmeler varken güvenlidir ve neden?
3. Başlangıç değeri olmayan bir global değişken hangi bölüme düşer? Reset sonrasında değeri ne olur ve bunu hangi kod sağlar?
4. Cortex-M'de vektör tablosunun ilk iki kelimesi nedir? İşlemci reset sonrası bu iki değeri nasıl kullanır?
5. RAM'i 20 KB olan bir cihazda 8 KB yığın ve 12 KB veri var. Yığın taşmasını derleme zamanında ya da çalışma zamanında nasıl tespit edersin?
6. Bir çağrıda dönüş adresi x86 ve ARM'da nerede saklanır? Bu fark bir fonksiyonun yığın kullanımını nasıl etkiler?
7. Bit alanları donanım yazmacı tanımı için neden taşınabilir değildir? Bir derleyicinin bit alanlarını farklı sıraya koyabileceği bir senaryo düşün.
8. FPU kapalıyken bir kayan nokta işlemi Cortex-M4'te ne olur ve bunu bir HardFault analizinde nasıl fark edersin?
:::
