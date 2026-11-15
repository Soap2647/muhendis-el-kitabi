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
{{CIKTI:cikti/menzil_dis.txt}}
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
{{KOD:host/volatile_deney.c|1-41}}
```

Programın ilk beş fonksiyonu `volatile`'ın etkisini gösterir. İkinci kısım ise dikkat çekici bir gözlemi içerir.

```c
{{KOD:host/volatile_deney.c|42-71}}
```

Şimdi derlenmiş çıktıyı okuyalım. Aşağıdaki kesit yalnızca dört fonksiyonu içeriyor; tam listeyi `volatile_deney.o` ile kendin üretebilirsin:

```term
$ arm-none-eabi-objdump -d volatile_deney.o
{{CIKTI:cikti/volatile_secim.txt}}
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
