
## 43.5 Bit işlemleri, bit alanları ve bit-band

Donanım yazmaçları bit bit anlamlıdır. Bir GPIO yazmacında her bit bir pinin durumunu taşır; bir kesme bayrağının tek bir biti "oldu" ya da "olmadı" der. Bu yüzden bit işlemleri gömülü C'nin günlük dilidir. Önce güvenilir makroları yazıp rastgele işlemlerle test edeceğiz; sonra iki tehlikeye bakacağız: okuma-değiştirme-yazma (read-modify-write) ve bit alanları (bit-field). Son olarak Cortex-M'nin bit-band özelliğine değineceğiz.

Aşağıdaki program dört bitlik işlemi ve bit-band adres hesabını birlikte sınıyor. Bit işlemleri için 100 000 rastgele işlem üretiyor, her birinde sonucu naif bir modelle karşılaştırıyor. Rastgelelik için sabit tohumlu bir xorshift kullandık; bu sayede her çalıştırmada aynı diziyi görürsün.

```c
{{KOD:host/bit_testleri.c|1-38}}
```

Fonksiyonun asıl gövdesi, bit işlemlerini modelle karşılaştıran bölümdür. Burada `switch` ile üç işlemden biri seçiliyor: set, clear ve toggle. Her işlemden sonra iki şey kontrol ediliyor: tüm yazmacın modelle aynı olması ve seçilen bitin test edilen değerinin de tutması.

```c
{{KOD:host/bit_testleri.c|39-68}}
```

Son bölüm bit-band adresini modelle karşılaştırıyor ve tamsayı yükseltme tuzağını gösteriyor.

```c
{{KOD:host/bit_testleri.c|69-}}
```

Bu programı WSL içinde, sanitizer'lar açıkken derledik. Çıktı şöyle:

```term
$ gcc -O2 -Wall -Wextra -std=c11 \
    -fsanitize=address,undefined bit_testleri.c
$ ./bit_testleri
{{CIKTI:cikti/host_bit_temiz.txt}}
```

Çıktının üç satırı önemlidir. İlk satırda 100 000 işlemde hata sayısı 0; yani set, clear ve toggle makroları naif modelle tutarlı. Bit-band satırında 96 kontrolün (3 adres x 32 bit) hiçbiri uyuşmuyor; formül ile model aynı sonucu veriyor. Üçüncü grup ise `uint8_t` tuzağıdır: `a + b` ifadesi `int`'e yükseltilir, bu yüzden 300 çıkar ve `(uint8_t)(a + b)` 44 olur. Dördüncü satır, koşulun `int` karşılaştırması olduğunu gösterir: `a + b > 255` doğrudur.

Bu tuzağın gömülüde neden önemli olduğu hemen anlaşılır: bir yazmacın 8 bitlik bir alanını okuyup bunu bir sayaçla topladığında, derleyici taşmayı 8 bit içinde değil 32 bit ya da `int` içinde yapar. Taşma sınırını elle kontrol etmezsen sonuç sessizce yanlış olur. Tamsayı yükseltme kurallarını ve işaretli taşmanın tanımsız davranış (UB) olduğunu Bölüm 1 ve Bölüm 2'de gördün; burada aynı kuralın yazmaç biçiminde nasıl göründüğünü gördün.

### Okuma-değiştirme-yazma tehlikesi

`GPIOD->ODR |= (1u << 12)` ifadesi aslında üç adımdır: yazmacı oku, bitini değiştir, sonucu yaz. Tek çekirdekli bir sistemde bu tek bir kesme gelene kadar güvenlidir; ama ana döngü `ODR`'yi okuyup yazarken bir kesme aynı yazmacın başka bir bitini değiştirirse, kesmenin yazdığı değer ana döngünün yazışıyla ezilir. Bu hataya "kayıp güncelleme" (lost update) denir ve bulması çok zordur, çünkü yalnızca nadir zamanlamalarda ortaya çıkar.

STM32'nin **BSRR** yazmacı bu sorunu donanım seviyesinde çözer. BSRR'nin düşük 16 biti bir pini set eder, yüksek 16 biti bir pini sıfırlar ve her bit için yalnızca yazılan değer etkilidir. Okuma gerekmez, bu yüzden yarış penceresi yoktur. Resmi HAL'in `HAL_GPIO_WritePin` fonksiyonu da bunu kullanır. Aşağıdaki kesit STM32F4 HAL v1.8.0 kaynağından (`stm32f4xx_hal_gpio.c`) alındı; EV Dashboard'un kullandığı HAL sürümünü bilmiyoruz, bu yüzden Mert'in projesinde sürümü kontrol etmek gerekir:

```c
{{KOD:hal/gpio.c|411-424}}
```

Fonksiyon, `PinState` değeri `GPIO_PIN_RESET` değilse `GPIOx->BSRR = GPIO_Pin` yazar; değilse pin değerini 16 bit kaydırıp `BSRR`'ye yazar. Yani yazma tek bir kayıt erişimidir; `ODR`'nin okunup değiştirilmesi gerekmez. Tasarım kararının bedeli, BSRR'nin pin durumunu **okumak için kullanılamamasıdır**: pinin durumunu öğrenmek için `ODR` ya da `IDR` okunur.

