%% kisim_no: XI
%% kisim_ad: Gömülü Sistem
%% bolum_no: 44
%% baslik: Kesme & Zamanlayıcı

## Giriş: Donanım bir olayı ne zaman fark eder?

Bölüm 24'te işlemcinin bir komutu nasıl getirip yürüttüğünü gördük. Bölüm 26'da ise işletim sisteminin birden çok süreci nasıl sıraya koyduğunu ve bir zamanlayıcının çalışan süreci nasıl kesip başkasına verdiğini öğrendik. Bu bölümde soru tersine dönüyor: **dünyadan gelen bir olay işlemciye nasıl haber verilir?** Bir düğmeye basıldığında, bir UART baytı geldiğinde, bir ADC örneği hazır olduğunda ya da bir zamanlayıcı sayımı tamamladığında, işlemcinin bunu bir yerden öğrenmesi gerekir. Bu öğrenme yolunun iki temel biçimi vardır: işlemci sürekli bakar (yoklama, polling) ya da donanım işlemciyi bir kesmeyle dürter (interrupt).

Bu ayrım gömülü sistemlerde yalnızca bir performans konusu değildir. Savunma sanayiinde bir uçuş kontrol döngüsü, bir sensörün her yeni örneğini belirli bir süre içinde işlemek zorundadır. Bir görev, zamanında çalışmazsa sonuç bir yazılım hatası değil, bir kaza olabilir. Bu yüzden mülakatlarda "kesme nedir, neden ISR içinde `printf` yazılmaz, bir zamanlayıcı kesmesi ile sürekli döngü arasındaki fark nedir?" soruları sık gelir. Bu bölümü okuduktan sonra bu sorulara yalnızca ezberden değil, bir zaman çizelgesi çizerek cevap verebilmelisin.

Kendi projelerinde bu konuya iki kez yakınsın. Birincisi MertOS: çekirdeğinde x86 IDT'si kurulmuş, klavye tuşları IRQ1 kesmesiyle halka tampona yazılıyor (Bölüm 27'deki SPSC tamponu). İkincisi EV Dashboard: STM32F4 ana döngüsü her 200 ms'de bir Daly BMS, Kelly motor sürücüsü ve Raspberry Pi'ye UART üzerinden konuşuyor. Bu döngünün zamanlamasının neden 200 ms'de sabit kalmadığını, bölüm sonundaki hesapta göreceksin.

::: not
Bu bölümdeki ölçümlerin kaynağı üç ayrı yerdir ve metinde her biri ayrıca işaretlenmiştir. (1) **Derleme:** ARM GCC 13.3.1 (`arm-none-eabi-gcc`) ile Cortex-M4 için üretilmiş nesne dosyalarının döküm çıktıları; bunları gerçek bir kartta çalıştırmadık. (2) **Benzetim:** Python ve C ile yazılmış cevrim-düzeyi ve olay-düzeyi modeller; sonuçlar modelin varsayımlarına bağlıdır, gerçek bir mikrodenetleyici ölçümü değildir. (3) **Ölçüm:** WSL2 (Ubuntu) üzerinde Linux `setitimer` ile yapılan periyodik sinyal ölçümü; bu bir ana bilgisayar ölçümüdür, mikrodenetleyici değildir. Unicorn Engine ile yapılan emülasyon yalnızca kesme **govdesini** ve ana döngü kodunu çalıştırır; donanımın kesme girişindeki yığınlamayı emüle etmez. Metinde "genel bilgi" ifadesi, ilgili değerin üretici belgesinden alındığını ama bu ortamda doğrulanmadığını gösterir.
:::

## 44.1 Yoklama mı, kesme mi?

Bir olayı yakalamanın en basit yolu **yoklamadır**: işlemci bir bayrağa (ya da bir donanım yazmacına) bakar, olay yoksa bir sonraki bakışa kadar başka iş yapar ya da bekler. Bu, bir bayrağa sürekli bakan bir döngüdür.

Yoklama, en kolay anlaşılan modeldir ama iki maliyeti vardır. Birincisi **gecikme**: olay, iki bakış arasında gelirse, işlemci onu bir sonraki bakışa kadar fark etmez. Olaylar bakış aralığı `P` boyunca eşit olasılıkla düştüğünde ortalama gecikme `P/2`, en kötü gecikme `P`'dir. İkincisi **CPU bedeli**: her bakış `c` süre alıyorsa, olay olmasa bile CPU'nun `c/P` oranı bu işe gider. Yani yoklamada iş yokken bile işlemci meşguldür.

Kesme modelinde ise donanım, olayın geldiği anda işlemciye bir sinyal gönderir; işlemci o an yaptığı işi bırakıp bir **kesme işleyicisine (ISR, Interrupt Service Routine)** dallanır, işi bitirince kaldığı yerden devam eder. Yoklamanın gecikmesi bakış aralığına bağlıydı; kesmede gecikme donanımın ve işlemcinin kabul süresine bağlıdır. Kesme CPU'yu yalnızca olay olduğunda meşgul eder. Bu ilişkiyi Şekil 44.1'de görebilirsin.

![Şekil 44.1: Yoklama ile kesmenin zaman çizelgesi karşılaştırması. Yoklamada olay, bir sonraki bakışa kadar beklenir; kesmede işleyici olayın hemen ardından çalışır.](gorseller/b44_yoklama_kesme.png)

Rakamlarla bakalım. Bir Cortex-M4'ü 168 MHz'de çalıştırdığını varsay. Bir bakış `c = 2 µs` sürsün (varsayım) ve bakış periyodu `P = 1 ms` olsun. Yoklamanın CPU bedeli `2 µs / 1 ms = %0,2`'dir ve bu oran olay olmasa da sürer. Ortalama gecikme `0,5 ms`, en kötü gecikme `1 ms`'dir.

