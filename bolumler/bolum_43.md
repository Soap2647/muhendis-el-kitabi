%% kisim_no: XI
%% kisim_ad: Gömülü Sistem
%% kisim_ayrac: evet
%% bolum_no: 43
%% baslik: Bare-Metal C

## Giriş: Yazılımın donanımla konuştuğu yer

Şu ana kadar yazdığın her programın altında bir işletim sistemi vardı. `printf` çağırdığında arkada çekirdek, kütüphane ve sayfalama çalışıyordu; dosyayı açtığında bir disk denetleyicisi senin yerine konuşuyordu. Bu bölümde o katmanların hiçbirini varsayamayacağız. Bir mikrodenetleyiciye güç verilir, işlemci sabit bir adresten okumaya başlar ve senin yazdığın C kodu bir LED'in yanıp sönmesinden bir sensörün okunmasına kadar her şeyi kendisi yapar. Bu ortama **bare-metal** (çıplak metal) denir.

Bu neden önemli? Savunma sanayiinde yazılımın büyük kısmı tam bu katmanda yaşar. Bir İHA'nın uçuş kontrol kartı, bir motor sürücüsü, bir radyo modülü ya da bir sensör füzyon birimi işletim sistemi olmadan ya da çok küçük bir çekirdekle çalışır. Mülakatlarda "`volatile` neden var?", "bir donanım yazmacına nasıl yazarsın?", "bu global değişken hangi bellek bölgesine düşer?" gibi sorular bu konudan gelir. Cevabı ezberlemek yetmez; derleyicinin ürettiği komutu okuyabilmen ve yazdığın kodun donanımda ne yaptığını tahmin edebilmen gerekir.

Mert'in kendi projesi bu bölümün doğal referansıdır. EV Dashboard'un `main.c` dosyası bir STM32F4 üzerinde çalışıyor: Daly BMS'ten ve Kelly motor sürücüsünden UART ile veri okuyor, GPIO pinlerinden vites ve sinyal durumunu alıyor, sonra bunları JSON'a çevirip Raspberry Pi'ye yolluyor. Bu koddaki her HAL çağrısının altında bir yazmaç okuması ya da yazması yatıyor. Bölümün sonunda bu katmanları somut olarak göstereceğiz (Bölüm 43.8). UART protokolünün kendisi Bölüm 45'in konusudur.

Bu bölümde iddiaların çoğunu ölçtük. Kodu ARM çapraz derleyicisiyle derledik, çıktıyı `objdump`, `nm`, `size` ve bağlayıcı haritasıyla inceledik, Cortex-M4 komutlarını Unicorn Engine ile emülatörde çalıştırdık. **Kodu gerçek bir karta yüklemedik.** Metindeki her çalıştırma sonucu emülatör çıktısıdır; kartta denenmemiş bir şey varsa bunu açıkça yazdık.

::: not
Bu bölümdeki kodların ve çıktıların tamamı GNU Arm Embedded araç zinciri 13.3.rel1 (arm-none-eabi-gcc 13.3.1; STM32CubeIDE 1.19.0 ile gelen sürüm), Unicorn Engine 2.1.4 ve Python 3.12.10 ile üretildi. Host tarafındaki C denemeleri WSL2 içinde (Ubuntu 24.04, gcc 13.3.0) AddressSanitizer ve UBSan açıkken çalıştırıldı. Kodlar kitapta birebir yer alır; derleme komutlarında yalnızca metinde açıklanan bayraklar gösterildi.
:::

## 43.1 Gömülü dünyanın kısıtları

Gömülü sistem, belirli bir işi yapmak için bir cihazın içine yerleştirilmiş bilgisayardır. Çamaşır makinesinin denetleyicisi, bir aracın batarya yönetim birimi ve bir İHA'nın uçuş kontrol kartı bu gruba girer. Genel amaçlı bir bilgisayara göre dört kısıt belirleyicidir.

**Bellek sınırlıdır.** Masaüstünde gigabaytlarca RAM ve sanal bellek varken, bir Cortex-M4 mikrodenetleyicisinde birkaç yüz kilobaytlık flash ve onlarca ya da yüzlerce kilobaytlık SRAM bulunur. Bu çalışmada kullandığımız bağlayıcı betiği STM32F407VG için 1 MB flash ve 128 KB SRAM varsayar; bu değerler F407VG için genel bilgidir, kendi kartının belgesinden doğrulaman gerekir.