### Bit alanları (bit-field): kullanışlı ama tehlikeli

C'de bir yapının üyesinin kaç bit tutacağını belirtebilirsin. Donanım yazmacını bit alanlarıyla modellemek cazip görünür:

```c
{{KOD:host/bitfield.c|1-18}}
```

Bu yapının bit düzeni derleyiciye bırakılmıştır. C standardı bit alanlarının bellekte hangi sırayla ve hangi sınırlarla yerleşeceğini **uygulamaya bağlı** bırakır. Aynı kaynak başka bir derleyicide farklı bir düzen üretebilir ve bu yüzden donanım yazmacı için taşınabilir değildir. Ayrıca bit alanına yazmak, derleyicinin bütün kelimeyi okuyup değiştirip geri yazmasını gerektirir. Aşağıda iki fonksiyonun ARM çıktısını görüyorsun: ikisi de bir `ldr`, bir değiştirme ve bir `str` üretiyor.

```term
$ arm-none-eabi-objdump -d bitfield.o
{{CIKTI:cikti/bitfield_dis.txt}}
```

Bit alanı versiyonunda derleyici `bfi` (bit alanı yerleştir) komutunu kullandı; maske versiyonunda `bic` ve `orr` kullandı. İkisi de **okuma-değiştirme-yazma** yapar. Yani bit alanı, RMW tehlikesini ortadan kaldırmaz, yalnızca sözdizimini değiştirir. Bu yüzden gömülü projelerde iki kural yaygındır: yazmaç erişimlerini `volatile` maskeler ve sabitlerle yazarsın (Bölüm 43.8'deki `reg.h` böyle); bit alanını yalnızca yerleşimi `_Static_assert` ile sınadığın yerlerde kullanırsın. Bölüm 23'teki temiz kod ilkeleri ve MISRA C'nin yapı ve bit alanı kuralları bu tercihin arkasındadır.

### Bit-band: tek bit, tek adres

Cortex-M3 ve M4 çekirdeklerinde (genel bilgi: ARMv8-M'de bulunmaz) **bit-band** özelliği vardır. Çevre birimi bölgesinin (`0x40000000`-`0x400FFFFF`) ve SRAM bölgesinin (`0x20000000`-`0x200FFFFF`) her bitine, o bölgenin dışında ayrı bir **takma adres** karşılık gelir. Bu takma adrese yazan bir komut, yalnızca o biti değiştirir; okuma-değiştirme-yazma yapılmaz. Formül şudur:

```text
alias = bitband_baz + (adres - bolge_baz) * 32 + bit * 4
```

Çevre birimi bölgesi için `bitband_baz` `0x42000000`, bölge başı `0x40000000`dür. Bu bölümde doğruladığımız örnekte `GPIOD->ODR` yazmacı `0x40020C14` adresindedir. Bit 12 için hesap şöyle yapılır: `(0x40020C14 - 0x40000000) = 0x20C14`; bunu 32 ile çarparsan `0x418280`; bit 12 için `12 * 4 = 0x30` eklenir; sonuç `0x424182B0`. Host testi bu değeri çıktıda da verdi (`ODR bit 12 -> 0x424182B0`). Şekil 43.4 aynı hesabı şematik olarak gösteriyor.

![Şekil 43.4: Bit-band eşlemesi. Yazmacın her biti, bit-band bölgesinde kendi 32 bitlik takma kelimesine sahiptir; alias adresi yazıldığında yalnızca o bit değişir.](gorseller/b43_bit_band.png)

Bit-band'in kazancı, kesmelerle paylaşılan tek bir bayrağı okuma-değiştirme-yazma olmadan değiştirebilmektir. Ama bu özellik her Cortex-M'de yoktur ve yalnızca bu bölgeler için geçerlidir. Bu yüzden yazılımın hangi çipte çalıştığını bilmek ve bit-band'i kullanmadan önce üreticinin belgesine bakmak gerekir. Bu bölümdeki bit-band kodu bir adres hesabı olarak doğrulandı; donanım davranışı (bir alias'a yazmanın gerçekten yalnızca bir biti değiştirmesi) kartta ya da emülatörde **sınanmadı**; Unicorn bit-band semantiğini modellemez.

## 43.6 Başlangıç kodu: vektör tablosu ve reset işleyicisi

İşlemci güç verildiğinde (ya da reset'te) ilk iş olarak bellekte sabit bir yere bakar: **vektör tablosu**. ARMv7-M'de tablonun ilk iki kelimesi özeldir: birincisi başlangıç MSP değeridir, ikincisi reset işleyicisinin adresidir. Donanım bu iki değeri okur, SP ve PC'yi ayarlar, sonra reset işleyicisine geçer. Bizim C programımız, bu tabloyu bir dizi olarak yazıp `.isr_vector` adlı bir bölüme koyduğu ve reset işleyicisini kendisi yazdığı için hiç assembly dosyası kullanmaz.

```c
{{KOD:ornek/startup.c|1-36}}
```

Tablonun üç özelliğine dikkat et. Birincisi, `_estack` bağlayıcı betiğinde tanımlanan bir sembolün **adresidir**; yani tablonun ilk değeri, RAM'in sonunu gösterir ve yığın oradan aşağı doğru büyür. İkincisi, fonksiyon adresleri derleyici tarafından 1 ile *veya*'lanmıştır (Thumb biti). Bu kuralı objdump çıktısında doğrulayabilirsin. Üçüncüsü, `(void *)0` gibi ayrılmış girişler yerinde bırakılır; tablonun her girişinin doğru konumda olması zorunludur, çünkü donanım sıra numarasına göre adres okur.

`objdump -s` ile tablonun bellekteki ham hâline bakalım:

```term
$ arm-none-eabi-objdump -s -j .isr_vector blink.elf
{{CIKTI:cikti/vec.txt}}
```

Satırın ilk dört baytı `00 00 02 20`dir; bayt sırası little-endian olduğundan bu `0x20020000` eder ve `_estack` ile aynıdır. İkinci dört bayt `45 00 00 08`dir, yani `0x08000045`tir. Son bit 1 olduğu için bu bir Thumb adresidir; gerçek fonksiyon adresi `0x08000044` (`Reset_Handler`) ve Thumb biti ekli hâlidir. Diğer kesme girişleri `0x08000041`, yani `Varsayilan_Isleyici` (`0x08000040`) fonksiyonuna işaret eder. Şekil 43.5, tablonun ilk girişlerini bu değerlerle birlikte gösteriyor.

![Şekil 43.5: Vektör tablosunun ilk girişleri ve bu programdan okunan gerçek değerler. Thumb biti, fonksiyon adresinin en düşük bitinde taşınır.](gorseller/b43_vektor.png)

Reset işleyicisinin görevi üç işi sırayla yapmaktır: `.data` bölümünü flash'tan RAM'e kopyalamak, `.bss` bölümünü sıfırlamak ve `main`'i çağırmak. Ayrıca bu programda FPU'yu açıyoruz, çünkü FPU kapalıyken kayan nokta komutu çalıştırmak bir usage fault üretir.

```c
{{KOD:ornek/startup.c|37-}}
```

Kopyalama ve sıfırlama döngüleri bağlayıcı betiğinin sağladığı sembollerle çalışır: `_sidata` flash'taki kaynağın adresidir, `_sdata` ve `_edata` RAM'deki hedef aralığın başı ve sonudur, `_sbss` ve `_ebss` sıfırlanacak aralıktır. Sembollerin adreslerini ve anlamlarını Bölüm 43.7'de bağlayıcı betiğinden göreceksin. Şekil 43.6 reset akışını sırayla gösteriyor.

![Şekil 43.6: Reset akışı. Donanım SP ve PC'yi vektör tablosundan yükler; Reset_Handler kopyalama, sıfırlama ve FPU adımlarından sonra main'e geçer.](gorseller/b43_reset_akisi.png)

**Neden iki bayrak?** Derleme komutunda iki bayrak kullandık: `-ffreestanding` derleyiciye ortamın barındırılmış (hosted) olmadığını, yani libc'nin hazır olmadığını söyler; `-fno-tree-loop-distribute-patterns` ise derleyicinin bir döngüyü `memcpy` ya da `memset` çağrısına çevirme optimizasyonunu kapatır. Bu bayrağın gerekliliğini deneyle sınadık: bu kodda ve bu derleyicide (`-O2` ve `-O3`) kopyalama döngüleri inline açıldı, `memcpy` çağrısı üretilmedi. Yani bayrak bir önlemdir; bu projede gözlemlenmiş bir hata değildir. Yine de bağlayıcının `memcpy` bulamadığı bir ortamda bu tür bir çağrı çalışmayan bir programa yol açar, bu yüzden önlemi açık tutmak sağlam bir alışkanlıktır.

Son olarak bellekte `.data` bölümünün **iki adresi** olduğunu unutma. Flash'taki adres (LMA: load memory address) başlangıç değerinin saklandığı yerdir; RAM'deki adres (VMA: virtual memory address, gömülüde çalışma adresi) değişkenin programın içinde kullanıldığı yerdir. Şekil 43.7 bu ayrımı gösteriyor.

![Şekil 43.7: .data bölümünün LMA ve VMA adresleri. Başlangıç değeri flash'ta, çalışma kopyası RAM'de yaşar; Reset_Handler bir kopyayı diğerine taşır.](gorseller/b43_lma_vma.png)

## 43.7 Bağlayıcı betiği, map dosyası ve bellek bütçesi

Derleyici bir kaynak dosyayı bitirdiğinde adresleri henüz belli değildir (Bölüm 37.9'da gördüğün gibi). Bağlayıcı, bu nesne dosyalarını bir araya getirir, her bölümü bir bellek bölgesine yerleştirir ve sembollere adres atar. Gömülü tarafta bu adım, programın flash ve RAM'e ne kadar yer kapladığını belirleyen yerdir. Bağlayıcı betiği bu işin kurallarını yazdığımız dosyadır.

```c
{{KOD:ornek/link.ld|1-41}}
```

Betiğin ilk bölümü bellek bölgelerini tanımlar. `FLASH` 1 MB, `RAM` 128 KB boyutundadır; `rx` ve `rwx` nitelikleri bölgelerin okuma, yazma ve çalıştırma izinlerini tanımlar. `_estack = ORIGIN(RAM) + LENGTH(RAM);` satırı yığının tepesini RAM'in sonuna koyar; yığın aşağı doğru büyür, yani en düşük adresinden önce kendi tepesine kadar boş olmalıdır.

```c
{{KOD:ornek/link.ld|42-}}
```

Betiğin ikinci bölümü ne nereye gider sorusunu cevaplar. `KEEP(*(.isr_vector))` vektör tablosunu, bağlayıcının çöp toplama (`--gc-sections`) sırasında atmasını engelleyerek flash'ın en başına koyar. `.data` için yazdığımız `> RAM AT> FLASH` ifadesi, bölümün **VMA**sını RAM'e, **LMA**sını flash'a koyar. `_sidata = LOADADDR(.data);` ise flash'taki kaynağın adresini bir sembole bağlar; Reset_Handler bu sembolü kullanır. `PROVIDE(end = _ebss);` sembolü, newlib-nano'nun `_sbrk` fonksiyonunun beklediği bir bağlantıdır (Bölüm 43.10'da printf'te görülecek). Son satırdaki `ASSERT` bir bütçe denetimidir: `.bss` sonu ile yığın tepesi arasında en az 1 KB boşluk yoksa bağlayıcı hata verir. Bu, RAM taşmasını derleme aşamasında yakalamanın en ucuz yoludur.

Bağlayıcının sonucunu `objdump -h` ile görebilirsin. Her bölüm için iki adres vardır: **VMA** (çalışırken kullanılan) ve **LMA** (dosyada yerleşeceği yer).

```term
$ arm-none-eabi-objdump -h blink.elf
{{CIKTI:cikti/objdump_h.txt}}
```

`.data` satırında VMA `20000000` (RAM), LMA `08000164` (flash) olduğunu görüyorsun. Bu bizim Şekil 43.7'deki ayrımın kanıtıdır. `.rodata` (4 bayt) LMA ve VMA'nın aynı olduğu, flash'ta kalan bir bölümdür; `kademe` dizisi buraya düşer. `.bss` ise yalnızca VMA'ya sahiptir, dosyada yer kaplamaz (`ALLOC` ama `CONTENTS` yok); yani sıfırlanacak alan flash'ta bir şey tutmaz.

Sembol adreslerini `nm` ile ayrıca okuyabilirsin:

```term
$ arm-none-eabi-nm -n blink.elf
{{CIKTI:cikti/nm_blink.txt}}
```

Listede `kademe` (`08000160`, flash'ta, `R` yani salt okunur), `acilis_degeri` (`20000000`, `D` yani başlangıçlı veri), `sonuc_menzil` ve `dongu_sayaci` (`B`, başlangıçsız, `.bss`) görünüyor. Dikkat et, `_sbss`/`_ebss` gibi sınır sembolleri de birer adrestir; kendileri veri taşımaz.

Bağlayıcı `-Wl,-Map=blink.map` ile bir map dosyası da üretir. Map dosyası bir programın "neden bu kadar büyük?" sorusunun cevabıdır: hangi girdi dosyasının hangi bölüme, hangi adrese yerleştiğini ve hangi sembolün nerede olduğunu gösterir. Aşağıdaki kesit bellek yapılandırmasını gösteriyor:

```term
$ less blink.map
{{CIKTI:cikti/map_ozet1.txt}}
```

Ve `.rodata`, `.data`, `.bss` ile bütçe denetiminin yer aldığı kesit:

```term
$ less blink.map
{{CIKTI:cikti/map_ozet2.txt}}
```

İkinci kesitte iki ayrıntıya dikkat et. Birincisi, map dosyası `.rel.dyn` ve `.igot.plt` gibi bölümleri de gösterir; bunlar bizim betiğimizde tanımlanmayan (orphan) bölümlerdir ve boyutları sıfırdır. Bağlayıcı bu bölümleri standart kurallarla yerleştirir. İkincisi, `ASSERT` satırı bütçe denetiminin çalıştığını gösterir: `_ebss + 0x400 <= _estack` ifadesi doğru olduğu için bağlayıcı sessiz kalır.

Boyut özeti `size` komutuyla gelir:

```term
$ arm-none-eabi-size blink.elf
{{CIKTI:cikti/size_blink.txt}}
```

`size` üç sütun verir: `text` (kod ve sabit veriler), `data` (başlangıç değeri olan RAM verisi) ve `bss` (sıfırlanacak RAM). Bunlardan bütçeyi şöyle hesaplarsın: **flash kullanımı = text + data**, **RAM kullanımı = data + bss**. Bu programda flash 356 + 4 = 360 bayt, RAM 4 + 8 = 12 bayt. `text` sütununun 356 olduğunu da kontrol edebilirsin: `.isr_vector` 64 bayt (`0x40`), `.text` 288 bayt (`0x120`) ve `.rodata` 4 bayt; toplam 356. Yani `size`'daki "text", kodla birlikte vektör tablosunu ve sabit verileri de taşır. Bu hesap, Örnek 3'te bir bütçe kararı verirken kullanacağın temel formüldür.

Yığın için ayrı bir ölçüm gerekir. `-fstack-usage` ile derleyici her fonksiyonun yığın çerçevesini `.su` dosyasına yazar (ayrıntısı Bölüm 43.9'da). Bu programın `.su` dosyası şöyle:

```term
$ cat blink.su
{{CIKTI:cikti/su_blink.txt}}
```

Bu iki fonksiyon yerel değişken kullanmadığı için çerçeve boyutu düşük; `main` 8 bayt ayırıyor. Bağlayıcının ürettiği son bütçe şu anlama gelir: RAM'de 12 bayt sabit veri, en fazla birkaç bayt yığın; geri kalan yaklaşık 128 KB'ın tamamı yığına ve sonraki gelişmelere (tamponlar, kesme yığınları) açık.

Şekil 43.8, bağlayıcının üç girdiyi (startup.o, blink.o ve betik) bu iki bellek bölgesine nasıl yerleştirdiğini özetliyor.

![Şekil 43.8: Bağlayıcının girdi bölümlerini betik kurallarına göre flash ve RAM bölgelerine yerleştirmesi.](gorseller/b43_baglayici.png)

## 43.8 İlk program: GPIO ile LED ve yazmaçların anatomisi

Gömülü dünyanın "merhaba dünyası" bir LED'in yanıp sönmesidir. Bunu bir kütüphane olmadan yapacağız: yazmaçların adreslerini ve düzenini bir başlık dosyasında tanımlayacak, LED pinini bu yazmaçlardan sürecek ve bekleme döngüsünü yazacağız.

Önce yazmaç düzeni. Bir çevre biriminin yazmaçları bellekte ardışık ve belirli ofsetlerdedir; bunu bir `struct` ile modellemek hem okunaklı hem de derleyici tarafından denetlenebilir bir yoldur. Aşağıdaki başlık dosyası GPIO ve RCC yazmaçlarını bu şekilde tanımlıyor.

```c
{{KOD:ornek/reg.h|1-24}}
```

Her üye `volatile uint32_t` olarak işaretlenmiştir, çünkü her biri bir donanım yazmacıdır. `GPIO_TypeDef` yapısı STM32F4'ün referans kılavuzundaki yazmaç sırasını izler: `MODER` ofset `0x00`, `IDR` `0x10`, `ODR` `0x14`, `BSRR` `0x18`. Yapıdaki her alanın ofsetinin doğru olduğunu derleme aşamasında `_Static_assert` ile denetliyoruz; yanlış bir ofset derlemeyi durdurur.

```c
{{KOD:ornek/reg.h|25-48}}
```

RCC yapısı da aynı yöntemle kuruldu. `AHB1ENR` yazmacı ofset `0x30`dadır; bu yazmaç GPIO portlarının saat kapılarını açar. Yapıların doğruluğunu bağımsız bir kaynakla da kontrol ettik: STMicroelectronics'in resmi cihaz başlığı `stm32f407xx.h` (sürüm v2.6.10) `GPIO_TypeDef` ve `RCC_TypeDef` yapılarını aynı alan sırasıyla tanımlıyor; `GPIOD_BASE` değerini `AHB1PERIPH_BASE + 0x0C00` olarak, `RCC_BASE` değerini `AHB1PERIPH_BASE + 0x3800` olarak veriyor. Yani kendi başlığımız ile resmi başlık aynı adresleri kullanır. Gerçek projelerde bu başlığı elle yazmazsın; üretici başlığını kullanırsın. Biz yapıyı görmek için kendimiz yazdık.

Şimdi LED programı. Kart olarak STM32F4 Discovery'nin yeşil LED'ini (PD12) varsaydık; kendi kartında pin farklı olabilir.

```c
{{KOD:ornek/blink.c|1-27}}
```

Bu dosyada dört tür global değişken var ve her biri bağlayıcıda farklı bir bölüme düşer. `acilis_degeri` başlangıç değeri taşıdığı için `.data`dadır; flash'tan RAM'e kopyalanır. `dongu_sayaci` ve `sonuc_menzil` başlangıçsızdır, `.bss`te yaşar ve reset işleyicisi tarafından sıfırlanır. `kademe` `const` olduğu için `.rodata`ya, yani flash'a yerleşir; RAM'i harcamaz. `menzil_hesapla` EV Dashboard'daki `Menzil_Hesapla` fonksiyonunun tam sayı karşılığıdır; kayan nokta yerine tam sayı kullanır, böylece FPU'suz bir yolda da aynı sonucu verir.

```c
{{KOD:ornek/blink.c|28-}}
```

`main` üç adımda çalışır. İlk adımda RCC'nin AHB1 saat kapısını açar (`GPIODEN` biti, bit 3). İkinci adımda PD12'nin modunu ayarlar: `MODER` yazmacında her pin için 2 bit vardır ve pin 12 için bu bitler `[25:24]`tür. Önce bu iki biti temizler (`&= ~(3u << 24)`), sonra `01` (genel çıkış) değerini yazar. Bu okuma-değiştirme-yazma bu tek yazılımda güvenlidir, çünkü `main` dışında bu yazmacı değiştiren bir kod yoktur; kesme kullanan bir projede bu bölüm daha dikkatli olmalıdır (43.5'teki tehlike). Üçüncü adımda döngü, `BSRR` yazmacına pin 12'yi set eder ya da reset eder ve arada gecikme çağırır.

Derlemeyi bir kez daha, şimdi tüm bayraklarıyla yapalım. Komut satırını 74 karakterin altında tutmak için bayrakları değişkende topluyoruz:

```term
$ CF="-mcpu=cortex-m4 -mthumb -mfloat-abi=hard"
$ CF="$CF -mfpu=fpv4-sp-d16 -ffreestanding -Wall -Wextra -std=c11"
$ CF="$CF -fno-tree-loop-distribute-patterns"
$ arm-none-eabi-gcc $CF -O2 -c startup.c -o startup.o
$ arm-none-eabi-gcc $CF -O2 -c blink.c -o blink.o
$ arm-none-eabi-gcc $CF -O2 -nostdlib -nostartfiles -T link.ld \
    -Wl,-Map=blink.map startup.o blink.o -o blink.elf
$ arm-none-eabi-size blink.elf
{{CIKTI:cikti/size_blink.txt}}
```

Bayrakların çoğunu zaten açıkladık: `-mcpu`, `-mthumb` ve `-mfloat-abi=hard -mfpu=fpv4-sp-d16` hedef çekirdeği ve FPU'yu tanımlar; `-nostdlib -nostartfiles` ise standart başlangıç dosyasını ve libc'yi bağlamaz, çünkü başlangıç kodu bizim. `-Wl,-Map=` map dosyasını üretir.

### Emulatörde çalıştırmak

Kartımız olmadığı için programın gerçekten çalışıp çalışmadığını bir emulatörde denedik. Unicorn Engine, ARM komut kümesini çalıştıran bir CPU emulatörüdür; Thumb ve Cortex-M modunu destekler (`UC_MODE_THUMB | UC_MODE_MCLASS`). Emulatör çevre birimlerini modellemez; yalnızca komutları ve bellek yazmalarını çalıştırır. Bu yüzden LED'in gerçekten yandığını değil, programın yazmaçlara **doğru değerleri yazdığını** doğrulayabiliriz. Harness'ın kodu dört parçada:

```python
{{KOD:emu/harness.py|1-34}}
```

```python
{{KOD:emu/harness.py|35-68}}
```

```python
{{KOD:emu/harness.py|69-106}}
```

```python
{{KOD:emu/harness.py|107-}}
```

Harness önce `.bin` görüntüsünü ve vektör tablosunu okur, SP ve PC'yi tablodan yükler (43.6'daki kural), ardından reset'ten `main`'e kadar çalıştırır ve bu sırada her komutun adresini ve R1-R3 yazmaçlarını kaydeder. İkinci fazda `main`'i 2,5 milyon komut boyunca çalıştırır ve GPIOD `BSRR` yazmacına yapılan her yazmayı toplar. Çalıştırmanın çıktısı:

```term
$ python -I harness.py blink.elf blink.bin cikti
{{CIKTI:cikti/emu_cikti.txt}}
```

Çıktıyı okuyalım. Vektör değerleri Şekil 43.5'tekilerle aynı. Startup **36 komutta** `main`'e ulaşıyor. `.data` kaynağı (`0xCAFE0001`) RAM'e kopyalanmış, `.bss` ilk iki kelimesi sıfır, CPACR'nin `0x00F00000` olması FPU'nun açıldığını gösteriyor. `RCC AHB1ENR = 0x8` bit 3'ün (GPIODEN) açıldığını, `GPIOD MODER`'in `0x01000000` olması ise pin 12'nin `01` (çıkış) moduna geçtiğini gösteriyor. `sonuc_menzil = 82` değeri `kademe[1] = 50` için `50 * 165 / 100 = 82` sonucuyla tutarlı. `dongu_sayaci = 3` ise iki tam çevrim sonunda artışın gerçekten gerçekleştiğini gösterir.

BSRR yazmalarına bakalım. Beş yazma var: ilki komut 30'da `0x00001000` (pin 12 set), ikincisi komut 600034'te `0x10000000` (pin 12 reset), üçüncüsü 1200042'de yine set; yani her yarım periyot yaklaşık 600 000 komut sürüyor. Bunun nedeni `gecikme` fonksiyonunun her turunda altı komut çalıştırmasıdır (`ldr`, `subs`, `str`, `ldr`, `cmp`, `bne`); 100 000 turun 6 komutla çarpımı 600 000'dir. Bu bir **busy-wait** gecikmedir ve iki sorunu var: gerçek süresi saat frekansına ve derleyicinin ürettiği komut sayısına bağlıdır (kartta ölçülmedi), ve bu süre boyunca işlemci başka hiçbir iş yapamaz. Bölüm 44'te bu gecikmenin yerine SysTick zamanlayıcısını koyacağız.

Çıktının bir noktası emülatörün sınırını gösterir: `GPIOD ODR` yazmacı 0 kalmış görünüyor. Donanımda BSRR'ye yazmak ODR'yi değiştirir; Unicorn ise BSRR yazmasını yalnızca bellek olarak kaydeder ve ODR'ye yansıtmaz. Bu bir **model farkıdır**. Bu yüzden pinin durumunu emülatörde ODR'den değil, yalnızca yazılan BSRR değerlerinden izleyebiliriz; harness bu yüzden BSRR yazmalarını ayrıca döküyor.

### HAL, LL ve çıplak yazmaç: aynı yazmaç, üç yol

EV Dashboard `main.c` dosyasında GPIO'yu okumak için `HAL_GPIO_ReadPin` kullanılıyor (`Girisler_Guncelle`, 98-110. satırlar). HAL (Hardware Abstraction Layer) bu çağrıyı üç katmanda gerçekleştirir: uygulama kodu, HAL fonksiyonu ve yazmaç. Şekil 43.9 bu katmanları iki örnek üzerinde gösteriyor: solda GPIO okuma, sağda UART gönderme.

![Şekil 43.9: HAL çağrısının yazmaç düzeyine inmesi. Solda GPIO okuması IDR yazmacına, sağda UART gönderimi SR ve DR yazmaçlarına iner.](gorseller/b43_katmanlar.png)

`HAL_GPIO_ReadPin`'in gövdesi kısa; onu tam olarak gösterebiliriz (HAL v1.8.0, `stm32f4xx_hal_gpio.c`, 375-391. satırlar). Fonksiyonun asıl işi tek bir karşılaştırmadır: `GPIOx->IDR & GPIO_Pin`.

```c
{{KOD:hal/gpio.c|375-391}}
```

`assert_param` çağrıları, HAL'in parametre denetim makrolarıdır. HAL'in genel tasarımına göre bu makrolar yalnızca `USE_FULL_ASSERT` tanımlıysa etkindir (genel bilgi; bu sürümün başlık dosyasını bu bölümde indirmedik). Yani üretim kodunda bu denetimler çoğunlukla sıfır maliyetlidir; geliştirme sırasında açmak yararlıdır.

Üç yolu yan yana koyalım:

| Yol | Ne yazarsın | Yazmaç erişimi | Maliyet ve esneklik |
|---|---|---|---|
| HAL | `HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_0)` | Fonksiyon içinde `IDR` okuma | Taşınabilir ama fonksiyon çağrısı ve ek denetim var |
| LL (Low Layer) | `LL_GPIO_IsInputPinSet(...)` (genel bilgi) | Satır içi (inline) yazmaç erişimi | HAL'e göre ince, çoğu zaman daha küçük kod |
| Çıplak yazmaç | `(GPIOB->IDR & 1u)` | Doğrudan | En küçük, en hızlı; her ayrıntı sana ait |

Bu tablo üçünün de aynı yazmacı kullandığını gösteriyor. Farkı belirleyen şey, hangi katmanın sorumluluğunda olduğu: HAL taşınabilirlik ve hata denetimi sağlar, çıplak yazmaç ise sana tam kontrol ve sorumluluk verir. EV Dashboard'da HAL'i bırakmak mantıklı olabilir; ama bir sürücünün zaman bütçesini hesaplamak istediğinde HAL'in gizlediği zaman aşımlarını görmek zorundasın (aşağıda).

### CMSIS, aygıt başlıkları ve offsetof ile doğrulama

Bu bölümde kendi yazmaç yapımızı yazdık. Gerçek projelerde bu iş üretici tarafından yapılır: ARM'ın **CMSIS** (Cortex Microcontroller Software Interface Standard) çekirdek başlığı (`core_cm4.h`) çekirdeğin yazmaçlarını tanımlar, her MCU üreticisi ise kendi aygıt başlığını (`stm32f4xx.h`, `stm32f407xx.h`) bunun üstüne kurar. Aygıt başlığı önce `__NVIC_PRIO_BITS`, `__FPU_PRESENT` gibi makroları tanımlar, sonra `core_cm4.h`'yi dahil eder. Bunu bir iskelet olarak gösterelim:

```c
{{KOD:cmsis/aygit.h}}
```

Bu iskeletin kendisi bir aygıt başlığı değildir; yalnızca CMSIS'in ihtiyaç duyduğu tanımların sırasını gösterir. Ardından gerçek `core_cm4.h` (CMSIS_5 sürüm 5.9.0 etiketinden, başlık sürümü V5.1.2) ile SCB yapısının ofsetlerini derleme aşamasında denetleyen bir test yazalım:

```c
{{KOD:cmsis/ofs_testi.c}}
```

`_Static_assert` satırları, SCB yapısının her önemli alanının ofsetini belgelenmiş değerlerle karşılaştırır. Bir alan yanlış yerdeyse derleme başarısız olur. Derleme sonucu:

```term
$ arm-none-eabi-gcc $CF -std=c11 -Wall -I. -c ofs_testi.c -o ofs_testi.o
$ arm-none-eabi-size ofs_testi.o
{{CIKTI:cikti/ofs.txt}}
```

Çıktı yalnızca derlemenin ve sınamanın geçtiğini söyler; bir yazmaç ofsetinin derleme aşamasında doğrulanması, yanlış adrese yazmanın kartta sessiz bir hata olarak ortaya çıkmasını engeller. Bu teknik `offsetof` ile yapılır: `offsetof(SCB_Type, CPACR)` değeri `0x088` olmalıdır, ve CPACR'nin mutlak adresi `SCB_BASE + 0x088 = 0xE000ED88`dir; Reset_Handler'daki FPU açma adresi tam olarak budur. Bir başka örnek: CFSR (`0x028`) ve HFSR (`0x02C`) hata durum yazmaçları SCB'nin `0xE000ED28` ve `0xE000ED2C` adreslerindedir; bu adresleri Bölüm 43.11'de HardFault analizinde kullanacağız.

### EV Dashboard'da ne oluyor? Zaman bütçesi

Şimdi bu katmanları Mert'in gerçek koduna uygulayalım. EV Dashboard'un `main` döngüsü `Daly_BataryaGuncelle`, `Kelly_MotorGuncelle`, `Girisler_Guncelle`, `Menzil_Hesapla`, `JSON_Olustur` ve `RaspberryPi_Gonder` çağrılarını sırayla yapar, sonra `HAL_Delay(200)` ile 200 ms bekler. Kod yorumu "5 Hz yayın frekansı" diyor. Bu bir **zaman sözleşmesidir**; bunu HAL'in zaman aşımı semantiğiyle karşılaştırmalıyız.

Kaynağa bakalım. `HAL_UART_Transmit` ve `HAL_UART_Receive` çağrıları bir `Timeout` değeri alır. HAL v1.8.0 kaynağında bekleme fonksiyonu (`UART_WaitOnFlagUntilTimeout`) şöyle çalışır: çağrının başında alınan `Tickstart` değeri ile `HAL_GetTick()` arasındaki farkı `Timeout` ile karşılaştırır ve aşılırsa `HAL_TIMEOUT` döndürür. Yani bir çağrının en fazla bloklanma süresi, `Timeout` değeriyle sınırlıdır; bir çağrının içindeki birden çok bekleme aynı başlangıç zamanını paylaşır.

Bu semantiğe göre `main.c`deki çağrıların en kötü durum sürelerini toplayalım:

| Çağrı (main.c) | Timeout (ms) | En kötü süre (ms) |
|---|---|---|
| `Daly_VeriOku` içinde `HAL_UART_Transmit` (55. satır) | 100 | 100 |
| `Daly_VeriOku` içinde `HAL_UART_Receive` (56. satır) | 200 | 200 |
| `Daly_BataryaGuncelle` üç kez `Daly_VeriOku` çağırır | — | 3 x 300 = 900 |
| `Kelly_MotorGuncelle` Transmit (88) + Receive (89) | 100 + 200 | 300 |
| `RaspberryPi_Gonder` Transmit (139-140) | 100 | 100 |
| `HAL_Delay(200)` (165. satır) | — | 200 |
| **Toplam üst sınır** | | **1500** |

Bu tablo bir **üst sınırdır**: her çağrı zaman aşımına uğrarsa döngü 1,5 saniyeye kadar uzar. Normal koşulda cevaplar hızlı gelir ve döngü 200 ms'e yakındır; ama BMS veya motor sürücüsü yanıt vermediğinde döngü 200 ms'de kalmaz. Bu, "5 Hz" yorumunun her koşulda doğru olmadığı anlamına gelir. Bu bir sonuçtur: gerçek süreyi kartta ölçmedik, yalnızca kaynağa dayanan bir üst sınır verdik. Bu sınırı azaltmanın yolu, zaman aşımlarını kısaltmak ya da yanıtsız kalan bir aygıtı bu döngüden ayırmaktır (Bölüm 44'te zamanlayıcı ile).

Aynı kodda ayrıca bir uyumsuzluk görünüyor. `Kelly_MotorGuncelle` içinde `arac.hiz = (gelen[1] << 8) | gelen[2];` satırının yanındaki yorum "RPM -> km/h" diyor, ama kodda RPM değerinin km/h'ye çevrildiği bir katsayı yok; ham değer doğrudan atanıyor. Bu, bir birim dönüşümünün eksik olabileceğini gösteren bir işarettir. Düzeltme için tekerlek çevresi ve dişli oranı gibi bilgiler gerekir; bunlar kodda yok. Hangisinin doğru olduğunu yalnızca proje sahibi ve donanım belgesi söyleyebilir; biz burada yalnızca yorum ile kodun uyuşmadığını belirtiyoruz.

Bu bölümde yaptığımız okumanın özeti: EV Dashboard'un her girişi (GPIO) bir IDR okumasıdır, her çıkışı (UART) bir DR yazmasıdır ve her beklemesi bir SR bayrağını yoklamadır. Bu yazmaçların hepsi `volatile`dır ve hepsi bu bölümdeki kurallara tabidir. Sürücünün zaman bütçesini doğru tahmin etmek için bu yoklama döngülerinin üst sınırını bilmek gerekir; çıplak yazmaç sürücüsü bu sınırı senin kontrolüne verir (Kendin Yap Projesi 2).