Aynı olaylar kesmeyle işlenirse, kabul ve yığınlamanın (ayrıntısı 44.4'te) yaklaşık 12 çevrim sürdüğünü genel bilgi olarak kabul edelim. Bu, `12 / 168 MHz = 0,071 µs` eder. Her olay için giriş ve çıkış birlikte yaklaşık 22 çevrim, yani `0,131 µs` tutar. Saniyede 50 olay varsa toplam kesme yükü `50 × 0,131 µs = 6,6 µs` olur; bu, saniyenin `%0,00066`'sıdır. Olay olmadığı zaman bu yük sıfırdır.

Bu hesabın bir uyarısı var: kesme olaylarının sayısı artınca yük de artar. Olaylar çok sık gelirse (ör. her 10 µs'de bir), kesme yükü yoklamadan daha pahalı olabilir çünkü her olay için giriş-çıkış bedeli ödenir. Yoklama ise birden çok olayı tek bakışta toplu okuyabilir. Bu nedenle pratikte iki yöntem birlikte kullanılır: seyrek ve zamanlaması önemli olaylar kesmeyle, yoğun veri akışları DMA ya da tampon ile toplu işlenir (DMA ve UART ayrıntısı Bölüm 28 ve Bölüm 45'te).

::: ipucu
Bir yoklama döngüsünün CPU bedelini ölçmek için döngüyü bir GPIO pini ile işaretleyip osiloskopta yüksek seviyenin süresine bak. Yüksek seviye oranı, yoklamanın işlemci yükünü doğrudan gösterir.
:::

Kesmenin bir de **güç** boyutu var. Gömülü işlemcilerde `WFI` (Wait For Interrupt) komutu işlemciyi bir uyku durumuna sokar ve bir kesme gelene kadar saat dalgalarını durdurur (genel bilgi). Yoklama döngüsünde işlemci uyuyamaz; her bakışta çalışır. Ölçülebilir güç farkı, kullanılan modele ve kart üreticisinin uyku modlarına bağlıdır; bu bölümde güç değeri vermiyoruz, çünkü bunu ölçmek için kart ve ampermetre gerekir.

## 44.2 Kesme kavramı ve vektör tablosu: x86'dan Cortex-M'ye

Bir kesmenin yaşam döngüsü kabaca dört aşamadan oluşur. Önce **kaynak** bir olay üretir (zamanlayıcı sayımı bitti, UART baytı geldi). Bu olay donanımda bir **bekleyen (pending)** bayrağı olarak tutulur. Sonra denetleyici, bu bayrağın **maskelenmemiş** ve **öncelik** olarak işlemcinin o anki işinden üstün olup olmadığına bakar. Üstünse işlemci **kabul** eder: o anki bağlamını yığına koyar, **vektör tablosundan** işleyicinin adresini okur ve dallanır. İşleyici bitince bayrak temizlenir ve işlemci önceki bağlamını geri yükler.

Burada "vektör" sözcüğü önemli. Her kesme kaynağının bir numarası vardır ve işlemci bu numarayı bir tablonun dizini olarak kullanır. Böylece işlemci, hangi işleyicinin çalışacağını bir arama ile bulur. Bölüm 2'de gördüğümüz **geri çağırma (callback)** deseninin donanım karşılığı budur: "şu olay olunca şu fonksiyonu çağır" bilgisi tabloda tutulur.

Bu kavramı iki mimaride karşılaştıralım. Önce MertOS'un x86-64 kesme düzeni, çünkü bunu kendi kodundan okuyabilirsin. `kernel/arch/x86_64/idt.cpp` içindeki `IDT::registerHandler` fonksiyonu (imzası 66. satırda: vektör numarası, işleyici adresi ve DPL alır) kapıyı şöyle kurar; gövde alıntısı:

```cpp
    // type_attr: Present(1) | DPL | Type(0xE = 64-bit interrupt gate)
    uint8_t attr = 0x8E | ((dpl & 0x3) << 5);
    setGate(vector, reinterpret_cast<uint64_t>(handler), 0x08, attr);
}
```

`type_attr` değerindeki `0x8E` bayrağı şunu anlatır: bit 7 (P, mevcut), DPL alanı (ring) ve tip `0xE`, yani **kesme kapısı (interrupt gate)**. Kesme kapısı, girerken `IF` bayrağını silerek aynı kesmenin ve sonradan gelen (maskelenebilir) kesmelerin işleyicinin ortasında kesmesini engeller. Tip `0xF` olan tuzak kapısı (trap gate) ise `IF`'e dokunmaz. `setGate` içindeki `0x08` seçicisi, GDT'deki çekirdek kod segmentine işaret eder: MertOS'un `gdt.cpp` dosyasında 1. girdi çekirdek kod segmentidir (`setDescriptor(1, ...)`, 44. satır) ve seçici değeri `1 × 8 = 0x08`'dir. Bölüm 24.10'da GDT ve segmentin kesmelerle birlikte ele alınacağını söylemiştik; işte bu seçici, kapının hangi segment tanımlayıcısını kullanacağını söyler. `EX_BREAKPOINT` kapısına verilen `3` ise DPL'dir: halka 3'teki bir kullanıcı programının `int3` ile bu kapıyı çağırabilmesi için tanımlanmıştır. Diğer kapılarda DPL `0`'dır; kullanıcı programı onları çağıramaz.

x86'da işlemcinin kendisi IDT'nin yerini `lidt` komutuyla öğrenir. MertOS bunu `load` fonksiyonunda yapar ve hemen ardından `sti` ile kesmeleri açar:

```cpp
void IDT::load()
{
    asm volatile("lidt %0" : : "m"(pointer) : "memory");
    asm volatile("sti");   // Interrupt'ları aktif et
}
```

Bu iki satır, bir x86 kesmesinin "bağlanma" anını gösterir. Donanım kesmesi gelince işlemci IDT'den kapıyı alır, yığına dönüş bilgisini koyar ve kapının işleyicisine dallanır. MertOS'un işleyicisi ise bütün genel amaçlı yazmaçları elle yığına kaydeder. Bunu `isr_stubs.asm` dosyasındaki `IRQ_STUB` makrosu yapar:

```asm
%macro IRQ_STUB 2               ; %1 = IRQ numarası, %2 = C handler
global irq_stub_%1
irq_stub_%1:
    SAVE_REGS
    ; handler(frame*)
    lea  rdi, [rsp + 15*8]      ; InterruptFrame pointer
    call %2
    RESTORE_REGS
    iretq
%endmacro
```

Burada iki şey dikkat çekicidir. Birincisi, `SAVE_REGS` makrosu 15 yazmacı elle yığına iter; x86'da donanım bunların hiçbirini kaydetmez. İkincisi, işleyici `iretq` ile döner; dönüş adresi ve bayrakları donanım yığından geri alır. Bölüm 24'te `call` komutunun dönüş adresini yığına itmesini görmüştük; kesme girişinde ise dönüş bilgisini donanım kendisi iter.

Şimdi Cortex-M4'e geçelim. Cortex-M'de `lidt` yoktur. Bunun yerine **vektör tablosu** bellekte düz bir dizidir ve ilk öğesi MSP'nin (ana yığın işaretçisinin) başlangıç değeri, ikincisi Reset işleyicisinin adresidir. Her girdi 4 bayttır ve adresin en düşük biti 1 olmalıdır; bu bit Thumb modunda olunduğunu belirtir. Tabloyu `vektor.c` dosyasında bir dizi olarak tanımlayıp `.isr_vector` bölümüne yerleştiriyoruz. Bağlayıcı betiği bu bölümü flash'ın başına koyar (bağlayıcı betiğinin ayrıntısı Bölüm 43'te).

```c
/* vektor.c - Cortex-M4 vektor tablosu (STM32F407 IRQ numaralari) */
#include <stdint.h>

extern uint32_t _estack;            /* baglayiciden: RAM sonu */
extern uint32_t _sbss, _ebss;       /* .bss sinirlari */
void Reset_Handler(void);
void Default_Handler(void);
void TIM2_IRQHandler(void);
void USART1_IRQHandler(void);
int main(void);

/* Tablo: [0] MSP, [1] Reset, [2..15] istisnalar, [16+n] IRQn */
__attribute__((section(".isr_vector"), used))
const void *g_vektor[16 + 60] = {
    [0]  = &_estack,
    [1]  = Reset_Handler,
    [2]  = Default_Handler,         /* NMI */
    [3]  = Default_Handler,         /* HardFault */
    [14] = Default_Handler,         /* PendSV */
    [15] = Default_Handler,         /* SysTick */
    [16 + 28] = TIM2_IRQHandler,    /* IRQ28: TIM2 */
    [16 + 37] = USART1_IRQHandler,  /* IRQ37: USART1 */
};

void Reset_Handler(void)
{
    uint32_t *p;

    for (p = &_sbss; p < &_ebss; p++) *p = 0;
    main();
    for (;;) { }
}

void Default_Handler(void)
{
    for (;;) { }
}
```

Bu tabloda istisnalar (`[2]` ile `[15]` arası) ve IRQ'lar ayrı ayrı tanımlanır. Bir IRQ'nun tablodaki yeri `16 + n` formülüyle bulunur: IRQ0 tablonun 16. girdisidir. Kesme numaraları, üreticinin cihaz başlığında tanımlanır; STM32F407 için CMSIS başlığında `TIM2_IRQn` değeri 28 ve `USART1_IRQn` değeri 37'dir (genel bilgi, kullandığın kütüphane sürümünde kontrol et). Bu bölümde derlediğimiz tabloda bu iki girdinin ofsetini, derleyicinin ürettiği dökümden doğrudan okuyabiliriz.

Aşağıdaki komut, bu programı ARM araç zinciriyle derleyip bağlar ve vektör tablosunun ilk satırlarını döker:

```term
$ arm-none-eabi-objdump -s -j .isr_vector fw.elf

out/fw.elf:     file format elf32-littlearm

Contents of section .isr_vector:
 8000000 00000220 35010008 31010008 31010008  ... 5...1...1...
 8000010 00000000 00000000 00000000 00000000  ................
 8000020 00000000 00000000 00000000 00000000  ................
 8000030 00000000 00000000 31010008 31010008  ........1...1...
 8000040 00000000 00000000 00000000 00000000  ................
 8000050 00000000 00000000 00000000 00000000  ................
```

Çıktıda `00000220` gibi görünen ilk sözcük, little-endian bellekte `0x20020000` değerini tutar; bu, RAM'in sonu, yani başlangıç MSP'sidir. İkinci sözcük `35010008`, yani `0x08000135`: Reset işleyicisinin adresi `0x08000134` ile bit 0 birleşmiş hâlidir. Dökümün devamında `0x080000B0` (IRQ28, TIM2) ve `0x080000D4` (IRQ37, USART1) adreslerindeki girdileri görürsün. Bu adresler `16 + 28` ve `16 + 37` dizinlerine denk gelir (`28 × 4 = 0x70`, `+ 0x40 = 0xB0`; `37 × 4 = 0x94`, `+ 0x40 = 0xD4`). Bu girdilerdeki sözcükler işleyicilerin adresleridir: `0x08000165` (TIM2) ve `0x08000181` (USART1). Adreslerin bit 0'ının 1 olması Thumb modu için gereklidir.

Bu iki mimarinin farkını tek bakışta görmek için Şekil 44.2'ye bak.

![Şekil 44.2: Solda x86-64 IDT; her kapı bir işleyiciye gider ve kesme kapısı (0x8E) IF bayrağını siler. Sağda Cortex-M4 vektör tablosu: dizin doğrudan kesme numarasıdır, girdi bir işleyici adresidir.](gorseller/b44_x86_idt_nvic.png)

| Konu | x86-64 (MertOS) | Cortex-M4 (STM32F4) |
|---|---|---|
| Tablo | IDT, 256 kapı, 16 bayt/kapı | Vektör tablosu, 4 bayt/girdi |
| Tabloyu bulma | `lidt` ile IDTR yazmacı | Tablo bellekte sabit adreste (VTOR ile taşınabilir, genel bilgi) |
| Donanım kaydı | Dönüş adresi ve bayraklar; genel yazmaçlar yazılımca | R0-R3, R12, LR, PC, xPSR donanımca (44.4) |
| Dönüş | `iretq` | Özel bir `EXC_RETURN` değeri ile `bx lr` ya da dönüş komutu |
| Kesme bayrağı | `IF`: kesme kapısında otomatik silinir | `PRIMASK` yazmacı; ayrı bir kapı tipi yok |
| Öncelik | Yoktur; PIC ile dışarıda çözülür | NVIC içinde donanım önceliği (44.3) |
| Segmentler | GDT seçicisi (`0x08`) gerekir | Segment yok; bellek koruması MPU ile (Bölüm 25) |

MertOS'un klavye sürücüsünde iki ayrıntı daha var. Donanım PIC (8259) kullanıyor ve kesmenin bittiğini ona **kendi eliyle** bildirmek gerekiyor. Bu, `kernel.cpp` içindeki klavye köprüsünde yapılır: işleyici önce `handleInterrupt()` çağırır, sonra `0x20` değerini `0x20` bağlantı noktasına yazar. Cortex-M'de bu tür bir EOI yoktur; kesmenin bekleyen bayrağı işlemci tarafından otomatik temizlenir, fakat çevre birimin (ör. bir UART'ın alım bayrağı) kendi bayrağını yazılımla temizlemesi gerekir. Çevre birimi kendi bayrağını temizlemezse ve kaynak koşulu sürdürüyorsa, işleyici bittiğinde kesme yeniden bekler ve işlemci aynı işleyiciye tekrar girer.

Son olarak `keyboard.hpp` içindeki bir alan, bu bölümün ilerleyen kısmında önemli olacak:

```cpp
    volatile int m_head;    // Okuma pozisyonu
    volatile int m_tail;    // Yazma pozisyonu
```

Bu iki `volatile int` alanı, klavye ISR'ı (üretici) ve ana döngü (tüketici) arasında paylaşılan halka tamponun indeksleridir. `volatile` ile ne yapılabildiği ve ne yapılamadığı 44.6'da ayrıntılı işlenecek.

## 44.3 NVIC: kesme numaraları, durumlar, öncelik ve maskeler

Cortex-M'deki kesme denetleyicisi **NVIC** (Nested Vectored Interrupt Controller) adını taşır; adındaki "iç içe" ve "vektörlü" sözcükleri iki temel özelliğe işaret eder: kesmeler birbirinin içine girebilir ve her kesmenin kendi vektörü vardır. NVIC, her kesme kaynağı için dört durumdan birini tutar:

- **Pasif (inactive):** kesme ne bekliyor ne de çalışıyor.
- **Bekliyor (pending):** olay geldi, işlemci henüz kabul etmedi.
- **Aktif (active):** işleyici çalışıyor.
- **Aktif + bekliyor:** işleyici çalışırken aynı kesme yeniden tetiklendi.

Bu durumlar donanım yazmaçlarıyla gözlemlenebilir. Genel bilgi olarak: `ISER` ve `ICER` ile bir kesme etkinleştirilir ve devre dışı bırakılır; `ISPR` ve `ICPR` ile bekleyen bayrak yazılıp silinir; `IABR` ile aktif olan kesme okunur; `IPR` ile öncelik değeri ayarlanır. Bu adlar CMSIS başlığındaki kayıt adlarıdır; uygulamada genellikle `NVIC_EnableIRQ` gibi fonksiyonlarla yazılır. Bu bölümde yazmaçların ham adreslerini değil, mantığı öğreniyoruz.

Şekil 44.3, durumlar arasındaki geçişleri gösteriyor.

![Şekil 44.3: NVIC kesme durumları. Olay geldiğinde kesme bekler; kabul edilince aktif olur; işleyici biterken bekleyen aynı kesme varsa yeniden aktif olur.](gorseller/b44_nvic_durum.png)

**Öncelik.** Cortex-M'de öncelik değeri küçüldükçe önem artar: 0 en yüksek, daha büyük sayılar daha düşük önceliktir. STM32F4 öncelik değerlerini 8 bitlik bir alanda tutar ama yalnızca üst 4 biti kullanır; bu yüzden 16 öncelik seviyesi vardır (genel bilgi, `NVIC_PRIO_BITS = 4`). Her 4 bit'lik değer, bir öncelik grubu ayarına göre iki parçaya bölünür: **önceliklendirme (preemption)** kısmı, bir kesmenin başka bir kesmeyi kesip kesemeyeceğini belirler; **alt öncelik (subpriority)** kısmı ise aynı önceliklendirme seviyesinde bekleyen iki kesmeden hangisinin önce çalışacağını belirler. Bölünme, `AIRCR` yazmacındaki `PRIGROUP` alanıyla yapılır. STM32 HAL kütüphanesi `HAL_Init()` çağrısında öncelik grubunu 4'e ayarlar; bu durumda 4 bitin tamamı önceliklendirme için kullanılır ve alt öncelik yoktur (genel bilgi, HAL sürümüne göre doğrula).

Bu ayrımın pratik sonucu şudur: iki kesme aynı önceliklendirme seviyesindeyse, biri çalışırken diğeri onu kesemez; sadece bekler. Alt öncelik yalnızca iki bekleyen kesme arasındaki sıralamayı değiştirir.

**Maskeler.** Bir kesmeyi geçici olarak susturmanın üç yolu vardır:

- **PRIMASK:** tek bitlik bir yazmaç. Ayarlanınca NMI ve HardFault dışındaki bütün yapılandırılabilir kesmeleri maskeler. Komutları `cpsid i` (ayarla) ve `cpsie i` (temizle) komutlarıdır.
- **FAULTMASK:** HardFault dahil her şeyi maskeler; yalnızca NMI kalır. Sürücü içinde nadiren kullanılır.
- **BASEPRI:** yalnızca öncelik değeri belirli bir eşiğin üstünde (sayıca büyük, yani daha az önemli) olan kesmeleri maskeler. Sıfır değeri maskelemeyi kapatır.

BASEPRI'nin özel değeri, seçici maskelemeyi mümkün kılar: çok kritik olmayan kesmeleri kapatırken bazı zaman kritik kesmelerin çalışmasına izin verebilirsin. FreeRTOS'un bağlam değişimi kodu da bu yolla çalışır; Kod Okuma bölümünde bu kodu göreceksin.

::: dikkat
Bir kesme işleyicisinin içinde PRIMASK ile tüm kesmeleri kapatıp uzun bir iş yapmak, sistemin yanıt süresini bütünüyle bozar. Kritik bölge ne kadar kısaysa o kadar iyidir; bunu 44.6 ve Bölüm 27.19'da görüyoruz.
:::

## 44.4 Donanımın yığına koyduğu çerçeve ve EXC_RETURN

Bir kesme kabul edildiğinde işlemci, işleyici C kodunun ilk satırından önce birkaç şeyi kendi kendine yapar. Bunların en önemlisi **yığınlamadır**: işlemci, kesilen programın bazı yazmaçlarını aktif yığına otomatik olarak iter. Cortex-M'de bu çerçeve sekiz sözcüktür: `R0`, `R1`, `R2`, `R3`, `R12`, `LR`, `PC` (dönüş adresi) ve `xPSR`. Bu sekiz sözcük 32 bayt eder ve Şekil 44.4'te görüldüğü gibi, yığın işaretçisi `SP` bu çerçevenin en düşük adresini gösterecek şekilde yerleşir.

Neden bu sekiz yazmaç? Çünkü bunlar, bir C fonksiyonunun **çağıran tarafından korunmayan** (caller-saved) yazmaçlarıdır ve işleyici bunları kullanmak zorunda kalabilir. Derleyici, işleyici içinde `R4`-`R11` gibi çağrı boyunca korunması gereken yazmaçları kullanırsa yalnızca onları kendi prologunda yığına iter. Bu, AAPCS çağrı kuralının bir sonucudur ve Bölüm 24.4'te gördüğümüz çağrı kurallarının aynısıdır. Dolayısıyla ISR'ın C fonksiyonu, donanımın kaydettiği yazmaçları tekrar kaydetmez.

![Şekil 44.4: Donanımın yığına koyduğu çerçeve. Temel çerçeve 8 sözcüktür; FPU bağlamı aktifse S0-S15, FPSCR ve ayrılmış bir sözcük eklenir ve toplam 26 sözcüğe çıkar.](gorseller/b44_yigin_cerceve.png)

**Derleyicinin bunu nasıl yaptığını görelim.** Aşağıdaki kesme işleyicisi bir fonksiyon çağrısı olmadan yalnızca bir değişkeni artırıyor ve bir tampona yazıyor. Derleyici bu işleyiciyi bir kuyruk çağrısı (tail call) olarak derler: yığın çerçevesi açmaz, yalnızca `rb_yaz` fonksiyonuna dallanır. Bu, işleyicinin hiçbir yazmaç kaydetmediği anlamına gelir; çünkü ihtiyaç duyulan yazmaçlar zaten donanımın çerçevesindedir.

```c
void adc_isr_govde(uint8_t ornek)
{
    g_tick++;
    rb_yaz(&g_rb, ornek);
}
```

Bu fonksiyonun derlenmiş hâlini şöyle görürsün (ARM GCC 13.3.1, `-mcpu=cortex-m4 -mthumb -O2`):

```term
$ arm-none-eabi-objdump -d isr_test.o
00000000 <adc_isr_govde>:
   0:	4b04      	ldr	r3, [pc, #16]	@ (14 <adc_isr_govde+0x14>)
   2:	681a      	ldr	r2, [r3, #0]
   4:	4601      	mov	r1, r0
   6:	4618      	mov	r0, r3
   8:	3201      	adds	r2, #1
   a:	f840 2b04 	str.w	r2, [r0], #4
   e:	f7ff bffe 	b.w	0 <rb_yaz>
  12:	bf00      	nop
  14:	00000000 	.word	0x00000000

00000018 <ana_dongu_topla>:
  18:	b5f0      	push	{r4, r5, r6, r7, lr}
  1a:	4605      	mov	r5, r0
  1c:	b083      	sub	sp, #12
  1e:	b188      	cbz	r0, 44 <ana_dongu_topla+0x2c>
```

Çıktıda `b.w 0 <rb_yaz>` komutu, fonksiyonun sonunda `rb_yaz`'a dallandığını gösterir. Ön taraftaki `ldr`, `adds` ve `str.w r2, [r0], #4` komutları `g_tick` değişkenini artırır. Hiçbir `push` yok. Eğer `rb_yaz` bir fonksiyon çağrısı değil de işleyicinin ortasında olsaydı, derleyici yine yalnızca kullandığı `R4`-`R11` yazmaçlarını yığına iterdi.

Şimdi bir de kayan noktalı işleyici. Kesme gelmeden önce bir FPU bağlamı aktifse, donanım `S0`-`S15` ve `FPSCR` yazmaçlarını da yığına koyar; bu **genişletilmiş çerçevedir** (26 sözcük, 104 bayt; genel bilgi). Ancak burada önemli bir ayrıntı var: çağrı kuralına göre `S16`-`S31` çağrı boyunca korunmak zorundadır ve bunları işleyicinin kendisi kaydetmek zorundadır. Aşağıdaki kod bunu gösteriyor:

```c
/* fpu_isr.c - kayan noktali kesme isleyicisi */
#include <stdint.h>

volatile float g_girdi[4];
volatile float g_cikti;

/* Baska birimde tanimli, yavas bir hesap */
extern float yavas_hesap(float x);

void SysTick_Handler(void)
{
    float a = g_girdi[0];
    float b = g_girdi[1];
    float c = g_girdi[2];
    float d = g_girdi[3];
    float s = a * b + c * d;

    /* Cagri: s16-s31 cagri boyunca korunur */
    float t = yavas_hesap(s);
    g_cikti = t * a - b;
}
```

Derlenmiş hâli, işleyicinin hem tamsayı hem de kayan nokta yazmaçlarını nasıl ele aldığını gösterir:

```term
$ arm-none-eabi-objdump -d fpu_isr.o
00000000 <SysTick_Handler>:
   0:	b510      	push	{r4, lr}
   2:	4c0e      	ldr	r4, [pc, #56]	@ (3c <SysTick_Handler+0x3c>)
   4:	ed2d 8b02 	vpush	{d8}
   8:	ed94 8a00 	vldr	s16, [r4]
   c:	edd4 8a01 	vldr	s17, [r4, #4]
  10:	edd4 7a02 	vldr	s15, [r4, #8]
  14:	ed94 7a03 	vldr	s14, [r4, #12]
  18:	ee28 0a28 	vmul.f32	s0, s16, s17
  1c:	ee67 7a87 	vmul.f32	s15, s15, s14
  20:	ee30 0a27 	vadd.f32	s0, s0, s15
  24:	f7ff fffe 	bl	0 <yavas_hesap>
  28:	ee28 8a00 	vmul.f32	s16, s16, s0
  2c:	ee38 8a68 	vsub.f32	s16, s16, s17
  30:	ed84 8a04 	vstr	s16, [r4, #16]
  34:	ecbd 8b02 	vpop	{d8}
```

`push {r4, lr}` ile tamsayı yazmaçları, `vpush {d8}` ile `S16`-`S17` (yani `d8`) kaydediliyor. `S0`-`S15` yazmaçlarına ise derleyici dokunuyor ama onları kaydetmiyor: bunları işleyici çağrı kuralına göre korumak zorunda değil, donanım zaten FPU bağlamı aktifse genişletilmiş çerçevede yığına koyuyor. Burada **tembel yığınlama (lazy stacking)** devreye girer: genel bilgi olarak, Cortex-M4F'te donanım FP yazmaçlarını hemen yığına yazmaz; yalnızca işleyici ilk FP komutunu çalıştırdığında gerçekten kaydeder. Bu, FPU kullanmayan kesmelerin gecikmesini kısaltır. Bu davranış `FPCCR` yazmacındaki `LSPEN` bitiyle yönetilir (genel bilgi, ayrıntılar üretici belgesinde).

Bölüm 24'ün alıştırmalarından birinde (soru 10) "gömülü bir kesme işleyicisinde kayan nokta birimi kullanmak neden dikkat ister?" diye sormuştuk. Cevabın özeti budur: FP kullanan bir işleyici, hem donanımın genişletilmiş çerçevesini (yığın payı) hem de kendi `vpush`/`vpop` maliyetini ödemek zorundadır. Kesme sıklığı yüksekse bu maliyet toplamda anlamlı olur.

**EXC_RETURN.** Kesme girişinde `LR` yazmacı dönüş adresi **tutmaz**. İşlemci onun yerine özel bir değer koyar: **EXC_RETURN**. İşleyici `bx lr` ile döndüğünde işlemci bu değere bakarak nereye ve hangi yığından döneceğine karar verir. Sık görülen değerler şunlardır (genel bilgi, ARMv7-M mimari belgesi):

| EXC_RETURN | Dönüş yeri | Yığın | Çerçeve |
|---|---|---|---|
| `0xFFFFFFF1` | işleyiciye (iç içe kesme) | MSP | temel (8 sözcük) |
| `0xFFFFFFF9` | iş parçacığına (thread) | MSP | temel |
| `0xFFFFFFFD` | iş parçacığına | PSP | temel |
| `0xFFFFFFE1`, `0xFFFFFFE9`, `0xFFFFFFED` | yukarıdakilerin aynısı | MSP/PSP | genişletilmiş (bit 4 = 0) |

Tablodan okunacak üç bilgi var. Bit 3 dönüşün işleyiciye mi (0) yoksa iş parçacığına mı (1) olduğunu, bit 2 hangi yığının (PSP = 1, MSP = 0) kullanılacağını, bit 4 ise çerçevenin temel (1) mi genişletilmiş (0) mi olduğunu söyler. FreeRTOS'un bağlam değişimi kodunda `tst r14, #0x10` komutu bu bit 4'ü sınar; bunu Kod Okuma bölümünde göreceksin.

::: ipucu
Derleyici, FPU örneğinde gördüğün gibi işleyicinin prologunda `LR`'yi yığına iter (`push {r4, lr}`) ve epilogda `pop {r4, pc}` ile `PC`'ye geri yükler. Burada `LR`'de duran EXC_RETURN değeri `PC`'ye yüklenince işlemci bunu bir dönüş olarak yorumlar. Bu yüzden kesme işleyicileri normal C fonksiyonları gibi yazılabilir. Yığın hizası AAPCS gereği 8 bayttır; donanım gerektiğinde bunu xPSR'nin bit 9'u ile kendisi düzeltir (genel bilgi).
:::

## 44.5 İç içe kesmeler, kuyruk zinciri ve geç gelen kesme

Bir işleyici çalışırken daha yüksek öncelikli bir kesme gelirse, işlemci çalışan işleyiciyi **keser** ve yenisine geçer. Buna **iç içe kesme (nesting, preemption)** denir. Kesilen işleyicinin kalan işi yığında bekler; yeni işleyici bitince kesilen devam eder. Bu, Bölüm 26'daki çok görevli zamanlamanın donanım düzeyindeki benzeridir, ama burada bağlam değiştirme bir işletim sistemi kararı değil, donanımın öncelik kuralıdır.

İki özel durum, bu zamanlamayı verimli kılar. **Kuyruk zinciri (tail-chaining):** bir işleyici biterken bekleyen başka bir kesme varsa, işlemci araya girip bağlamı yığından açmak ve tekrar yığınlamak yerine doğrudan sıradaki işleyiciye geçer. Bu, çıkış ve yeniden giriş bedelini (genel bilgi, modelde 10 + 12 çevrim) kısa bir geçişe (modelde 6 çevrim) indirir. **Geç gelen kesme (late arrival):** yığınlama sürerken daha yüksek öncelikli bir kesme gelirse, işlemci yığınlamayı bitirir ve önce yeni kesmeye geçer; yığınlamayı baştan yapmaz.

Şekil 44.5'te üç senaryo var. Senaryolar aşağıdaki betikte tanımlıdır. Betiğin tamamı bir olay simülatörüdür: her çevrimde işlemcinin hangi fazda olduğunu (T = iş parçacığı, E = yığınlama, H = işleyici, X = çıkış, L = kuyruk zinciri) kaydeder.

![Şekil 44.5: Üç senaryonun cevrim düzeyi benzetimi. A: düşük öncelikli UART işleyicisi çalışırken ADC kesmesi gelir ve onu keser. B: TIM işleyicisi biterken bekleyen UART kuyruk zinciriyle hemen başlar. C: UART yığınlanırken ADC gelir; ADC önce çalışır, UART sonra gelir.](gorseller/b44_ic_ice_kuyruk.png)

Benzetimin ana bölümü, her çevrimde durumu güncelleyen bir döngüdür. Önce kesme kabulü, sonra geç gelen kontrolü, sonra fazın kendi işi gelir. Kodu üç parçada veriyoruz.

```python
# -*- coding: utf-8 -*-
"""Cevrim-duzeyi kesme denetleyicisi benzetimi (NVIC benzeri).

BENZETIM: Gercek bir MCU olcumu degildir. Zamanlamalar modelde
varsayilandir: ENTRY = 12 (kabul ve yiginlama), EXIT = 10 (cikis),
TAIL = 6 (kuyruk zinciri). Kucuk sayi = yuksek oncelik.
"""
import csv
import random
import statistics

ENTRY, EXIT, TAIL = 12, 10, 6
YOK = 99                      # calisan kesme yok: ana dongu

def simule(olaylar, ufuk, kuyruk=True, gec=True):
    """olaylar: [(varis, ad, oncelik, govde)]. Doner: (izler, gec)."""
    bekle = []                # bekleyen ornekler
    kalan = sorted(olaylar)
    yigin = []                # calisan ya da kesilmis isleyiciler
    faz, hedef, rem = "THREAD", None, 0
    izler, gecikmeler = [], []

    def en_iyi(esik):
        aday = [b for b in bekle if b["p"] < esik]
        if not aday:
            return None
        return min(aday, key=lambda b: (b["p"], b["v"]))

    def ust():
        return yigin[-1]["p"] if yigin else YOK

    for t in range(ufuk):
        while kalan and kalan[0][0] == t:
            v, ad, p, g = kalan.pop(0)
            bekle.append({"v": v, "ad": ad, "p": p, "g": g})
        if faz in ("THREAD", "HANDLER"):
            b = en_iyi(ust())
            if b is not None:               # kabul: yiginlama
                bekle.remove(b)
                hedef, faz, rem = b, "ENTRY", ENTRY
        if faz == "ENTRY" and gec:
            b = en_iyi(min(ust(), hedef["p"]))
            if b is not None:               # gec gelen: daha onemli
                bekle.remove(b)
```

Gecikme, bir olayın varış anından işleyicinin ilk komutunun çalışmaya başladığı ana kadar geçen süredir. Benzetimde varsayılan değerler `ENTRY = 12`, `EXIT = 10` ve `TAIL = 6` çevrimdir. Bunlar genel bilgi olarak ARM'ın Cortex-M4 belgelerindeki tipik değerlerdir, ancak bir kartta ölçülmüş değil; bu yüzden tablo değerlerini ölçüm gibi değil, modelin sonucu olarak okumalısın.

```python
                bekle.append(hedef)
                hedef = b
        if faz == "THREAD":
            izler.append((t, "T", ""))
        elif faz == "ENTRY":
            izler.append((t, "E", hedef["ad"]))
            rem -= 1
            if rem == 0:
                faz = "HANDLER"
                hedef["kalan"] = hedef["g"]
                gecikmeler.append((hedef["ad"], t + 1 - hedef["v"]))
                yigin.append(hedef)
                hedef = None
        elif faz == "HANDLER":
            ust_is = yigin[-1]
            izler.append((t, "H", ust_is["ad"]))
            ust_is["kalan"] -= 1
            if ust_is["kalan"] == 0:
                yigin.pop()
                if kuyruk:                  # kuyruk zinciri
                    aday = en_iyi(ust())
                    if aday is not None:
                        bekle.remove(aday)
                        hedef, faz, rem = aday, "TAIL", TAIL
                        continue
                faz, rem = "EXIT", EXIT
        elif faz == "EXIT":
            izler.append((t, "X", ""))
            rem -= 1
            if rem == 0:
                faz = "HANDLER" if yigin else "THREAD"
        elif faz == "TAIL":
            izler.append((t, "L", hedef["ad"]))
            rem -= 1
            if rem == 0:
                faz = "HANDLER"
                hedef["kalan"] = hedef["g"]
                gecikmeler.append((hedef["ad"], t + 1 - hedef["v"]))
                yigin.append(hedef)
                hedef = None
    return izler, gecikmeler

SENARYO = {
    "ic_ice": [(0, "UART", 2, 40), (20, "ADC", 1, 15)],
```

```python
    "kuyruk_zinciri": [(0, "TIM", 1, 10), (5, "UART", 2, 8)],
    "gec_gelen": [(0, "UART", 2, 20), (4, "ADC", 1, 6)],
}

def rastgele_yuk(tohum, ufuk):
    """Uc kaynak, Poisson varisler (ortalama aralik ile)."""
    rnd = random.Random(tohum)
    kaynak = [("ADC", 1, 400, 20, 40), ("UART", 2, 250, 30, 60),
              ("TIM", 3, 1000, 80, 120)]
    olaylar = []
    for ad, p, ort, lo, hi in kaynak:
        t = 0.0
        while True:
            t += rnd.expovariate(1.0 / ort)
            if t >= ufuk:
                break
            olaylar.append((int(t), ad, p, rnd.randint(lo, hi)))
    return olaylar

def yoklama(varislar, periyot):
    """Yoklama: bir sonraki yoklama anina kadar bekleme."""
    return [(periyot - v % periyot) % periyot for v in varislar]
```

Betiğin son kısmı üç senaryoyu çalıştırır, kuyruk zinciri ve geç gelen mekanizmalarını kapatarak karşılaştırma yapar ve rastgele bir yük altında gecikme dağılımını üretir. Rastgele yük, tohumu `44` olan bir `random.Random` nesnesiyle üretilir; böylece sonuçlar tekrarlanabilir.

```python
if __name__ == "__main__":
    print("== Senaryolar (ENTRY=12 EXIT=10 TAIL=6) ==")
    tum = []
    for ad, olay in SENARYO.items():
        izler, gec = simule(olay, 80)
        print("-- %s --" % ad)
        for k, g in gec:
            print("  %-6s kabul gecikmesi = %3d cevrim" % (k, g))
        tum += [(ad, t, e, n) for t, e, n in izler]
    print("== Kuyruk zinciri kapali (B) ==")
    _, g = simule(SENARYO["kuyruk_zinciri"], 80, kuyruk=False)
    for k, v in g:
        print("  %-6s gecikme = %3d cevrim" % (k, v))
    print("== Gec gelen kapali (C) ==")
    _, g = simule(SENARYO["gec_gelen"], 80, gec=False)
    for k, v in g:
        print("  %-6s gecikme = %3d cevrim" % (k, v))

    print("== Rastgele yuk: 300000 cevrim, tohum=44 ==")
    olaylar = rastgele_yuk(44, 300000)
    _, gec = simule(olaylar, 300000)
    adc = [v for k, v in gec if k == "ADC"]
    tum_k = [v for k, v in gec]
    yok = yoklama([o[0] for o in olaylar if o[1] == "ADC"], 200)
    for ad, d in (("kesme ADC", adc), ("kesme tum", tum_k),
                  ("yoklama ADC (P=200)", yok)):
        p95 = sorted(d)[int(0.95 * (len(d) - 1))]
        print("%-20s n=%5d ort=%6.1f p95=%4d max=%4d" % (
            ad, len(d), statistics.mean(d), p95, max(d)))

    # Sekiller icin CSV dosyalari: calisma dizinine yazilir
    with open("b44_nvic_senaryo.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["senaryo", "zaman", "etiket", "ad"])
        w.writerows(tum)
    with open("b44_gecikme.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tur", "kaynak", "gecikme_cevrim"])
        for ad, v in gec:
            w.writerow(["kesme", ad, v])
        for v in yok:
            w.writerow(["yoklama", "ADC", v])
```

Betiği çalıştırdığında çıktı şöyle olur:

```term
$ python nvic_sim.py
== Senaryolar (ENTRY=12 EXIT=10 TAIL=6) ==
-- ic_ice --
  UART   kabul gecikmesi =  12 cevrim
  ADC    kabul gecikmesi =  12 cevrim
-- kuyruk_zinciri --
  TIM    kabul gecikmesi =  12 cevrim
  UART   kabul gecikmesi =  23 cevrim
-- gec_gelen --
  ADC    kabul gecikmesi =   8 cevrim
  UART   kabul gecikmesi =  24 cevrim
== Kuyruk zinciri kapali (B) ==
  TIM    gecikme =  12 cevrim
  UART   gecikme =  39 cevrim
== Gec gelen kapali (C) ==
  UART   gecikme =  12 cevrim
  ADC    gecikme =  20 cevrim
== Rastgele yuk: 300000 cevrim, tohum=44 ==
kesme ADC            n=  723 ort=  14.0 p95=  30 max=  65
kesme tum            n= 2208 ort=  23.3 p95=  71 max= 538
yoklama ADC (P=200)  n=  723 ort= 100.4 p95= 190 max= 199
```

Tabloyu okumayı bir örnekle açalım. Senaryo A'da UART yığınlandıktan sonra (0-11 çevrim) işleyici 12. çevrimde başlar; gecikme `12` çevrimdir. ADC 20. çevrimde gelir; UART o anda 8 çevrim çalışmış ve 32 çevrim işi kalmıştır. ADC, yeni bir yığınlama ile (20-31) 32. çevrimde başlar. Yani gecikme yine `12` çevrimdir. Senaryo B'de TIM bitince UART bekler; kuyruk zinciri sayesinde UART, varışından `23` çevrim sonra (28. çevrimde) başlar. Zincir kapalı olsaydı çıkış ve yeniden giriş (10 + 12) eklenirdi ve gecikme `39` olurdu. Bu fark, benzetimde `39 − 23 = 16` çevrimdir (`10 + 12 − 6`). Senaryo C'de ADC, UART yığınlanırken gelir; geç gelen mekanizma sayesinde ADC, varışından `8` çevrim sonra başlar. Mekanizma kapalıyken ADC, UART'ın yığınlanmasını bitirmesini bekler, sonra onu keser: gecikme `20` olur. Yani geç gelen mekanizma yüksek öncelikli olayın gecikmesini `12` çevrim azaltır.

Bu sayılardan çıkan ders şudur: **yüksek öncelikli bir kesme, düşük öncelikli bir işleyicinin ne kadar uzun sürdüğüne bağlı beklemez; onu keser.** Gecikmeyi asıl uzatan iki durum vardır: PRIMASK ile tüm kesmelerin kapatıldığı kritik bölgeler ve aynı ya da daha yüksek öncelikli bir işleyicinin içinde kalan olaylar. Kesme gecikmesinin üst sınırını hesaplarken bu iki durumu ayırmak gerekir; Bölüm 44.10'da bu fikri zamanlanabilirlik analizine bağlayacağız.

Bu benzetimin güvendiği dış değerler: kesme kaynaklarının rastgele geldiği ve işleyici sürelerinin uniform aralıkta olduğu varsayımı. Gerçek bir sistemde işleyici süreleri, önbellek, bellek bekleme durumları ve diğer bus trafiği yüzünden daha geniş bir dağılım gösterir. Bu yüzden benzetimin çıktısını bir kartta ölçülmüş değer gibi değil, bir **model** olarak kullanmalısın.

## 44.6 Kesme işleyicisi yazım kuralları: kısa tut, veriyi koru

Bir kesme işleyicisi ana programın ortasında çalışır. Ana program o anda bir değişkeni okuyup yazıyor olabilir; işleyici o değişkene dokunursa veri tutarsız kalabilir. Bu bölümün en kritik kısmı budur: **ISR ile ana döngü arasında veri nasıl paylaşılır ve nasıl korunur**. Bölüm 27'de iki iş parçacığı için aynı problemi gördük; burada aynı problem tek çekirdekte kesme ile ana döngü arasında ortaya çıkıyor.

Önce altın kurallar. (1) ISR **kısa** olmalıdır: bayrağı kaldırır, bir değeri tampona yazar, zamanlayıcıyı yeniden kurar; ağır iş ana döngüye bırakılır. Bu desene **bayrak + ertelenmiş iş (bottom half)** denir. (2) ISR ile paylaşılan her değişken `volatile` olarak bildirilir: derleyici bu değişkenin değerini yazmaç içinde tutup bellekteki değişimi görmezden gelmesin diye. (3) Kritik bölgeler (ana döngünün ISR ile paylaştığı verilere eriştiği kısa anlar) kesmeleri susturarak korunur; ya da veri yapısı, yalnızca bir tarafın yazdığı şekilde tasarlanır.

Kesme ile ana döngü arasındaki veri yolunun en yaygın yapısı halka tamponudur. Şekil 44.6, iki indeksin kimin tarafından yazıldığını gösterir: kesme işleyicisi yalnızca `kuyruk`'u, ana döngü yalnızca `bas`'ı ilerletir.

![Şekil 44.6: Tek üretici/tek tüketici halka tamponu. Kesme işleyicisi veriyi yazıp `kuyruk`'u, ana döngü veriyi okuyup `bas`'ı ilerletir; 16 yuvalık tamponda boş/dolu ayrımı için bir yuva boş bırakılır.](gorseller/b44_halka_tampon.png)

**Halka tamponu (SPSC).** Bir UART ya da ADC kesmesi gelen veriyi bir tampona yazar, ana döngü bu tampondan okur. Tampon, tek üretici (ISR) ve tek tüketici (ana döngü) olduğu için kilitsiz tasarlanabilir: üretici yalnızca `kuyruk` indeksini, tüketici yalnızca `bas` indeksini yazar. Tampon boyu 2'nin kuvveti olduğunda indeks maskeleme ile sarar. Aşağıdaki kod, MertOS'taki klavye tamponunun (Bölüm 27) gömülü karşılığıdır.

```c
/* ringbuf.h - tek uretici / tek tuketici (SPSC) halka tamponu */
#ifndef RINGBUF_H
#define RINGBUF_H
#include <stdint.h>

/* Kapasite 2'nin kuvveti olmali: indeksler maskeyle sarar */
#define RB_KAPASITE 16u
#define RB_MASKE    (RB_KAPASITE - 1u)

typedef struct {
    volatile uint32_t bas;       /* tuketici yazar */
    volatile uint32_t kuyruk;    /* uretici yazar */
    volatile uint8_t  veri[RB_KAPASITE];
    volatile uint32_t dusen;     /* dolu iken atilan olay sayisi */
} rb_t;

/* Uretici (ISR): dolu ise olayi dusurur ve sayar. 1 = basarili */
int rb_yaz(rb_t *rb, uint8_t b);

/* Tuketici (ana dongu): bos ise 0 doner */
int rb_oku(rb_t *rb, uint8_t *b);

/* Tuketici icin: su an kac eleman var */
uint32_t rb_dolu(const rb_t *rb);

#endif
```

Tampon fonksiyonları şöyle:

```c
/* ringbuf.c - SPSC halka tamponu: kesme ile ana dongu arasinda */
#include "ringbuf.h"

int rb_yaz(rb_t *rb, uint8_t b)
{
    uint32_t kuyruk = rb->kuyruk;             /* kendi indeksimiz */
    uint32_t sonraki = (kuyruk + 1u) & RB_MASKE;

    if (sonraki == rb->bas) {                 /* tuketici bekliyor */
        rb->dusen++;                          /* dolu: olayi at */
        return 0;
    }
    rb->veri[kuyruk] = b;                     /* once veri yazilir */
    rb->kuyruk = sonraki;                     /* indeks yayinlanir */
    return 1;
}

int rb_oku(rb_t *rb, uint8_t *b)
{
    uint32_t bas = rb->bas;

    if (bas == rb->kuyruk) return 0;          /* bos */
    *b = rb->veri[bas];
    rb->bas = (bas + 1u) & RB_MASKE;
    return 1;
}

uint32_t rb_dolu(const rb_t *rb)
{
    return (rb->kuyruk - rb->bas) & RB_MASKE;
}
```

Derlenmiş `rb_yaz` fonksiyonunda sıra önemlidir. Aşağıda veri yazma (`strb`) komutu, indeksin yayınlandığı (`str r2, [r3, #4]`) komuttan önce gelir:

```term
$ arm-none-eabi-objdump -d ringbuf.o
00000000 <rb_yaz>:
   0:	4603      	mov	r3, r0
   2:	6840      	ldr	r0, [r0, #4]
   4:	b410      	push	{r4}
   6:	1c42      	adds	r2, r0, #1
   8:	681c      	ldr	r4, [r3, #0]
   a:	f002 020f 	and.w	r2, r2, #15
   e:	4294      	cmp	r4, r2
  10:	d008      	beq.n	24 <rb_yaz+0x24>
  12:	eb03 0c00 	add.w	ip, r3, r0
  16:	2001      	movs	r0, #1
  18:	f88c 1008 	strb.w	r1, [ip, #8]
  1c:	f85d 4b04 	ldr.w	r4, [sp], #4
  20:	605a      	str	r2, [r3, #4]
  22:	4770      	bx	lr
  24:	699a      	ldr	r2, [r3, #24]
  26:	f85d 4b04 	ldr.w	r4, [sp], #4
  2a:	3201      	adds	r2, #1
  2c:	2000      	movs	r0, #0
  2e:	619a      	str	r2, [r3, #24]
  30:	4770      	bx	lr
  32:	bf00      	nop

00000034 <rb_oku>:
```

Bu sıra tek çekirdekte donanımın kendi yazmalarını **program sırasına göre** uygulamasıyla korunur. Dolayısıyla tüketici, `kuyruk` indeksini yeni değerle gördüğünde `veri[]` içindeki baytın da yazılmış olduğunu bilir. Ancak bu garanti, aynı sistemde ikinci bir çekirdek ya da bellek bariyeri (`DMB`) gerektiren bir sistemde geçerli değildir (genel bilgi). Bu nedenle `volatile` tek başına bir senkronizasyon aracı değildir: Bölüm 27.19'da gördüğümüz gibi yalnızca derleyiciye "bu değer beklenmedik yerden değişebilir" der, bellek sıralaması garantisi vermez.

Kodun doğruluğunu bir kartta test edemediğimiz için iki yolla doğruladık. Birincisi, aynı nesne dosyalarını Unicorn Engine ile Cortex-M4 Thumb kodu olarak çalıştırıp Python'daki referans modeliyle karşılaştırmak. Aşağıdaki betik, `rb_yaz` ve `rb_oku` fonksiyonlarını sanal bir Cortex-M4 üzerinde çağırır, her yazma ve okumadan sonra tampon durumunu referans modelle karşılaştırır.

```python
# -*- coding: utf-8 -*-
"""Cortex-M4 (Thumb) kodunu Unicorn ile calistirir, Python modeliyle
karsilastirir. Kesme cercevesi (NVIC) emule EDILMEZ; yalnizca kesme
govdesi ve ana dongu kodu calisir.
Kullanim: python unicorn_kisa.py emu.bin emu.elf
"""
import random
import subprocess
import sys
from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS,
                     UC_PROT_ALL)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_SP, UC_ARM_REG_LR)

FLASH, RAM = 0x08000000, 0x20000000
SENTINEL = 0x08000F00          # donus adresi: burada durulur
NM = "arm-none-eabi-nm"        # PATH'te olmali

bin_yolu, elf_yolu = sys.argv[1], sys.argv[2]
sembol = {}
for satir in subprocess.run([NM, "-n", elf_yolu], capture_output=True,
                            text=True).stdout.splitlines():
    p = satir.split()
    if len(p) == 3:
        sembol[p[2]] = int(p[0], 16)

uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
uc.mem_map(FLASH, 0x00100000, UC_PROT_ALL)
uc.mem_map(RAM, 0x00020000, UC_PROT_ALL)
uc.mem_write(FLASH, open(bin_yolu, "rb").read())

def cagir(ad, r0=0, r1=0):
    """Thumb fonksiyonunu cagir, R0'daki donus degerini dondur."""
    uc.reg_write(UC_ARM_REG_SP, RAM + 0x1FFF0)
    uc.reg_write(UC_ARM_REG_R0, r0)
    uc.reg_write(UC_ARM_REG_R1, r1)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
    uc.mem_write(SENTINEL, b"\x00\xbf")          # nop
    uc.emu_start(sembol[ad] | 1, SENTINEL, count=20000)
```

```python
    return uc.reg_read(UC_ARM_REG_R0)

def oku32(adr):
    return int.from_bytes(uc.mem_read(adr, 4), "little")

class Model:
    """Referans: 16 yuvali, 15 elemanli SPSC tampon."""
    def __init__(self):
        self.veri, self.bas, self.kuy, self.dusen = [0] * 16, 0, 0, 0

    def yaz(self, b):
        s = (self.kuy + 1) & 15
        if s == self.bas:
            self.dusen += 1
            return 0
        self.veri[self.kuy], self.kuy = b, s
        return 1

    def oku(self):
        if self.bas == self.kuy:
            return None
        b = self.veri[self.bas]
        self.bas = (self.bas + 1) & 15
        return b

def test_rastgele(tohum, adim=3000):
    rnd = random.Random(tohum)
    m, rb, tmp = Model(), sembol["g_rb"], sembol["g_rb"] + 0x40
    uc.mem_write(rb, b"\x00" * 28)
    hata = 0
    for _ in range(adim):
        if rnd.random() < 0.55:
            b = rnd.randrange(256)
            cagir("adc_isr_govde", b)          # ISR govdesi
            m.yaz(b)
        else:
            r = cagir("rb_oku", rb, tmp)       # ana dongu
```

```python
            b = m.oku()
            if (b is None) != (r == 0):
                hata += 1
            elif b is not None and uc.mem_read(tmp, 1)[0] != b:
                hata += 1
        if (oku32(rb), oku32(rb + 4), oku32(rb + 24)) != \
           (m.bas, m.kuy, m.dusen):
            hata += 1
    return hata, m.dusen

if __name__ == "__main__":
    rb = sembol["g_rb"]
    uc.mem_write(rb, b"\x00" * 28)
    dizi = [cagir("rb_yaz", rb, k) for k in range(16)]
    print("16 yazma sonucu:", dizi)
    print("bas, kuyruk, dusen =", oku32(rb), oku32(rb + 4),
          oku32(rb + 24))
    for tohum in (1, 2, 3):
        hata, dusen = test_rastgele(tohum)
        print("tohum=%d hata=%d dusen=%d" % (tohum, hata, dusen))
    ps = sembol["g_paylasilan"]
    uc.mem_write(ps, b"\x00" * 4)
    cagir("kritik_artir", 1000)
    print("kritik_artir(1000) -> %d" % oku32(ps))
```

Betiği, derlenmiş `emu.bin` ve sembol tablosu ile çalıştırdığında:

```term
$ python unicorn_kisa.py emu.bin emu.elf
16 yazma sonucu: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
bas, kuyruk, dusen = 0 15 1
tohum=1 hata=0 dusen=338
tohum=2 hata=0 dusen=340
tohum=3 hata=0 dusen=364
kritik_artir(1000) -> 1000
```

Bu çıktı şunu gösterir: 16 yazmadan 15'i kabul edilir ve 16. düşürülür (tampon 15 elemanlıdır, bir yuva boş bırakılır); üç farklı rastgele dizide (tohum 1, 2, 3) hiçbir uyuşmazlık yoktur; kritik bölge ile 1000 kez artırılan sayaç 1000 olur. Bu bir **emülasyon** kanıtıdır: kodun Thumb komutları doğru çalışıyor, ama kesmenin donanımsal giriş ve çıkışı burada yoktur.

**Kritik bölge.** Ana döngüde bir değişkeni artırırken ISR aynı değişkene dokunabilirse, kayıp güncelleme olur. Bunu bir ayrık model ile görelim. Ana kod `g = g + 1` ifadesini üç mikro-işlemle yapar: yükle (LOAD), artır (ADD), yaz (STORE). ISR de aynı işlemi yapar. Altı mikro-işlemin 20 olası sırası vardır; her birini deniyoruz.

```python
# -*- coding: utf-8 -*-
"""Ana dongu ile kesme isleyicisi arasinda paylasilan sayac yarisi.

Her iki taraf  g = g + 1  ifadesini uc mikro-islemle yapar:
  LOAD (g'yi yazmaca al), ADD (+1), STORE (geri yaz).
Iki dizinin 20 olasi sirasi tek tek sinanir. Bu, donanim olcumu
degil, mikro-islem duzeyinde ayrik bir modeldir.
"""
from itertools import combinations

def calistir(sira, g0=0):
    """sira: 'M' (ana kod) ve 'I' (kesme) harflerinden bir dizi.
    Her harf, o tarafin bir sonraki mikro-islemini calistirir."""
    g = g0
    yazmac = {"M": 0, "I": 0}
    adim = {"M": 0, "I": 0}
    for taraf in sira:
        k = adim[taraf]
        if k == 0:
            yazmac[taraf] = g                  # LOAD
        elif k == 1:
            yazmac[taraf] += 1                 # ADD
        else:
            g = yazmac[taraf]                  # STORE
        adim[taraf] += 1
    return g

def tum_siralar():
    """6 konumdan 3'u 'M' olacak sekilde C(6,3) = 20 sira."""
    for konum in combinations(range(6), 3):
        sira = ["I"] * 6
        for k in konum:
            sira[k] = "M"
        yield "".join(sira)
```

```python
if __name__ == "__main__":
    print("== Kilitsiz: kesme her yerde girebilir ==")
    sonuc = {}
    for sira in tum_siralar():
        sonuc.setdefault(calistir(sira), []).append(sira)
    for v in sorted(sonuc):
        print("son deger = %d : %d sira" % (v, len(sonuc[v])))
    print("kaybolan siralar:")
    for s in sonuc.get(1, []):
        print("  ", s)
    print("== PRIMASK: ana kodun 3 adimi bolunmez ==")
```

```term
$ python yaris_ayrik.py
== Kilitsiz: kesme her yerde girebilir ==
son deger = 1 : 18 sira
son deger = 2 : 2 sira
kaybolan siralar:
   MMIMII
   MMIIMI
   MMIIIM
   MIMMII
   MIMIMI
   MIMIIM
   MIIMMI
   MIIMIM
   MIIIMM
   IMMMII
   IMMIMI
   IMMIIM
   IMIMMI
   IMIMIM
   IMIIMM
   IIMMMI
   IIMMIM
   IIMIMM
== PRIMASK: ana kodun 3 adimi bolunmez ==
MMMIII -> 2
IIIMMM -> 2
```

Yirmi sıradan yalnızca ikisi doğru sonucu (2) verir: ana kod işini bitirdikten sonra ISR çalışırsa ya da tam tersi. Geri kalan 18 sırada iki işlem örtüşür ve bir güncelleme kaybolur. Bu, bir hata ayıklama oturumunda hiç görünmeyebilir, çünkü kesme her zaman aynı sırada gelmez; iş yükü değiştikçe sıra değişir. Bölüm 6'daki "heisenbug" fikri burada da geçerlidir.

Çözüm, `g = g + 1` ifadesini bir **kritik bölgeye** almaktır: bu üç mikro-işlem arasına kesme girememelidir. Cortex-M'de bunu `PRIMASK` yazmacıyla yaparız. Bu kodu, derlenmiş olarak Unicorn ile doğruladığımız `kritik_artir` fonksiyonunda görüyorsun:

```c

/* Kritik bolge: PRIMASK ile paylasilan sayaci guvenli artir */
static inline uint32_t primask_kaydet(void)
{
    uint32_t p;
    __asm volatile("mrs %0, primask\n\t"
                   "cpsid i" : "=r"(p) :: "memory");
    return p;
}

static inline void primask_geri(uint32_t p)
{
    __asm volatile("msr primask, %0" :: "r"(p) : "memory");
}

void kritik_artir(uint32_t n)
{
    for (uint32_t i = 0; i < n; i++) {
        uint32_t p = primask_kaydet();
        g_paylasilan = g_paylasilan + 1u;
        primask_geri(p);
    }
}
```

`primask_kaydet` önce eski değeri okuyup `cpsid i` ile kesmeleri kapatır; `primask_geri` ise eski değeri geri yazar. Eski değeri geri yazmak önemlidir: kritik bölge bir başka kritik bölgenin içindeyse, dış bölgeyi bozmamak için kesmeleri açmamalıyız. Bu, Bölüm 27'deki kilitlerin iç içe kullanımına benzer bir disiplindir.

PRIMASK, her yapılandırılabilir kesmeyi kapatır. Oysa çoğu zaman yalnızca belirli bir öncelik aralığını kapatmak yeterlidir. Bu durumda BASEPRI kullanılır: `BASEPRI` belirli bir değerin üstündeki (daha az önemli) kesmeleri maskeler, daha önemli kesmeler çalışmaya devam eder. FreeRTOS, kendi çekirdek kritik bölgelerinde bunu yapar ve yalnızca kendi API'sini çağıran kesmelerin önceliğini sınırlar (Kod Okuma'da göreceksin).

::: dikkat
ISR içinde şunları yapma. `printf` ve benzeri stdio fonksiyonları iç kilit kullanır ve yeniden girişli değildir; ana döngü o kilidi tutarken kesme bunu çağırırsa sistem kilitlenir (genel bilgi). `malloc` çalışma zamanında belirsiz süre alır ve bellek tahsis kilidini kullanabilir; Bölüm 7'de gördüğümüz gibi ISR içinde dinamik bellek yerine sabit boyutlu tampon kullan. `HAL_Delay` uyur gibi görünse de `uwTick` değişkenini SysTick kesmesinde artırır; SysTick'ten daha yüksek öncelikli bir ISR içinde çağrılırsa değişken hiç artmaz ve bekleme sonsuza kadar sürer (genel bilgi). Uzun döngüler ve mutex beklemeleri de ISR içinde yasaktır.
:::

**Bayrak + ertelenmiş iş.** ISR yalnızca bir bayrağı kaldırır ve veriyi tampona koyar; ana döngü o bayrağa bakar ve işi yapar. EV Dashboard'u düşünelim: 200 ms'de bir ölçüm yapmak için bir zamanlayıcı kesmesi her 200 ms'de `flag = 1` yapar ve ana döngü bu bayrağı görünce Daly ve Kelly'den veri okur. Kesme işleyicisi kısa kalır, ölçüm süresi ana döngüde tahmin edilebilir olur. Bu desen, Şekil 44.9'da "zamanlayıcı tetikli" mimarinin temelidir.

## 44.7 Kesme gecikmesi ve titreşim (jitter)

Bir kesmenin "ne kadar hızlı" olduğunu iki sayıyla anlatırız. **Gecikme (latency)**, olayın gelişi ile işleyicinin ilk komutunun çalışması arasındaki süredir. **Titreşim (jitter)** ise bu gecikmenin her olayda aynı olmamasıdır: ortalama 12 çevrim olan bir gecikmede bazı olaylar 12, bazıları 40 çevrim sürebilir. Gerçek zamanlı sistemde ikinci sayı genellikle birinciden daha önemlidir: bir ölçüm döngüsü her seferinde aynı aralıkla çalışmak zorundaysa, titreşim doğrudan kontrol kalitesini bozar.

Bir kartta bu süreyi ölçmenin klasik yolu, işleyicinin giriş ve çıkışında bir GPIO pinini değiştirip osiloskopla pin sinyalinin kenarları arasındaki farkı okumaktır (genel bilgi). Bu yöntem, işleyicinin kendi ölçümünü yapmasından daha doğrudur, çünkü ölçüm kodu süreye karışmaz. Bu bölümde bu tür bir kart ölçümü yapamadık; bunun yerine iki ölçüm kaynağı kullandık ve ikisini birbirinden ayırarak okuyoruz.

Birinci kaynak, 44.5'teki **benzetimdir**. Rastgele yük altında 300 000 çevrim boyunca ADC kesmesinin gecikmesi, tohum 44 ile üretilmiş bir dağılım verir. Bu, modelin varsayımlarıyla birlikte okunmalıdır. İkinci kaynak, WSL2 üzerinde Linux `setitimer` ile yapılan bir **ana bilgisayar ölçümüdür**: periyodik bir sinyal (SIGALRM) üretilir ve ana döngü her sinyali yakalayıp zamanını kaydeder. Bu ölçüm bir mikrodenetleyici değildir; Linux çekirdeğinin zamanlaması, sanal makinenin donanım katmanı ve diğer süreçler de sonucu etkiler. Yine de titreşimin "tipik" bir görünümünü verir: ortalama doğru, ama dağılım bir kuyruk taşıyor.

Ölçüm programı, sinyal işleyicisinde yalnızca bir sayaç artırır (Bölüm 26'daki async-signal-safe kuralı), zamanı ana döngüde alır:

```c
/* jitter.c - setitimer ile periyodik SIGALRM olcumu.
 * Bu bir ANA BILGISAYAR (Linux / WSL2) olcumudur, MCU degil.
 * Isleyici yalnizca sayaci artirir (async-signal-safe kural).
 * Kullanim: ./jitter <ornek_sayisi> <periyot_us> */
#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t sayac = 0;

static void isleyici(int sig)
{
    (void)sig;
    sayac++;
}

static long long ns_simdi(void)
{
    struct timespec t;

    clock_gettime(CLOCK_MONOTONIC, &t);
    return (long long)t.tv_sec * 1000000000LL + t.tv_nsec;
}
```

```c
int main(int argc, char **argv)
{
    int n = argc > 1 ? atoi(argv[1]) : 2000;
    int us = argc > 2 ? atoi(argv[2]) : 1000;
    long long *zaman = malloc(sizeof(long long) * (size_t)(n + 1));
    struct sigaction sa = {0};
    struct itimerval it = {0};
    int k = 0, son = 0;

    if (!zaman) return 1;
    sa.sa_handler = isleyici;
    sigaction(SIGALRM, &sa, NULL);
    it.it_interval.tv_usec = us;
    it.it_value.tv_usec = us;
    setitimer(ITIMER_REAL, &it, NULL);

    zaman[k++] = ns_simdi();
    while (k <= n) {
        pause();                      /* SIGALRM gelene kadar uyu */
        if (sayac != son) {           /* ana dongude damgala */
            son = sayac;
            zaman[k++] = ns_simdi();
        }
    }
    it.it_value.tv_usec = 0;          /* zamanlayiciyi durdur */
    it.it_interval.tv_usec = 0;
    setitimer(ITIMER_REAL, &it, NULL);

    printf("aralik_us\n");
    for (int i = 1; i <= n; i++)
        printf("%.3f\n", (zaman[i] - zaman[i - 1]) / 1000.0);
    free(zaman);
    return 0;
}
```

Ölçümü şöyle çalıştırdık. Derleme WSL içinde, `gcc` ile yapıldı; süreç tek bir çekirdeğe (`taskset -c 3`) sabitlendi:

```term
$ gcc -O2 -Wall -Wextra -std=c11 jitter.c -o jitter
```

```term
$ taskset -c 3 ./jitter 3000 1000 > jitter_1ms.csv
```

Çıkan dosya 3000 aralık değeri içerir (her biri mikrosaniye cinsinden). Özet istatistikleri şu betikle hesapladık:

```python
# -*- coding: utf-8 -*-
"""jitter.c ciktisinin ozet istatistikleri (aralik, mikrosaniye).
Kullanim: python jitter_istatistik.py jitter_1ms.csv 1000
"""
import statistics as st
import sys

satirlar = open(sys.argv[1], encoding="utf-8").read().split()[1:]
hedef = float(sys.argv[2])
xs = sorted(float(s) for s in satirlar)
n = len(xs)

def yuzdelik(q):
    return xs[int(q * (n - 1))]

print("ornek sayisi      : %d" % n)
print("ortalama          : %.3f us" % st.mean(xs))
print("standart sapma   : %.3f us" % st.pstdev(xs))
print("hedef periyot    : %.1f us" % hedef)
print("medyan (p50)     : %.3f us" % yuzdelik(0.5))
print("p99              : %.3f us" % yuzdelik(0.99))
print("en kucuk / buyuk : %.3f / %.3f us" % (xs[0], xs[-1]))
```

```term
$ python jitter_istatistik.py jitter_1ms.csv 1000
ornek sayisi      : 3000
ortalama          : 1000.015 us
standart sapma   : 46.422 us
hedef periyot    : 1000.0 us
medyan (p50)     : 999.084 us
p99              : 1132.013 us
en kucuk / buyuk : 449.743 / 1582.848 us
```

Sonuçta hedef periyot 1000 µs iken ortalama `1000,015` µs çıktı; standart sapma `46,4` µs ve 99. yüzdelik `1132` µs'dir. En kısa aralık `449,7` µs, en uzun `1582,8` µs'dir. Kısa aralık ile uzun aralık birbirini dengeler: geç uyanan bir sinyal, bir sonraki aralığı kısaltır. Bu, aynı zamanda bir ölçüm yanlılığıdır, çünkü zamanı ana döngüde aldığımız için uyanma gecikmesi de ölçülen aralığa girer. Şekil 44.7'nin sağ panelinde bu dağılımı görürsün.

Sol panel benzetimin gecikme dağılımını gösterir. Yoklama (P = 200 çevrim) gecikmeleri 0 ile 199 arasında düzgün dağılmıştır; kesme (ADC) gecikmelerinin büyük kısmı 12 çevrimde yoğunlaşır. Kuyruk ise şundan gelir: ADC en yüksek öncelikte olsa da kendi önceliğindeki bir örneği kesemez; önceki ADC işleyicisi bitene kadar (ve kuyruk zinciriyle birlikte) bekler. Bu yüzden 12'nin çok üstündeki değerler, o an çalışan bir ADC işleyicisinin kalan süresinden ve sıradaki örneklerden oluşur.

![Şekil 44.7: Solda benzetim: yoklama (P = 200) ile ADC kesmesinin gecikme histogramları, 300 000 çevrim, tohum 44. Sağda WSL2 üzerinde setitimer ile 3000 örnek: aralığın 1000 µs'den sapması.](gorseller/b44_kesme_gecikme_dagilim.png)

Titreşimin kaynaklarını sıralayalım. (1) **Kritik bölgeler:** PRIMASK ile kapatılmış bir bölgeye denk gelen kesme, bölge bitene kadar bekler. (2) **Daha öncelikli işleyiciler:** kesme, daha önemli bir işleyici bitene kadar başlayamaz. (3) **Bellek bekleme durumları:** flash'ten komut okumak, işlemcinin hızına göre birkaç çevrim bekletebilir; bu, işleyicinin ilk komutlarının gecikmesini değiştirir (genel bilgi). (4) **Önbellek:** Cortex-M7 gibi önbellekli çekirdeklerde, işleyicinin kodu önbellekte değilse ilk çalıştırma yavaşlar (genel bilgi). (5) **Veri yolu yarışı:** DMA ya da başka bir ana aygıt aynı belleğe erişirken işlemci bekleyebilir (genel bilgi). (6) **Ölçüm yapısı:** ölçümü işleyicinin içinde yaparsan, ölçümün kendisi gecikmeyi uzatır. Bu yüzden titreşim sayısını bir kartta ölçerken işaret pinini mümkün olduğunca erken ve geç yerleştirmek gerekir.

::: not
Titreşimi "azaltmak" için tek bir ayar yoktur. Bir zamanlama garantisi istiyorsan iki şey yapılır: kritik bölgeler mümkün olduğunca kısa tutulur, ve kritik olayların işleyicileri en yüksek önceliğe konur. Her iki adımın da ölçülmesi ve kanıtlanması gerekir; bu, Bölüm 44.10'daki en kötü durum analizinin de girdisidir.
:::

## 44.8 Zamanlayıcılar: SysTick, genel amaçlı timer, yakalama, PWM ve watchdog

Zamanlayıcılar, işlemci saatinin sayılmış ve belirli değerlerde olay üreten donanım sayaçlarıdır. Bir mikrodenetleyicide birkaç çeşidi vardır ve her biri farklı bir iş yapar.

**SysTick.** Her Cortex-M çekirdeğinde bulunan 24 bitlik, aşağı sayan bir sayaçtır. Sayaç `LOAD` değerinden başlar, sıfıra ulaşınca bir kesme üretir ve `LOAD` değerine geri döner. Bu nedenle bir periyot `LOAD + 1` sayımdır. 168 MHz'de 1 ms'lik bir tick için `LOAD = 168 000 − 1 = 167 999` olmalıdır. Bu değer 24 bitlik sınırın (2^24 − 1 = 16 777 215) içindedir. SysTick kesmesi, HAL kütüphanesinde `HAL_IncTick()` çağrısıyla `uwTick` sayacını artırır ve `HAL_Delay` bu sayacı izler. Yani EV Dashboard'daki `HAL_Delay(200)` çağrısı, SysTick kesmesinin artırdığı `uwTick` değerini bekleyen bir döngüdür. Bu döngü işlemciyi uyutmaz; meşgul bekleme yapar (HAL'ın bu sürümde düşük güçlü bir bekleme kullandığını varsayma, kendi sürümünü kontrol et).

Aşağıdaki betik, bu bölümde kullandığımız EV Dashboard süre hesabını da içerir: UART zaman aşımlarını toplar, SysTick `LOAD` değerini hesaplar ve bağımsız izleyici (IWDG) zaman aşımını verir.

```python
# -*- coding: utf-8 -*-
"""EV Dashboard ana dongusunun en kotu sure analizi (main.c).

HAL_UART_Transmit (100 ms) ve HAL_UART_Receive (200 ms) zaman asimli
cagrilardir; HAL_Delay(200) dongunun sonunda gelir. Dongu periyodu
= govde suresi + 200 ms. Sabit 200 ms periyot DEGILDIR.
"""
# (cagri, zaman asimi ms): Daly x3 (T+R), Kelly (T+R), RPi (T)
CAGRILAR = [
    ("Daly 1 (T)", 100), ("Daly 1 (R)", 200),
    ("Daly 2 (T)", 100), ("Daly 2 (R)", 200),
    ("Daly 3 (T)", 100), ("Daly 3 (R)", 200),
    ("Kelly (T)", 100), ("Kelly (R)", 200),
    ("RPi (T)", 100),
]
GECIKME_MS = 200

def uart_suresi_ms(bayt, baud):
    """8N1 cerceve: bayt basina 10 bit (genel bilgi)."""
    return bayt * 10 / baud * 1000.0

if __name__ == "__main__":
    govde = sum(z for _, z in CAGRILAR)
    print("En kotu govde suresi    : %d ms" % govde)
    print("En kotu dongu periyodu  : %d ms" % (govde + GECIKME_MS))
    print("13 bayt @115200 baud    : %.3f ms"
          % uart_suresi_ms(13, 115200))
    print("13 bayt @9600 baud      : %.3f ms"
          % uart_suresi_ms(13, 9600))
    f_hclk = 168_000_000
    load = f_hclk // 1000 - 1
    print("SysTick LOAD (1 ms)     : %d" % load)
    print("LOAD siniri (2^24 - 1)  : %d" % (2 ** 24 - 1))
    print("gercek tick suresi      : %.6f ms"
          % ((load + 1) / f_hclk * 1000))
    for pr, rl in ((4, 1249), (6, 4095)):
        t = 4 * 2 ** pr * (rl + 1) / 32000
        print("IWDG PR=%d RL=%d        : %.3f s" % (pr, rl, t))
```

```term
$ python ev_dongu.py
En kotu govde suresi    : 1300 ms
En kotu dongu periyodu  : 1500 ms
13 bayt @115200 baud    : 1.128 ms
13 bayt @9600 baud      : 13.542 ms
SysTick LOAD (1 ms)     : 167999
LOAD siniri (2^24 - 1)  : 16777215
gercek tick suresi      : 1.000000 ms
IWDG PR=4 RL=1249        : 2.500 s
IWDG PR=6 RL=4095        : 32.768 s
```

Çıktının ilk iki satırı, EV Dashboard'un en kötü durumunu verir. Ana döngü gövdesinde (`main.c` içindeki `Daly_BataryaGuncelle`, `Kelly_MotorGuncelle` ve `RaspberryPi_Gonder`) toplam dokuz UART çağrısı vardır; her çağrının zaman aşımı, iletim için 100 ms ve alım için 200 ms'dir. Bunların hepsi zaman aşımına uğrarsa gövde en fazla 1300 ms sürer. `HAL_Delay(200)` bu gövdenin **bittikten sonra** gelir; yani döngü periyodu sabit 200 ms değil, gövde süresi artı 200 ms'dir. Normal koşulda BMS yanıt verirse gövde birkaç milisaniye sürebilir (baud hızına ve yanıt süresine bağlı); ama en kötü durumda periyot 1,5 saniyeye çıkabilir. Bu, gerçek bir kod incelemesi bulgusudur: döngünün "200 ms'de bir" olduğu yorumu doğru değildir, "en az 200 ms ara" olduğu doğrudur.

**Genel amaçlı zamanlayıcılar.** Bir STM32'deki TIM birimleri şu zincirle çalışır: giriş saati (`f_tim`), bir önbölücü (`PSC`), bir sayıcı (`CNT`), bir otomatik yeniden yükleme değeri (`ARR`) ve bir karşılaştırma değeri (`CCR`). Sayıcı her `PSC + 1` saat darbesinde bir artar; `ARR` değerine ulaşınca sıfırlanır ve bir **güncelleme olayı** üretir. Bu olaydan bir kesme ya da DMA isteği çıkabilir. Güncelleme frekansı şöyledir:

`f_güncelleme = f_tim / ((PSC + 1) × (ARR + 1))`

Şekil 44.8'in üst panelinde bu zincir görülüyor. Bir hedef frekans verildiğinde `PSC` ve `ARR` çiftini bulmak bir tamsayı arama problemidir: çarpım `f_tim / f_hedef` değerine eşit (ya da çok yakın) olmalıdır, `PSC` ve `ARR` ise 16 bit sınırında olmalıdır. Aşağıdaki betik, bu aramayı yapar ve hata yüzdesini verir. Zamanlayıcı saati, APB hattına ve bölücü ayarına bağlıdır; burada varsayılan olarak 84 MHz (genel bilgi) kullandık, kartının değerine göre değiştir.

```python
# -*- coding: utf-8 -*-
"""Zamanlayici icin PSC/ARR bulucu ve PWM hesabi.

f_guncelleme = f_tim / ((PSC + 1) * (ARR + 1))
gorev (%)    = CCR / (ARR + 1)        (kenar hizali PWM)
f_tim: sayacin giris saati (kartina gore kontrol et). 16 bit:
PSC ve ARR en fazla 65535.
"""
import math

F_TIM = 84_000_000
MAKS = 65535

def adaylar(hedef_hz, f_tim=F_TIM, n=4):
    """Her PSC icin en yakin ARR; hataya gore ilk n aday."""
    liste = []
    for psc in range(MAKS + 1):
        arr1 = round(f_tim / (hedef_hz * (psc + 1)))
        if 1 <= arr1 <= MAKS + 1:
            arr = arr1 - 1
            gercek = f_tim / ((psc + 1) * (arr + 1))
            hata = abs(gercek - hedef_hz) / hedef_hz * 100.0
            liste.append((psc, arr, hata, gercek))
    liste.sort(key=lambda x: (round(x[2], 9), x[0]))
    return liste[:n]

def en_iyi(hedef_hz, f_tim=F_TIM):
    """En dusuk hata; esitlikte en kucuk PSC."""
    return adaylar(hedef_hz, f_tim, n=1)[0]

def ccr_hesap(gorev, arr):
    ccr = round(gorev * (arr + 1))
    return ccr, ccr / (arr + 1)
```

```python
if __name__ == "__main__":
    print("f_tim = %.0f MHz" % (F_TIM / 1e6))
    print()
    print("== PWM 1 kHz, gorev %37.5 ==")
    psc, arr, hata, gercek = en_iyi(1000)
    print("secilen PSC=%d ARR=%d f=%.3f Hz hata=%.6f %%"
          % (psc, arr, gercek, hata))
    ccr, g = ccr_hesap(0.375, arr)
    print("CCR=%d  gercek gorev=%.4f %%" % (ccr, g * 100))
    print()
    print("== Aday tablosu: 333 Hz (tam bolunmez) ==")
    for psc, arr, h, f in adaylar(333, n=5):
        print("PSC=%5d ARR=%6d f=%.6f Hz hata=%.6f %%"
              % (psc, arr, f, h))
    print()
    print("== Servo: 50 Hz, darbe 1 ms ile 2 ms arasi ==")
    psc, arr, hata, gercek = en_iyi(50)
    print("PSC=%d ARR=%d f=%.4f Hz hata=%.6f %%"
          % (psc, arr, gercek, hata))
    sayim_us = (psc + 1) / F_TIM * 1e6
    print("bir sayim = %.4f us" % sayim_us)
    print("1 ms = %d sayim, 2 ms = %d sayim"
          % (round(1000 / sayim_us), round(2000 / sayim_us)))
    print()
    print("== Frekans - cozunurluk takasi ==")
    for f in (50, 1000, 5000, 20000, 50000):
        psc, arr, hata, gercek = en_iyi(f)
        print("f=%6d Hz PSC=%5d ARR=%6d adim=%6d ~%.1f bit"
              % (f, psc, arr, arr + 1, math.log2(arr + 1)))
```

```term
$ python zamanlayici_hesap.py
f_tim = 84 MHz

== PWM 1 kHz, gorev %37.5 ==
secilen PSC=1 ARR=41999 f=1000.000 Hz hata=0.000000 %
CCR=15750  gercek gorev=37.5000 %

== Aday tablosu: 333 Hz (tam bolunmez) ==
PSC=    3 ARR= 63062 f=333.000333 Hz hata=0.000100 %
PSC=    5 ARR= 42041 f=333.000333 Hz hata=0.000100 %
PSC=    6 ARR= 36035 f=333.000333 Hz hata=0.000100 %
PSC=    8 ARR= 28027 f=333.000333 Hz hata=0.000100 %
PSC=   10 ARR= 22931 f=333.000333 Hz hata=0.000100 %

== Servo: 50 Hz, darbe 1 ms ile 2 ms arasi ==
PSC=27 ARR=59999 f=50.0000 Hz hata=0.000000 %
bir sayim = 0.3333 us
1 ms = 3000 sayim, 2 ms = 6000 sayim

== Frekans - cozunurluk takasi ==
f=    50 Hz PSC=   27 ARR= 59999 adim= 60000 ~15.9 bit
f=  1000 Hz PSC=    1 ARR= 41999 adim= 42000 ~15.4 bit
f=  5000 Hz PSC=    0 ARR= 16799 adim= 16800 ~14.0 bit
f= 20000 Hz PSC=    0 ARR=  4199 adim=  4200 ~12.0 bit
f= 50000 Hz PSC=    0 ARR=  1679 adim=  1680 ~10.7 bit
```

Çıktı üç şeyi gösterir. 1 kHz ve %37,5 görev için `PSC = 1`, `ARR = 41999` çıkar; `PSC = 0` için `ARR = 83999` 16 bit sınırını aşar, bu yüzden geçersizdir. 333 Hz için hiçbir çift tam sonuç vermez; en iyi aday bile `0,0001 %` hata verir. Servo için 50 Hz'de `PSC = 27`, `ARR = 59 999` seçilir ve her sayım `0,333 µs`'dir, bu da 1 ms için 3000, 2 ms için 6000 sayım demektir.

**PWM.** Kenar hizalı PWM modunda çıkış, sayıcı `CCR`'den küçük olduğu sürece yüksek olur. Görev oranı `CCR / (ARR + 1)` ile verilir. Bu, sayıcının her turunda `CCR` sayımı kadar yüksek kalması demektir. 1 kHz'lik bir PWM'de `ARR + 1 = 42 000` sayım olduğu için %37,5 görev `CCR = 15 750` ile elde edilir; `15 750 / 42 000 = 0,375`.

Servo motorları 50 Hz (20 ms periyot) ister ve darbe genişliği genellikle 1 ms ile 2 ms arasındadır. Bu, görev oranlarının %5 ile %10 arasında olması demektir. Şekil 44.8'in orta panelinde iki darbe gösterilmiştir.

Bir son bağlantı: frekans arttıkça çözünürlük düşer. `ARR` en fazla 65 535 olabildiğinden, daha yüksek frekansta sayım adımı azalır. Şekil 44.8'in alt panelinde 50 Hz'de yaklaşık 15,9 bit, 50 kHz'de yaklaşık 10,7 bit çözünürlük görürsün. Motor sürücüsü için 20 kHz PWM seçen bir tasarımcı, görev oranında yaklaşık 12 bitlik bir çözünürlük elde eder.

**Giriş yakalama (input capture).** Bir dış sinyalin kenarlarının zamanını sayıcıyla kaydetmek için kullanılır. İki ardışık yükselen kenarın zaman farkı periyodu, periyodun tersi de frekansı verir. Bir enkoder ya da Hall sensörü darbeleri, bir motorun dönüş hızını bu şekilde ölçer: `RPM = 60 × f / p` (burada `f` darbe frekansı, `p` tur başına darbe sayısıdır; genel bilgi). EV Dashboard'daki hız hesabı da bu prensibe dayanabilir; yalnızca `Kelly_MotorGuncelle` içinde hız, sürücünün kendi UART paketinden okunuyor, bir sensörden değil.

**Bağımsız izleyici (watchdog).** Yazılımın takılıp takılmadığını izlemek için bir zamanlayıcıdır. Ana döngü belirli aralıklarla izleyiciyi "besler" (yeniden yükler); besleme gelmezse izleyici sistemi sıfırlar. IWDG (bağımsız izleyici) kendi düşük frekanslı saatiyle (LSI, nominal 32 kHz, genel bilgi) çalışır ve zaman aşımı şöyledir:

`T = 4 × 2^PR × (RL + 1) / f_LSI`

Burada `PR` önbölücü seçimi, `RL` yeniden yükleme değeridir. Yukarıdaki betik iki örnek verdi: `PR = 4`, `RL = 1249` için `2,5 s`; `PR = 6`, `RL = 4095` için `32,768 s`. LSI frekansı üretim ve sıcaklıkla değiştiği için gerçek zaman aşımı nominalden sapabilir (genel bilgi); güvenlik kritik bir tasarımda izleyici süresi, kart üzerinde ölçülmelidir.

Kritik nokta şudur: **izleyici beslemesi ana döngüde yapılmalıdır, kesme işleyicisinde değil.** Eğer izleyici bir zamanlayıcı kesmesinin içinde besleniyorsa, ana döngü takılsa bile kesme çalışmaya devam eder ve izleyici hiç tetiklenmez. Yani izleyici tam da kontrol etmesi gereken hatayı kaçırır. Ana döngüde besleme, döngünün gerçekten ilerlediğinin kanıtıdır.

Pencereli izleyici (WWDG) ise besleme zamanını bir pencereye sınırlar: çok erken beslemek de bir hata sayılır (genel bilgi). Bu, bir döngünün takılmasını değil, döngünün çok hızlı "sahte" besleme yapmasını da yakalar.

**Düşük güç ve kesmeyle uyanma.** Kesme sisteminin bir yan faydası, işlemciyi uyutmaktır. `WFI` komutu işlemciyi bir kesme gelene kadar bekletir (genel bilgi). Sistem uyur, yalnızca bir zamanlayıcı ya da UART kesmesi onu uyandırır. Bir tick ile uyanıp bir ölçüm yapan ve tekrar uyuyan bir tasarım, sürekli yoklama yapan bir tasarıma göre çok daha az enerji harcar. Uyku modlarının ayrıntıları (`Sleep`, `Stop`, `Standby`) üreticiye ve kartın güç yapılandırmasına bağlıdır; bu bölümde mod isimlerinin ötesine geçmiyoruz.

![Şekil 44.8: Üstte genel amaçlı zamanlayıcı zinciri (f_tim, PSC, CNT, ARR, CCR ve çıkış). Altta solda 1 kHz ve %37,5 görev; sağda 50 Hz servo darbeleri (1 ms ve 2 ms). En altta PWM frekansına karşı çözünürlük takası.](gorseller/b44_zamanlayici_pwm.png)

## 44.9 Zamanlama mimarileri: süper döngüden işbirlikçi zamanlayıcıya

Donanım zamanlayıcılarını ve kesmeleri öğrendik. Şimdi asıl soruya gelelim: bu parçaları bir programın içinde nasıl düzenlersin? Gömülü yazılımda üç temel mimari vardır ve her birinin bedeli farklıdır.

**Süper döngü.** En basit yapı, her şeyi sırayla yapan sonsuz bir döngüdür. EV Dashboard'un bugünkü `main` fonksiyonu tam olarak budur. Şekil 44.9'un A panelinde gördüğün gibi, döngünün süresi bütün görevlerin sürelerinin toplamıdır. Bir görev uzarsa, diğer görevlerin periyodu da uzar; kimse bunu kendiliğinden fark etmez. Üstelik her görevin "ne zaman" çalışacağı döngünün hangi noktasında olduğuna bağlıdır, bu da titreşim demektir.

**Zamanlayıcı tetikli döngü.** Bir zamanlayıcı kesmesi periyodik olarak bir bayrak kaldırır; ana döngü bayrağa bakar, bayrak varsa işi yapar, yoksa `wfi` ile uyur. Burada periyot zamanlayıcıya aittir ve kesme gecikmesi dışında titreşim yoktur. EV Dashboard için tasarım fikri şöyledir: 200 ms'lik bir TIM kesmesi yalnızca bayrağı kaldırır; UART alım kesmesi gelen baytları bir halka tampona (44.6) yazar; ana döngü bayrağı görünce BMS ve motor sorgularını yapar. Bu yapıda bile bir sorgunun (ör. 300 ms sürebilen bir UART yanıtı) bir sonraki bayrağı kaçırabileceğini unutma: bunu bir zaman aşımı ve durum makinesiyle sınırlamak gerekir. Bu tasarımı kendi başına yapmak Kendin Yap Projesi 2'nin konusudur.

**İşbirlikçi zamanlayıcı.** Süper döngüyle RTOS arasında bir ara adım, bir görev zamanlayıcısının kendisini yazmaktır. Her görev bir periyot ve bir vade taşır; tick kesmesi vadesi gelen görevin bayrağını kaldırır; ana döngü bayrağı görünce görevi **bitirene kadar** çalıştırır. "İşbirlikçi" sözcüğü, bir görevin kendi isteğiyle CPU'yu bırakmasından gelir: kimse onu kesemez. Aşağıdaki C programı bu fikri host üzerinde deterministik olarak uygular: tick sayılır, görevler simüle edilir.

```c
/* isbirlikci.c - isbirlikci (cooperative) zamanlayici benzetimi.
 * Tick isleyicisi bir sayaci artirir ve vadesi gelen gorevin
 * bayragini kaldirir. Ana dongu bayragi gorurse gorevi bitirene
 * kadar calistirir: hicbir gorev kesilmez.
 * Gecikme = gorevin basladigi tick - vade tick'i. */
#include <stdio.h>

#define GOREV_SAYISI 3
#define TOPLAM_TICK  400

typedef struct {
    const char *ad;
    int periyot;           /* tick */
    int is_suresi;         /* tick: bitene kadar CPU'yu tutar */
    int vade;              /* bir sonraki vade tick'i */
    volatile int bayrak;   /* tick isleyicisi yazar */
    int en_buyuk_gecikme;
    int calisma;
} gorev_t;

static gorev_t g[GOREV_SAYISI] = {
    {"A_hizli",  10,  1, 10, 0, 0, 0},
    {"B_orta",   25,  2, 25, 0, 0, 0},
    {"C_uzun",   50, 30, 50, 0, 0, 0},   /* uzun is */
};

static volatile int tick;

/* Tick "kesmesi": her tick'te vadesi gelen gorevi isaretler */
static void tick_isleyici(void)
{
    tick++;
    for (int i = 0; i < GOREV_SAYISI; i++) {
        if (tick >= g[i].vade) g[i].bayrak = 1;
    }
}
```

```c
int main(void)
{
    int simdi = 0;

    while (simdi < TOPLAM_TICK) {
        tick_isleyici();
        simdi = tick;
        for (int i = 0; i < GOREV_SAYISI; i++) {
            if (!g[i].bayrak) continue;
            /* baslangic gecikmesi */
            int gecikme = tick - g[i].vade;
            if (gecikme > g[i].en_buyuk_gecikme)
                g[i].en_buyuk_gecikme = gecikme;
            /* isbirlikci: gorev bitene kadar tick'ler sayilir */
            for (int k = 0; k < g[i].is_suresi; k++)
                tick_isleyici();
            g[i].bayrak = 0;
            g[i].calisma++;
            g[i].vade += g[i].periyot;
        }
    }
    printf("gorev      periyot is_suresi calisma max_gecikme\n");
    for (int i = 0; i < GOREV_SAYISI; i++)
        printf("%-10s %6d %9d %7d %11d\n", g[i].ad, g[i].periyot,
               g[i].is_suresi, g[i].calisma, g[i].en_buyuk_gecikme);
    return 0;
}
```

Programın çıktısı:

```term
$ ./isbirlikci
gorev      periyot is_suresi calisma max_gecikme
A_hizli        10         1      40          24
B_orta         25         2      16          10
C_uzun         50        30       8           3
```

Çıktı, işbirlikçi tasarımın temel sorununu gösterir. `C_uzun` görevi tek bir çalışmada 30 tick sürer. Bu süre boyunca `A_hizli` (periyodu 10 tick) ve `B_orta` görevleri başlayamaz. `A_hizli` görevinin en büyük gecikmesi `24` tick'tir: yani vadesi geldiğinde 24 tick beklemek zorunda kalmıştır, bu da periyodun iki katından fazladır. Görevi parçalayıp her parçadan sonra yeniden sıraya girmesini sağlarsan gecikme azalır. Ama bu kez de görevin iş mantığı parçalanır; sürekli elle yapılan bu bölme, RTOS'un çözdüğü problemin ta kendisidir: **görevi kesebilen bir zamanlayıcı**.

Bu tablo, Bölüm 26.7'deki Round Robin ve MLFQ simülasyonlarını hatırlatıyor olmalı. Fark şu: orada işletim sistemi süreçleri zaman dilimi ile kesiyordu; burada bir görev kendi kararıyla CPU'yu bırakana kadar kesilemez.

Son olarak EV Dashboard'a dönelim. Üç mimari için karar tablosu:

| Mimari | Periyot kontrolü | Uzun görev etkisi | Karmaşıklık | Savunma kullanımı |
|---|---|---|---|---|
| Süper döngü | Yok (toplam süreye bağlı) | Herkesi geciktirir | Düşük | Basit, küçük sistemler |
| Zamanlayıcı tetikli | Donanım zamanlayıcısı | Ana döngüde gecikir, kesme etkilenmez | Orta | Sık kullanılan, dikkatli tasarım |
| İşbirlikçi zamanlayıcı | Yazılım tick | Görev bitene kadar herkes bekler | Orta | Kısa, öngörülebilir görevler |
| Öncelikli kesintili (RTOS) | Tick + öncelik | Yalnızca daha önemli görevler gecikir | Yüksek | Büyük, karmaşık sistemler |

![Şekil 44.9: Üç mimari. A: süper döngü, her şey sırayla; B: zamanlayıcı kesmesi bayrak kaldırır, ana döngü uyur; C: RTOS, tick ve öncelik ile en yüksek hazır görevi seçer, bağlam değişimi PendSV ile yapılır.](gorseller/b44_superdongu_rtos.png)

## 44.10 RTOS'a giriş: öncelikli kesintili zamanlama ve zanaat sınırları

Gerçek zamanlı işletim sistemi (RTOS), görevleri öncelikleriyle yönetir ve zamanlayıcı tick'inde en yüksek öncelikli **hazır** görevi seçer. Bir görev, bir kuyruk ya da semafor beklediğinde **engelli (blocked)** olur ve CPU'yu bırakır. Görev durumları genel olarak dörttür: **çalışan (running)**, **hazır (ready)**, **engelli (blocked)** ve **askıda (suspended)**; FreeRTOS bu adları kullanır (genel bilgi). Bir görev daha önemli bir görev hazır olduğunda kesilir ve yeni görev bağlam değişimiyle çalışır. Bu, Bölüm 26'daki çok görevli zamanlamanın gerçek zamanlı biçimidir.

FreeRTOS'un temel kavramları şunlardır (genel bilgi): **görev (task)**, kendi yığınına sahip bir fonksiyon; **kuyruk (queue)**, görevler arası veri aktarımı; **semafor**, bir kaynak ya da olay sayacı; **mutex**, karşılıklı dışlama. Mutex'in önemli bir özelliği **öncelik kalıtımıdır** (priority inheritance): düşük öncelikli bir görev bir mutex'i tutarken yüksek öncelikli bir görev onu beklerse, düşük öncelikli görevin önceliği geçici olarak yükselir. Bu, Bölüm 27.13'te gördüğümüz öncelik terslemesini (priority inversion) önler. Binary semafor ile mutex arasındaki fark da burada yatar: yalnızca mutex kalıtım sağlar (genel bilgi).

**WCET: en kötü durum yürütme süresi.** Bir görevin çalışma süresinin üst sınırıdır (Worst-Case Execution Time). Gerçek zamanlı bir sistemde "çoğu zaman 2 ms" bir garanti değildir; garanti, bütün yollar için verilmiş bir üst sınırdır. WCET iki şekilde bulunur: ölçümle (test çalıştırmaları; ama her yolu kapsadığını kanıtlayamazsın) ya da statik analizle (kod yapısından, önbellek ve boru hattı modelinden). Bu bölümde yalnızca üst sınır kavramını kullanıyoruz; statik WCET analizi ayrı bir uzmanlık alanıdır (genel bilgi).

**Rate Monotonic Scheduling (RMS).** Liu ve Layland, 1973'te her görevin periyodu ile önceliğinin ters orantılı olduğu sabit öncelikli bir zamanlama için bir kullanım sınırı kanıtladılar. `n` görevlik bir sistemde görevlerin toplam kullanımı `U = Σ C_i / T_i` bu sınırın altındaysa, bütün son teslimler karşılanır:

`U ≤ n (2^(1/n) − 1)`

Bu sınır `n` arttıkça `ln 2 ≈ 0,693`'e yaklaşır. `n = 1` için 1,0; `n = 2` için `0,8284`; `n = 3` için `0,7798`'dir. Bu bir **yeterli koşuldur**, gerekli değil: sınırın üstündeki bir sistem de zamanında çalışabilir. Kesin testi **yanıt süresi analizi (RTA)** yapar: `R_i = C_i + Σ_{j yüksek öncelik} ⌈R_i / T_j⌉ C_j` denklemini, `R_i` değeri yakınsayana kadar çözer; `R_i ≤ T_i` ise görev uygundur.

**EDF.** En erken son teslimli (Earliest Deadline First) zamanlamada, her an son teslimi en yakın hazır iş çalışır. Son teslim `T`'ye eşit ve görevler kesilebilirse, EDF için `U ≤ 1` hem yeter hem gerekli koşuldur. Bölüm 18.5'te EDF'nin gecikmeyi en küçükleyen açgözlü kural olduğunu gördük; burada ise kesilebilir periyodik görevlerle, bu sonucun gerçek zamanlı biçimini kullanıyoruz.

Aşağıdaki betik RM sınırını, RTA'yı, bir tam sayı zaman benzetimini ve EDF'yi karşılaştırır. Rastgele kümeler UUniFast yöntemiyle üretilir (Bini ve Buttazzo, 2005; genel bilgi).

```python
# -*- coding: utf-8 -*-
"""RM ve EDF zamanlanabilirlik analizi (tam sayi zamanli).

Gorev (C, T): islem suresi C, periyot T, son teslim D = T.
  U = toplam(C/T)
  RM siniri (Liu & Layland 1973): n(2^(1/n) - 1)  (yeterli)
  RTA: R = C_i + toplam ceil(R/T_j) * C_j  (j: daha yuksek oncelik)
  EDF (kesilebilir, D = T): U <= 1 yeter ve gerekir.
"""
import csv
import math
import random

def rms_siniri(n):
    return n * (2 ** (1.0 / n) - 1)

def kullanim(gorevler):
    return sum(c / t for c, t in gorevler)

def rta(gorevler):
    """Periyoda gore sirala (RM). Her gorev icin yanit suresi."""
    sirali = sorted(gorevler, key=lambda g: g[1])
    sonuc = []
    for i, (c, t) in enumerate(sirali):
        r = c
        while True:
            yeni = c + sum(math.ceil(r / tj) * cj
                           for cj, tj in sirali[:i])
            if yeni == r:
                break
            r = yeni
            if r > t:                           # yakinsamadi
                break
        sonuc.append((c, t, r if r <= t else None))
    return sonuc

def rta_uygun(gorevler):
    return all(r is not None for _, _, r in rta(gorevler))
```

```python
def simule(gorevler, politika):
    """Kesilebilir RM ya da EDF. Doner: (kacirilan, dilimler)."""
    ufuk = math.lcm(*[t for _, t in gorevler])
    isler, kacan, dilim = [], 0, []
    for t in range(ufuk):
        for idx, (c, p) in enumerate(gorevler):
            if t % p == 0:
                isler.append([c, t + p, idx])   # kalan, son, no
        for j in isler:
            if j[0] > 0 and t >= j[1]:
                kacan += 1                      # son teslim kacti
                j[0] = 0
        isler = [j for j in isler if j[0] > 0]
        etiket = None
        if isler:
            if politika == "RM":
                sec = min(isler,
                          key=lambda j: (gorevler[j[2]][1], j[1]))
            else:
                sec = min(isler,
                          key=lambda j: (j[1], gorevler[j[2]][1]))
            sec[0] -= 1
            etiket = sec[2]
        if dilim and dilim[-1][2] == etiket and dilim[-1][1] == t:
            dilim[-1] = (dilim[-1][0], t + 1, etiket)
        else:
            dilim.append((t, t + 1, etiket))
    for j in isler:                             # donem sonu kacaklari
        if j[0] > 0 and ufuk >= j[1]:
            kacan += 1
    return kacan, dilim
```

```python
def rastgele_kumeler(tohum, adet=1000, n=3):
    """UUniFast (Bini & Buttazzo 2005) ile rastgele kume."""
    rnd = random.Random(tohum)
    kumeler = []
    for _ in range(adet):
        kalan = rnd.uniform(0.6, 1.0)
        us = []
        for i in range(1, n):
            sonraki = kalan * rnd.random() ** (1.0 / (n - i))
            us.append(kalan - sonraki)
            kalan = sonraki
        us.append(kalan)
        kumeler.append([(max(1, round(u * t)), t) for u, t in
                        ((u, rnd.randint(4, 40)) for u in us)])
    return kumeler
```

```python
if __name__ == "__main__":
    ornek = [(1, 4), (2, 6), (3, 12)]
    print("== Ornek 1:", ornek)
    print("U = %.4f  RM siniri = %.4f" % (kullanim(ornek),
                                         rms_siniri(3)))
    print("RTA:", rta(ornek))
    print("RM kacirilan:", simule(ornek, "RM")[0])
    ornek2 = [(2, 5), (4, 7)]
    print("== Ornek 2:", ornek2, "U = %.4f" % kullanim(ornek2))
    print("RTA:", rta(ornek2))
    print("RM kacirilan:", simule(ornek2, "RM")[0])
    print("EDF kacirilan:", simule(ornek2, "EDF")[0])
    print("== 1000 rastgele kume, n=3, tohum=44 ==")
    sayac = {"RM siniri": 0, "RTA": 0, "EDF U<=1": 0, "sim RM": 0,
             "RTA-sim ters": 0, "EDF sim": 0, "EDF-U ters": 0}
    for g in rastgele_kumeler(44):
        u, ok_rta = kullanim(g), rta_uygun(g)
        ok_sim = simule(g, "RM")[0] == 0
        sayac["RM siniri"] += u <= rms_siniri(3)
        sayac["RTA"] += ok_rta
        sayac["EDF U<=1"] += u <= 1.0
        sayac["sim RM"] += ok_sim
        sayac["RTA-sim ters"] += ok_rta != ok_sim
        ok_edf = simule(g, "EDF")[0] == 0
        sayac["EDF sim"] += ok_edf
        sayac["EDF-U ters"] += ok_edf != (u <= 1.0)
    for k, v in sayac.items():
        print("%-13s %4d / 1000" % (k, v))
    with open("b44_rms_zaman.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["senaryo", "bas", "son", "gorev"])
        for ad, g, pol in (("RM_ornek1", ornek, "RM"),
                           ("RM_ornek2", ornek2, "RM"),
                           ("EDF_ornek2", ornek2, "EDF")):
            for bas, son, et in simule(g, pol)[1]:
                w.writerow([ad, bas, son,
                            "" if et is None else et + 1])
```

```term
$ python rms_analiz.py
== Ornek 1: [(1, 4), (2, 6), (3, 12)]
U = 0.8333  RM siniri = 0.7798
RTA: [(1, 4, 1), (2, 6, 3), (3, 12, 10)]
RM kacirilan: 0
== Ornek 2: [(2, 5), (4, 7)] U = 0.9714
RTA: [(2, 5, 2), (4, 7, None)]
RM kacirilan: 1
EDF kacirilan: 0
== 1000 rastgele kume, n=3, tohum=44 ==
RM siniri      390 / 1000
RTA            811 / 1000
EDF U<=1       932 / 1000
sim RM         811 / 1000
RTA-sim ters     0 / 1000
EDF sim        932 / 1000
EDF-U ters       0 / 1000
```

Çıktıdan üç sonuç çıkar. Birincisi, RM sınırı 1000 rastgele kümenin yalnızca `390`'ında yeterlidir, RTA ise `811`'inde uygundur: sınır oldukça muhafazakârdır. İkincisi, RTA ile zaman benzetimi her kümede aynı sonucu verir (`RTA-sim ters = 0`); bu, RTA hesabımızın doğruluğunu gösterir. Üçüncüsü, EDF benzetimi `U ≤ 1` koşuluyla birebir aynı sonucu verir (`EDF-U ters = 0`). Bu sayılar, tohum `44` ile yeniden üretilebilir.

Şekil 44.10, iki küme için zaman çizelgesini gösterir: birinci küme RM ile sorunsuz çalışır; ikinci küme RM'de `t = 7`'de bir son teslim kaçırır, EDF ise aynı kümeyi kaçırmadan çalıştırır. Bu sonucu Çözümlü Örnek 4'te elle izleyeceksin.

![Şekil 44.10: RM ve EDF zaman çizelgeleri. Birinci satır, RM ile uygun bir üçlü küme. İkinci satır, RM ile (2,5) ve (4,7) kümesi: t=7'de ikinci görevin ilk işi son teslimini kaçırır. Üçüncü satır, aynı küme EDF ile sorunsuz çalışır.](gorseller/b44_rms_zaman.png)

**Gerçek dünya ve güvenlik.** Bir İHA uçuş kontrolcüsünde iç döngüler (tutum ve motor kontrolü) yüksek frekansta, navigasyon ve telemetri ise daha yavaş çalışır (genel bilgi); kesin frekanslar araca ve tasarıma göre değişir. Bu döngülerin hiçbiri "genellikle zamanında" yeterli değildir; kontrol kararının zamanı değişirse kontrol kazancı ve kararlılık bozulabilir. Havacılık yazılımı için DO-178C gibi standartlar, zamanlama davranışının analiz ve kanıtını ister (genel bilgi). Bu nedenle bu bölümdeki hesaplar, bir sistemin "çalıştığını gözlemek" yerine "neden zamanında çalışacağını göstermek" için bir başlangıçtır.

## Çözümlü Örnekler

Aşağıdaki dört örnek, Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntü bul, iyileştir, doğrula. Her örneğin sonunda elle iz sürme tablosu vardır ve örnek, aynı tekniği kullanan bir varyasyon sorusuyla biter. Sorulara cevabı önce kâğıt üzerinde, sonra araçla kontrol ederek vermeni öneririz.

### Örnek 1 (★): 1 kHz PWM ve %37,5 görev için PSC, ARR, CCR

**Adım 1 — Anla.** Girdi: zamanlayıcı saati `f_tim = 84 MHz`, hedef PWM frekansı `1 kHz`, görev oranı `%37,5`. İstenen: `PSC`, `ARR`, `CCR` değerleri, hepsi 16 bit sınırında (en fazla 65 535). Formüller: `f = f_tim / ((PSC + 1)(ARR + 1))` ve `görev = CCR / (ARR + 1)`.

**Adım 2 — Örnekle.** Önce küçük bir sayısal durum deneyelim. Eğer `PSC = 0` olursa `ARR + 1 = 84 000` olur. Bu, 16 bitlik `ARR` için fazladır (en fazla 65 536 sayım). Demek ki `PSC` en az 1 olmalı.

**Adım 3 — Kaba çöz.** Her `PSC` için `ARR + 1 = 84 000 / (PSC + 1)` hesaplayıp tamsayı olup olmadığına ve 65 536'nın altında kalıp kalmadığına bakabiliriz. Bu bir arama problemidir; kaba yol budur.

**Adım 4 — Örüntü.** `84 000 = 2^5 × 3 × 5^3 × 7`. `PSC + 1` bu sayının bir böleni olduğunda `ARR + 1` tam sayı çıkar. Bölen olan `PSC + 1` değerleri arasında 16 bit sınırını sağlayan en küçük olanı seçmek, en fazla sayım adımını (çözünürlüğü) verir. Çünkü `ARR + 1` ne kadar büyükse, görev oranı o kadar ince ayarlanabilir.

**Adım 5 — İyileştir.** En küçük geçerli `PSC` değeri `1`'dir (`PSC + 1 = 2`). Bu durumda `ARR + 1 = 42 000`, yani `ARR = 41 999`. Görev için `CCR = 0,375 × 42 000 = 15 750` olur; bu bir tamsayıdır, yani görev oranı tam olarak `%37,5` tutar.

**Adım 6 — Doğrula.** Elle iz tablosu:

| PSC | PSC + 1 | ARR + 1 = 84 000 / (PSC+1) | 16 bit'e sığar mı? | Gerçek f | Hata |
|---|---|---|---|---|---|
| 0 | 1 | 84 000 | hayır (> 65 536) | — | — |
| 1 | 2 | 42 000 | evet | 1000,000 Hz | 0 |
| 2 | 3 | 28 000 | evet | 1000,000 Hz | 0 |
| 3 | 4 | 21 000 | evet | 1000,000 Hz | 0 |

Tablo, `PSC = 1` ve `PSC = 2` ve `PSC = 3` için frekansın tam tutduğunu gösterir, ama en küçük `PSC` en fazla sayımı verir. Aracın çıktısı da aynı sonucu doğrular:

```term
$ python zamanlayici_hesap.py
f_tim = 84 MHz

== PWM 1 kHz, gorev %37.5 ==
secilen PSC=1 ARR=41999 f=1000.000 Hz hata=0.000000 %
CCR=15750  gercek gorev=37.5000 %
```

Çıktıdaki `CCR=15750` ve `gercek gorev=37.5000 %` satırı, elle yaptığımız hesabı onaylar.

**Bunu AI'sız yazabilir misin?** 20 kHz'lik bir PWM ve %25 görev oranı için `PSC`, `ARR` ve `CCR` değerlerini bul. Önce `84 MHz / 20 kHz = 4200` sayısının bölenlerini düşün; sonra `CCR`'yi `0,25 × (ARR + 1)` ile hesapla. Cevabını `zamanlayici_hesap.py` içindeki `en_iyi(20000)` çağrısıyla karşılaştır.

### Örnek 2 (★★): İç içe kesme zaman çizelgesi

**Adım 1 — Anla.** Düşük öncelikli bir UART işleyicisi (`40` çevrim gövde) çalışırken, daha yüksek öncelikli bir ADC kesmesi (`15` çevrim gövde) `t = 20`'de gelir. Modelin değerleri: `ENTRY = 12`, `EXIT = 10`. Sorular: ADC'nin gecikmesi kaç çevrim, UART'ın gövdesi ne zaman biter? Öncelik kuralı: sayı küçüldükçe önem artar.

**Adım 2 — Örnekle.** Önce basit bir durum: UART `t = 0`'da gelsin ve hiç başka kesme olmasın. Yığınlama `0..11`, gövde `12..51` (40 çevrim), bitiş `52`. Bu bizim referansımızdır.

**Adım 3 — Kaba çöz.** Kaba bir tahmin: ADC'nin 20'de gelip hemen başlaması, yani gecikme `0`. Bu yanlış olur; çünkü işlemci UART'ın yığınını henüz tamamlamıştır ve ADC'yi kabul etmek için yeniden yığınlama yapması gerekir. Kaba çözümde `ENTRY` maliyetini unuttuk.

**Adım 4 — Örüntü.** Yığın LIFO çalışır: ADC, UART'ı keser ve bitince UART kaldığı yerden devam eder. Her kesme girişi `ENTRY`, her çıkış `EXIT` maliyeti taşır. İki kesme için toplam ek maliyet `ENTRY + ENTRY + EXIT = 12 + 12 + 10`, ama UART'ın gövdesi bütün bunlardan sonra kalan işini tamamlar. Kısaca: UART'ın bitiş zamanı = UART gövdesi (40) + UART yığınlama (12) + ADC yığınlama (12) + ADC gövdesi (15) + çıkış (10) = `89`.

**Adım 5 — İyileştir.** İç içe kesmenin maliyeti, kesmelerin sayısıyla birlikte artar. Burada kuyruk zinciri ile bir kazanç olmaz, çünkü ADC bir **kesme** ile girer, bir bitiş ile değil. Kazancı Senaryo B'de görürüz (44.5). Tasarımda yapılacak iyileştirme, kritik olmayan UART işinin uzunluğunu kısaltmak ya da onu ana döngüye taşımaktır (44.6).

**Adım 6 — Doğrula.** Elle iz tablosu, benzetimin Senaryo A'sı ile karşılaştırılmıştır:

| Zaman (çevrim) | Faz | Aktif işleyici | Yığın (üstten alta) | Açıklama |
|---|---|---|---|---|
| 0–11 | E | UART | — | UART yığınlanıyor |
| 12–19 | H | UART | UART | UART gövdesinin 8 çevrimi |
| 20–31 | E | ADC | UART (kesilmiş) | ADC kabul, yığınlama |
| 32–46 | H | ADC | ADC, UART | ADC gövdesi (15 çevrim) |
| 47–56 | X | — | ADC, UART | çıkış, ADC kalktı |
| 57–88 | H | UART | UART | UART'ın kalan 32 çevrimi |

Benzetimin gecikme çıktısı, elle hesabı doğrular:

```term
$ python nvic_sim.py
== Senaryolar (ENTRY=12 EXIT=10 TAIL=6) ==
-- ic_ice --
  UART   kabul gecikmesi =  12 cevrim
  ADC    kabul gecikmesi =  12 cevrim
```

ADC'nin gecikmesi `12`, UART'ın gecikmesi `12` (ilk kabul) çıkar; bitiş zamanı tabloda `89` (`88` son çevrim). Eşleşme tamdır.

**Bunu AI'sız yazabilir misin?** Aynı UART (40 çevrim) ve ADC (15 çevrim) olaylarında, ADC bu kez UART'ın 30. çevriminde gelsin. UART'ın bitiş zamanını ve ADC'nin gecikmesini elle hesapla. Sonra `nvic_sim.py` içindeki `simule` fonksiyonunu bu senaryoyla çağırarak doğrula.

### Örnek 3 (★★): ISR ile ana döngü arasında paylaşılan sayaç yarışı

**Adım 1 — Anla.** Ana döngü ve bir kesme işleyicisi, aynı `g` değişkenini `g = g + 1` ile bir kez artırıyor. İki artış sonucunda `g = 2` olmasını bekleriz. Soru: hangi sıralarda bu beklenti tutmaz?

**Adım 2 — Örnekle.** Her taraf üç mikro-işlem yapar: LOAD (yazmaca al), ADD (artır), STORE (geri yaz). Bir sıra, altı harften oluşur; `M` ana koddan, `I` kesmeden bir adım. Bir örnek sıra `MIMMII`: önce ana kodun LOAD'u, sonra kesmenin LOAD'u, ardından ana kodun ADD ve STORE'u, en sonunda kesmenin ADD ve STORE'u.

**Adım 3 — Kaba çöz.** "İki artış var, sonuç 2 olmalı" diye düşünürsek her sıra doğru görünür. Bu kaba çözüm yanlış: artışlar ayrık değildir, ikisi de aynı eski değeri okuyabilir.

**Adım 4 — Örüntü.** Eğer bir taraf işini tamamen bitirmeden diğeri başlamazsa (`MMMIII` ya da `IIIMMM`), sonuç 2 olur. Diğer her sırada, bir tarafın LOAD'u ile STORE'u arasına diğerinin LOAD'u girer ve bir güncelleme kaybolur. Yirmi sıradan 18'i kayıplıdır.

**Adım 5 — İyileştir.** Ana kodun üç mikro-işlemini bir kritik bölgeye almak (PRIMASK ile kesmeleri susturmak) yalnızca iki kesmesiz sırayı bırakır, yani kayıp olmaz. Ayrıca tek üretici-tek tüketici tamponu (44.6) gibi, her indeksin yalnızca bir tarafça yazıldığı yapılar da bu problemi ortadan kaldırır.

**Adım 6 — Doğrula.** `MIMMII` sırası için elle iz tablosu (her satır bir mikro-işlem; `rM` ana kodun, `rI` kesmenin yazmacı):

| Adım | Taraf | İşlem | rM | rI | g |
|---|---|---|---|---|---|
| 1 | M | LOAD | 0 | — | 0 |
| 2 | I | LOAD | 0 | 0 | 0 |
| 3 | M | ADD | 1 | 0 | 0 |
| 4 | M | STORE | 1 | 0 | 1 |
| 5 | I | ADD | 1 | 1 | 1 |
| 6 | I | STORE | 1 | 1 | 1 |

Son değer `1`'dir: bir artış kaybolmuştur. Tabloyu tüm 20 sıra için çalıştıran betiğin çıktısı şöyledir:

```term
$ python yaris_ayrik.py
== Kilitsiz: kesme her yerde girebilir ==
son deger = 1 : 18 sira
son deger = 2 : 2 sira
kaybolan siralar:
   MMIMII
   MMIIMI
   MMIIIM
   MIMMII
   MIMIMI
   MIMIIM
   MIIMMI
   MIIMIM
   MIIIMM
   IMMMII
   IMMIMI
   IMMIIM
   IMIMMI
   IMIMIM
   IMIIMM
   IIMMMI
   IIMMIM
   IIMIMM
== PRIMASK: ana kodun 3 adimi bolunmez ==
MMMIII -> 2
IIIMMM -> 2
```

Kritik bölge çözümünü Unicorn ile çalıştırılmış gerçek kodda da doğruladık: `kritik_artir(1000)` çağrısı 1000 sonucunu verdi (44.6). Bu kanıt, iki kanıtın birleşimidir: model yanlış sıraları gösterir, emülasyon düzeltilmiş kodun gerçekten doğru çalıştığını gösterir.

**Bunu AI'sız yazabilir misin?** Ana kod iki kez artırıyor (her artış üç mikro-işlem), kesme bir kez artırıyor. Toplam dokuz mikro-işlemlik (`3 + 3 + 3`) bir sıra kümesi düşünürsek, kaç sıra vardır? Hepsi sayılabilir mi? Kaç tanesi doğru sonuç verir? (İpucu: doğru sonuçlar yalnızca iki artışın hiç örtüşmediği sıralardır.)

### Örnek 4 (★★★): Üç görevlik RM zamanlanabilirliği ve kaçırılan son teslim

**Adım 1 — Anla.** İki küme inceleyeceğiz. Küme 1: `(C, T) = (1, 4), (2, 6), (3, 12)`; küme 2: `(2, 5), (4, 7)`. Her görev için son teslim `T`'dir. Sorular: RM ile her küme zamanında çalışır mı? EDF ne yapar?

**Adım 2 — Örnekle.** Hiperperiyot (periyotların en küçük ortak katı): küme 1 için `lcm(4, 6, 12) = 12`, küme 2 için `lcm(5, 7) = 35`. Zaman benzetimi bu aralıkları tarar.

**Adım 3 — Kaba çöz.** Küme 1'in kullanımı `U = 1/4 + 2/6 + 3/12 = 0,8333`. RM sınırı üç görev için `0,7798`. Kaba sonuç: `U` sınırı aştığı için RM başarısız olur.

**Adım 4 — Örüntü.** RM sınırı yeterli koşuldur, gerekli değildir; sınırı aşan bir küme yine de uygun olabilir. Kesin test RTA'dır: `R_i = C_i + Σ ⌈R_i / T_j⌉ C_j`. Küme 1 için görev 1 `R = 1`; görev 2 için `R = 2 + ⌈R/4⌉ × 1` denklemi `R = 3`'te yakınsar; görev 3 için `R = 3 + ⌈R/4⌉ + 2⌈R/6⌉` denklemi `R = 10`'da yakınsar (`10 ≤ 12`). Demek ki küme 1 uygundur. Küme 2 için görev 2: `R = 4 + ⌈R/5⌉ × 2`; `R = 4` için `6`, `R = 6` için `8` çıkar, `8 > 7`: yakınsamaz, uygun değildir.

**Adım 5 — İyileştir.** Küme 2'de RM'nin kaçırdığı son teslimi EDF çözebilir: `U = 2/5 + 4/7 = 0,9714 < 1` olduğu için EDF bu kümeyi uygun çalıştırır. Dolayısıyla RM ile EDF arasında bir seçim yapılabilir: RM, yalnızca sabit öncelik istenen ve mühendislik açısından öngörülebilir olan sistemlerde; EDF, son teslime göre dinamik öncelik gerektiğinde ve `U ≤ 1` koşulu sağlandığında.

**Adım 6 — Doğrula.** Küme 2 için RM çizelgesi (birinci görev `(2,5)`, ikinci `(4,7)`):

| Zaman | RM'de çalışan | Kalan iş | Olay |
|---|---|---|---|
| 0–2 | görev 1 | — | ilk iş bitti |
| 2–5 | görev 2 | 4 → 1 | görev 2 ilk işini 3 birim yaptı |
| 5–7 | görev 1 (ikinci iş) | — | görev 1 öncelikli, görev 2 bekledi |
| 7 | — | görev 2 ilk işinde 1 birim kaldı | **son teslim (t = 7) kaçtı** |

EDF çizelgesi aynı kümede:

| Zaman | EDF'te çalışan | Gerekçe |
|---|---|---|
| 0–2 | görev 1 | son teslim 5 < 7 |
| 2–6 | görev 2 | ilk iş 4 birimi tamamladı, son teslim 7 |
| 6–8 | görev 1 (ikinci iş) | son teslim 10 |

Benzetim aynı sonucu verir: RM ile bir kaçırılan son teslim, EDF ile sıfır. Araç çıktısı:

```term
$ python rms_analiz.py
== Ornek 1: [(1, 4), (2, 6), (3, 12)]
U = 0.8333  RM siniri = 0.7798
RTA: [(1, 4, 1), (2, 6, 3), (3, 12, 10)]
RM kacirilan: 0
== Ornek 2: [(2, 5), (4, 7)] U = 0.9714
RTA: [(2, 5, 2), (4, 7, None)]
RM kacirilan: 1
EDF kacirilan: 0
== 1000 rastgele kume, n=3, tohum=44 ==
```

Çıktıdaki `RTA: [(2, 5, 2), (4, 7, None)]` satırı, görev 2'nin RTA ile uygun olmadığını doğrular (`None`). Son satırda `EDF kacirilan: 0` ile RM'nin `1` kaçırılan son teslimi karşılaştırabilirsin.

**Bunu AI'sız yazabilir misin?** Üç görev `(1, 3), (1, 4), (2, 8)` için `U`'yu hesapla. RM sınırını karşılaştır. RTA'yı elle çöz: görev 3 için `R = 2 + ⌈R/3⌉ + ⌈R/4⌉`. Yakınsıyor mu, `R ≤ 8` mi? Son olarak EDF'in durumunu yaz.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kesme işleyicisinin nasıl yazılacağını, tamponun nasıl korunacağını ve zamanlayıcının hangi değerlerle kurulacağını kendi kararlarınla vermen gerekiyor. Derleyiciyi, Python'u ve bu bölümün benzetim betiklerini kullanabilirsin; ama tasarım kararlarını ve sonuçların yorumunu sen yazmalısın.
:::

### Proje 1 (★★): Host üzerinde öncelikli kesintili mini zamanlayıcı

**Amaç.** İşletim sistemi çekirdeğinin temel parçası olan öncelikli, kesintili bir zamanlayıcıyı host üzerinde simüle etmek. Bu projede gerçek bir kesme yoktur; tick bir döngü sayacıdır. Yine de önceliklerin, gecikmelerin ve bir mutex'te öncelik kalıtımının nasıl davrandığını gözlemleyebilirsin.

**Beklenen davranış.** Program en az üç görev tanımlar; her görevin önceliği, periyodu ve her çalışmada harcadığı tick sayısı vardır. Her tick'te zamanlayıcı, hazır görevler arasından en yüksek öncelikli olanı seçer ve bir tick çalıştırır; yüksek öncelikli bir görev hazır olduğunda düşük öncelikli olan kesilir. Görevler `gecikme(n)` ile bekleyebilir ve bir `semafor` ile diğer görevleri bekletebilir. Bir `mutex` alındığında, bekleyen daha yüksek öncelikli bir görev varsa tutan görevin önceliği geçici olarak yükselir. Program sonunda her görevin zaman çizelgesini (hangi tick'te hangi görev çalıştı) yazdırır.

**Önerilen yaklaşım (ipucu).** Her görev için bir `gorev_t` yapısı tanımla: ad, öncelik, durum (hazır, çalışıyor, engelli, askıda), kalan iş süresi, bekleme sayacı. Tick fonksiyonunda önce bekleme sayaçlarını azalt, sonra hazır olan en yüksek öncelikli görevi seç. Bir görev bloke olduğunda durumunu değiştir ve zamanlayıcıyı yeniden çalıştır. Kalıtım için mutex'e sahibi ve bekleyenler listesi ekle; sahibin önceliğini, bekleyenlerin en yükseğine yükselt ve mutex bırakıldığında eski önceliği geri koy. Bölüm 27.13'teki Mars Pathfinder senaryosunu tohum olarak kullanabilirsin: üç görev (yüksek, orta, düşük) ve bir mutex.

**Başarı kriterleri.**
- Kalıtım kapalıyken ve açıkken aynı senaryoyu iki kez çalıştır; yüksek öncelikli görevin mutex bekleme süresi farkını tablo olarak göster. Kalıtım açıkken süre belirgin biçimde kısalmalıdır.
- Zaman çizelgesi çıktısında her tick'in hangi göreve ait olduğu görünmeli ve toplam tick sayısı, görevlerin toplam işiyle tutarlı olmalı.
- Programı `-fsanitize=address,undefined` ile derle (WSL'de `gcc`); hiçbir uyarı ya da hata çıkmamalı.
- Raporda, bu benzetimin gerçek bir kesme ve bağlam değişimi kadar gerçekçi olmadığı üç noktayı açıkça yaz.

### Proje 2 (★★★): EV Dashboard'un kesme güdümlü yeniden tasarımı

**Amaç.** `ev-dashboard/stm32/main.c` dosyasındaki süper döngüyü, zamanlayıcı ve UART kesmeleri ile çalışan bir yapıya dönüştürmek; Cortex-M4 için derlenebilir ve boyutu raporlanmış bir sürüm üretmek.

**Beklenen davranış.** (1) Bir zamanlayıcı kesmesi her 200 ms'de bir bayrak kaldırır ve ana döngü bu bayrağı görünce BMS ve motor sorgularını yapar. (2) UART alım kesmesi gelen baytları 44.6'daki tipte bir halka tamponuna yazar; ana döngü tampondan okur. Tampon dolarsa baytlar sayılarak düşürülür. (3) Bağımsız izleyici (IWDG) yalnızca ana döngüde beslenir. (4) Sorgu zaman aşımı, tek bir sorgunun ana döngüyü bütünüyle kilitlemesini engeller. (5) Derleme `arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -O2 -Wall -Wextra` ile uyarısız tamamlanır ve `arm-none-eabi-size` çıktısı rapora eklenir.

**Önerilen yaklaşım (ipucu).** Önce donanımdan bağımsız bir çekirdek yaz: halka tamponu, bayrak yapısı ve durum makinesi. Bunları host üzerinde test et (Bölüm 39'daki test yaklaşımı). Sonra donanım bağlantısını ekle: `TIM` ve `USART` kesmelerinin vektör tablosundaki isimlerini kullan (44.2), kesme önceliklerini NVIC'te açıkça belirle (44.3). ISR'lerin içinde HAL çağrılarından kaçın; yalnızca bayrak kaldır ve tampona yaz. Zaman aşımlarını HAL çağrılarının parametresiyle değil, durum makinesinin sayacıyla yönet; böylece bir BMS sorgusunun 1,3 saniyelik en kötü durumu ana döngüyü kilitlemez (44.8'deki hesap).

**Başarı kriterleri.**
- Derleme çıktısında uyarı yok; `arm-none-eabi-size` ile `text`, `data`, `bss` değerlerini raporla ve RAM kullanım yüzdesini hesapla.
- Host testlerinde halka tamponu, 1000 rastgele işlemde hiçbir veriyi kaybetmeden ve sırayı bozmadan çalışmalı; dolu tamponda düşen bayt sayısı doğru olmalı.
- Ana döngünün bir sorgu sırasında takılması durumunda izleyicinin sıfırlamaya gittiğini gösteren bir senaryo tarif et (host simülasyonu yeterlidir) ve izleyici süresini Bölüm 44.8'deki formülle hesapla.
- Raporda, 200 ms'nin "tam periyot" olmadığını, ölçülen ya da hesaplanan en kötü periyotla birlikte açıkla.

## Ek Alıştırmalar

1. ★ Olay sıklığı saniyede 100, yoklama periyodu 1 ms ve bir bakış 3 µs sürüyor. Yoklamanın CPU yükünü hesapla. Aynı olaylar kesmeyle işlenirse ve her kesme 22 çevrim ek maliyet taşıyorsa (168 MHz), yükü hesapla. Hangisi daha düşük?
2. ★ Bir kesme işleyicisinin içinde `printf` çağırmanın neden tehlikeli olduğunu iki farklı nedenle açıkla. (Mülakat)
3. ★ 72 MHz çekirdek saatinde 1 ms'lik bir SysTick tick'i için `LOAD` değerini bul. Değer 24 bit sınırına sığıyor mu?
4. ★★ Kapasitesi 8 olan bir halka tamponunda (her indeks `% 8` ile sarar) ve tek bir boş yuva bırakma kuralıyla kaç eleman tutulabilir? Boş ile dolu durumunu, indekslerin farkı dışında hangi ek bilgiyle ayırt edersin? (Mülakat)
5. ★★ Kesme girişinde LR yazmacına neden dönüş adresi değil de EXC_RETURN konur? Bu seçimin ISR çıkışında ne gibi bir avantajı var? (Mülakat)
6. ★★ 84 MHz'de 20 kHz'lik bir PWM ve %60 görev için PSC, ARR ve CCR değerlerini bul. Görev oranındaki çözünürlüğü (kaç farklı adım) hesapla.
7. ★★ Bir UART kesmesi bayt geldikçe bir halka tamponuna yazıyor, ana döngü ise her 10 ms'de bir tamponu boşaltıyor. Tampon kapasitesi 64 bayt ve bayt hızı 115 200 baud'da (8N1, bayt başına 10 bit), tampon hangi süreden sonra dolar? Bu hesabı ana döngü boşaltma aralığı ile karşılaştır. (Mülakat yok; uygulamalı.)
8. ★★ Üç görev `(1, 3)`, `(1, 4)`, `(2, 8)` için kullanımı hesapla, RM sınırıyla karşılaştır ve görev 3'ün RTA değerini elle bul. Sonuç uygun mu?
9. ★★★ Bir yüksek öncelikli görev (H), bir orta (M) ve bir düşük öncelikli görev (L) aynı mutex'i kullanıyor. L mutex'i tutarken H bekliyor ve M çalışmaya başlıyor. Öncelik kalıtımı olmadan H'nin bekleme süresini ve kalıtım ile bu sürenin nasıl değiştiğini açıkla. (Mülakat)
10. ★★★ "`volatile` bir senkronizasyon aracı mıdır?" sorusuna tek cümlede hayır demek kolay; neden olduğunu iki farklı mimari (tek çekirdek Cortex-M ve çok çekirdek) üzerinden anlat. (Mülakat)
11. ★★ Bağımsız izleyiciyi bir zamanlayıcı kesmesinin içinde beslemenin hangi hatayı gizlediğini bir örnekle anlat. (Mülakat)
12. ★★★ Bir kayan noktalı kesme işleyicisinde hangi yazmaçlar donanım tarafından, hangileri yazılım tarafından kaydedilir? Genişletilmiş çerçevenin hangi koşulda oluştuğunu ve tembel yığınlamanın bu süreye nasıl etki ettiğini açıkla. (Mülakat)

## Kod Okuma Egzersizi

Bağlam değişiminin Cortex-M üzerindeki gerçek hâlini bir açık kaynak projede okuyalım. FreeRTOS-Kernel'in V11.1.0 sürümünde Cortex-M4F için bağlam değişimini yapan `xPortPendSVHandler` fonksiyonu, `portable/GCC/ARM_CM4F/port.c` dosyasının 505–559. satırları arasındadır. Kaynak: `https://raw.githubusercontent.com/FreeRTOS/FreeRTOS-Kernel/V11.1.0/portable/GCC/ARM_CM4F/port.c`.

Aşağıdaki kesit birebir kopyadır; tek fark, satır sonlarındaki C yorumlarının (`/* ... */`) ve `WORKAROUND_PMU_CM001` ile başlayan koşullu bloğun çıkarılmasıdır. Bu bloğun XMC4000 kartlarındaki bir donanım hatası için olduğunu not düşmek yeterlidir. Assembly komutlarının metni aynen korunmuştur.

```c
void xPortPendSVHandler( void )
{

    __asm volatile
    (
        "   mrs r0, psp                         \n"
        "   isb                                 \n"
        "                                       \n"
        "   ldr r3, pxCurrentTCBConst           \n"
        "   ldr r2, [r3]                        \n"
        "                                       \n"
        "   tst r14, #0x10                      \n"
        "   it eq                               \n"
        "   vstmdbeq r0!, {s16-s31}             \n"
        "                                       \n"
        "   stmdb r0!, {r4-r11, r14}            \n"
        "   str r0, [r2]                        \n"
        "                                       \n"
        "   stmdb sp!, {r0, r3}                 \n"
        "   mov r0, %0                          \n"
        "   msr basepri, r0                     \n"
        "   dsb                                 \n"
        "   isb                                 \n"
        "   bl vTaskSwitchContext               \n"
        "   mov r0, #0                          \n"
        "   msr basepri, r0                     \n"
        "   ldmia sp!, {r0, r3}                 \n"
        "                                       \n"
        "   ldr r1, [r3]                        \n"
```

```c
        "   ldr r0, [r1]                        \n"
        "                                       \n"
        "   ldmia r0!, {r4-r11, r14}            \n"
        "                                       \n"
        "   tst r14, #0x10                      \n"
        "   it eq                               \n"
        "   vldmiaeq r0!, {s16-s31}             \n"
        "                                       \n"
        "   msr psp, r0                         \n"
        "   isb                                 \n"
        "                                       \n"
        #endif
        "                                       \n"
        "   bx r14                              \n"
        "                                       \n"
        "   .align 4                            \n"
        "pxCurrentTCBConst: .word pxCurrentTCB  \n"
        ::"i" ( configMAX_SYSCALL_INTERRUPT_PRIORITY )
    );
}
```

Kesitin mantığı şöyle akar. `mrs r0, psp` ile kesilen görevin yığın işaretçisi alınır. `tst r14, #0x10` komutu, EXC_RETURN'ün bit 4'ünü sınar (44.4'te gördüğün tablo). Bit 4 sıfırsa çerçeve genişletilmiştir, yani görev FPU bağlamını kullanıyordur ve `vstmdbeq` komutu `s16`-`s31` yazmaçlarını da kaydeder. Ardından `r4`-`r11` ile `r14` (EXC_RETURN) yığına itilir ve yeni yığın işaretçisi görevin TCB'sinin ilk alanına yazılır. Sonra `basepri` yazmacı `configMAX_SYSCALL_INTERRUPT_PRIORITY` değerine ayarlanır: bu, FreeRTOS API'sini çağırabilen kesmelerin öncelik sınırıdır; bu sınırın üstündeki kesmeler, zamanlayıcının kritik bölgesi sırasında çalışmaya devam edebilir. `bl vTaskSwitchContext` çağrısı, bir sonraki görevi seçer. `basepri` sıfırlanır, yeni görevin yığın işaretçisi TCB'den okunur, kaydedilmiş yazmaçlar geri yüklenir ve `bx r14` ile yeni görev, EXC_RETURN'ün gösterdiği bağlamda devam eder.

Bu, Bölüm 26.9'daki `switchContext` (MertOS) ile aynı fikirdir: yazmaçları kaydet, yeni bağlamın yığınını yükle, dön. Fark, Cortex-M'de bu geçişin bir **kesme işleyicisi** içinde ve donanımın yığınladığı çerçevenin üstünde yapılmasıdır.

**Sorular — cevaplamadan geçme:**

1. FreeRTOS, `PendSV` işleyicisini genellikle en düşük önceliğe ayarlar (genel bilgi). Bunun nedenini açıkla: bağlam değişimi, başka bir kesme işi bittikten sonra mı, yoksa onu keserek mi yapılmalıdır? Bu işleyici başka bir kesme tarafından kesilirse hangi veri tutarsız kalabilir?
2. `tst r14, #0x10` ile `vstmdbeq r0!, {s16-s31}` komutları neden yalnızca bir FPU bağlamı varken çalışır? Bu koşul olmasaydı ne kaybolurdu?
3. `mov r0, %0` / `msr basepri, r0` çiftinde `%0` yerine hangi değer gelir ve bu değerin `configMAX_SYSCALL_INTERRUPT_PRIORITY` ile ilişkisi nedir? Değer, `FreeRTOSConfig.h` dosyasında nasıl tanımlanır?
4. `stmdb sp!, {r0, r3}` ile `ldmia sp!, {r0, r3}` arasında `bl vTaskSwitchContext` çağrısı var. Bu çağrı sırasında `sp` hangi yığını gösterir ve neden `r0` ile `r3`'ü yığında saklamak zorundayız?
5. `ldmia r0!, {r4-r11, r14}` komutu `r14`'ü yükler. Bu değer dönüş adresi midir, yoksa bir EXC_RETURN midir? Yanıtını 44.4'teki tabloya dayandır.
6. Bu işleyici ile MertOS'taki `isr_common` (`isr_stubs.asm`) arasındaki en önemli üç farkı yaz. Hangisi kayıt sayısını, hangisi yığın yönetimini, hangisi dönüş mekanizmasını etkiler?

## Bölüm Özeti

- Yoklama basit ama CPU'yu meşgul eder ve gecikmesi bakış periyoduna bağlıdır; kesme, olay olduğunda çalışır ve gecikmesi donanım kabul süresine bağlıdır.
- x86'da IDT kapıları ve PIC ile EOI kullanılır; Cortex-M'de vektör tablosu doğrudan kesme numarasıyla indekslenir ve öncelik NVIC içindedir.
- NVIC her kesme için pasif, bekliyor, aktif durumlarını tutar; öncelik değeri küçüldükçe önem artar; PRIMASK, BASEPRI ve FAULTMASK ile maskeleme yapılır.
- Donanım, yığınlama çerçevesini (8 ya da FPU ile 26 sözcük) kendisi kurar; dönüş bilgisi bir EXC_RETURN değeridir ve bit 4 çerçevenin türünü söyler.
- Kuyruk zinciri ve geç gelen kesme, iç içe kesmelerin gecikmesini azaltır; benzetimde kuyruk zinciri 16 çevrim, geç gelen mekanizma 12 çevrim kazandırdı.
- ISR kısa olmalı; ISR ile ana döngü arasında paylaşılan veri, tek üretici-tek tüketici tamponu veya PRIMASK ile kritik bölgede korunmalı; `volatile` bellek sıralaması sağlamaz.
- Zamanlayıcılarda PSC ve ARR seçimi çözünürlük ile frekans arasında takas yapar; izleyici beslemesi ana döngüde yapılmalı ve SysTick `HAL_Delay` gibi kütüphane işlevlerinin bağımlılığı bilinmelidir.
- Süper döngü, zamanlayıcı tetikli döngü, işbirlikçi zamanlayıcı ve RTOS, artan karmaşıklıkta zamanlama mimarileridir; RM sınırı yeterli ama gerekli değildir, RTA kesin testtir ve EDF'de `U ≤ 1` koşulu yeter.

**Sonraki bölümde:** Bu bölümde kesmelerin ve zamanlayıcıların donanım tarafını gördük. Bölüm 45'te, bu kesmelerin asıl veri taşıdığı yolları inceleyeceğiz: UART, SPI, I2C ve CAN. UART alım kesmesinin ve DMA'nın ayrıntısını orada işleyeceğiz; bu bölümdeki halka tamponu ve kesme önceliği bilgisi, o protokollerin çerçeve ve tampon tasarımının temeli olacak.

::: mulakat
1. Bir kesme işleyicisinde `malloc` çağırmak neden sorunludur? Yerine hangi veri yapısını kullanırsın ve bunun hangi garantisi vardır?
2. Tek üretici ve tek tüketici için kilitsiz bir halka tamponu yazarken, tamponun dolu ile boş durumunu hangi koşullarla ayırt edersin ve neden bir yuva boş bırakılır?
3. Cortex-M'de bir kesme kabul edildiğinde hangi yazmaçlar donanım tarafından yığına konur? Derleyici hangi yazmaçları ayrıca kaydeder ve bunun nedeni nedir?
4. Yüksek öncelikli bir kesme ile düşük öncelikli bir kesme aynı anda beklerken, işlemci hangisini seçer ve bunu hangi donanım kuralı belirler?
5. Bir yazılımcı, bağımsız izleyiciyi zamanlayıcı kesmesi içinde besliyor. Bu tasarımda hangi hata sessizce gizlenir?
6. Rate Monotonic zamanlamada bir görev kümesi `U = 0,80` ile RM sınırının (3 görev için `0,78`) üstünde. Bu küme zamanında çalışabilir mi? Hangi test kesin cevabı verir?
7. Öncelik terslemesi nedir, bir mutex'te öncelik kalıtımı bunu nasıl çözer ve kalıtımın sınırı nedir?