**İşletim sistemi ya da sanal bellek yoktur.** Her adres fiziksel adrestir. Cortex-M çekirdeğinde MMU bulunmaz; onun yerine bölge tabanlı bir MPU vardır (Bölüm 25'te gördük). Sayfa hatası, takas ve talep üzerine sayfalama yoktur. Bir hata yaptığında işletim sistemi sana bir "segmentation fault" mesajı vermez; işlemci bir HardFault istisnasına girer ya da yanlış bir değer üretip sessizce devam eder.

**Zamanlama bir gereksinimdir.** Bir uçuş kontrol döngüsünün her 10 milisaniyede bir çalışması gerekiyorsa, bu süre bir tercih değil bir sözleşmedir. Bu yüzden gerçek zamanlı sistemlerde "ortalamada hızlı" yetmez; en kötü durum süresi (worst-case) önemlidir. Kesmeler ve zamanlayıcılar bu konunun merkezidir ve Bölüm 44'ün konusudur.

**Güç ve güvenilirlik ön plandadır.** Pille çalışan bir sensör düğümü saatlerini kapatıp uyur; bir uçağın yazılımı ise yanlış bir bit yüzünden bile güvenli bir duruma geçebilmelidir. Bu da watchdog zamanlayıcılar, sağlama toplamları ve "hata durumunda güvenli çıkış" gibi tasarım kararlarını gerektirir.

Tablo 43.1 bu iki dünyayı yan yana koyuyor. Sağdaki sütundaki her satır, C'de belirli bir alışkanlığa dönüşür: dinamik bellek yerine sabit tamponlar, yığın bütçesi, `volatile` ve donanım yazmaçları, derleme boyutu ölçümü.

| Konu | Masaüstü (Linux) | Gömülü (Cortex-M4, bare-metal) |
|---|---|---|
| Bellek | GB'lar, sanal bellek | KB'lar ila birkaç MB, fiziksel adres |
| Başlatma | Çekirdek, `ld.so`, libc | Reset vektörü, senin yazdığın başlangıç kodu |
| G/Ç | Sistem çağrısı (`read`, `write`) | Yazmaca yazmak, bellek eşlemeli G/Ç |
| Hata | Sinyal, `segmentation fault` | HardFault istisnası, watchdog |
| Zamanlama | En iyi çaba | Sınırlı en kötü durum süresi |
| Kod boyutu | MB'lar, paylaşımlı kütüphaneler | KB'lar; her bayt flash'ta yer kaplar |

## 43.2 Mikrodenetleyicinin anatomisi

Mikrodenetleyici (microcontroller, MCU), tek bir çipin içine bir işlemci, bellek ve dış dünyayla konuşan çevre birimlerini koyan bütünleşik bir sistemdir. Şekil 43.1 tipik bir STM32F4 ailesinin iç düzenini genel hatlarıyla gösteriyor. Ayrıntılar modele göre değişir; ama her MCU'da bu blokların hemen hemen hepsi bulunur.

![Şekil 43.1: Tipik bir MCU'nun blok diyagramı. Çekirdek, bus matrisi üzerinden flash, SRAM ve çevre birimlerine bağlanır; saat ağacı çevre birimlerine saat dağıtır.](gorseller/b43_mcu_blok.png)

**Çekirdek** (Cortex-M4) komutları çalıştıran kısımdır. **Flash** programın kendisini ve sabit verilerini saklar; güç kesildiğinde içeriği kalır. **SRAM** çalışma sırasındaki değişkenleri ve yığını tutar; güç kesilince silinir. **Bus matrisi** çekirdeğin, DMA'nın ve diğer ana birimlerin belleğe ve çevre birimlerine nasıl eriştiğini yönetir. Bus'lar genellikle AHB (yüksek hızlı) ve APB (düşük hızlı) olarak katmanlanır. Başlık dosyasında USART1'in tabanının `0x40011000` olduğunu ve `APB2PERIPH_BASE` (`0x40010000`) bölgesinde yer aldığını görebilirsin; bu, USART1'in APB2 bus'ına bağlı olduğu anlamına gelir.

**Çevre birimleri** GPIO (pin girişleri ve çıkışları), USART (seri haberleşme), zamanlayıcılar, ADC ve benzerleridir. Her biri bir dizi yazmacın (register) arkasındadır. Yazmaç, belirli bir adreste duran ve okunup yazılabilen bir donanım belleğidir; bu bölümün asıl konusu budur.

**Saat ağacı** (RCC: Reset and Clock Control) çekirdeğe ve her çevre birimine giden saat sinyalini üretir ve kapılar. Kullanmadığın bir birimin saatini kapatmak güç tüketimini düşürür. Ama bu kapının bir sonucu vardır: saat kapısı kapalıyken çevre birimi yazmacına yazmak genellikle etkisizdir. Bu yüzden her programın ilk işi, kullanacağı çevre biriminin saatini açmaktır (Bölüm 43.8'de LED programında gösterilecek).

**DMA** (Direct Memory Access), çekirdeği meşgul etmeden çevre birimi ile bellek arasında veri taşır. Bölüm 28'de gördüğün DMA fikrinin gömülü karşılığıdır. **Hata ayıklama** arayüzü (SWD ya da JTAG) bir programcı/hata ayıklayıcının çekirdeği durdurmasına, belleği okumasına ve yazmaçları incelemesine izin verir (Bölüm 43.11).

## 43.3 Cortex-M4 programcı modeli

Cortex-M4, ARM'ın ARMv7-E-M mimarisini uygular. Bu mimaride komutlar **Thumb-2** kümesindedir: komutlar 16 veya 32 bit uzunluktadır ve ARM'ın eski 32 bit kodlamasından farklı olarak işlemci yalnızca Thumb modunda çalışır. Bu yüzden derlerken `-mthumb` bayrağı kullanılır ve bir fonksiyonun adresinin en düşük biti (Thumb biti) 1 olmalıdır. Bunu vektör tablosunda göreceğiz (Bölüm 43.6).

Programcının gördüğü yazmaçlar şunlardır:

| Yazmaç | Rol |
|---|---|
| R0-R3 | Çağrı argümanları; dönüş değeri R0'da |
| R4-R11 | Çağıranın korumak zorunda olduğu genel amaçlı yazmaçlar |
| R12 (IP) | Geçici (intra-procedure) yazmaç |
| R13 (SP) | Yığın işaretçisi; MSP veya PSP olarak iki kopyası vardır |
| R14 (LR) | Dönüş adresi (link register) |
| R15 (PC) | Program sayacı |
| xPSR | Bayraklar ve yürütme durumu |
| S0-S31 | Kayan nokta birimi (FPU) yazmaçları, FPU açıldığında |

**Çift yığın işaretçisi.** Cortex-M'de iki yığın işaretçisi vardır: **MSP** (Main Stack Pointer) reset sonrası ve kesme işleyicilerinde kullanılan varsayılan yığındır; **PSP** (Process Stack Pointer) ise bir işletim sistemi çekirdeği kullanıldığında görev (thread) yığınıdır. Çıplak metal programda yalnızca MSP kullanırsın. Bu ayrım Bölüm 26'daki süreç ve iş parçacığı yığınlarının küçük bir karşılığıdır.

**Ayrıcalık modeli.** Bölüm 24.10'da x86'nın halkalarını (ring 0, ring 3) ve ARM'ın Exception Level'larını gördük. Cortex-M çekirdeğinde bu model daha sadedir: işlemci ya **işleyici modunda** (handler mode, istisna ve kesme işleyicileri) ya da **iş parçacığı modunda** (thread mode, `main`) çalışır. İş parçacığı modu da CONTROL yazmacındaki bitlerle ayrıcalıklı ya da ayrıcalıksız olabilir. Gömülü tek görevli bir programda çoğunlukla ayrıcalıklı modda çalışırsın; MPU ile ayrıcalıksız bir görev sınırlandırılabilir (genel bilgi).

**Çağrı kuralı.** ARM ABI (AAPCS) argümanları R0-R3'e koyar, dönüş değerini R0'a yazar ve dönüş adresini LR'ye (R14) koyar. x86'da `call` komutu dönüş adresini yığına iter (Bölüm 24.4); ARM'da `bl` komutu LR'yi doldurur ve fonksiyon sonunda `bx lr` ile dönülür. Aşağıda derlenmiş `menzil_hesapla` fonksiyonunda bu iki noktayı görebilirsin. Fonksiyon, batarya yüzdesini R0'da alır, sonucu R0'da döndürür ve `bx lr` ile çağırana döner.

```c
uint32_t menzil_hesapla(uint8_t batarya)
{
    return ((uint32_t)batarya * 165u) / 100u;
}
```

Bu fonksiyonun makine kodu şöyle:

```term
$ arm-none-eabi-objdump -d blink.elf
080000b0 <menzil_hesapla>:
 80000b0:	4b04      	ldr	r3, [pc, #16]	@ (80000c4 <menzil_hesapla+0x14>)
 80000b2:	eb00 0080 	add.w	r0, r0, r0, lsl #2
 80000b6:	eb00 1040 	add.w	r0, r0, r0, lsl #5
 80000ba:	fba3 3000 	umull	r3, r0, r3, r0
 80000be:	0940      	lsrs	r0, r0, #5
 80000c0:	4770      	bx	lr
 80000c2:	bf00      	nop
 80000c4:	51eb851f 	.word	0x51eb851f
```

Dikkat edilmesi gereken iki şey var. Birincisi, `/ 100` bir bölme olmasına rağmen derleyici bölmeyi **çarpma ve kaydırma** ile değiştirmiş: `0x51eb851f` sabiti (yaklaşık 2^37/100) ile `umull` komutu ve ardından `lsrs #5` kullanılmış. Bu, sabit bölmenin tipik bir optimizasyonudur ve Cortex-M4'ün donanım bölme birimi olmasa bile geçerlidir. İkincisi, `(uint32_t)batarya * 165u` ifadesi için `add.w` ile `lsl` kombinasyonu kullanılmış; yani derleyici 165'i kaydırma ve toplama ile kurmuş. Bu ayrıntıları bilmek, boyut ve hız tahmininin temelidir.

Son olarak endianness: Cortex-M4 little-endian çalışır; düşük bayt düşük adrese yazılır (Bölüm 1.5'teki sözleşme). STM32 ailesinin paket ve yazmaç düzeni de bu sırayı izler.

## 43.4 Bellek haritası ve bellek eşlemeli G/Ç

Cortex-M'de tüm adresler (kod, veri, çevre birimleri, sistem yazmaçları) tek bir 4 GB'lık adres uzayının içindedir. ARMv7-M mimarisi bu uzayı Şekil 43.2'deki gibi sabit bölgelere ayırır. Bunlar mimarinin genel haritasıdır; belirli bir çipte flash ve SRAM'in nerede başlayıp nerede bittiği üreticinin belgesinde yazar.

![Şekil 43.2: ARMv7-M genel bellek haritası. Kod, SRAM, çevre birimleri ve sistem bölgesi sabit adres aralıklarında; bit-band takma adres bölgeleri çevre birimi ve SRAM'in üstünde ayrı aralıklardadır.](gorseller/b43_bellek_haritasi.png)

İki bölge bu bölümün merkezindedir. **`0x40000000` ve üzeri** çevre birimleridir; GPIOD'nin tabanı `0x40020C00`, RCC'nin tabanı `0x40023800`dür. **`0xE0000000` ve üzeri** sistem bölgesidir; CPACR gibi çekirdek yazmaçları burada durur (`0xE000ED88`). Bu adresleri ezberlemek zorunda değilsin, ama her birinin bir kaynağı olmalı. Biz adresleri resmi cihaz başlığından (`stm32f407xx.h`, STMicroelectronics/cmsis_device_f4 sürüm v2.6.10) ve CMSIS çekirdek başlığından (`core_cm4.h`, CMSIS_5 sürüm 5.9.0) kontrol ettik.

**Bellek eşlemeli G/Ç** (memory-mapped I/O) bir donanım yazmacına normal bir bellek adresi gibi erişmek demektir. Bir GPIO çıkış yazmacına yazmak için şunu yazarsın:

```c
*(volatile uint32_t *)0x40020C14u = 0x1000u;
```

Bu satırda iki şey sıradışıdır. Birincisi, adres bir değişkenin adresi değil, sabit bir sayıdır; yani adres sana ait değildir, donanıma aittir. İkincisi, `volatile` anahtar kelimesi. Bu ikisini ayrı ayrı anlamadan bir gömülü sürücü yazamazsın.

### volatile: derleyiciye verilen söz

`volatile` bir değişkenin değerinin **programın kontrolü dışında değişebileceğini** derleyiciye söyler. Derleyici bu söz üzerine dört şeyi yapmaz: (1) erişimi atlamaz, (2) değerini yazmaçta önbelleğe alıp belleğe bakmadan kullanmaz, (3) bir yazmayı gereksiz diye silmez, (4) volatile erişimler arasındaki sırayı kendi başına değiştirmez. Bu sözün önemi, bir donanım yazmacının değeri senin kodun dışındaki bir olayla değişebilmesidir. Bir GPIO giriş yazmacını bir kez okuyup sonra sonsuza kadar aynı değeri kullanırsan, pin değişse bile programın haberi olmaz.

`volatile` **senkronizasyon aracı değildir.** Çok çekirdekli sistemlerde ya da kesmelerle paylaşılan veride bellek sıralaması ve atomiklik gerekir; bunun resmi karşılığı C11 `_Atomic` ve Bölüm 27'nin konusudur. Tek çekirdekli bir MCU'da kesme ile ana döngü arasında `volatile` çoğu durumda yeterlidir, ama bu bir garanti değildir (Bölüm 7'de gördüğümüz tampon örneğindeki uyarı).

Şimdi bunu derleyicinin gerçekte ne yaptığını görerek doğrulayalım. Aşağıdaki program aynı döngüyü, `volatile` olan ve olmayan biçimlerde yazıyor. Hepsini `-O2` ile derledik ve makine kodunu okuduk.

```c
/* volatile_deney.c - derleyici hangi bellek erisimlerini siler? */
#include <stdint.h>

#define DURUM_REG (*(volatile uint32_t *)0x40020010u)

/* 1: volatile yok, bos dongu */
void gecikme_normal(void)
{
    for (uint32_t i = 0; i < 100000u; i++) {
    }
}

/* 2: sayac volatile */
void gecikme_vol(void)
{
    for (volatile uint32_t i = 0; i < 100000u; i++) {
    }
}

/* 3: parametre volatile */
void gecikme_param(volatile uint32_t n)
{
    while (n != 0u) {
        n--;
    }
}

/* 4: yoklama, volatile yok */
void bekle_normal(void)
{
    while (*(uint32_t *)0x40020010u == 0u) {
    }
}

/* 5: yoklama, volatile erisim */
void bekle_vol(void)
{
    while (DURUM_REG == 0u) {
    }
}

```

Programın ilk beş fonksiyonu `volatile`'ın etkisini gösterir. İkinci kısım ise dikkat çekici bir gözlemi içerir.

```c
/* 6: sonsuz dongu, global sayac, volatile yok */
uint32_t global_sayac;
void sonsuz_normal(void)
{
    while (1) {
        global_sayac++;
    }
}

/* 7: ayni dongu, global volatile */
volatile uint32_t global_vol;
void sonsuz_vol(void)
{
    while (1) {
        global_vol++;
    }
}

/* 8: inline edilen volatile parametre */
static void gecikme_satir(volatile uint32_t n)
{
    while (n != 0u) {
        n--;
    }
}

void bekle_satir(void)
{
    gecikme_satir(100000u);
}
```

Şimdi derlenmiş çıktıyı okuyalım. Aşağıdaki kesit yalnızca dört fonksiyonu içeriyor; tam listeyi `volatile_deney.o` ile kendin üretebilirsin:

```term
$ arm-none-eabi-objdump -d volatile_deney.o
00000000 <gecikme_normal>:
   0:	4770      	bx	lr
   2:	bf00      	nop
00000040 <bekle_normal>:
  40:	4b02      	ldr	r3, [pc, #8]	@ (4c <bekle_normal+0xc>)
  42:	691b      	ldr	r3, [r3, #16]
  44:	b903      	cbnz	r3, 48 <bekle_normal+0x8>
  46:	e7fe      	b.n	46 <bekle_normal+0x6>
  48:	4770      	bx	lr
  4a:	bf00      	nop
  4c:	40020000 	.word	0x40020000
00000060 <sonsuz_normal>:
  60:	e7fe      	b.n	60 <sonsuz_normal>
  62:	bf00      	nop
00000074 <bekle_satir>:
  74:	4b01      	ldr	r3, [pc, #4]	@ (7c <bekle_satir+0x8>)
  76:	3b01      	subs	r3, #1
  78:	d1fd      	bne.n	76 <bekle_satir+0x2>
  7a:	4770      	bx	lr
  7c:	000186a0 	.word	0x000186a0
```

Bu çıktıdan çıkan sonuçları tek tek yazalım:

- **`gecikme_normal`** (1. durum): `bx lr` yalnızca. Boş bir `for` döngüsü tamamen silinmiş. Derleyici döngünün hiçbir yan etkisi olmadığını görüp kaldırmış. Gecikme isteyen bir kod bu yüzden hiç gecikme üretmez.
- **`bekle_normal`** (4. durum): donanım yazmacının adresi bir kez yüklenip okunuyor (`ldr r3, [r3, #16]`), sonra `cbnz` ile bakılıyor; sıfırsa `b .` ile sonsuz döngüye giriliyor. Donanım bu arada bayrağı değiştirse bile program bunu asla görmez. Klasik "bayrak hiç değişmiyor" hatasının makine kodudur.
- **`bekle_vol`** (5. durum; tam çıktı `volatile_deney.o` dosyasında): her turda bellekten okuma yapılır, döngü gerçekten bekler.
- **`sonsuz_normal`** (6. durum): `global_sayac++` artırımı tamamen silinmiş, geriye yalnızca `b .` kalmış. Program dışarıdan izlenemeyen bir değişken için iş yapmıyor. C standardı bu tür artırımları gözlemlenebilir davranış saymaz; bu yüzden derleyici onları silebilir.
- **`gecikme_satir`** (8. durum, `bekle_satir` içinde): parametresi `volatile` olmasına rağmen döngü yalnızca bir yazmaçla (`subs r3, #1`) çalışıyor; bellek erişimi yok. Yani `volatile` parametre, fonksiyon satır içine alındığında bu garantiyi kaybetmiş görünüyor. Bu gözlem GCC 13.3.1 ve `-O2` ile yapıldı; genel bir kural değil, bir uyarıdır. Bu yüzden bizim `blink.c` dosyasında gecikmeyi `volatile` bir **yerel** değişkenle yazdık; yerel değişken satır içi açılsa da bellek erişimini korudu (Bölüm 43.8'deki kod, 6 komutluk bir döngü üretiyor).

Şekil 43.3 aynı kaynağın iki farklı makine koduna nasıl dönüştüğünü özetliyor.

![Şekil 43.3: volatile olmadan ve volatile ile aynı yoklama döngüsünün -O2 çıktısı. Volatile yokken okuma bir kez yapılır ve program sonsuz döngüde kalır; volatile iken her yinelemede bellekten okunur.](gorseller/b43_volatile_yolu.png)

Bu deneyden çıkan kural şudur: **donanım yazmacına her erişim `volatile` olmalıdır**, yazmaç adresini de bir `volatile` işaretçiyle ya da yapı (struct) üyesiyle ifade et. Yapı üyeleri için de aynı kural geçerlidir; Bölüm 43.8'de yazmaç yapısını bu kuralla kuracağız.


## 43.5 Bit işlemleri, bit alanları ve bit-band

Donanım yazmaçları bit bit anlamlıdır. Bir GPIO yazmacında her bit bir pinin durumunu taşır; bir kesme bayrağının tek bir biti "oldu" ya da "olmadı" der. Bu yüzden bit işlemleri gömülü C'nin günlük dilidir. Önce güvenilir makroları yazıp rastgele işlemlerle test edeceğiz; sonra iki tehlikeye bakacağız: okuma-değiştirme-yazma (read-modify-write) ve bit alanları (bit-field). Son olarak Cortex-M'nin bit-band özelliğine değineceğiz.

Aşağıdaki program dört bitlik işlemi ve bit-band adres hesabını birlikte sınıyor. Bit işlemleri için 100 000 rastgele işlem üretiyor, her birinde sonucu naif bir modelle karşılaştırıyor. Rastgelelik için sabit tohumlu bir xorshift kullandık; bu sayede her çalıştırmada aynı diziyi görürsün.

```c
/* bit_testleri.c - bit islemleri, bit-band adresi, tamsayi
 * yukseltme. WSL derleme:
 * gcc -O2 -Wall -Wextra -std=c11 -fsanitize=address,undefined */
#include <stdint.h>
#include <stdio.h>

#define BIT(n)         (1u << (n))
#define BIT_SET(r, n)  ((r) |= BIT(n))
#define BIT_CLR(r, n)  ((r) &= ~BIT(n))
#define BIT_TOG(r, n)  ((r) ^= BIT(n))
#define BIT_TEST(r, n) (((r) >> (n)) & 1u)

/* Bit-band takma adresi (ARMv7-M), cevre birimi bolgesi:
 *   alias = 0x42000000 + (adres - 0x40000000) * 32 + bit * 4 */
static uint32_t bitband_adres(uint32_t adres, unsigned bit)
{
    return 0x42000000u + (adres - 0x40000000u) * 32u + bit * 4u;
}

/* Model: once bayt ofsetinden toplam bit sayisi, sonra adres */
static uint32_t bitband_model(uint32_t adres, unsigned bit)
{
    uint32_t bayt_ofseti = adres - 0x40000000u;
    uint32_t bit_toplam = bayt_ofseti * 8u + bit;
    return 0x42000000u + bit_toplam * 4u;
}

/* Sabit tohumlu xorshift: her calistirmada ayni sayilar */
static uint32_t xorshift(uint32_t *s)
{
    uint32_t x = *s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *s = x;
    return x;
}

```

Fonksiyonun asıl gövdesi, bit işlemlerini modelle karşılaştıran bölümdür. Burada `switch` ile üç işlemden biri seçiliyor: set, clear ve toggle. Her işlemden sonra iki şey kontrol ediliyor: tüm yazmacın modelle aynı olması ve seçilen bitin test edilen değerinin de tutması.

```c
int main(void)
{
    /* 1. Bit islemleri: rastgele islemleri modelle karsilastir */
    uint32_t seed = 43u;
    uint32_t r = 0, model = 0;
    uint32_t hata = 0;
    for (int i = 0; i < 100000; i++) {
        uint32_t x = xorshift(&seed);
        unsigned n = x % 32u;
        switch ((x >> 8) % 3u) {
        case 0:
            BIT_SET(r, n);
            model |= (uint32_t)1 << n;
            break;
        case 1:
            BIT_CLR(r, n);
            model &= ~((uint32_t)1 << n);
            break;
        default:
            BIT_TOG(r, n);
            model ^= (uint32_t)1 << n;
            break;
        }
        if (r != model || BIT_TEST(r, n) != ((model >> n) & 1u)) {
            hata++;
        }
    }
    printf("bit islemleri: 100000 islem, hata = %u\n", hata);
    printf("son r = 0x%08X\n", r);

```

Son bölüm bit-band adresini modelle karşılaştırıyor ve tamsayı yükseltme tuzağını gösteriyor.

```c
    /* 2. Bit-band: formul ve model ayni mi? */
    uint32_t adresler[3] = { 0x40020C14u, 0x40020000u, 0x40023830u };
    uint32_t uyusmazlik = 0;
    for (int k = 0; k < 3; k++) {
        for (unsigned b = 0; b < 32; b++) {
            if (bitband_adres(adresler[k], b) !=
                bitband_model(adresler[k], b)) {
                uyusmazlik++;
            }
        }
    }
    printf("bit-band: 96 kontrol, uyusmazlik = %u\n", uyusmazlik);
    printf("ODR bit 12 -> 0x%08X\n", bitband_adres(0x40020C14u, 12));
    printf("ODR bit 0  -> 0x%08X\n", bitband_adres(0x40020C14u, 0));

    /* 3. Tamsayi yukseltme: uint8_t toplamasi int'e yukselir */
    uint8_t a = 200, b = 100;
    int toplam = a + b;
    uint8_t sarmali = (uint8_t)(a + b);
    printf("uint8: a+b = %d, (uint8_t)(a+b) = %u\n", toplam, sarmali);
    if (a + b > 255) {
        printf("a+b > 255 DOGRU (int karsilastirmasi)\n");
    }
    return (hata != 0 || uyusmazlik != 0) ? 1 : 0;
}
```

Bu programı WSL içinde, sanitizer'lar açıkken derledik. Çıktı şöyle:

```term
$ gcc -O2 -Wall -Wextra -std=c11 \
    -fsanitize=address,undefined bit_testleri.c
$ ./bit_testleri
bit islemleri: 100000 islem, hata = 0
son r = 0x5DCE42E4
bit-band: 96 kontrol, uyusmazlik = 0
ODR bit 12 -> 0x424182B0
ODR bit 0  -> 0x42418280
uint8: a+b = 300, (uint8_t)(a+b) = 44
a+b > 255 DOGRU (int karsilastirmasi)
```

Çıktının üç satırı önemlidir. İlk satırda 100 000 işlemde hata sayısı 0; yani set, clear ve toggle makroları naif modelle tutarlı. Bit-band satırında 96 kontrolün (3 adres x 32 bit) hiçbiri uyuşmuyor; formül ile model aynı sonucu veriyor. Üçüncü grup ise `uint8_t` tuzağıdır: `a + b` ifadesi `int`'e yükseltilir, bu yüzden 300 çıkar ve `(uint8_t)(a + b)` 44 olur. Dördüncü satır, koşulun `int` karşılaştırması olduğunu gösterir: `a + b > 255` doğrudur.

Bu tuzağın gömülüde neden önemli olduğu hemen anlaşılır: bir yazmacın 8 bitlik bir alanını okuyup bunu bir sayaçla topladığında, derleyici taşmayı 8 bit içinde değil 32 bit ya da `int` içinde yapar. Taşma sınırını elle kontrol etmezsen sonuç sessizce yanlış olur. Tamsayı yükseltme kurallarını ve işaretli taşmanın tanımsız davranış (UB) olduğunu Bölüm 1 ve Bölüm 2'de gördün; burada aynı kuralın yazmaç biçiminde nasıl göründüğünü gördün.

### Okuma-değiştirme-yazma tehlikesi

`GPIOD->ODR |= (1u << 12)` ifadesi aslında üç adımdır: yazmacı oku, bitini değiştir, sonucu yaz. Tek çekirdekli bir sistemde bu tek bir kesme gelene kadar güvenlidir; ama ana döngü `ODR`'yi okuyup yazarken bir kesme aynı yazmacın başka bir bitini değiştirirse, kesmenin yazdığı değer ana döngünün yazışıyla ezilir. Bu hataya "kayıp güncelleme" (lost update) denir ve bulması çok zordur, çünkü yalnızca nadir zamanlamalarda ortaya çıkar.

STM32'nin **BSRR** yazmacı bu sorunu donanım seviyesinde çözer. BSRR'nin düşük 16 biti bir pini set eder, yüksek 16 biti bir pini sıfırlar ve her bit için yalnızca yazılan değer etkilidir. Okuma gerekmez, bu yüzden yarış penceresi yoktur. Resmi HAL'in `HAL_GPIO_WritePin` fonksiyonu da bunu kullanır. Aşağıdaki kesit STM32F4 HAL v1.8.0 kaynağından (`stm32f4xx_hal_gpio.c`) alındı; EV Dashboard'un kullandığı HAL sürümünü bilmiyoruz, bu yüzden Mert'in projesinde sürümü kontrol etmek gerekir:

```c
{
  /* Check the parameters */
  assert_param(IS_GPIO_PIN(GPIO_Pin));
  assert_param(IS_GPIO_PIN_ACTION(PinState));

  if(PinState != GPIO_PIN_RESET)
  {
    GPIOx->BSRR = GPIO_Pin;
  }
  else
  {
    GPIOx->BSRR = (uint32_t)GPIO_Pin << 16U;
  }
}
```

Fonksiyon, `PinState` değeri `GPIO_PIN_RESET` değilse `GPIOx->BSRR = GPIO_Pin` yazar; değilse pin değerini 16 bit kaydırıp `BSRR`'ye yazar. Yani yazma tek bir kayıt erişimidir; `ODR`'nin okunup değiştirilmesi gerekmez. Tasarım kararının bedeli, BSRR'nin pin durumunu **okumak için kullanılamamasıdır**: pinin durumunu öğrenmek için `ODR` ya da `IDR` okunur.

### Bit alanları (bit-field): kullanışlı ama tehlikeli

C'de bir yapının üyesinin kaç bit tutacağını belirtebilirsin. Donanım yazmacını bit alanlarıyla modellemek cazip görünür:

```c
/* bitfield.c - bit alani ile maske yazmanin makine kodu */
#include <stdint.h>

typedef struct {
    uint32_t dusuk  : 4;   /* bit 0-3 */
    uint32_t orta   : 8;   /* bit 4-11 */
    uint32_t yuksek : 20;  /* bit 12-31 */
} alan_t;

void alan_yaz(volatile alan_t *r)
{
    r->orta = 0x5Au;
}

void maske_yaz(volatile uint32_t *r)
{
    *r = (*r & ~(0xFFu << 4)) | (0x5Au << 4);
}
```

Bu yapının bit düzeni derleyiciye bırakılmıştır. C standardı bit alanlarının bellekte hangi sırayla ve hangi sınırlarla yerleşeceğini **uygulamaya bağlı** bırakır. Aynı kaynak başka bir derleyicide farklı bir düzen üretebilir ve bu yüzden donanım yazmacı için taşınabilir değildir. Ayrıca bit alanına yazmak, derleyicinin bütün kelimeyi okuyup değiştirip geri yazmasını gerektirir. Aşağıda iki fonksiyonun ARM çıktısını görüyorsun: ikisi de bir `ldr`, bir değiştirme ve bir `str` üretiyor.

```term
$ arm-none-eabi-objdump -d bitfield.o
00000000 <alan_yaz>:
   0:	6803      	ldr	r3, [r0, #0]
   2:	225a      	movs	r2, #90	@ 0x5a
   4:	f362 130b 	bfi	r3, r2, #4, #8
   8:	6003      	str	r3, [r0, #0]
   a:	4770      	bx	lr
0000000c <maske_yaz>:
   c:	6803      	ldr	r3, [r0, #0]
   e:	f423 637f 	bic.w	r3, r3, #4080	@ 0xff0
  12:	f443 63b4 	orr.w	r3, r3, #1440	@ 0x5a0
  16:	6003      	str	r3, [r0, #0]
  18:	4770      	bx	lr
  1a:	bf00      	nop
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
/* startup.c - Cortex-M4 icin C ile yazilmis baslangic kodu.
 * Assembly yok: vektor tablosu, reset ve varsayilan isleyici.
 * Derleme bayraklari: -ffreestanding (libc varsayimi yok) ve
 * -fno-tree-loop-distribute-patterns (kopyalama dongusunun
 * memcpy'ye donusmesini onleyen onlem; bu kodda gozlemlenmedi). */
#include <stdint.h>

/* Baglayici betiginin tanimladigi semboller (adres) */
extern uint32_t _estack;                 /* RAM sonu: yigin tepesi */
extern uint32_t _sidata, _sdata, _edata; /* .data: kaynak ve hedef */
extern uint32_t _sbss, _ebss;            /* .bss: sifirlanacak */

extern int main(void);
void Reset_Handler(void);
void Varsayilan_Isleyici(void);

/* Vektor tablosu: ilk kelime baslangic MSP, ikincisi reset.
 * Fonksiyon adreslerinin bit 0'i derleyici tarafindan 1 yapilir
 * (Thumb biti). Kesme girisleri Bolum 44'te anlatilir. */
__attribute__((used, section(".isr_vector")))
void *const vektor_tablosu[16] = {
    (void *)&_estack,            /* 0  baslangic MSP */
    (void *)Reset_Handler,       /* 1  reset */
    (void *)Varsayilan_Isleyici, /* 2  NMI */
    (void *)Varsayilan_Isleyici, /* 3  HardFault */
    (void *)Varsayilan_Isleyici, /* 4  MemManage */
    (void *)Varsayilan_Isleyici, /* 5  BusFault */
    (void *)Varsayilan_Isleyici, /* 6  UsageFault */
    (void *)0, (void *)0, (void *)0, (void *)0, /* 7-10 */
    (void *)Varsayilan_Isleyici, /* 11 SVCall */
    (void *)Varsayilan_Isleyici, /* 12 DebugMonitor */
    (void *)0,                   /* 13 ayrilmis */
    (void *)Varsayilan_Isleyici, /* 14 PendSV */
    (void *)Varsayilan_Isleyici, /* 15 SysTick */
};

```

Tablonun üç özelliğine dikkat et. Birincisi, `_estack` bağlayıcı betiğinde tanımlanan bir sembolün **adresidir**; yani tablonun ilk değeri, RAM'in sonunu gösterir ve yığın oradan aşağı doğru büyür. İkincisi, fonksiyon adresleri derleyici tarafından 1 ile *veya*'lanmıştır (Thumb biti). Bu kuralı objdump çıktısında doğrulayabilirsin. Üçüncüsü, `(void *)0` gibi ayrılmış girişler yerinde bırakılır; tablonun her girişinin doğru konumda olması zorunludur, çünkü donanım sıra numarasına göre adres okur.

`objdump -s` ile tablonun bellekteki ham hâline bakalım:

```term
$ arm-none-eabi-objdump -s -j .isr_vector blink.elf

blink.elf:     file format elf32-littlearm

Contents of section .isr_vector:
 8000000 00000220 45000008 41000008 41000008  ... E...A...A...
 8000010 41000008 41000008 41000008 00000000  A...A...A.......
 8000020 00000000 00000000 00000000 41000008  ............A...
 8000030 41000008 00000000 41000008 41000008  A.......A...A...
```

Satırın ilk dört baytı `00 00 02 20`dir; bayt sırası little-endian olduğundan bu `0x20020000` eder ve `_estack` ile aynıdır. İkinci dört bayt `45 00 00 08`dir, yani `0x08000045`tir. Son bit 1 olduğu için bu bir Thumb adresidir; gerçek fonksiyon adresi `0x08000044` (`Reset_Handler`) ve Thumb biti ekli hâlidir. Diğer kesme girişleri `0x08000041`, yani `Varsayilan_Isleyici` (`0x08000040`) fonksiyonuna işaret eder. Şekil 43.5, tablonun ilk girişlerini bu değerlerle birlikte gösteriyor.

![Şekil 43.5: Vektör tablosunun ilk girişleri ve bu programdan okunan gerçek değerler. Thumb biti, fonksiyon adresinin en düşük bitinde taşınır.](gorseller/b43_vektor.png)

Reset işleyicisinin görevi üç işi sırayla yapmaktır: `.data` bölümünü flash'tan RAM'e kopyalamak, `.bss` bölümünü sıfırlamak ve `main`'i çağırmak. Ayrıca bu programda FPU'yu açıyoruz, çünkü FPU kapalıyken kayan nokta komutu çalıştırmak bir usage fault üretir.

```c
/* Reset: .data'yi flash'tan RAM'e kopyala, .bss'yi sifirla,
 * FPU'yu ac, sonra main'e gec. */
void Reset_Handler(void)
{
    uint32_t *kaynak = &_sidata;
    uint32_t *hedef = &_sdata;
    while (hedef < &_edata) {
        *hedef++ = *kaynak++;
    }

    for (uint32_t *p = &_sbss; p < &_ebss; p++) {
        *p = 0u;
    }

    /* CPACR (0xE000ED88) bit 20-23: CP10, CP11 tam erisim.
     * Bu acilmadan ilk kayan nokta komutu usage fault uretir. */
    *(volatile uint32_t *)0xE000ED88u |= (0xFu << 20);

    main();
    while (1) {
    }
}

void Varsayilan_Isleyici(void)
{
    while (1) {
    }
}
```

Kopyalama ve sıfırlama döngüleri bağlayıcı betiğinin sağladığı sembollerle çalışır: `_sidata` flash'taki kaynağın adresidir, `_sdata` ve `_edata` RAM'deki hedef aralığın başı ve sonudur, `_sbss` ve `_ebss` sıfırlanacak aralıktır. Sembollerin adreslerini ve anlamlarını Bölüm 43.7'de bağlayıcı betiğinden göreceksin. Şekil 43.6 reset akışını sırayla gösteriyor.

![Şekil 43.6: Reset akışı. Donanım SP ve PC'yi vektör tablosundan yükler; Reset_Handler kopyalama, sıfırlama ve FPU adımlarından sonra main'e geçer.](gorseller/b43_reset_akisi.png)

**Neden iki bayrak?** Derleme komutunda iki bayrak kullandık: `-ffreestanding` derleyiciye ortamın barındırılmış (hosted) olmadığını, yani libc'nin hazır olmadığını söyler; `-fno-tree-loop-distribute-patterns` ise derleyicinin bir döngüyü `memcpy` ya da `memset` çağrısına çevirme optimizasyonunu kapatır. Bu bayrağın gerekliliğini deneyle sınadık: bu kodda ve bu derleyicide (`-O2` ve `-O3`) kopyalama döngüleri inline açıldı, `memcpy` çağrısı üretilmedi. Yani bayrak bir önlemdir; bu projede gözlemlenmiş bir hata değildir. Yine de bağlayıcının `memcpy` bulamadığı bir ortamda bu tür bir çağrı çalışmayan bir programa yol açar, bu yüzden önlemi açık tutmak sağlam bir alışkanlıktır.

Son olarak bellekte `.data` bölümünün **iki adresi** olduğunu unutma. Flash'taki adres (LMA: load memory address) başlangıç değerinin saklandığı yerdir; RAM'deki adres (VMA: virtual memory address, gömülüde çalışma adresi) değişkenin programın içinde kullanıldığı yerdir. Şekil 43.7 bu ayrımı gösteriyor.

![Şekil 43.7: .data bölümünün LMA ve VMA adresleri. Başlangıç değeri flash'ta, çalışma kopyası RAM'de yaşar; Reset_Handler bir kopyayı diğerine taşır.](gorseller/b43_lma_vma.png)

## 43.7 Bağlayıcı betiği, map dosyası ve bellek bütçesi

Derleyici bir kaynak dosyayı bitirdiğinde adresleri henüz belli değildir (Bölüm 37.9'da gördüğün gibi). Bağlayıcı, bu nesne dosyalarını bir araya getirir, her bölümü bir bellek bölgesine yerleştirir ve sembollere adres atar. Gömülü tarafta bu adım, programın flash ve RAM'e ne kadar yer kapladığını belirleyen yerdir. Bağlayıcı betiği bu işin kurallarını yazdığımız dosyadır.

```c
/* link.ld - STM32F407VG baglayici betigi (sadelestirilmis).
 * FLASH 1 MB @0x08000000, SRAM 128 KB @0x20000000.
 * Adresler RM0090 bellek haritasina gore. */
ENTRY(Reset_Handler)

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

/* Yigin RAM'in en ustunden asagi dogru buyur */
_estack = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
  .isr_vector :
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector))  /* vektor tablosu basta */
    . = ALIGN(4);
  } > FLASH

  .text :
  {
    . = ALIGN(4);
    *(.text)
    *(.text*)
    . = ALIGN(4);
    _etext = .;
  } > FLASH

  .rodata :
  {
    . = ALIGN(4);
    *(.rodata)
    *(.rodata*)
    . = ALIGN(4);
  } > FLASH

  /* LMA: flash'taki kaynak; VMA: RAM'deki calisma adresi */
```

Betiğin ilk bölümü bellek bölgelerini tanımlar. `FLASH` 1 MB, `RAM` 128 KB boyutundadır; `rx` ve `rwx` nitelikleri bölgelerin okuma, yazma ve çalıştırma izinlerini tanımlar. `_estack = ORIGIN(RAM) + LENGTH(RAM);` satırı yığının tepesini RAM'in sonuna koyar; yığın aşağı doğru büyür, yani en düşük adresinden önce kendi tepesine kadar boş olmalıdır.

```c
  _sidata = LOADADDR(.data);

  .data :
  {
    . = ALIGN(4);
    _sdata = .;
    *(.data)
    *(.data*)
    . = ALIGN(4);
    _edata = .;
  } > RAM AT> FLASH

  .bss (NOLOAD) :
  {
    . = ALIGN(4);
    _sbss = .;
    *(.bss)
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;
  } > RAM

  /* newlib-nano'nun _sbrk'si bu sembolu ister */
  PROVIDE(end = _ebss);

  /* Butce denetimi: veri ile yigin cakismamali */
  ASSERT(_ebss + 1024 <= _estack, "RAM: yigin icin 1 KB yok")
}
```

Betiğin ikinci bölümü ne nereye gider sorusunu cevaplar. `KEEP(*(.isr_vector))` vektör tablosunu, bağlayıcının çöp toplama (`--gc-sections`) sırasında atmasını engelleyerek flash'ın en başına koyar. `.data` için yazdığımız `> RAM AT> FLASH` ifadesi, bölümün **VMA**sını RAM'e, **LMA**sını flash'a koyar. `_sidata = LOADADDR(.data);` ise flash'taki kaynağın adresini bir sembole bağlar; Reset_Handler bu sembolü kullanır. `PROVIDE(end = _ebss);` sembolü, newlib-nano'nun `_sbrk` fonksiyonunun beklediği bir bağlantıdır (Bölüm 43.10'da printf'te görülecek). Son satırdaki `ASSERT` bir bütçe denetimidir: `.bss` sonu ile yığın tepesi arasında en az 1 KB boşluk yoksa bağlayıcı hata verir. Bu, RAM taşmasını derleme aşamasında yakalamanın en ucuz yoludur.

Bağlayıcının sonucunu `objdump -h` ile görebilirsin. Her bölüm için iki adres vardır: **VMA** (çalışırken kullanılan) ve **LMA** (dosyada yerleşeceği yer).

```term
$ arm-none-eabi-objdump -h blink.elf

blink.elf:     file format elf32-littlearm

Sections:
Idx Name          Size      VMA       LMA       File off  Algn
  0 .isr_vector   00000040  08000000  08000000  00001000  2**2
                  CONTENTS, ALLOC, LOAD, READONLY, DATA
  1 .text         00000120  08000040  08000040  00001040  2**2
                  CONTENTS, ALLOC, LOAD, READONLY, CODE
  2 .rodata       00000004  08000160  08000160  00001160  2**2
                  CONTENTS, ALLOC, LOAD, READONLY, DATA
  3 .data         00000004  20000000  08000164  00002000  2**2
                  CONTENTS, ALLOC, LOAD, DATA
  4 .bss          00000008  20000004  08000168  00002004  2**2
                  ALLOC
  5 .comment      00000043  00000000  00000000  00002004  2**0
                  CONTENTS, READONLY
  6 .ARM.attributes 00000034  00000000  00000000  00002047  2**0
                  CONTENTS, READONLY
```

`.data` satırında VMA `20000000` (RAM), LMA `08000164` (flash) olduğunu görüyorsun. Bu bizim Şekil 43.7'deki ayrımın kanıtıdır. `.rodata` (4 bayt) LMA ve VMA'nın aynı olduğu, flash'ta kalan bir bölümdür; `kademe` dizisi buraya düşer. `.bss` ise yalnızca VMA'ya sahiptir, dosyada yer kaplamaz (`ALLOC` ama `CONTENTS` yok); yani sıfırlanacak alan flash'ta bir şey tutmaz.

Sembol adreslerini `nm` ile ayrıca okuyabilirsin:

```term
$ arm-none-eabi-nm -n blink.elf
08000000 R vektor_tablosu
08000040 T Varsayilan_Isleyici
08000044 T Reset_Handler
080000b0 T menzil_hesapla
080000c8 T main
08000160 T _etext
08000160 R kademe
08000164 A _sidata
20000000 D _sdata
20000000 D acilis_degeri
20000004 D _edata
20000004 B _sbss
20000004 B sonuc_menzil
20000008 B dongu_sayaci
2000000c B _ebss
20020000 R _estack
```

Listede `kademe` (`08000160`, flash'ta, `R` yani salt okunur), `acilis_degeri` (`20000000`, `D` yani başlangıçlı veri), `sonuc_menzil` ve `dongu_sayaci` (`B`, başlangıçsız, `.bss`) görünüyor. Dikkat et, `_sbss`/`_ebss` gibi sınır sembolleri de birer adrestir; kendileri veri taşımaz.

Bağlayıcı `-Wl,-Map=blink.map` ile bir map dosyası da üretir. Map dosyası bir programın "neden bu kadar büyük?" sorusunun cevabıdır: hangi girdi dosyasının hangi bölüme, hangi adrese yerleştiğini ve hangi sembolün nerede olduğunu gösterir. Aşağıdaki kesit bellek yapılandırmasını gösteriyor:

```term
$ less blink.map
Memory Configuration

Name             Origin             Length             Attributes
FLASH            0x08000000         0x00100000         xr
RAM              0x20000000         0x00020000         xrw
*default*        0x00000000         0xffffffff
```

Ve `.rodata`, `.data`, `.bss` ile bütçe denetiminin yer aldığı kesit:

```term
$ less blink.map
.rodata         0x08000160        0x4
                0x08000160                        . = ALIGN (0x4)
 *(.rodata)
 .rodata        0x08000160        0x4 blink.o
                0x08000160                kademe
 *(.rodata*)
                0x08000164                        . = ALIGN (0x4)
   ...

.rel.dyn        0x08000164        0x0
 .rel.iplt      0x08000164        0x0 startup.o

.data           0x20000000        0x4 load address 0x08000164
                0x20000000                        . = ALIGN (0x4)
                0x20000000                        _sdata = .
 *(.data)
 .data          0x20000000        0x0 startup.o
 .data          0x20000000        0x4 blink.o
                0x20000000                acilis_degeri
 *(.data*)
                0x20000004                        . = ALIGN (0x4)
                0x20000004                        _edata = .

.igot.plt       0x20000004        0x0 load address 0x08000168
 .igot.plt      0x20000004        0x0 startup.o

.bss            0x20000004        0x8 load address 0x08000168
                0x20000004                        . = ALIGN (0x4)
                0x20000004                        _sbss = .
 *(.bss)
 .bss           0x20000004        0x0 startup.o
 .bss           0x20000004        0x8 blink.o
                0x20000004                sonuc_menzil
                0x20000008                dongu_sayaci
 *(.bss*)
 *(COMMON)
                0x2000000c                        . = ALIGN (0x4)
                0x2000000c                        _ebss = .
                [!provide]                        PROVIDE (end = _ebss)
   ...
```

İkinci kesitte iki ayrıntıya dikkat et. Birincisi, map dosyası `.rel.dyn` ve `.igot.plt` gibi bölümleri de gösterir; bunlar bizim betiğimizde tanımlanmayan (orphan) bölümlerdir ve boyutları sıfırdır. Bağlayıcı bu bölümleri standart kurallarla yerleştirir. İkincisi, `ASSERT` satırı bütçe denetiminin çalıştığını gösterir: `_ebss + 0x400 <= _estack` ifadesi doğru olduğu için bağlayıcı sessiz kalır.

Boyut özeti `size` komutuyla gelir:

```term
$ arm-none-eabi-size blink.elf
   text	   data	    bss	    dec	    hex	filename
    356	      4	      8	    368	    170	blink.elf
```

`size` üç sütun verir: `text` (kod ve sabit veriler), `data` (başlangıç değeri olan RAM verisi) ve `bss` (sıfırlanacak RAM). Bunlardan bütçeyi şöyle hesaplarsın: **flash kullanımı = text + data**, **RAM kullanımı = data + bss**. Bu programda flash 356 + 4 = 360 bayt, RAM 4 + 8 = 12 bayt. `text` sütununun 356 olduğunu da kontrol edebilirsin: `.isr_vector` 64 bayt (`0x40`), `.text` 288 bayt (`0x120`) ve `.rodata` 4 bayt; toplam 356. Yani `size`'daki "text", kodla birlikte vektör tablosunu ve sabit verileri de taşır. Bu hesap, Örnek 3'te bir bütçe kararı verirken kullanacağın temel formüldür.

Yığın için ayrı bir ölçüm gerekir. `-fstack-usage` ile derleyici her fonksiyonun yığın çerçevesini `.su` dosyasına yazar (ayrıntısı Bölüm 43.9'da). Bu programın `.su` dosyası şöyle:

```term
$ cat blink.su
blink.c:21:10:menzil_hesapla	0	static
blink.c:36:5:main	8	static
```

Bu iki fonksiyon yerel değişken kullanmadığı için çerçeve boyutu düşük; `main` 8 bayt ayırıyor. Bağlayıcının ürettiği son bütçe şu anlama gelir: RAM'de 12 bayt sabit veri, en fazla birkaç bayt yığın; geri kalan yaklaşık 128 KB'ın tamamı yığına ve sonraki gelişmelere (tamponlar, kesme yığınları) açık.

Şekil 43.8, bağlayıcının üç girdiyi (startup.o, blink.o ve betik) bu iki bellek bölgesine nasıl yerleştirdiğini özetliyor.

![Şekil 43.8: Bağlayıcının girdi bölümlerini betik kurallarına göre flash ve RAM bölgelerine yerleştirmesi.](gorseller/b43_baglayici.png)

## 43.8 İlk program: GPIO ile LED ve yazmaçların anatomisi

Gömülü dünyanın "merhaba dünyası" bir LED'in yanıp sönmesidir. Bunu bir kütüphane olmadan yapacağız: yazmaçların adreslerini ve düzenini bir başlık dosyasında tanımlayacak, LED pinini bu yazmaçlardan sürecek ve bekleme döngüsünü yazacağız.

Önce yazmaç düzeni. Bir çevre biriminin yazmaçları bellekte ardışık ve belirli ofsetlerdedir; bunu bir `struct` ile modellemek hem okunaklı hem de derleyici tarafından denetlenebilir bir yoldur. Aşağıdaki başlık dosyası GPIO ve RCC yazmaçlarını bu şekilde tanımlıyor.

```c
/* reg.h - STM32F407 yazmac haritasi (RM0090 adresleri).
 * Her yazmac sabit bir adreste duran volatile bir tamsayidir.
 * Ofsetler _Static_assert ile derleme aninda denetlenir. */
#ifndef REG_H
#define REG_H

#include <stdint.h>
#include <stddef.h>

#define RCC_BASE    0x40023800u
#define GPIOD_BASE  0x40020C00u

typedef struct {
    volatile uint32_t MODER;    /* 0x00: pin modu (2 bit/pin) */
    volatile uint32_t OTYPER;   /* 0x04: cikis tipi */
    volatile uint32_t OSPEEDR;  /* 0x08: hiz */
    volatile uint32_t PUPDR;    /* 0x0C: cekme direnci */
    volatile uint32_t IDR;      /* 0x10: giris verisi (okuma) */
    volatile uint32_t ODR;      /* 0x14: cikis verisi */
    volatile uint32_t BSRR;     /* 0x18: set/reset (yalniz yazma) */
    volatile uint32_t LCKR;     /* 0x1C: kilit */
    volatile uint32_t AFR[2];   /* 0x20, 0x24: alternatif islev */
} GPIO_TypeDef;

```

Her üye `volatile uint32_t` olarak işaretlenmiştir, çünkü her biri bir donanım yazmacıdır. `GPIO_TypeDef` yapısı STM32F4'ün referans kılavuzundaki yazmaç sırasını izler: `MODER` ofset `0x00`, `IDR` `0x10`, `ODR` `0x14`, `BSRR` `0x18`. Yapıdaki her alanın ofsetinin doğru olduğunu derleme aşamasında `_Static_assert` ile denetliyoruz; yanlış bir ofset derlemeyi durdurur.

```c
typedef struct {
    volatile uint32_t CR;         /* 0x00 */
    volatile uint32_t PLLCFGR;    /* 0x04 */
    volatile uint32_t CFGR;       /* 0x08 */
    volatile uint32_t CIR;        /* 0x0C */
    volatile uint32_t AHB1RSTR;   /* 0x10 */
    volatile uint32_t AHB2RSTR;   /* 0x14 */
    volatile uint32_t AHB3RSTR;   /* 0x18 */
    uint32_t          RESERVED0;  /* 0x1C */
    volatile uint32_t APB1RSTR;   /* 0x20 */
    volatile uint32_t APB2RSTR;   /* 0x24 */
    uint32_t          RESERVED1[2]; /* 0x28, 0x2C */
    volatile uint32_t AHB1ENR;    /* 0x30: AHB1 saat kapisi */
} RCC_TypeDef;

_Static_assert(offsetof(GPIO_TypeDef, MODER) == 0x00, "MODER");
_Static_assert(offsetof(GPIO_TypeDef, ODR) == 0x14, "ODR");
_Static_assert(offsetof(GPIO_TypeDef, BSRR) == 0x18, "BSRR");
_Static_assert(offsetof(RCC_TypeDef, AHB1ENR) == 0x30, "AHB1ENR");

#define GPIOD ((GPIO_TypeDef *)GPIOD_BASE)
#define RCC   ((RCC_TypeDef *)RCC_BASE)

#endif /* REG_H */
```

RCC yapısı da aynı yöntemle kuruldu. `AHB1ENR` yazmacı ofset `0x30`dadır; bu yazmaç GPIO portlarının saat kapılarını açar. Yapıların doğruluğunu bağımsız bir kaynakla da kontrol ettik: STMicroelectronics'in resmi cihaz başlığı `stm32f407xx.h` (sürüm v2.6.10) `GPIO_TypeDef` ve `RCC_TypeDef` yapılarını aynı alan sırasıyla tanımlıyor; `GPIOD_BASE` değerini `AHB1PERIPH_BASE + 0x0C00` olarak, `RCC_BASE` değerini `AHB1PERIPH_BASE + 0x3800` olarak veriyor. Yani kendi başlığımız ile resmi başlık aynı adresleri kullanır. Gerçek projelerde bu başlığı elle yazmazsın; üretici başlığını kullanırsın. Biz yapıyı görmek için kendimiz yazdık.

Şimdi LED programı. Kart olarak STM32F4 Discovery'nin yeşil LED'ini (PD12) varsaydık; kendi kartında pin farklı olabilir.

```c
/* blink.c - STM32F407 uzerinde PD12 LED'i yalnizca yazmaclarla
 * surer. Kart: STM32F4 Discovery varsayimi (PD12 yesil LED).
 * Bu program kartta denenmedi; dogrulama emulatorde yapildi. */
#include <stdint.h>
#include "reg.h"

#define LED_PIN 12u   /* PD12 */

/* Baslangic degeri olan global: .data (flash'tan RAM'e kopya) */
uint32_t acilis_degeri = 0xCAFE0001u;
/* Baslangicsiz global: .bss (reset isleyicisi sifirlar).
 * volatile: artirimi derleyici silemez (bkz. Bolum metni). */
volatile uint32_t dongu_sayaci;
/* Yalniz okunur tablo: .rodata'da flash'ta kalir */
const uint8_t kademe[4] = { 25u, 50u, 75u, 100u };
/* Emulator bu degiskeni RAM'den okur */
volatile uint32_t sonuc_menzil;

/* Batarya yuzdesinden menzil: EV Dashboard'daki modelin tam sayi
 * karsiligi (batarya / 100 * 165). Kayan nokta yerine tam sayi. */
uint32_t menzil_hesapla(uint8_t batarya)
{
    return ((uint32_t)batarya * 165u) / 100u;
}

/* Yerel sayac volatile: her azaltma bellege yazilir; derleyici
 * dongunun etkisiz oldugunu dusunup silemez. */
```

Bu dosyada dört tür global değişken var ve her biri bağlayıcıda farklı bir bölüme düşer. `acilis_degeri` başlangıç değeri taşıdığı için `.data`dadır; flash'tan RAM'e kopyalanır. `dongu_sayaci` ve `sonuc_menzil` başlangıçsızdır, `.bss`te yaşar ve reset işleyicisi tarafından sıfırlanır. `kademe` `const` olduğu için `.rodata`ya, yani flash'a yerleşir; RAM'i harcamaz. `menzil_hesapla` EV Dashboard'daki `Menzil_Hesapla` fonksiyonunun tam sayı karşılığıdır; kayan nokta yerine tam sayı kullanır, böylece FPU'suz bir yolda da aynı sonucu verir.

```c
static void gecikme(uint32_t n)
{
    volatile uint32_t sayac = n;
    while (sayac != 0u) {
        sayac--;
    }
}

int main(void)
{
    RCC->AHB1ENR |= (1u << 3);                /* GPIODEN */
    GPIOD->MODER &= ~(3u << (2u * LED_PIN));  /* 2 bit sil */
    GPIOD->MODER |=  (1u << (2u * LED_PIN));  /* 01: cikis */

    sonuc_menzil = menzil_hesapla(kademe[acilis_degeri & 3u]);
    dongu_sayaci = acilis_degeri & 0xFFu;

    while (1) {
        GPIOD->BSRR = (1u << LED_PIN);          /* set: yanar */
        gecikme(100000u);
        GPIOD->BSRR = (1u << (LED_PIN + 16u));  /* reset: soner */
        gecikme(100000u);
        dongu_sayaci++;
    }
}
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
   text	   data	    bss	    dec	    hex	filename
    356	      4	      8	    368	    170	blink.elf
```

Bayrakların çoğunu zaten açıkladık: `-mcpu`, `-mthumb` ve `-mfloat-abi=hard -mfpu=fpv4-sp-d16` hedef çekirdeği ve FPU'yu tanımlar; `-nostdlib -nostartfiles` ise standart başlangıç dosyasını ve libc'yi bağlamaz, çünkü başlangıç kodu bizim. `-Wl,-Map=` map dosyasını üretir.

### Emulatörde çalıştırmak

Kartımız olmadığı için programın gerçekten çalışıp çalışmadığını bir emulatörde denedik. Unicorn Engine, ARM komut kümesini çalıştıran bir CPU emulatörüdür; Thumb ve Cortex-M modunu destekler (`UC_MODE_THUMB | UC_MODE_MCLASS`). Emulatör çevre birimlerini modellemez; yalnızca komutları ve bellek yazmalarını çalıştırır. Bu yüzden LED'in gerçekten yandığını değil, programın yazmaçlara **doğru değerleri yazdığını** doğrulayabiliriz. Harness'ın kodu dört parçada:

```python
# -*- coding: utf-8 -*-
"""Cortex-M4 ikilisini Unicorn ile calistirir (simulasyon).

Kullanim: python -I harness.py <elf> <bin> <cikti_klasoru>
  <bin> : objcopy -O binary ile uretilmis flash goruntusu
Ciktilar: ekrana dokum; ayrica <cikti_klasoru> altina
  startup_iz.csv (startup komutlari, r1-r3 durumu) ve
  led_trafik.csv (GPIOD BSRR yazmalari).
Not: Unicorn islevsel bir emulatordur; zamanlama ve cevre
birimi davranisi modellenmez. BSRR yazmasi ODR'yi degistirmez
(donanimda degistirir); bu bir model farkidir.
"""
import os
import struct
import subprocess
import sys

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS
from unicorn import UC_PROT_ALL, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_R1
from unicorn.arm_const import UC_ARM_REG_R2, UC_ARM_REG_R3

# Windows'ta Python'dan tam yol: ortam PATH'ine bagli olmasin
NM = ("C:/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins/"
      "com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32."
      "13.3.rel1.win32_1.0.0.202411081344/tools/bin/"
      "arm-none-eabi-nm.exe")
FLASH = (0x08000000, 0x00100000)
RAM = (0x20000000, 0x00020000)
PERIF = (0x40020000, 0x00004000)
SCB = (0xE000E000, 0x00001000)
BSRR = 0x40020C18


```

```python
def simgeler(elf):
    out = subprocess.run([NM, "-n", elf], capture_output=True,
                         text=True, check=True).stdout
    tablo = {}
    for satir in out.splitlines():
        p = satir.split()
        if len(p) == 3:
            tablo[p[2]] = int(p[0], 16)
    return tablo


def main():
    elf, binf, cikti = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(cikti, exist_ok=True)
    sym = simgeler(elf)
    flash = open(binf, "rb").read()

    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    for taban, boy in (FLASH, RAM, PERIF, SCB):
        uc.mem_map(taban, boy, UC_PROT_ALL)
    uc.mem_write(FLASH[0], flash)
    uc.mem_write(RAM[0], b"\xAA" * 0x100)   # bilinen desen

    sp0, reset = struct.unpack("<II", flash[0:8])
    uc.reg_write(UC_ARM_REG_SP, sp0)
    print("Vektor[0] (SP)    = 0x%08X" % sp0)
    print("Vektor[1] (reset) = 0x%08X  (Thumb biti=%d)"
          % (reset, reset & 1))

    say = [0]
    iz = []
    yaz = []
    faz = [1]

```

```python
    def komut(uc_, adr, boy, _u):
        say[0] += 1
        if faz[0] == 1:
            iz.append((adr,
                       uc_.reg_read(UC_ARM_REG_R1),
                       uc_.reg_read(UC_ARM_REG_R2),
                       uc_.reg_read(UC_ARM_REG_R3)))

    def bellek(uc_, tur, adr, boy, deger, _u):
        if PERIF[0] <= adr < PERIF[0] + PERIF[1]:
            yaz.append((say[0], adr, deger & 0xFFFFFFFF))

    uc.hook_add(UC_HOOK_CODE, komut)
    uc.hook_add(UC_HOOK_MEM_WRITE, bellek)

    def oku32(adr):
        return struct.unpack("<I", bytes(uc.mem_read(adr, 4)))[0]

    main_adr = sym["main"] & ~1
    # 1. faz: reset -> main (startup)
    uc.emu_start(reset, main_adr, 0, 0)
    print("\n[1] Startup: main'e varis, komut = %d" % say[0])
    print("  .data kaynagi (flash)  : 0x%08X"
          % oku32(sym["_sidata"]))
    print("  acilis_degeri (RAM)    : 0x%08X"
          % oku32(sym["acilis_degeri"]))
    print("  .bss ilk kelime        : 0x%08X" % oku32(sym["_sbss"]))
    print("  .bss ikinci kelime     : 0x%08X"
          % oku32(sym["_sbss"] + 4))
    print("  CPACR (0xE000ED88)     : 0x%08X" % oku32(0xE000ED88))
    with open(os.path.join(cikti, "startup_iz.csv"), "w") as f:
        f.write("sira,adres,r1,r2,r3\n")
        for k, (a, r1, r2, r3) in enumerate(iz, 1):
            f.write("%d,0x%08X,0x%08X,0x%08X,0x%08X\n"
                    % (k, a, r1, r2, r3))

    # 2. faz: main dongusu
    faz[0] = 2
```

```python
    say[0] = 0
    yaz.clear()
    uc.emu_start(main_adr | 1, 0, 0, 2500000)
    print("\n[2] main calisti, komut = %d" % say[0])
    print("  RCC AHB1ENR (0x40023830): 0x%08X" % oku32(0x40023830))
    print("  GPIOD MODER (0x40020C00): 0x%08X" % oku32(0x40020C00))
    print("  sonuc_menzil (RAM)      : %d"
          % oku32(sym["sonuc_menzil"]))
    print("  dongu_sayaci (RAM)      : %d"
          % oku32(sym["dongu_sayaci"]))
    bsrr_list = [y for y in yaz if y[1] == BSRR]
    print("  GPIOD ODR (0x40020C14)  : 0x%08X" % oku32(0x40020C14))
    print("  BSRR yazma sayisi       : %d" % len(bsrr_list))
    print("\nBSRR yazmalari (komut sayisi, deger):")
    for n, adr, deger in bsrr_list:
        print("  komut=%-8d 0x%08X  <- 0x%08X" % (n, adr, deger))
    with open(os.path.join(cikti, "led_trafik.csv"), "w") as f:
        f.write("komut,deger\n")
        for n, adr, deger in bsrr_list:
            f.write("%d,0x%08X\n" % (n, deger))


if __name__ == "__main__":
    main()
```

Harness önce `.bin` görüntüsünü ve vektör tablosunu okur, SP ve PC'yi tablodan yükler (43.6'daki kural), ardından reset'ten `main`'e kadar çalıştırır ve bu sırada her komutun adresini ve R1-R3 yazmaçlarını kaydeder. İkinci fazda `main`'i 2,5 milyon komut boyunca çalıştırır ve GPIOD `BSRR` yazmacına yapılan her yazmayı toplar. Çalıştırmanın çıktısı:

```term
$ python -I harness.py blink.elf blink.bin cikti
Vektor[0] (SP)    = 0x20020000
Vektor[1] (reset) = 0x08000045  (Thumb biti=1)

[1] Startup: main'e varis, komut = 36
  .data kaynagi (flash)  : 0xCAFE0001
  acilis_degeri (RAM)    : 0xCAFE0001
  .bss ilk kelime        : 0x00000000
  .bss ikinci kelime     : 0x00000000
  CPACR (0xE000ED88)     : 0x00F00000

[2] main calisti, komut = 2500000
  RCC AHB1ENR (0x40023830): 0x00000008
  GPIOD MODER (0x40020C00): 0x01000000
  sonuc_menzil (RAM)      : 82
  dongu_sayaci (RAM)      : 3
  GPIOD ODR (0x40020C14)  : 0x00000000
  BSRR yazma sayisi       : 5

BSRR yazmalari (komut sayisi, deger):
  komut=30       0x40020C18  <- 0x00001000
  komut=600034   0x40020C18  <- 0x10000000
  komut=1200042  0x40020C18  <- 0x00001000
  komut=1800046  0x40020C18  <- 0x10000000
  komut=2400054  0x40020C18  <- 0x00001000
```

Çıktıyı okuyalım. Vektör değerleri Şekil 43.5'tekilerle aynı. Startup **36 komutta** `main`'e ulaşıyor. `.data` kaynağı (`0xCAFE0001`) RAM'e kopyalanmış, `.bss` ilk iki kelimesi sıfır, CPACR'nin `0x00F00000` olması FPU'nun açıldığını gösteriyor. `RCC AHB1ENR = 0x8` bit 3'ün (GPIODEN) açıldığını, `GPIOD MODER`'in `0x01000000` olması ise pin 12'nin `01` (çıkış) moduna geçtiğini gösteriyor. `sonuc_menzil = 82` değeri `kademe[1] = 50` için `50 * 165 / 100 = 82` sonucuyla tutarlı. `dongu_sayaci = 3` ise iki tam çevrim sonunda artışın gerçekten gerçekleştiğini gösterir.

BSRR yazmalarına bakalım. Beş yazma var: ilki komut 30'da `0x00001000` (pin 12 set), ikincisi komut 600034'te `0x10000000` (pin 12 reset), üçüncüsü 1200042'de yine set; yani her yarım periyot yaklaşık 600 000 komut sürüyor. Bunun nedeni `gecikme` fonksiyonunun her turunda altı komut çalıştırmasıdır (`ldr`, `subs`, `str`, `ldr`, `cmp`, `bne`); 100 000 turun 6 komutla çarpımı 600 000'dir. Bu bir **busy-wait** gecikmedir ve iki sorunu var: gerçek süresi saat frekansına ve derleyicinin ürettiği komut sayısına bağlıdır (kartta ölçülmedi), ve bu süre boyunca işlemci başka hiçbir iş yapamaz. Bölüm 44'te bu gecikmenin yerine SysTick zamanlayıcısını koyacağız.

Çıktının bir noktası emülatörün sınırını gösterir: `GPIOD ODR` yazmacı 0 kalmış görünüyor. Donanımda BSRR'ye yazmak ODR'yi değiştirir; Unicorn ise BSRR yazmasını yalnızca bellek olarak kaydeder ve ODR'ye yansıtmaz. Bu bir **model farkıdır**. Bu yüzden pinin durumunu emülatörde ODR'den değil, yalnızca yazılan BSRR değerlerinden izleyebiliriz; harness bu yüzden BSRR yazmalarını ayrıca döküyor.

### HAL, LL ve çıplak yazmaç: aynı yazmaç, üç yol

EV Dashboard `main.c` dosyasında GPIO'yu okumak için `HAL_GPIO_ReadPin` kullanılıyor (`Girisler_Guncelle`, 98-110. satırlar). HAL (Hardware Abstraction Layer) bu çağrıyı üç katmanda gerçekleştirir: uygulama kodu, HAL fonksiyonu ve yazmaç. Şekil 43.9 bu katmanları iki örnek üzerinde gösteriyor: solda GPIO okuma, sağda UART gönderme.

![Şekil 43.9: HAL çağrısının yazmaç düzeyine inmesi. Solda GPIO okuması IDR yazmacına, sağda UART gönderimi SR ve DR yazmaçlarına iner.](gorseller/b43_katmanlar.png)

`HAL_GPIO_ReadPin`'in gövdesi kısa; onu tam olarak gösterebiliriz (HAL v1.8.0, `stm32f4xx_hal_gpio.c`, 375-391. satırlar). Fonksiyonun asıl işi tek bir karşılaştırmadır: `GPIOx->IDR & GPIO_Pin`.

```c
GPIO_PinState HAL_GPIO_ReadPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin)
{
  GPIO_PinState bitstatus;

  /* Check the parameters */
  assert_param(IS_GPIO_PIN(GPIO_Pin));

  if((GPIOx->IDR & GPIO_Pin) != (uint32_t)GPIO_PIN_RESET)
  {
    bitstatus = GPIO_PIN_SET;
  }
  else
  {
    bitstatus = GPIO_PIN_RESET;
  }
  return bitstatus;
}
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
/* aygit.h - bir aygit baslik dosyasinin (stm32f4xx.h) iskeleti.
 * Gercek dosya ayni sirayla: once CMSIS'in ihtiyaci olan makrolar ve
 * IRQn_Type tanimlanir, sonra core_cm4.h include edilir. */
#ifndef AYGIT_H
#define AYGIT_H
#define __CM4_REV              0x0001U
#define __MPU_PRESENT          1U
#define __NVIC_PRIO_BITS       4U
#define __Vendor_SysTickConfig 0U
#define __FPU_PRESENT          1U

typedef enum IRQn {
    NonMaskableInt_IRQn = -14,
    HardFault_IRQn      = -13,
    SysTick_IRQn        = -1,
    WWDG_IRQn           = 0
} IRQn_Type;

#include "core_cm4.h"
#endif
```

Bu iskeletin kendisi bir aygıt başlığı değildir; yalnızca CMSIS'in ihtiyaç duyduğu tanımların sırasını gösterir. Ardından gerçek `core_cm4.h` (CMSIS_5 sürüm 5.9.0 etiketinden, başlık sürümü V5.1.2) ile SCB yapısının ofsetlerini derleme aşamasında denetleyen bir test yazalım:

```c
/* ofs_testi.c - gercek CMSIS core_cm4.h ile ofset denetimi.
 * Derleme basarili ise tum _Static_assert'ler gecmistir. */
#include <stddef.h>
#include "aygit.h"

_Static_assert(offsetof(SCB_Type, CPUID) == 0x000, "CPUID");
_Static_assert(offsetof(SCB_Type, ICSR) == 0x004, "ICSR");
_Static_assert(offsetof(SCB_Type, VTOR) == 0x008, "VTOR");
_Static_assert(offsetof(SCB_Type, SHP) == 0x018, "SHP");
_Static_assert(offsetof(SCB_Type, CFSR) == 0x028, "CFSR");
_Static_assert(offsetof(SCB_Type, HFSR) == 0x02C, "HFSR");
_Static_assert(offsetof(SCB_Type, CPACR) == 0x088, "CPACR");

int main(void)
{
    return 0;
}
```

`_Static_assert` satırları, SCB yapısının her önemli alanının ofsetini belgelenmiş değerlerle karşılaştırır. Bir alan yanlış yerdeyse derleme başarısız olur. Derleme sonucu:

```term
$ arm-none-eabi-gcc $CF -std=c11 -Wall -I. -c ofs_testi.c -o ofs_testi.o
$ arm-none-eabi-size ofs_testi.o
ofs_testi derlendi, rc=0
   text	   data	    bss	    dec	    hex	filename
     16	      0	      0	     16	     10	ofs_testi.o
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


## 43.9 Gömülü C disiplini

Gömülü C, masaüstü C ile aynı dildir; ama çalıştığı ortam farklı olduğu için bazı alışkanlıklar yasak, bazıları zorunlu hâle gelir. Bu bölümün geri kalanında gördüğümüz her ölçüm bu disiplinin bir parçasıdır. Şimdi en önemli beş kuralı ve her birinin kaynağını sıralayalım.

**Dinamik bellek kullanma.** Bölüm 2.8'de `malloc` sözleşmesini ve Bölüm 25'te ayırıcıların iç işleyişini gördün. Gömülüde `malloc` üç nedenle tehlikelidir. Birincisi, bir ayırıcı parçalanma (fragmentation) yaşar: uzun süre çalışan bir cihazda bellek var ama yeterince büyük bir parça yoktur. İkincisi, süresi belirsizdir: bir `malloc` çağrısının kaç komut süreceği, serbest listenin durumuna bağlıdır. Üçüncüsü, başarısız olabilir ve masaüstünde olduğu gibi işletim sistemi sana bellek ekleyemez; `malloc` bir `NULL` döndürür ya da daha kötüsü, kontrol etmediğin bir yerde çöker. Bu yüzden gömülü projelerde tamponlar derleme anında sabit boyutludur, ya da en fazla bir havuz (pool) ayırıcı (Bölüm 25.14) kullanılır. Kesme işleyicisi içinde `malloc` çağırmak ise ayrıca yasaktır: kesme beklenmedik bir anda gelir ve ayırıcının yarım kalmış durumunu bozabilir (Bölüm 44'te kesmeler ayrıntılanacak).

**Yığını ölç.** Yerel değişken yığında yaşar ve derleyici her fonksiyonun çerçeve boyutunu bilir. `-fstack-usage` bu bilgiyi `.su` dosyasına yazar. Aşağıdaki program, Örnek 3'teki çağrı zincirinin kaynağıdır:

```c
/* yigin.c - -fstack-usage ciktisini gormek icin */
#include <stdint.h>

volatile uint32_t cikti;

/* 64 baytlik yerel tampon: yiginda ayrilir */
uint32_t ic_fonk(uint32_t x)
{
    volatile uint8_t tampon[64];
    for (uint32_t i = 0; i < 64u; i++) {
        tampon[i] = (uint8_t)(x + i);
    }
    return tampon[x & 63u];
}

uint32_t orta(uint32_t x)
{
    return ic_fonk(x) + ic_fonk(x + 1u);
}

uint32_t dis(uint32_t x)
{
    return orta(x) ^ 0xA5u;
}

int main(void)
{
    cikti = dis(7u);
    return 0;
}
```

`ic_fonk` içindeki `volatile uint8_t tampon[64]` dizisi 64 bayt yığında yer ayırır; bu yüzden `.su` dosyasında `ic_fonk` için 64 görürsün. `orta` ve `dis` fonksiyonları ise çağrı için gereken kaydetme alanlarını ekler. Dikkat etmen gereken sütun son sütundur: `static` demek, çerçeve boyutunun derleme zamanında sabit olduğunu ve yığında dinamik (değişken uzunluklu) bir alan ayrılmadığını gösterir. Değişken uzunluklu diziler (VLA) ve `alloca` gibi yapılar bu garantiyi bozar; gömülü standartların çoğu bunları yasaklar.

Özyineleme (recursion), Bölüm 15'te gördüğümüz gibi derinliğe bağlı bir yığın tüketimi üretir. Gömülüde bu derinlik önceden bilinmediğinde özyineleme yasaktır; bir özyinelemeli ayrıştırıcıyı yinelemeli (iteratif) bir yapıya çevirmek ya da en fazla derinliği açıkça sınırlamak gerekir.

**Sabit genişlikli türleri kullan.** `<stdint.h>` içindeki `uint8_t`, `int32_t` gibi türler bir donanım yazmacının ya da bir paketin genişliğini açıkça belirtir. `int` ve `long` ise platforma göre değişir: Bölüm 2'de gördüğümüz gibi Windows 64 bit'te `long` 4 bayttır; arm-none-eabi'de de `long` 32 bittir (genel bilgi). Gömülüde `long`un ne kadar büyük olduğuna güvenmek yerine `uint32_t` yazarsın. Ayrıca Bölüm 43.5'teki tamsayı yükseltme tuzağını hatırla: `uint8_t` işlemleri `int`'e yükselir. İşaretli tamsayı taşması (`int` için `INT_MAX + 1`) tanımsız davranıştır (UB); bu yüzden sayaçları işaretsiz tamsayıyla tutmak hem güvenli hem öngörülebilirdir.

**`const` ile flash'a yerleştir.** Bir dizi `const` olarak tanımlandığında derleyici onu `.rodata` bölümüne koyar ve bağlayıcı bunu flash'ta tutar; RAM'de yer kaplamaz. Bu bölümdeki `kademe` dizisinin `nm` çıktısında `08000160 R` olarak görünmesi bunun kanıtıdır (Bölüm 43.7). `const` unutulan bir tablo RAM'e kopyalanır ve bu, küçük bir çipte fark yaratabilir.

**MISRA ruhunu benimse.** Bölüm 23'te temiz kod ilkelerini gördün. Güvenlik-kritik gömülü yazılım için MISRA C kuralları bu ilkeleri daha katı bir kümeye dönüştürür: dinamik bellek yok, özyineleme yok, açık tür dönüşümleri, işaretli ve işaretsiz karışımı yok, her uyarı ele alınır. Bu kuralların hepsi bu bölümde gördüğümüz tehlikelerle ilgilidir; MISRA'yı ezberlemek yerine her kuralın hangi hatayı önlediğini düşünmek daha öğreticidir. Derleyicide `-Wall -Wextra` açık olmalı ve uyarılar hata gibi ele alınmalıdır.

**Hata durumunda güvenli çıkış.** Gömülü bir programın hataya düştüğünde ne yapacağı bir tasarım kararıdır. `assert` masaüstünde bir programı durdurur; gömülüde ise `printf` ile mesaj yazacak bir konsol yoktur ve program durursa motor sürücüsü son komutu sürdürebilir. Bu yüzden hata işleyicisi genellikle önce çıkışları güvenli bir duruma çeker (motoru kapat, fren uygula), sonra bir hata kodunu bir yazmaca ya da RAM'deki bir değişkene yazar ve watchdog'un sistemi yeniden başlatmasını bekler (watchdog Bölüm 44'te). HAL'deki `assert_param` gibi denetimler çoğunlukla yalnızca geliştirme sırasında etkindir (genel bilgi; bkz. Bölüm 43.8).

## 43.10 Derleme seçenekleri, boyut ölçümü ve printf

Bir gömülü projede boyut bir özellik değil, bir kısıttır: flash dolarsa program sığmaz, RAM dolarsa program başlamaz. Bu yüzden derleme seçeneklerinin boyuta etkisini ölçmeden tahmin etmek yanlış olur. Bu alt bölümde üç soruyu ölçerek cevaplayacağız: `-O0`, `-O2` ve `-Os` arasında ne fark vardır; ölü kodu (kullanılmayan fonksiyon ve tabloları) bağlayıcı atabilir mi; ve `printf` ne kadar yer kaplar.

Ölçüm için `app.c` adlı küçük bir uygulama yazdık. İçinde kullanılan bir fonksiyon (`menzil_hesapla`) ve kullanılmayan iki parça (`crc_yardimci` ve `tablo`) var.

```c
/* app.c - boyut olcumu icin ornek uygulama */
#include <stdint.h>

const uint8_t kademe[4] = { 25u, 50u, 75u, 100u };
volatile uint32_t sonuc;

uint32_t menzil_hesapla(uint8_t batarya)
{
    return ((uint32_t)batarya * 165u) / 100u;
}

/* Kullanilmayan yardimci: --gc-sections bunu atabilir */
uint32_t crc_yardimci(const uint8_t *v, uint32_t n)
{
    uint32_t c = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < n; i++) {
        c ^= v[i];
        for (int k = 0; k < 8; k++) {
            c = (c & 1u) ? (c >> 1) ^ 0xEDB88320u : (c >> 1);
        }
    }
    return ~c;
}

```

```c
/* Kullanilmayan tablo: o da atilabilir */
const uint32_t tablo[8] = {
    0x11111111u, 0x22222222u, 0x33333333u, 0x44444444u,
    0x55555555u, 0x66666666u, 0x77777777u, 0x88888888u,
};

uint32_t tablo_topla(void)
{
    uint32_t t = 0;
    for (uint32_t i = 0; i < 8; i++) {
        t += tablo[i];
    }
    return t;
}

int main(void)
{
    sonuc = menzil_hesapla(kademe[1]);
    return (int)sonuc;
}
```

Derleme için ortak değişkenleri tanımlayıp her yapılandırmayı ayrı ayrı bağladık:

```term
$ RS="-nostdlib -nostartfiles -T link.ld"
$ arm-none-eabi-gcc $CF -O2 $RS startup.o app.c -o app_O2.elf
$ arm-none-eabi-size app_O2.elf
```

Tüm yapılandırmaların `size` çıktıları aşağıda toplanmıştır. Her satırda önce yapılandırma adı, sonra `size`'ın `text`, `data`, `bss`, toplam, hex ve dosya sütunları yer alır:

```term
$ arm-none-eabi-size <her ikili için>
app -O0     464	      0	      4	    468	    1d4	app_O0.elf
app -O2     320	      0	      4	    324	    144	app_O2.elf
app -Os     300	      0	      4	    304	    130	app_Os.elf
app -Os gc     192	      0	      4	    196	     c4	app_gc.elf
printf_yok nano -Os     192	      0	      4	    196	     c4	pyok.elf
printf nano -Os    5688	     92	    344	   6124	   17ec	pnano.elf
printf nano -Os gc    4152	     92	    340	   4584	   11e8	pnano_gc.elf
```

Bu tabloyu okurken dikkat edilecek sütunlar `text`, `data` ve `bss`dir. Flash için `text + data`, RAM için `data + bss` hesabını hatırla. Sonuçlar şöyle okunur. `-O0` (optimizasyon yok) 464 bayt kod üretiyor; `-O2` 320 bayt; `-Os` (boyut odaklı) ise 300 bayt, yani bu küçük örnekte `-Os` en küçük sonucu veriyor. `-O2` hızı artırmaya öncelik verir, `-Os` boyutu. Hangisinin doğru olduğu, hedef kısıtına bağlıdır: flash doluyorsa `-Os`, zaman kritikse `-O2`.

Şekil 43.10 aynı ölçümleri bir grafikte gösteriyor; printf'li sürümlerin büyüklüğü ölçeği nasıl değiştirdiğine dikkat et.

![Şekil 43.10: Derleme seçeneklerinin ve printf'in flash ve RAM maliyeti. Yalnızca printf eklemek, bu küçük programın flash kullanımını yaklaşık 5 KB artırır.](gorseller/b43_boyut.png)

**Ölü kodu atmak.** Bir fonksiyon her çeviri biriminde ayrı bir bölüm olarak derlenirse (`-ffunction-sections -fdata-sections`), bağlayıcı kullanılmayan bölümleri `--gc-sections` ile atabilir. Bu seçeneklerle derlediğimizde bağlayıcı beş ölü bölümü tanımladı:

```term
$ arm-none-eabi-gcc $CF -Os -ffunction-sections -fdata-sections \
    -nostdlib -nostartfiles -T link.ld -Wl,--gc-sections \
    -Wl,--print-gc-sections startup.o app.o -o app_gc2.elf
removing unused section '.text.menzil_hesapla' in file 'app.o'
removing unused section '.text.crc_yardimci' in file 'app.o'
removing unused section '.text.tablo_topla' in file 'app.o'
removing unused section '.rodata.tablo' in file 'app.o'
removing unused section '.rodata.kademe' in file 'app.o'
    192	      0	      4	    196	     c4	app_gc2.elf
```

Son satır, atılmadan sonra kalan boyutu gösteriyor: 192 bayt flash. Atılan beş bölümün dördü fonksiyon ya da veri olarak açıkça kullanılmıyor: `crc_yardimci` ve `tablo_topla` hiç çağrılmıyor, `tablo` hiçbir yerden okunmuyor. Beşincisi ise ilginç: `menzil_hesapla` ve `kademe` atıldı, çünkü `main` onları `menzil_hesapla(kademe[1])` olarak çağırıyor ve derleyici bu çağrıyı sabit katlayarak `sonuc = 82` yazmış. Yani optimizasyon, çağrının sonucunu zaten bildiği için fonksiyona ihtiyaç bırakmamış. Bağlayıcının bunları atabilmesi için derleyicinin her fonksiyonu kendi bölümüne koyması gerekir; bu, `-ffunction-sections -fdata-sections` bayraklarının işidir.

**printf'in bedeli.** `printf` gömülüde en çok yer kaplayan kütüphane çağrılarından biridir, çünkü biçimlendirme kodunu, tamsayı ve kayan nokta dönüşümünü ve tampon yönetimini içerir. newlib-nano (`--specs=nano.specs`) bunu küçültür, ama sıfıra indirmez. Aşağıdaki iki program aynı işi yapar; biri `printf` çağırır, biri çağırmaz.

```c
/* printf_deney.c - printf'in boyut maliyetini olcmek icin */
#include <stdio.h>
#include <stdint.h>

volatile uint32_t sonuc;

int main(void)
{
    printf("menzil=%u km\n", (unsigned)sonuc);
    return 0;
}
```

```c
/* printf_yok.c - ayni program, printf olmadan (karsilastirma) */
#include <stdint.h>

volatile uint32_t sonuc;

int main(void)
{
    sonuc = sonuc + 1u;
    return 0;
}
```

Bu iki programı `--specs=nano.specs --specs=nosys.specs` ile derledik. `nosys` sistem çağrılarının (`_write` gibi) boş sürümlerini sağlar; bağlayıcı bunlar için "not implemented" uyarısı verir. Bu uyarılar boyutu etkilemez, ama bir üretim derlemesinde temiz uyarı istersen kendi `_write` fonksiyonunu yazarsın. Ölçüm sonuçlarını yukarıdaki `boyut.txt` tablosunda gördün: `printf` yokken 192 bayt flash, varken 5688 bayt metin (kod) ve 92 bayt veri. Yani bu tek `printf` çağrısı yaklaşık 5,5 KB'lık kod getirdi. Ölü bölüm atma ile bu 4152 bayta iniyor, ama hâlâ 4 KB civarında. Gömülüde `printf` yerine çoğu zaman yalnızca bir karakter yazan (`put_char`) ve sayıyı elle yazan küçük bir fonksiyon yeterlidir.

Bu ölçümlerde dikkat edilecek bir şey de şu: sonuçlar kullandığımız derleyici sürümüne ve bayraklara bağlıdır. Her yeni derleyici sürümünde bu rakamları yeniden ölçmelisin. Bu bölümdeki tüm rakamlar, yukarıda gösterilen komutlarla GNU Arm toolchain 13.3.rel1 üzerinde üretildi.

## 43.11 Hata ayıklama, önyükleyici ve güvenlik standartları

Gömülü hata ayıklama masaüstünden farklıdır: `printf` yoktur, ekran yoktur, belki bir LED'in yanıp sönmesi dışında geri bildirim yoktur. Bu yüzden hata ayıklama üç araca dayanır: bir donanım hata ayıklayıcısı, çekirdeğin durum yazmaçları ve dikkatli bir günlükleme (ya da bir çıktı pini).

**SWD ve JTAG.** Cortex-M çekirdeklerinin hata ayıklama arayüzü SWD (Serial Wire Debug) ya da JTAG'dir (genel bilgi). Bir programlayıcı (ör. ST-LINK) bu arayüzle çekirdeği durdurabilir, belleği okuyup yazabilir, yazmaçları görebilir ve kesme noktası (breakpoint) koyabilir. Bu hata ayıklayıcı yazılımı genellikle GDB'dir; GDB'yi bir OpenOCD ya da ST-LINK sunucusuyla bağlarsın (genel bilgi). Bu bölümde bu araçları kullanmadık; yalnızca emulatörle çalıştırdık. Yani "kartta hata ayıklama" iddiası yoktur.

**HardFault ve hata yazmaçları.** Bir Cortex-M çekirdeği yasa dışı bir erişim, tanımsız bir komut ya da bir FPU hatası yaptığında bir istisna (exception) üretir. Hepsini kapsayan istisna HardFault'tur. Hata nedenini anlamak için çekirdek, hata durum yazmaçlarını doldurur. Bu bölümde doğruladığımız SCB ofsetlerine göre bunlar `CFSR` (`0xE000ED28`) ve `HFSR` (`0xE000ED2C`) yazmaçlarıdır; CFSR kendi içinde üç hata alt grubunu (MemManage, BusFault ve UsageFault) tutar. Bu bölümdeki startup kodunda HardFault vektörü `Varsayilan_Isleyici`dir ve yalnızca sonsuz döngüye girer. Bu, geliştirme sırasında bir HardFault'un nerede takılı kaldığını gösterir, ama nedenini söylemez. Gerçek bir sistemde `HardFault_Handler` bu yazmaçları okuyup kaydetmelidir.

Bu bölümün başında FPU'yu açmadan kayan nokta komutu çalıştırmanın bir UsageFault ürettiğini söyledik. Genel bilgiye göre bu hata CFSR'nin UsageFault bölümündeki NOCP (no coprocessor) bitiyle işaretlenir. Bu bilgiyi doğrulamak için bizim emulatörümüzde bir FPU hatası üretmek kolay değildir, bu yüzden bunu kendi çıktı belgenden doğrulamanı öneririz. Bölüm 44'te istisnaların önceliklerini ve kesme işleyicilerinin yapısını ayrıntılı göreceğiz.

**Önyükleyici (bootloader) kavramı.** Ürün üzerinde çalışan bir cihazın yazılımını güncellemek için flash'a yeni bir program yazılır. Bunu yapan küçük bir program, önyükleyicidir: çip açıldığında önce o çalışır, güncelleme varsa flash'ı yeniden yazar, yoksa uygulamaya geçer. Uygulamanın kendi vektör tablosu flash'ın başında değil, bir ofset adresinde olabilir; bu durumda işlemci kendi vektör tablosunu **VTOR** (Vector Table Offset Register) yazmacıyla gösterir. CMSIS başlığında VTOR'un SCB içindeki ofseti `0x008`dir, yani mutlak adresi `0xE000ED08`dir (doğrulandı). Önyükleyici bu yazmacı uygulamanın tablo adresine ayarlayıp ona atlar. Bu bölümde bir önyükleyici yazmadık ve kartta denemedik; kavramı tanıman yeter.

**Güvenlik standartları.** Savunma, havacılık ve otomotiv yazılımında kod bir sertifikasyon sürecinden geçer. Bu süreçlerin ana çerçeveleri (genel bilgi): havacılık yazılımı için DO-178C, otomotiv fonksiyonel güvenliği için ISO 26262 ve genel endüstriyel güvenlik için IEC 61508. Bu standartlar, gereksinimden koda ve testlere kadar **izlenebilirlik**, yapısal kapsam (ör. MC/DC, Bölüm 39) ve tespit edilmiş her hatanın belgelenmesini ister. Bu bölümde anlatılan araçlar (`map` dosyası, `size`, `objdump`, `-fstack-usage`, bütçe denetimi) bu sürecin kanıt üreten parçalarıdır: her biri, derlenmiş kodun bellek ve yığın davranışı hakkında yazılı bir kayıt verir. Sertifikasyon kendi başına bu araçlarla kazanılmaz; ama bu araçların çıktısı olmadan bir kanıt zinciri de kurulamaz.

**Bu bölümün bağlantısı.** EV Dashboard'daki her kararı (GPIO okuması, UART gönderimi, 200 ms döngü) burada gördüğün katmanlardan geçerek makine koduna iner. Bir sonraki bölümde bu döngünün bir zamanlayıcı kesmesiyle nasıl yönetileceğini göreceğiz; ama önce bu bölümün dört sonucunu aklında tut: yazmaçlar `volatile`dır, vektör tablosu reset'in ilk adımıdır, bağlayıcı bütçeyi denetler ve derleme seçenekleri boyutu belirler.


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
/* ornek_dogrula.c - bolum orneklerindeki sayilari dogrular */
#include <stdint.h>
#include <stdio.h>

static void yaz_modeller(uint32_t m)
{
    for (int p = 15; p >= 12; p--) {
        printf("pin%d=%u%u ", p, (m >> (2 * p + 1)) & 1u,
               (m >> (2 * p)) & 1u);
    }
    printf("| 0x%08X\n", m);
}

static uint32_t bitband(uint32_t taban, uint32_t bolge, unsigned b)
{
    return taban + (bolge - 0x40000000u) * 32u + b * 4u;
}

int main(void)
{
    /* Ornek 1: MODER pin 12'yi 10 -> 01 yap, digerlerine dokunma */
    uint32_t m = 0x26000000u;
    printf("ilk:  "); yaz_modeller(m);
    m &= ~(3u << 24);
    printf("temizle:  "); yaz_modeller(m);
    m |= (1u << 24);
    printf("set:  "); yaz_modeller(m);

    /* Ornek 2: bit-band takma adresleri */
    printf("SRAM 0x20000004 bit3 -> 0x%08X\n",
           0x22000000u + (0x20000004u - 0x20000000u) * 32u + 3u * 4u);
    printf("ODR bit 31 -> 0x%08X\n",
           bitband(0x42000000u, 0x40020C14u, 31u));
    printf("ODR bit 0  -> 0x%08X\n",
           bitband(0x42000000u, 0x40020C14u, 0u));
    return 0;
}
```

```term
$ gcc -O2 -Wall -Wextra -std=c11 ornek_dogrula.c -o ornek_dogrula
$ ./ornek_dogrula
ilk:  pin15=00 pin14=10 pin13=01 pin12=10 | 0x26000000
temizle:  pin15=00 pin14=10 pin13=01 pin12=00 | 0x24000000
set:  pin15=00 pin14=10 pin13=01 pin12=01 | 0x25000000
SRAM 0x20000004 bit3 -> 0x2200008C
ODR bit 31 -> 0x424182FC
ODR bit 0  -> 0x42418280
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
yigin.c:7:10:ic_fonk	64	static
yigin.c:16:10:orta	16	static
yigin.c:21:10:dis	8	static
yigin.c:26:5:main	8	static
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

| Adım | Adres | Komut | r1 | r2 | r3 |
|---|---|---|---|---|---|
| 1 | 0x08000044 | `ldr r2, [pc, #84]` | 0x00000000 | 0x00000000 | 0x00000000 |
| 2 | 0x08000046 | `ldr r1, [pc, #88]` | 0x00000000 | 0x20000000 | 0x00000000 |
| 3 | 0x08000048 | `cmp r2, r1` | 0x20000004 | 0x20000000 | 0x00000000 |
| 4 | 0x0800004A | `push {r3, lr}` | 0x20000004 | 0x20000000 | 0x00000000 |
| 5 | 0x0800004C | `bcs.n 8000068` | 0x20000004 | 0x20000000 | 0x00000000 |
| 6 | 0x0800004E | `subs r1, #1` | 0x20000004 | 0x20000000 | 0x00000000 |
| 7 | 0x08000050 | `subs r1, r1, r2` | 0x20000003 | 0x20000000 | 0x00000000 |
| 8 | 0x08000052 | `ldr r3, [pc, #80]` | 0x00000003 | 0x20000000 | 0x00000000 |
| 9 | 0x08000054 | `bic.w r1, r1, #3` | 0x00000003 | 0x20000000 | 0x08000164 |
| 10 | 0x08000058 | `adds r1, #4` | 0x00000000 | 0x20000000 | 0x08000164 |
| 11 | 0x0800005A | `add r1, r3` | 0x00000004 | 0x20000000 | 0x08000164 |
| 12 | 0x0800005C | `ldr.w r0, [r3], #4` | 0x08000168 | 0x20000000 | 0x08000164 |
| 13 | 0x08000060 | `str.w r0, [r2], #4` | 0x08000168 | 0x20000000 | 0x08000168 |
| 14 | 0x08000064 | `cmp r3, r1` | 0x08000168 | 0x20000004 | 0x08000168 |
| 15 | 0x08000066 | `bne.n 800005c` | 0x08000168 | 0x20000004 | 0x08000168 |
| 16 | 0x08000068 | `ldr r3, [pc, #60]` | 0x08000168 | 0x20000004 | 0x08000168 |
| 17 | 0x0800006A | `ldr r2, [pc, #64]` | 0x08000168 | 0x20000004 | 0x20000004 |
| 18 | 0x0800006C | `cmp r3, r2` | 0x08000168 | 0x2000000C | 0x20000004 |
| 19 | 0x0800006E | `bcs.n 8000086` | 0x08000168 | 0x2000000C | 0x20000004 |
| 20 | 0x08000070 | `subs r2, #1` | 0x08000168 | 0x2000000C | 0x20000004 |
| 21 | 0x08000072 | `subs r2, r2, r3` | 0x08000168 | 0x2000000B | 0x20000004 |
| 22 | 0x08000074 | `bic.w r2, r2, #3` | 0x08000168 | 0x00000007 | 0x20000004 |
| 23 | 0x08000078 | `adds r2, #4` | 0x08000168 | 0x00000004 | 0x20000004 |
| 24 | 0x0800007A | `add r2, r3` | 0x08000168 | 0x00000008 | 0x20000004 |
| 25 | 0x0800007C | `movs r1, #0` | 0x08000168 | 0x2000000C | 0x20000004 |
| 26 | 0x0800007E | `str.w r1, [r3], #4` | 0x00000000 | 0x2000000C | 0x20000004 |
| 27 | 0x08000082 | `cmp r3, r2` | 0x00000000 | 0x2000000C | 0x20000008 |
| 28 | 0x08000084 | `bne.n 800007e` | 0x00000000 | 0x2000000C | 0x20000008 |
| 29 | 0x0800007E | `str.w r1, [r3], #4` | 0x00000000 | 0x2000000C | 0x20000008 |
| 30 | 0x08000082 | `cmp r3, r2` | 0x00000000 | 0x2000000C | 0x2000000C |
| 31 | 0x08000084 | `bne.n 800007e` | 0x00000000 | 0x2000000C | 0x2000000C |
| 32 | 0x08000086 | `mov.w r2, #3758153728` | 0x00000000 | 0x2000000C | 0x2000000C |
| 33 | 0x0800008A | `ldr.w r3, [r2, #3464]` | 0x00000000 | 0xE000E000 | 0x2000000C |
| 34 | 0x0800008E | `orr.w r3, r3, #15728640` | 0x00000000 | 0xE000E000 | 0x00000000 |
| 35 | 0x08000092 | `str.w r3, [r2, #3464]` | 0x00000000 | 0xE000E000 | 0x00F00000 |
| 36 | 0x08000096 | `bl 80000c8` | 0x00000000 | 0xE000E000 | 0x00F00000 |

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
/* SCB_Type: yorum satirlari cikarildi; alan adlari, tipler ve
   dizi boyutlari kaynakla aynidir (core_cm4.h, 445-468). */
typedef struct
{
 __IM uint32_t CPUID;
 __IOM uint32_t ICSR;
 __IOM uint32_t VTOR;
 __IOM uint32_t AIRCR;
 __IOM uint32_t SCR;
 __IOM uint32_t CCR;
 __IOM uint8_t SHP[12U];
 __IOM uint32_t SHCSR;
 __IOM uint32_t CFSR;
 __IOM uint32_t HFSR;
 __IOM uint32_t DFSR;
 __IOM uint32_t MMFAR;
 __IOM uint32_t BFAR;
 __IOM uint32_t AFSR;
 __IM uint32_t PFR[2U];
 __IM uint32_t DFR;
 __IM uint32_t ADR;
 __IM uint32_t MMFR[4U];
 __IM uint32_t ISAR[5U];
 uint32_t RESERVED0[5U];
 __IOM uint32_t CPACR;
} SCB_Type;
```

İkinci kesit, NVIC öncelik ayarlama fonksiyonu. Bu fonksiyonun kendisi Bölüm 44'ün konusudur, ama kodu şimdiden okuyabilirsin:

```c
/* __NVIC_SetPriority: core_cm4.h 1814-1824.
   Satir sonlari kitap sayfasina sigsin diye degistirildi;
   token dizisi kaynakla aynidir. */
__STATIC_INLINE void __NVIC_SetPriority(IRQn_Type IRQn,
                                        uint32_t priority)
{
  if ((int32_t)(IRQn) >= 0)
  {
    NVIC->IP[((uint32_t)IRQn)] =
        (uint8_t)((priority << (8U - __NVIC_PRIO_BITS))
                  & (uint32_t)0xFFUL);
  }
  else
  {
    SCB->SHP[(((uint32_t)IRQn) & 0xFUL)-4UL] =
        (uint8_t)((priority << (8U - __NVIC_PRIO_BITS))
                  & (uint32_t)0xFFUL);
  }
}
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
