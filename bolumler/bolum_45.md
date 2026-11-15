%% kisim_no: XI
%% kisim_ad: Gömülü Sistem
%% bolum_no: 45
%% baslik: İletişim Protokolleri

## Giriş: Mikrodenetleyici kendi başına bir ada

Bir STM32 kartı kendi başına çok şey yapabilir ama dünyayı ancak sensörler ve aygıtlar aracılığıyla görür. Bir bataryanın gerilimini, bir motor sürücüsünün hızını, bir ekranın komutunu, bir IMU'nun ivmesini okumak için kart bu aygıtlarla konuşmak zorundadır. Bu konuşmanın kuralları **iletişim protokolüdür**: hangi hatlar kullanılır, bitler hangi hızda gider, bir baytın nerede başlayıp nerede bittiği nasıl anlaşılır, alıcı bir hatayı nasıl fark eder.

Bu bölüm dört yaygın gömülü protokolü ele alır: **UART**, **SPI**, **I2C** ve **CAN**. Her biri farklı bir sorunu çözer. UART iki uç arasında ucuz ve basit bir kanal açar. SPI kısa mesafede hızlı, tam çift yönlü bir kaydırma yazmacı sunar. I2C tek bir çift telle birçok sensörü bağlar. CAN ise bir aracın içindeki birçok düğümü gürültülü ortamda, öncelikli ve sağlam biçimde konuşturur. Bu dördünün ortak bir tarafı da var: hepsi bitleri bir zaman çizelgesi üzerinde taşır, ve zaman çizelgesini bozan her şey (saat sapması, kenar kayması, çarpışma, gürültü) veriyi bozar.

Bölüm 45 aynı zamanda bir **uygulama düzeyi** sorusunu da sorar: bir protokolün üstünde kendi çerçevemizi nasıl kurarız? Bölüm 31'de TCP üzerinde uzunluk önekli çerçeveleme ve CRC'yi gördük. Burada aynı fikri seri bir hat üzerinde yapacağız; ayraç bayt olarak `0x00` kullanıp veriyi COBS ile kaçışlayacağız. Son olarak Mert'in EV Dashboard projesini bu gözle okuyacağız: Daly BMS'ten, Kelly motor sürücüsünden ve Raspberry Pi'ye giden telemetri hattından.

::: not
Bu bölümde donanım yok, ama bir simülasyon var. UART, SPI, I2C ve CAN için bit düzeyi modeller Python'da yazıldı; çıktıların hepsi **simülasyon** sonucudur, gerçek bir osiloskop ya da mantık analizörü ölçümü değildir. Şekillerde gördüğün dalga biçimleri bu modellerden çizildi. Gerçek bir hatta ölçtüğünde sonuçların değişebileceğini unutma; kenar gecikmeleri, parazit ve kablo kapasitansı modelde yoktur.
:::

## 45.1 Seri ve paralel, senkron ve asenkron: dört soru

Bir protokolü anlamanın en kısa yolu dört soruyu sormaktır. **Kaç hat var?** Bitler aynı anda mı (paralel), tek tek mi (seri) gider? **Saat var mı?** Alıcı hangi anda bit okuyacağını bir saat hattından mı öğrenir (senkron), yoksa kendi zamanlayıcısıyla mı tahmin eder (asenkron)? **Gerilim nasıl taşınır?** Tek bir hat ile toprağa göre mi ölçülür (tek uçlu), yoksa iki hattın farkıyla mı (diferansiyel)? **Kaç aygıt bağlanabilir?** Nokta-nokta mı, çoklu bağlantı mı?

Paralel bağlantı, her bit için bir tel kullanır. Hızlıdır ama tel sayısı arttıkça kablo kalınlaşır, bitler arasında kayma (skew) oluşur ve gürültü daha çok etkiler. Bu yüzden uzun mesafede seri bağlantı daha yaygındır. Gömülü dünyada bir ekrana veri basan paralel arayüzler hâlâ vardır, ama haberleşmenin çoğu seridir.

Senkron protokollerde bir saat hattı vardır ve alıcı her saat kenarında bit okur. SPI ve I2C bunun örnekleridir. Asenkron protokollerde saat hattı yoktur; iki taraf aynı hızı önceden kabul eder ve her çerçevenin başında bir kenarla senkronlanır. UART bunun örneğidir. Asenkron hatta iki tarafın saatleri birbirinden biraz sapabilir; bu sapma bu bölümün en önemli sınırlarından birini doğurur (45.2).

Tek uçlu hatta sinyal toprağa göre ölçülür. Hat boyunca gürültü, sinyale doğrudan eklenir. Diferansiyel hatta iki tel birbirinin ters sinyalini taşır ve alıcı yalnızca farkı okur; ortak gürültü iki telde de aynı görüneceği için büyük ölçüde iptal olur. CAN, RS-485 ve USB bu ilkeyle çalışır (genel bilgi). Gerilim seviyeleri de önemlidir: 3,3 V ve 5 V TTL mantığı kısa kablo içindir; RS-232 ise ±3 V ile ±15 V arasında işaretler kullanır (genel bilgi). Bir 3,3 V pini 5 V mantıkla konuşan bir aygıta doğrudan bağlamak, pinin yıpranmasına yol açabilir; araya bir **seviye dönüştürücü** koymak gerekir.

| Soru | UART | SPI | I2C | CAN |
|---|---|---|---|---|
| Hat sayısı | 2 (TX, RX) | 4 (SCK, MOSI, MISO, CS) | 2 (SDA, SCL) | 2 (CANH, CANL) |
| Saat | Yok (asenkron) | Var, ana üretir | Var, ana üretir | Yok (asenkron) |
| Gerilim | Tek uçlu | Tek uçlu | Tek uçlu, açık-drenaj | Diferansiyel |
| Topoloji | Nokta-nokta | Ana ve birçok uydu | Çoklu aygıt | Çoklu düğüm, yol |

## 45.2 UART: iki uç, iki saat

UART (Universal Asynchronous Receiver-Transmitter) en eski ve en yaygın seri protokoldür. Hatta iki tel vardır: gönderici için TX, alıcı için RX. Her iki tarafın da kendi saati vardır ve ortak bir saat hattı yoktur. Hattın boşta durumu **1** (yüksek) seviyesidir. Bir bayt gönderilmeden önce hat bir **başlangıç biti** (0) ile aşağı çekilir; bu kenar alıcıya "şimdi bir çerçeve başlıyor" der. Ardından 8 veri biti en az anlamlı bitten (LSB) başlayarak gider. En sonda bir ya da daha fazla **durdurma biti** (1) gelir ve hat yeniden boşta kalır.

Yaygın biçim **8N1**'dir: 8 veri biti, parite yok (N = none), 1 durdurma biti. Çerçeve toplam 10 bit tutar. Eşlik (parity) biti eklenirse 8E1 ya da 8O1 olur (E = çift, O = tek). Eşlik tek bitlik hataları yakalar ama düzeltemez; iki bit birlikte bozulursa yakalamayabilir.

Aşağıdaki şekil `0x4B` baytının 8N1 çerçevesini bit bit gösterir. Bir bit süresi 9600 bps'de yaklaşık 104,2 µs, 115200 bps'de yaklaşık 8,68 µs'dir (1 / hız).

![Şekil 45.1: 0x4B baytının 8N1 UART çerçevesi. LSB önce gider; her bit bir bit süresi uzunluğundadır.](gorseller/b45_uart_iz.png)

Alıcı başlangıç kenarını gördüğünde kendi saatini o anda başlatır. Her bitin **ortasında** örnek alır, çünkü kenarlar parazit ve gecikmeye en yakın yerlerdir. Bu, alıcının kendi bit süresini ortalarda ölçmesi anlamına gelir. Şimdi asıl soru: iki saat birbirinden ne kadar sapabilir?

### Baud hızı ve tolerans: saat sapması

Verici bit süresini `T`, alıcı ise `Tr = T(1 + d)` olarak ölçsün. `d`, iki saat arasındaki bağıl sapmadır. Alıcı, `k`. bit için `(k + 0.5) · Tr` anında örnek alır. Bu örnek, verici `k`. bitin penceresi olan `[k·T, (k+1)·T)` aralığında kalmalıdır. Kuralı yazarsak:

- Alt sınır: `(k + 0.5)(1 + d) ≥ k` ⟹ `d ≥ -0,5/(k + 0,5)`
- Üst sınır: `(k + 0.5)(1 + d) < k + 1` ⟹ `d < 0,5/(k + 0,5)`

En dar durum en büyük `k`'da, yani son veri bitinde ya da durdurma bitinde oluşur. 8N1'de son bit `k = 9`'dur (0 başlangıç, 1–8 veri, 9 durdurma). Bu durumda `0,5/9,5 ≈ %5,26` olur. Yani her iki saatin toplam sapması kabaca **%5**'i geçmemelidir. Bu sınırı bir simülasyonla da doğrulayabiliriz. Aşağıdaki program, alıcının bit süresini `(1 + d)` ile değiştirip 256 baytın tamamını örnekleyerek çözer. `coz` fonksiyonu alıcıyı, `sinir` fonksiyonu tolerans sınırını bulur.

```python
# ornek_uart.py: 8N1 UART'in saat sapmasi toleransi (simulasyon).
def cerceve(bayt):
    bitler = [0] + [(bayt >> i) & 1 for i in range(8)] + [1]
    return bitler

def coz(bayt, d):
    bitler = cerceve(bayt)
    tr = 1.0 + d                         # alici bit suresi (T = 1)
    ornek = []
    for k in range(len(bitler)):
        t = (k + 0.5) * tr               # bit ortasi
        ornek.append(bitler[int(t)] if t < len(bitler) else 1)
    if ornek[0] != 0 or ornek[9] != 1:
        return None
    return sum(b << i for i, b in enumerate(ornek[1:9]))

def hepsi_dogru(d):
    return all(coz(b, d) == b for b in range(256))

def sinir(yon):
    d, adim = 0.0, 0.0001 * yon
    while hepsi_dogru(d + adim):
        d += adim
    return d
```

Kodun devamı şöyledir:

```python
if __name__ == "__main__":
    print("0x4B cerceve:", "".join(map(str, cerceve(0x4B))))
    print("d=0 -> 0x4B:", "%02X" % coz(0x4B, 0.0))
    print("d=+4%% -> 0x4B: %02X" % coz(0x4B, 0.04))
    print("tolerans +: %+.2f %%" % (sinir(1) * 100))
    print("tolerans -: %+.2f %%" % (sinir(-1) * 100))
    print("teorik 0,5/9,5 = %.2f %%" % (0.5 / 9.5 * 100))
```

Programın çıktısı şöyledir. Simülasyonda her iki yönde de sınır, teorik değere yakın çıkmaktadır.

```term
$ python ornek_uart.py
0x4B cerceve: 0110100101
d=0 -> 0x4B: 4B
d=+4% -> 0x4B: 4B
tolerans +: +5.88 %
tolerans -: -5.26 %
teorik 0,5/9,5 = 5.26 %
```

Sonuçları formülle karşılaştıralım. Üst yönde (d > 0) ilk sınır `k = 8` bitinde aşılır: `0,5/8,5 ≈ %5,88`. Alt yönde (d < 0) ilk sınır `k = 9` bitinde aşılır: `0,5/9,5 ≈ %5,26`. Programın ölçtüğü değerler de bunlardır. Eşlik biti eklenince (8E1) son bit `k = 10` olur ve parite biti `k = 9`da alt yönde yeni sınırı belirler; tam simülasyonda üst sınır `+%5,26`, alt sınır `-%4,76` (`0,5/10,5`) çıktı. Pratik bir kural olarak, iki saatin toplam sapması %2'nin altında kaldığında rahat olursun. Sapma sınıra yaklaştığında yalnızca belirli bit desenleri (son veri biti 0 olan baytlar gibi) bozulur; bu da teşhisi zor, aralıklı bir hata demektir.

![Şekil 45.2: Sol: bit penceresi (kutu) ve örnek anları (nokta). +%6 sapmada son iki örnek pencere dışına düşer. Sağ: 256 baytın doğru çözülme oranı saat sapmasına göre; ±%5,26 çevresinde kırılma görülür.](gorseller/b45_uart_kayma.png)

Bu sınır, baud hızı seçerken de bir kısıt yaratır. İki tarafın da kristali (ya da dahili RC osilatörü) yüzde birkaç sapabilir. Dahili RC osilatörler birkaç yüzde sapabilir (genel bilgi; kullandığın MCU'nun datasheet'ine bak); bu yüzden STM32'de UART'ı harici kristalle sürmek ya da seri hat hızını kısa tutmak daha güvenlidir. Hızı ne kadar artırırsan, bit süresi kısalır ve aynı sapma daha büyük hata demektir.

### Akış kontrolü ve alım yöntemleri

Alıcı bir baytı işlemeden yeni bayt gelirse ne olur? Alıcının donanım tamponu dolarsa baytlar kaybolur. Bunu önlemek için **akış kontrolü** kullanılır. Donanım yöntemi RTS/CTS'dir: alıcı tamponu dolmak üzereyken CTS hattını indirir, verici de durur. Yazılım yöntemi XON/XOFF'tur: alıcı özel bir bayt (genellikle `0x13` = XOFF, `0x11` = XON) gönderir. Yazılım yöntemi tek telle çalışır ama ikili veriyle (örneğin `0x11` içeren bir paket) çakışabilir; bu yüzden ikili protokollerde genellikle donanım akış kontrolü ya da çerçeve düzeyinde kendi denetimimiz tercih edilir.

Alım için üç yöntem vardır ve farkları, CPU'nun ne kadar süre meşgul olduğunda yatar:

1. **Yoklama (polling):** Ana döngü, bayt geldi mi diye sürekli bakar. Basittir, ama başka iş yaparken bayt kaçırabilirsin.
2. **Kesme + halka tampon:** Her bayt geldiğinde kesme işleyicisi (ISR) baytı alıp bir halka tampona koyar, ana döngü tampondan okur. Bölüm 44'te kesme mekanizmasını ve Bölüm 7.7'deki dairesel tamponu bir arada göreceksin. Aşağıdaki SPSC (tek üretici, tek tüketici) halka tampon bu kalıbın C'deki en küçük hâlidir.
3. **DMA + boşta hat algılama (idle line):** DMA baytları CPU'ya dokunmadan belleğe taşır. Hat bir süre boş kaldığında (genellikle bir bayt süresinden uzun) donanım bir kesme üretir; bu, çerçeve sınırını bilmenin ucuz bir yoludur. Bölüm 28'de DMA'nın genel mantığını gördün.

Aşağıdaki halka tampon iki bağlamı ayırır: ISR yalnızca `son` dizinini, ana döngü yalnızca `bas` dizinini değiştirir. Bu ayrım kilitsiz çalışmayı mümkün kılar. Tampon kapasitesi `2^n` seçilirse indeks maskeleme ile kolayca sarılır.

```c
/* halka.h: tek uretici (ISR) - tek tuketici (ana dongu) halka tampon.
 * Kapasite 2'nin kuvveti olmali. Dizinler (bas, son) tek yazilir. */
#ifndef HALKA_H
#define HALKA_H
#include <stdint.h>

#define HALKA_KAPASITE 64u          /* 2^n olmali */

typedef struct {
    volatile uint32_t bas;          /* tuketici yazar */
    volatile uint32_t son;          /* uretici yazar */
    uint8_t veri[HALKA_KAPASITE];
} halka_t;

void halka_sifirla(halka_t *h);
int  halka_yaz(halka_t *h, uint8_t b);   /* 0: tamam, -1: dolu */
int  halka_oku(halka_t *h, uint8_t *b);  /* 0: tamam, -1: bos */

#endif
```

Kodun devamı şöyledir:

```c
/* halka.c: SPSC halka tampon (Bolum 27 ve 44 ile ayni fikir). */
#include "halka.h"

void halka_sifirla(halka_t *h)
{
    h->bas = 0;
    h->son = 0;
}

int halka_yaz(halka_t *h, uint8_t b)
{
    uint32_t son = h->son;
    if (son - h->bas >= HALKA_KAPASITE)     /* dolu */
        return -1;
    h->veri[son & (HALKA_KAPASITE - 1u)] = b;
    h->son = son + 1u;                      /* veriden sonra yayin */
    return 0;
}

int halka_oku(halka_t *h, uint8_t *b)
{
    uint32_t bas = h->bas;
    if (h->son == bas)                      /* bos */
        return -1;
    *b = h->veri[bas & (HALKA_KAPASITE - 1u)];
    h->bas = bas + 1u;
    return 0;
}
```

Aşağıdaki demo programı tamponun dolma davranışını gösterir. Kapasite 64 ise 70 yazma denemesinden 6'sı reddedilir.

```c
/* ornek_halka.c: halka tamponun dolma ve bosalma davranisi. */
#include <stdio.h>
#include "halka.h"

int main(void)
{
    halka_t h;
    uint8_t b;
    int yazilan = 0, reddedilen = 0;

    halka_sifirla(&h);
    for (int i = 0; i < 70; i++) {          /* kapasite 64 */
        if (halka_yaz(&h, (uint8_t)i) == 0)
            yazilan++;
        else
            reddedilen++;
    }
    printf("yazilan=%d reddedilen=%d\n", yazilan, reddedilen);
    if (halka_oku(&h, &b) == 0)
        printf("ilk okunan=%u\n", b);
    while (halka_oku(&h, &b) == 0)
        ;
    printf("bosaltildi, yeni okuma=%d\n", halka_oku(&h, &b));
    return 0;
}
```

```term
$ gcc -std=c11 ornek_halka.c halka.c; ./a.out
yazilan=64 reddedilen=6
ilk okunan=0
bosaltildi, yeni okuma=-1
```

Bu tampon yalnızca **tek üretici ve tek tüketici** için doğrudur. Birden fazla kesme birden fazla kesme bağlamı aynı tamponu yazarsa, `son` artışı yarış koşulu olur; Bölüm 27.10'daki üretici-tüketici problemi burada gerçek bir donanım hâlinde karşına çıkar. Ayrıca `volatile` bu tamponda derleyicinin okumaları bellekten yapmasını sağlar, ama çok çekirdekli sistemlerde atomiklik ve bellek sıralaması için ek adımlar gerekir (Bölüm 27.5). Tek çekirdekli bir Cortex-M4'te kesme ile ana döngü arasında bu sorun yoktur; 32 bitlik hizalı erişimlerin atomik olduğu varsayımına dayanılır (genel bilgi).

## 45.3 Uygulama düzeyi çerçeveleme: sınır nasıl bulunur?

UART bize bir bayt verir, ama mesaj nerede başlar, nerede biter? Bölüm 31.4'te iki çözüm gördün. **Uzunluk önekli** çerçevelemede her mesajın başına uzunluğunu koyarsın; alıcı o kadar bayt okur. **Ayraçlı** çerçevelemede mesajı bir ayraç baytı ile bitirirsin; alıcı ayraca kadar okur. Ayraçlı yöntemin sorunu, ayracın veri içinde de geçebilmesidir. Bir `0x0A` (satır sonu) ayraç seçersen, verinin içindeki her `0x0A` mesajı yanlış böler.

Çözüm, veriyi **kaçışlamaktır** (byte stuffing). SLIP (RFC 1055) bunun bilinen bir biçimidir: ayraç `0xC0`'dır ve veri içinde `0xC0` görülürse onu `0xDB 0xDC` ile değiştirir (genel bilgi). SLIP'in sorunu, ek yükünün veriye bağlı olmasıdır: kötü bir veri her baytı iki bayta çıkarabilir.

**COBS** (Consistent Overhead Byte Stuffing) farklı bir fikir kullanır: kodlanmış veride hiç `0x00` yoktur; sıfırlar, her bloğun uzunluğunu söyleyen **kod baytlarıyla** yer değiştirir. Bu sayede `0x00` ayraç olarak güvenle kullanılabilir. Ek yük, her 254 veri baytı için en fazla bir bayttır (artı bir sabit kod baytı); yani kötü bir veri bile yalnızca çok az büyür.

Algoritmayı bir örnekle izleyelim: `11 22 00 33`. Kodlayıcı, ilk kod baytını yer ayırarak yazar ve ilerlerken her sıfıra gelince, o sıfırın yerine geçecek kodu (bloğun uzunluğu + 1) geri yazar. Sonda kalan blok için son kod yazılır. Sonuç `03 11 22 02 33`'tür; `03` "ardından iki veri baytı var, sonra sıfır", `02` "ardından bir veri baytı var, sonra sıfır (ya da son)" anlamına gelir. Çerçeve sonuna da `0x00` ayraç konur.

![Şekil 45.3: COBS kodlaması. 0x00 bayt, kod baytı (02) ile yer değiştirir. Kodlu veride 0x00 yoktur; tek sıfır ayraç çerçeve sınırını belirler.](gorseller/b45_cobs.png)

Aşağıdaki C kodu hem kodlayıcıyı hem çözücüyü içerir. Kod derlenebilir ve başka bir modül bağımlılığı yoktur. Yalnızca standart `size_t` ve `uint8_t` kullanır.

```c
/* cobs.h: COBS kodlayici / cozucu. Hata: -1 dondurur. */
#ifndef COBS_H
#define COBS_H
#include <stddef.h>
#include <stdint.h>

/* Girisi kodlar. Kapasite yetmezse -1, degilse kod uzunlugu. */
int cobs_kodla(const uint8_t *giris, size_t n,
               uint8_t *cikis, size_t kapasite);

/* Kodlu veriyi cozer (sonlandirici 0x00 icermemeli). */
int cobs_coz(const uint8_t *kodlu, size_t n,
             uint8_t *cikis, size_t kapasite);

#endif
```

Kodun devamı şöyledir:

```c
/* cobs.c: Consistent Overhead Byte Stuffing. */
#include "cobs.h"

int cobs_kodla(const uint8_t *giris, size_t n,
               uint8_t *cikis, size_t kapasite)
{
    size_t w = 0;          /* yazma konumu */
    size_t kod_yeri = 0;   /* kod baytinin konumu */
    uint8_t kod = 1;
    if (kapasite < 1)
        return -1;
    w = 1;
    for (size_t i = 0; i < n; i++) {
        if (giris[i] == 0) {
            cikis[kod_yeri] = kod;
            kod_yeri = w;
            kod = 1;
        } else {
            if (w >= kapasite)
                return -1;
            cikis[w++] = giris[i];
            kod++;
            if (kod == 0xFF) {       /* 254 veri baytı: blok biter */
                cikis[kod_yeri] = kod;
                kod_yeri = w;
                kod = 1;
                if (w >= kapasite)
                    return -1;
                w++;
            }
            continue;
        }
        /* sifirda: kod yeri icin yer ayir */
        if (w >= kapasite)
            return -1;
        w++;
    }
    if (kod_yeri >= kapasite)
        return -1;
    cikis[kod_yeri] = kod;
    return (int)w;
}
```

Kodun devamı şöyledir:

```c

int cobs_coz(const uint8_t *kodlu, size_t n,
             uint8_t *cikis, size_t kapasite)
{
    size_t i = 0, w = 0;
    while (i < n) {
        uint8_t kod = kodlu[i++];
        if (kod == 0)
            return -1;
        if (i + (size_t)kod - 1 > n)
            return -1;
        for (uint8_t k = 1; k < kod; k++) {
            if (w >= kapasite)
                return -1;
            cikis[w++] = kodlu[i++];
        }
        if (kod != 0xFF && i < n) {
            if (w >= kapasite)
                return -1;
            cikis[w++] = 0;
        }
    }
    return (int)w;
}
```

Aşağıdaki demo programı aynı örneği bir kez kodlayıp çözer. Çıktı, şekildeki baytları birebir verir.

```c
/* ornek_cobs.c: COBS kodla / coz gidis-donusu. */
#include <stdio.h>
#include "cobs.h"

static void yazdir(const char *ad, const uint8_t *v, int n)
{
    printf("%s:", ad);
    for (int i = 0; i < n; i++)
        printf(" %02X", v[i]);
    printf("\n");
}

int main(void)
{
    const uint8_t giris[] = {0x11, 0x22, 0x00, 0x33};
    uint8_t kodlu[16], cozulmus[16];

    int k = cobs_kodla(giris, 4, kodlu, sizeof kodlu);
    yazdir("girdi ", giris, 4);
    yazdir("kodlu ", kodlu, k);
    int c = cobs_coz(kodlu, (size_t)k, cozulmus, sizeof cozulmus);
    yazdir("cozulm", cozulmus, c);
    return 0;
}
```

```term
$ gcc -std=c11 ornek_cobs.c cobs.c; ./a.out
girdi : 11 22 00 33
kodlu : 03 11 22 02 33
cozulm: 11 22 00 33
```

Bu kodun doğruluğu tek bir örnekle kanıtlanmaz. Yazdığım test, sıfır oranı değişen 3000 rastgele veri üzerinde gidiş-dönüş yapar, kodlu çıktıda hiç `0x00` olmadığını denetler ve kapasite yetmediğinde `-1` döndüğünü sınar. Testler WSL'de `gcc -fsanitize=address,undefined` ile çalıştırıldı ve hata çıkmadı. Ayrıca Python'daki başvuru uygulamasında 20000 rastgele durumda ek yükün `1 + ⌊n/254⌋` sınırını aşmadığı ölçüldü. Bu iki ölçüm, bu bölümdeki diğer sayıların da nasıl doğrulanabileceğinin örneğidir.

COBS yalnızca **çerçeve sınırını** çözer. Bir baytın bozulup bozulmadığını söylemez. Bu iş CRC'nindir (45.4). İkisini birlikte kullanmak, Bölüm 31.5'teki sürümlü başlığın seri hat karşılığıdır: önce sınır (COBS), sonra bütünlük (CRC), sonra anlam (sürüm ve alanlar).


## 45.4 CRC: bütünlük denetimi

COBS çerçevenin nerede başlayıp bittiğini söyler; bir baytın değişip değişmediğini söylemez. Bu iş **sağlama değeri** (checksum) ya da **CRC** (Cyclic Redundancy Check) işidir. Bölüm 31.5'te TCP üzerinde CRC-32 kullandık; burada hafif bir seri hat için CRC-16 kullanacağız.

Fikir basittir. Gönderici, veriyi bir polinomun bölümü olarak düşünür ve kalanı (CRC) mesajın sonuna ekler. Alıcı aynı işlemi tüm çerçeve üzerinde yapar; kalan sıfır çıkarsa çerçeve bütündür. Bölme işlemi ikili aritmetikte XOR ile yapılır, bu yüzden donanımda ve C'de hızlıdır. Hangi hataları yakaladığını da polinom belirler: tek bitlik hataları, çift bitlik hataları ve kısa "patlamaları" (burst) yakalar. Bu bölümde kullanacağımız **CRC-16/CCITT-FALSE** polinomu `0x1021` (x¹⁶ + x¹² + x⁵ + 1), başlangıç değeri `0xFFFF` ve sonuç üzerinde XOR yapılmadan kullanılır.

Standart bir test vektörü, gerçekleme doğruluğunu sınamanın en ucuz yoludur. CRC-16/CCITT-FALSE için `"123456789"` metninin sonucu `0x29B1`'dir. Aşağıdaki kod bitsel (bit bit) bir gerçekleme yapar: her bayt için önce üst baytı başlangıç değeriyle XOR'lar, sonra sekiz kez sola kaydırıp en yüksek bit 1 ise polinomla XOR'lar.

```c
/* crc16.h: CRC-16/CCITT-FALSE (poli 0x1021, ilk 0xFFFF). */
#ifndef CRC16_H
#define CRC16_H
#include <stddef.h>
#include <stdint.h>

uint16_t crc16_ccitt(const uint8_t *veri, size_t n);

#endif
```

Kodun devamı şöyledir:

```c
/* crc16.c: bit bit (tablosuz) CRC-16/CCITT-FALSE. */
#include "crc16.h"

uint16_t crc16_ccitt(const uint8_t *veri, size_t n)
{
    uint16_t crc = 0xFFFFu;
    for (size_t i = 0; i < n; i++) {
        crc ^= (uint16_t)((uint16_t)veri[i] << 8);
        for (int k = 0; k < 8; k++) {
            if (crc & 0x8000u)
                crc = (uint16_t)((crc << 1) ^ 0x1021u);
            else
                crc = (uint16_t)(crc << 1);
        }
    }
    return crc;
}
```

Aşağıdaki demo, test vektörünü ve birkaç ek girdiyi hesaplar. Boş girdi `0xFFFF` döndürür; bu, başlangıç değerinin doğrudan çıktıya geçtiğini gösterir.

```c
/* ornek_crc.c: CRC-16/CCITT-FALSE denemesi. */
#include <stdio.h>
#include <string.h>
#include "crc16.h"

int main(void)
{
    const char *girdi[] = {"123456789", "", "A", "MertOS"};
    for (int i = 0; i < 4; i++) {
        size_t n = strlen(girdi[i]);
        uint16_t c = crc16_ccitt((const uint8_t *)girdi[i], n);
        printf("\"%s\" -> 0x%04X\n", girdi[i], c);
    }
    return 0;
}
```

```term
$ gcc -std=c11 ornek_crc.c crc16.c; ./a.out
"123456789" -> 0x29B1
"" -> 0xFFFF
"A" -> 0xB915
"MertOS" -> 0xCC79
```

### Toplama sağlaması ile CRC: neden fark eder?

Gerçek bir aygıt her zaman CRC kullanmaz. Daly BMS'in 13 baytlık çerçevesinde sağlama değeri, **baytların toplamının alt 8 biti**dir. Bu, CRC'den çok daha ucuzdur ama zayıftır. Toplama sağlaması iki bayt yer değiştirdiğinde değişmez, çünkü toplam aynı kalır. Bunu bir örnekle görelim. Aşağıdaki program, Daly'nin 0x90 yanıtını (gerilim, akım, SOC alanları) üretir, sonra gerilim baytlarını yer değiştirir ve iki sağlamanın tepkisini izler.

```python
# ornek_daly.py: Daly 13 bayt yanitini iki farkli sekilde coz.
def toplama8(v):
    return sum(v) & 0xFF

def yanit_90(volt, akim, soc):
    g = [0xA5, 0x01, 0x90, 0x08] + [0] * 8
    v, a, s = int(volt * 10), int(akim * 10) + 30000, int(soc * 10)
    g[4], g[5] = v >> 8, v & 0xFF
    g[8], g[9] = a >> 8, a & 0xFF
    g[10], g[11] = s >> 8, s & 0xFF
    g.append(toplama8(g))
    return g

def main_c_hucre(g):                     # main.c'deki hucre satiri
    return ((g[4] << 8) | g[5]) / 1000.0

def yanit_95(kare, mv):
    g = [0xA5, 0x01, 0x95, 0x08, kare]
    for m in mv:
        g += [m >> 8, m & 0xFF]
    g += [0] * (12 - len(g))
    g.append(toplama8(g))
    return g
```

Kodun devamı şöyledir:

```python
if __name__ == "__main__":
    g = yanit_90(52.3, -12.5, 87.4)
    print("yanit :", " ".join("%02X" % x for x in g))
    print("toplama dogru:", toplama8(g[:12]) == g[12])
    h = list(g)
    h[4], h[5] = h[5], h[4]              # volt baytlari yer degisti
    print("yer degisimi, toplama dogru:", toplama8(h[:12]) == h[12])
    print("  gerilim = %.1f V" % (((h[4] << 8) | h[5]) / 10.0))
    k = yanit_95(1, [3300, 3287, 3312])
    print("0x95 yanit:", " ".join("%02X" % x for x in k))
    print("  main.c hucre = %.3f V" % main_c_hucre(k))
    print("  dogru hucre1 = %.3f V" % (((k[5] << 8) | k[6]) / 1000.0))
```

```term
$ python ornek_daly.py
yanit : A5 01 90 08 02 0B 00 00 74 B3 03 6A DF
toplama dogru: True
yer degisimi, toplama dogru: True
  gerilim = 281.8 V
0x95 yanit: A5 01 95 08 01 0C E4 0C D7 0C F0 00 13
  main.c hucre = 0.268 V
  dogru hucre1 = 3.300 V
```

Çıktıdaki ilk satır, Daly'nin yanıtının tam dökümüdür: başlık `A5`, adres `01`, komut `90`, uzunluk `08`, sekiz veri baytı ve sağlama `DF`. Yer değiştirmiş çerçevenin toplaması hâlâ tutar (`True`) ama gerilim `281,8 V` olarak okunur; gerçek değer `52,3 V`tur. Yani toplama sağlaması doğru görünen ama yanlış bir çerçeveyi kabul eder.

Bu farkı bir ölçümle de görelim. Aşağıdaki tablo, sabit tohum (45) ile 20000 rastgele Daly yanıtı üzerinde yapılan simülasyonun sonucudur. Hata türleri ve her iki sağlamanın yakalama oranı yan yana verilmiştir (simülasyon programı arşivdedir; kitapta yalnızca sonuç tablosu var).

| Hata türü | Deneme | Toplama yakaladı | CRC-16 yakaladı |
|---|---|---|---|
| Tek bit ters çevirme | 20000 | %100 | — (ölçülmedi) |
| İki veri baytının yer değişimi | 18657 | %0 | %100 |
| İki baytta rastgele değer | 19999 | %99,6 | %100 |
| Rastgele 13 bayt | 20000 | %99,6 | — (ölçülmedi) |

CRC sütunu, aynı hata türünün ayrı bir rastgele dizide denendiği ölçümdendir; bu yüzden deneme sayıları farklıdır. Tablo, toplama sağlamasının neden yetersiz olduğunu açıkça gösterir: yer değişimi hiç yakalanmıyor. CRC-16 ise bu ölçümde hiçbir hatayı kaçırmadı. Ama dikkat: bu bir **ölçüm**dür, bir garanti değildir. CRC-16 rastgele bir hatayı yaklaşık 1/65536 olasılıkla kaçırır (genel bilgi); 20000 denemede bu, ortalama bir kaçış demektir ve sıfır kaçış görmek şans olabilir. Kesin garanti için polinomun hangi hata desenlerini yakaladığını bilmek gerekir.

::: dikkat
CRC bir **bütünlük** kodudur, **kimlik doğrulama** değildir. Bir saldırgan çerçeveyi değiştirip CRC'yi yeniden hesaplayabilir; CRC'de anahtar yoktur (Bölüm 32.3). Ağdan ya da hattan gelen her bayt düşman olabilir gibi davran: CRC bozulmayı yakalar, ama kasıtlı değişikliği durdurmaz. Kasıtlı değişiklik için HMAC ya da benzeri bir anahtarlı doğrulama gerekir.
:::

## 45.5 SPI: dört hat, tam çift yönlü kaydırma

SPI (Serial Peripheral Interface) dört hat kullanır: **SCK** (saat, ana üretir), **MOSI** (ana → uydu veri), **MISO** (uydu → ana veri) ve **CS** (çip seçimi, genellikle düşük aktif). Bir SPI transferinin ilkesi, iki kaydırma yazmacının birbirine bağlanmasıdır. Ana her saat darbesinde kendi yazmacının en yüksek bitini MOSI'ye koyar; aynı anda uydunun yazmacının en yüksek biti MISO üzerinden ana'nın yazmacına girer. Sekiz darbe sonunda iki taraf birbirinin baytını almış olur. Bu yüzden SPI **tam çift yönlüdür**: okumak ve yazmak aynı işlemdir.

Bu mekanizmanın en büyük avantajı hızdır: saat yüksek tutulabilir ve çerçeve başlığı yoktur. Dezavantajı, her uydu için ayrı bir CS hattı gerekmesidir (ya da zincirleme, daisy-chain bağlantı). Pratikte SPI, birkaç MHz'den onlarca MHz'e kadar hızlarda çalışır; hız sınırı aygıtın ve kablo uzunluğunun kapasitansına bağlıdır (genel bilgi). Tipik kullanımlar: SPI flash bellekler, dokunmatik ve LCD ekranlar, ivme ve jiroskop sensörleri (IMU).

**Kip** (mode) kavramı, verinin hangi saat kenarında hazırlanıp hangi kenarda okunduğunu belirler. İki parametre vardır. **CPOL** (saat kutbu), saat boşta iken seviyesinin 0 mı 1 mi olduğunu söyler. **CPHA** (saat fazı) ise veri örneklemenin ilk (önde gelen) kenarda mı yoksa ikinci (arkadaki) kenarda mı yapılacağını belirler. Dört kombinasyon vardır: (0,0), (0,1), (1,0), (1,1).

Şekil 45.4, dört kipte ana saat dalgasını ve uydunun örnekleme anlarını (▼) gösterir. Veri hazırlama anları (■) ise anın kendi kenarlarında yer alır. CPHA = 0'da veri ilk kenardan önce hazır olmalıdır; CPHA = 1'de hazırlama ilk kenarda olur ve okuma ikinci kenarda yapılır.

![Şekil 45.4: SPI'nin dört kipi. Her kipte uydu örnekleme anları (▼) ve ana veri hazırlama anları (■) saat kenarlarına göre gösterilir.](gorseller/b45_spi_kipler.png)

Kipler arasındaki uyumsuzluk, sessiz ve tanısı zor hatalar üretir. Aşağıdaki program, ana ve uydunun kiplerini ayrı ayrı alıp iki tarafın hangi bitleri okuyacağını hesaplar. Model ideal bir kablo varsayar; bir bit, veri değişimi ile örnekleme aynı anda olursa **belirsiz** (X) sayılır, çünkü gerçek bir devrede kurulum/tutma süresi ihlal edilmiş olur.

```python
# ornek_spi.py: SPI CPOL/CPHA kiplerinde orneklem ve hazirlama anlari.
def kenarlar(sck_cpol):
    seviye, liste = sck_cpol, []
    for t in range(1, 17):
        seviye ^= 1
        liste.append((t, seviye))
    return liste

def anlar(sck_cpol, cpol, cpha):
    aktif = 1 - cpol                    # cihazin 'aktif' seviyesi
    onde = [t for t, s in kenarlar(sck_cpol) if s == aktif]
    arka = [t for t, s in kenarlar(sck_cpol) if s != aktif]
    if cpha == 0:
        return onde[:8], [0] + arka[:7]
    return arka[:8], onde[:8]

def degistir(a, b, ka, kb):
    """Ana (ka) ve uydu (kb) kipi; belirsiz bit 'X'."""
    sck = ka[0]
    ora, hra = anlar(sck, *ka)
    orb, hrb = anlar(sck, *kb)
    ba = [(a >> (7 - i)) & 1 for i in range(8)]
    bb = [(b >> (7 - i)) & 1 for i in range(8)]
    def oku(hazir, bits, t):
        if t in hazir:
            return "X"
        son = 0
        for i, th in enumerate(hazir):
            if th < t:
                son = bits[i]
        return son
    uydu = [oku(hra, ba, t) for t in orb]
    ana = [oku(hrb, bb, t) for t in ora]
    f = lambda L: "X" if "X" in L else "%02X" % sum(
        v << (7 - i) for i, v in enumerate(L))
    return f(ana), f(uydu)
```

Kodun devamı şöyledir:

```python
if __name__ == "__main__":
    kipler = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for kb in kipler:
        print("ana (0,0) uydu %s -> ana alir, uydu alir: %s" % (
            kb, degistir(0xA5, 0x3C, (0, 0), kb)))
    print("ana (0,0), uydu (0,0):",
          degistir(0xA5, 0x3C, (0, 0), (0, 0)))
```

```term
$ python ornek_spi.py
ana (0,0) uydu (0, 0) -> ana alir, uydu alir: ('3C', 'A5')
ana (0,0) uydu (0, 1) -> ana alir, uydu alir: ('X', 'X')
ana (0,0) uydu (1, 0) -> ana alir, uydu alir: ('X', 'X')
ana (0,0) uydu (1, 1) -> ana alir, uydu alir: ('1E', 'A5')
ana (0,0), uydu (0,0): ('3C', 'A5')
```

Çıktı iki şeyi gösterir. Birincisi, aynı kipler (0,0) ve (0,0) arasında değişim doğrudur: `3C` ile `A5` karşılıklı alınır. İkincisi, kip uyumsuzluğunda ya belirsiz bitler (`X`) ya da kayık bir bayt (`1E`) ortaya çıkar. (1,0) ile (0,1) kiplerinin davranışı aynıdır; bu, **CPOL ve CPHA farklarının aynı örnekleme kenarlarını ürettiğini** gösterir. Yani iki parametreden biri yanlışsa veya her ikisi birden değişmişse, etki birbirine benzer ya da birbirini götürür. Gerçek sistemde sorunu çözmek için iki tarafın datasheet'indeki kipleri eşleştirmek yeterlidir; ama bu programın gösterdiği gibi, bir kip hatasının bir baytı tamamen değiştirmek yerine **bir bit kaydırması** olarak görünmesi de mümkündür.

::: ipucu
Bir SPI aygıtı beklenmeyen veri döndürüyorsa önce kipi kontrol et, sonra CS'nin transfer boyunca düşük kaldığından emin ol, en son hıza bak. Çoğu SPI hatasının sebebi kiptir ya da CS'nin erken yükselmesidir.
:::

## 45.6 I2C: iki hat, açık-drenaj, adres ve ACK

I2C (Inter-Integrated Circuit), iki telle birçok aygıtı bağlar: **SDA** (veri) ve **SCL** (saat). Her iki hat da **açık-drenaj** (open-drain) çıkışlara bağlıdır. Bir aygıt hattı 0'a çekebilir, ama 1'e **sürmez**; hattı yukarı çeken tek şey dış **çekme direncidir** (pull-up). Böylece hiçbir aygıt diğerine karşı yüksek akım sürmez ve birden fazla aygıt aynı hattı güvenle paylaşır. Bu, birden çok aygıtın aynı anda 0 çekebilmesi anlamına gelir: hattın değeri, sürücülerden **herhangi biri 0 çekiyorsa 0**, aksi halde 1 olur. Buna **wired-AND** denir.

Şekil 45.5, iki çekme direncinin her hattı nasıl yukarı çektiğini gösterir. Çekme direnci değeri iki sınırla seçilir. Üst sınır, hattın yükselme süresini kısıtlar: bus kapasitansı `Cb` ile direnç `R` çarpımı, yükselmeyi yavaşlatır. Alt sınır ise çekiciyi (sürücü transistörünü) aşırı akımdan korur. UM10204 I2C belirtiminde Rmax = tr_max / (0,8473 · Cb) ve Rmin = (VDD − VOL) / IOL formülleri verilir (genel bilgi).

![Şekil 45.5: I2C açık-drenaj devresi. Her hat yalnızca bir çekme direnciyle 1 olur; aygıtlar yalnızca 0 çeker.](gorseller/b45_i2c_devre.png)

Aşağıdaki program, bu sınırları sayısal olarak hesaplar ve bir RC devresinin yükselme süresini sayısal integrasyonla ölçer. Yükselme süresi %30'dan %70'e kadar geçen zamandır; bu tanım `0,8473 · R · C` sonucunu verir.

```python
# ornek_i2c.py: I2C cekme direnci sinirlari ve RC yukselme suresi.
import math

def rmax(tr_max, cb):
    return tr_max / (0.8473 * cb)

def rmin(vdd, vol, iol):
    return (vdd - vol) / iol

def yukselme(r, c, vdd=3.3):
    """Sayisal: V(t)=VDD(1-e^(-t/RC)); %30 ile %70 arasi sure."""
    tau, dt = r * c, r * c / 20000.0
    t, t30, t70 = 0.0, None, None
    while t70 is None:
        v = vdd * (1 - math.exp(-t / tau))
        if t30 is None and v >= 0.3 * vdd:
            t30 = t
        if v >= 0.7 * vdd:
            t70 = t
        t += dt
    return t70 - t30
```

Kodun devamı şöyledir:

```python
if __name__ == "__main__":
    print("Rmin = %.0f ohm" % rmin(3.3, 0.4, 3e-3))
    print("Rmax (hizli, 300 ns, 400 pF) = %.0f ohm" %
          rmax(300e-9, 400e-12))
    print("Rmax (standart, 1000 ns, 400 pF) = %.0f ohm" %
          rmax(1000e-9, 400e-12))
    tr = yukselme(4700, 100e-12)
    print("R=4,7k C=100 pF: tr = %.1f ns" % (tr * 1e9))
    rc = 0.8473 * 4700 * 1e-10 * 1e9
```

```term
$ python ornek_i2c.py
Rmin = 967 ohm
Rmax (hizli, 300 ns, 400 pF) = 885 ohm
Rmax (standart, 1000 ns, 400 pF) = 2951 ohm
R=4,7k C=100 pF: tr = 398.2 ns
0,8473 RC        = 398.2 ns
```

Çıktıya göre `4,7 kΩ` ve `100 pF` ile yükselme süresi `398 ns`dir. Standart mod (100 kHz) için tr_max = 1000 ns olduğundan bu değer kabul edilebilir; hızlı mod (400 kHz) için tr_max = 300 ns olduğundan aynı direnç **yetersizdir**. Hızlı modda 400 pF hat için en fazla yaklaşık 885 Ω gerekir. Bu, hız seçiminin donanım sonucudur ve yazılımda düzeltilemez.

### Çerçeve yapısı: başlangıç, adres, ACK, durdurma

Bir I2C işlemi bir **START** koşuluyla başlar: SCL yüksekken SDA yukarıdan aşağı iner. Ardından 7 bitlik adres ve bir **R/W** biti gelir (0 = yazma, 1 = okuma), toplam 8 bit. Adresi alan aygıt, dokuzuncu bitte SDA'yı 0'a çekerek **ACK** verir. Hiçbir aygıt adresi tanımazsa SDA yüksek kalır; bu **NACK**'tir. Veri baytları da aynı şekilde 8 bit + ACK olarak gider. İşlem bir **STOP** koşuluyla biter: SCL yüksekken SDA aşağıdan yukarı çıkar. Aynı işlem içinde yeni bir START (tekrarlanan START, repeated START) gönderilerek STOP beklenmeden yön değiştirilebilir; bu, bir yazmanın hemen ardından okuma yapmak için yaygın kullanılır.

Aşağıdaki şekil, bir yazma sonrası tekrarlanan START ile okuma işlemini gösterir. Şekildeki zaman ekseni yarım bit adımlarıdır ve veri, simülasyonun bit düzeyi modelinden gelir.

![Şekil 45.6: I2C işlem dalga biçimi. Yaz (0x10 ← 0x5A, 0x6B), tekrarlanan START, sonra iki bayt oku. Dikey çizgiler START ve STOP koşullarını işaretler.](gorseller/b45_i2c_iz.png)

Bir **yazma** işleminin ilk baytı genellikle bir yazmaç (register) adresidir; ardından gelen baytlar o adrese yazılır. Bir **okuma** işleminde ana, önce yazmaç adresini yazar, sonra tekrarlanan START ile R/W = 1 gönderir ve aygıt istenen bayt sayısını döndürür. Ana son okunan bayttan sonra ACK yerine NACK gönderir ve STOP koyar; NACK, aygıta "artık veri istemiyorum" der.

### Saat germe ve tahkim

Saat germe (clock stretching), uydunun SCL'yi 0'da tutarak ananın hızını düşürmesidir. Ana SCL'yi bıraktığında hat hâlâ 0'daysa, ana bu yükselişi bekler. Model bu davranışı içerir: uyduya 4 adımlık germe eklendiğinde işlem sonucu değişmez, yalnızca süre uzar. Bu, yavaş bir sensörün (ör. ölçüm yapmakta olan bir dönüştürücü) hızlı bir ana ile bile çalışabilmesinin yoludur.

**Tahkim** (arbitration) iki ana aynı anda konuşmaya başladığında devreye girer. Her ana bir bit gönderirken hattı da okur; gönderdiği 1 ise hattın 0 olduğunu görürse, bir başka aygıt 0 çekiyor demektir ve ana kaybeder. Kaybeden ana durur ve STOP beklemeden hattı bırakır. Şekil 45.7, adresleri `0xA0` (0x50 yazma) ve `0xA2` (0x51 yazma) olan iki ananın tahkimini gösterir. Adresler 7 bitlik `0x50` ve `0x51` farkıyla ayrılır; bayt olarak bu fark bit 1'dedir (R/W bitinin bir üstü): `0xA0 = 1010 0000`, `0xA2 = 1010 0010`. Yedinci iletilen bitte ana B 1 gönderir, hat 0 okur ve kaybeder.

![Şekil 45.7: I2C tahkimi. Ana A ve ana B aynı anda yazar; B bir ürettiği 1 ile hattın 0 okunuşu arasındaki farkta kaybeder ve durur.](gorseller/b45_i2c_tahkim.png)

Tahkimin güzel yanı, kaybeden tarafın veri kaybetmemesidir: kazanan ana, kaybedenin gönderdiği baytın öneki ile aynı bit deseninde olan adresle çakışmadan konuşmaya devam eder. Ama uygulama açısından, kaybeden ananın yeniden deneme yapması gerekir.

### Hız kipleri ve hat kilitlenmesi

Standart mod 100 kbit/s, hızlı mod 400 kbit/s, hızlı mod plus 1 Mbit/s ve yüksek hız 3,4 Mbit/s'e kadardır (genel bilgi). Hız arttıkça tr_max küçülür; bu yüzden 45.6'daki çekme direnci hesabı hız seçimiyle birlikte yapılmalıdır.

Bir uydu bir bit ortasında reset olursa ya da bir gürültü darbesi onu yanlış durumda bırakırsa, SDA 0'da kilitlenebilir. Bu, hattın bütün aygıtlar için kapalı kalması demektir. Çözüm **dokuz saat darbesi** ile kurtarmadır: ana SCL'ye 9 kez darbe verir; uydu, takılı kaldığı baytı (8 bit) bitirir ve dokuzuncu darbede (ACK bitinde) SDA'yı bırakır. Simülasyonda, kilitli bir uydu 8 bit boyunca SDA'yı 0'da tutar ve ana dokuzuncu darbede hattın serbest kaldığını görür. Bu yüzden 9 darbe bir sihir sayı değil, tek bir baytın bitimini kapsayan ölçüdür.

::: dikkat
Kurtarma sırasında 9 darbeyi sayma hatası, hattı kilitli bırakır. Üretici yazılımlarında kurtarma döngüsünü bir zaman aşımı ile sınırla ve aygıtı yeniden başlatmanın son çare olduğunu unutma.
:::

Tipik I2C aygıtları, ivme ve sıcaklık sensörleri, EEPROM bellekler ve güç yönetim entegreleridir (genel bilgi). Bunların çoğunun adresi sabittir ve datasheet'te yazar; birden çok aynı tip aygıt bağlamak istersen adres pinlerini (A0, A1) değiştirerek farklı adres seçilebilir.

## 45.7 CAN: fark yaratan veri yolu

CAN (Controller Area Network), otomotiv için geliştirilmiş bir veri yoludur ve bugün araçların içinde motor, fren, şanzıman ve kabin düğümlerini birbirine bağlar. Bölüm 29'da gördüğün gibi, CAN bir IP ağı değildir: düğümler IP adresiyle değil **mesaj kimliğiyle** (ID) konuşur, ve her mesaj hat üzerinde yayınlanır; alıcılar kendi ilgilendiklerini kendileri seçer. Hat iki telden oluşur (CANH ve CANL) ve diferansiyel çalışır: mantıksal 0 (**baskın**, dominant) iki telin farkı 2 V civarıdır, 1 (**çekinik**, recessive) ise fark yokken oluşur (genel bilgi).

CAN'in en değerli özelliği **yıkıcı olmayan tahkimdir**. Düğümler aynı anda mesaj göndermeye başlarsa, hat wired-AND gibi davranır: baskın 0, çekinik 1'i ezer. Her düğüm gönderdiği bitle hattı karşılaştırır; çekinik gönderip baskın okuyan düğüm kaybeder ve bekler. Kazanan, mesajının hiçbir bitini kaybetmez. Bu yüzden **kimlik (ID) değeri ne kadar küçükse öncelik o kadar yüksektir**: ilk bitinde 0 olan mesaj, 1 olanı ezer.

Şekil 45.8, üç düğümün aynı anda `0x123`, `0x0A5` ve `0x3F0` kimlikleriyle başladığı tahkimi gösterir. Bit dizileri 11 bitlik kimlikten gelir ve başlangıçta bir SOF (başlangıç) biti eklenmiştir. Aşağıdaki program tahkimi bit bit çalıştırır ve kim kaybettiğini yazar.

![Şekil 45.8: CAN tahkimi. Koyu hücre baskın (0), açık hücre çekinik (1). Çekinik gönderip baskın okuyan düğüm kaybeder; 0x0A5 kazanır.](gorseller/b45_can_tahkim.png)

**Bit doldurma** (bit stuffing) CAN'in ikinci önemli kuralıdır. Alıcılar senkronizasyonu kenarlardan öğrenir; uzun aynı bit dizileri (örneğin `000000`) kenar üretmez ve alıcı saatini kaybedebilir. Bu yüzden gönderici, **beş ardışık aynı bitten sonra zıt bir bit** ekler; alıcı bu dolgu bitlerini çıkarır. Dolgu, SOF'tan CRC'nin sonuna kadar uygulanır. Doldurma bölgesinde altı ardışık aynı bit görülürse bu bir **doldurma hatası**dır; alıcı bunu hata çerçevesi ile bildirir (genel bilgi).

![Şekil 45.9: Bit doldurma. Beş ardışık aynı bitten sonra zıt bit eklenir (sarı kutular). Eklenen bit, yeni koşunun ilk bitidir.](gorseller/b45_can_doldurma.png)

Aşağıdaki kod, CAN'in CRC-15'ini (poli `0x4599`), bit doldurmayı ve tahkimi bir arada gösterir. CRC bit bit hesaplanır, çünkü CAN'de CRC bayt değil **bit** akışı üzerinden tanımlıdır.

```python
# ornek_can.py: CAN CRC-15, bit doldurma ve tahkim (ideal hat).
def crc15(bitler):
    crc = 0
    for bit in bitler:
        geri = ((crc >> 14) & 1) ^ bit
        crc = (crc << 1) & 0x7FFF
        if geri:
            crc ^= 0x4599
    return crc

def doldur(bitler):
    cikis, kosu, son = [], 0, None
    for b in bitler:
        cikis.append(b)
        kosu = kosu + 1 if b == son else 1
        son = b
        if kosu == 5:
            cikis.append(1 - b)
            son, kosu = 1 - b, 1
    return cikis
```

Kodun devamı şöyledir:

```python
def bits_of(k):
    return [(k >> (10 - i)) & 1 for i in range(11)]

def tahkim(kimlikler):
    akis = [doldur([0] + bits_of(k) + [0]) for k in kimlikler]
    aktif = list(range(len(kimlikler)))
    for idx in range(13):
        gonderen = {d: akis[d][idx] for d in aktif}
        hat = min(gonderen.values())     # 0 baskin
        kaybeden = [d for d in aktif if gonderen[d] == 1 and hat == 0]
        if kaybeden:
            print("bit %2d  hat=%d  kaybeden=%s" % (
                idx, hat, ",".join("0x%03X" % kimlikler[d]
                                   for d in kaybeden)))
        aktif = [d for d in aktif if d not in kaybeden]
        if len(aktif) == 1:
            break
    return kimlikler[aktif[0]]

if __name__ == "__main__":
    bits = [1, 0, 1, 1, 0, 0, 1]
    print("crc15 =", hex(crc15(bits)))
    print("kalan sifir:", crc15(bits + [(crc15(bits) >> (14 - i)) & 1
                                       for i in range(15)]) == 0)
    x = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1]
    print("girdi    ", "".join(map(str, x)))
    print("doldurulm", "".join(map(str, doldur(x))))
    print("kazanan = 0x%03X" % tahkim([0x123, 0x0A5, 0x3F0]))
```

```term
$ python ornek_can.py
crc15 = 0x6fcc
kalan sifir: True
girdi     0000011111000001
doldurulm 0000011111010000011
bit  2  hat=0  kaybeden=0x3F0
bit  3  hat=0  kaybeden=0x123
kazanan = 0x0A5
```

Çıktıda `kalan sifir: True` satırı CRC'nin temel özelliğini doğrular: mesajın sonuna kendi CRC'si eklenince kalan sıfır çıkar. `doldurulm` satırı, şekil 45.9'daki örneğin bit dizisini verir. Tahkim satırları, `0x3F0`'ın 2. bitte ve `0x123`'ün 3. bitte kaybettiğini, kazananın `0x0A5` olduğunu gösterir. Bu sonuç, ID'nin küçük olmasının neden öncelik anlamına geldiğinin doğrudan kanıtıdır.

Simülasyonda, bir çerçevenin 1, 2 ve 3 bitini rastgele ters çevirdiğimde 4000 denemenin tamamında hata yakalandı (CRC uymaz ya da doldurma hatası oluşur). Bu da iyi bir ölçüm sonucudur, ama CRC-15 garantisi yine polinomun özelliğine dayanır.

Hata yönetimi CAN'de ayrı bir konudur. Her düğümde iletim (TEC) ve alım (REC) hata sayaçları vardır; bir iletim hatasında TEC artar, başarılı iletimlerde azalır. TEC 255'i aştığında düğüm **bus-off** durumuna geçer ve hattan çekilir (genel bilgi, CAN 2.0 belirtimi). Bu mekanizma, bozuk bir düğümün hattı kilitlemesini engeller; ama hattın bağlantısı bozuksa tüm düğümler bus-off'a girebilir.

CAN FD, veri alanını 64 bayta kadar çıkarır ve veri kısmında daha yüksek bir hız kullanır (genel bilgi). Otomotivin dışında CAN'in kuzenleri vardır: havacılıkta **ARINC 429** tek yönlü, 32 bitlik kelimeler gönderen bir veri yoludur (genel bilgi); savunma sanayiinde **MIL-STD-1553** komut-yanıt mantığı ve bir veri yolu denetleyicisi ile çalışır (genel bilgi). Bu iki sistemde de sağlamlık ve doğrulama, bu bölümde gördüğümüz her şeyin sertleştirilmiş hâlidir; Bölüm 78'de bu gerekliliklere döneceğiz.

## 45.8 Protokol karşılaştırması ve seçim

Hangi protokolün seçileceği, mesafe, hız, hat sayısı ve aygıt sayısının bir dengesidir. Aşağıdaki tablo kabaca değerler verir; kesin sınırlar aygıta ve tasarıma göre değişir (genel bilgi).

| Özellik | UART | SPI | I2C | CAN |
|---|---|---|---|---|
| Tipik hız | 9600 bps – birkaç Mbps | birkaç MHz – onlarca MHz | 100 kbit/s – 3,4 Mbit/s | 500 kbit/s – 1 Mbit/s (klasik) |
| Hat sayısı | 2 | 4 (+ her uydu için CS) | 2 | 2 (diferansiyel) |
| Mesafe | Kısa (cm – birkaç m) | Çok kısa (PCB içi) | Kısa (PCB içi, birkaç cm–m) | Uzun (onlarca m) |
| Aygıt sayısı | 2 | Sınırlı (CS sayısı) | 112 kullanılabilir adres (7 bit, genel bilgi) | Düzinelerce düğüm |
| Topoloji | Nokta-nokta | Ana ve uydu | Çoklu, aynı hat | Çoklu, omurga (bus) |
| Karmaşıklık | Düşük | Düşük | Orta | Yüksek |
| Tipik kullanım | Debug konsolu, GPS, Bluetooth modülü | Flash, ekran, IMU | Sensör, EEPROM, RTC | Otomotiv, endüstriyel otomasyon |

Tablo bir sıralama değil bir karar yardımıdır. Kısa mesafede çok sensör varsa I2C; yüksek hızlı bir flash ya da ekran varsa SPI; iki kart arasında basit bir mesaj varsa UART; bir aracın içinde birbirini dinleyen birçok düğüm varsa CAN. Bir sistemde birkaç protokol birlikte bulunabilir: EV Dashboard tam olarak bunu yapar. Daly BMS ve Kelly motor sürücüsü UART, sensörler GPIO, Raspberry Pi ile STM32 arası UART; ve dış dünyaya kadar giden telemetri ise bir telsiz üzerinden geçer.

## 45.9 Hata ayıklama: mantık analizörü ve protokol çözücü

Bir protokol hatasını ancak hattı görürsen bulursun. Bunun iki aracı vardır. **Mantık analizörü** (logic analyzer), birkaç hattı yüksek örnekleme hızıyla kaydeder ve bit dizisini zaman çizelgesi olarak gösterir. **Protokol çözücü** (protocol decoder), bu ham kayıtları alır ve UART baytlarını, I2C adreslerini ya da CAN çerçevelerini anlamlı biçimde yazar. Bu iki kavram, bu bölümdeki şekillerin nasıl üretildiğinin de özüdür: simülasyon ham bit dizisini üretti, çizim onu zaman çizelgesine çevirdi.

Protokol çözücünün temel fikri bir **durum makinesidir**. I2C çözücüsü, SCL kenarlarını sayar, SDA'nın SCL yüksekken değişimini START ve STOP olarak tanır, 8 bit toplayıp ACK bitini okur. UART çözücüsü başlangıç kenarını bulur, bit ortalarında örnek alır, durdurma bitini doğrular. Bu tür bir çözücüyü yazmak, protokolü gerçekten anlamanın en iyi yoludur; Kendin Yap bölümündeki ikinci proje tam olarak bunu ister.

Bu bölümde en sık yapılan hata, ham dalga biçimine bakıp protokolü tahmin etmektir. Bunun yerine önce protokolün belirtimine göre bekleyeceğin zaman çizelgesini çiz, sonra gerçek kayıtla karşılaştır. Fark, ya kablonun, ya kip ya da hızın yanlış olduğunu gösterir.

## 45.10 Sürücü tasarımı: katmanlar, kesme ve sahte UART ile test

Bir protokol sürücüsünü tek bir büyük fonksiyon olarak yazmak kolaydır, ama bakımı zordur ve test edilemez. Bölüm 21.6'da gördüğün **bağımlılığın tersine çevrilmesi** (DIP) burada doğrudan işe yarar. Sürücü üç katmana ayrılır: en altta **donanım soyutlama** (HAL, STM32'nin `HAL_UART_Transmit` gibi çağrıları), ortada **protokol** (çerçeve ve sağlama), en üstte **uygulama** (hangi değerin ne anlama geldiği). Protokol katmanı donanımı bilmez; yalnızca bir arayüz üzerinden bayt gönderir ve alır.

Aşağıdaki başlık dosyası, Daly BMS sürücüsünün arayüzünü tanımlar: gönderme, bayt alma (zaman aşımlı) ve tampon temizleme işlevleri bir yapıda toplanır. STM32 tarafında bu işlevleri HAL'in çağrılarına bağlayan küçük bir sarmalayıcı yazılır; testte ise sahte (fake) bir sürüm verilir.

```c
/* daly.h: Daly BMS 13 bayt cerceve surucusu (donanimdan bagimsiz).
 * G/O fonksiyonlari disaridan verilir: test icin sahte, STM32 icin
 * HAL sarmalayicisi. Donus: 0 tamam, -1 zaman asimi, -2 bozuk. */
#ifndef DALY_H
#define DALY_H
#include <stdint.h>

typedef struct {
    void *ctx;
    int  (*gonder)(void *ctx, const uint8_t *v, uint32_t n);
    int  (*al_bayt)(void *ctx, uint8_t *b, uint32_t zaman_asimi_ms);
    void (*tampon_temizle)(void *ctx);
} daly_io_t;

int daly_sorgu(const daly_io_t *io, uint8_t komut, uint8_t cevap[13]);

#endif
```

Protokol katmanı, sorguyu gönderir, yanıtın başlığını arar (gürültü yüzünden kayık gelen baytları atlayarak), 13 baytı okur ve adres, komut ve sağlamayı denetler. Her hata türü ayrı bir dönüş kodu alır: zaman aşımı `-1`, bozuk çerçeve `-2`.

```c
/* daly.c: Daly BMS sorgusu; baslik, adres, komut, sağlama. */
#include "daly.h"

#define DALY_BASLIK   0xA5u
#define DALY_ADRES    0x01u     /* BMS yaniti (ESPHome'a gore) */
#define DALY_ZAMAN_MS 200u

static uint8_t topla8(const uint8_t *v, uint32_t n)
{
    uint8_t s = 0;
    for (uint32_t i = 0; i < n; i++)
        s = (uint8_t)(s + v[i]);
    return s;
}
```

Kodun devamı şöyledir:

```c

int daly_sorgu(const daly_io_t *io, uint8_t komut, uint8_t cevap[13])
{
    uint8_t istek[13] = {DALY_BASLIK, 0x40, komut, 0x08};
    uint8_t b = 0;
    int bulundu = 0;

    istek[12] = topla8(istek, 12);
    io->tampon_temizle(io->ctx);            /* eski bayt kalmasin */
    if (io->gonder(io->ctx, istek, 13) != 0)
        return -1;

    /* Baslik baytini ara: gurultu bayt kaymasina yol acabilir */
    for (int k = 0; k < 64 && !bulundu; k++) {
        if (io->al_bayt(io->ctx, &b, DALY_ZAMAN_MS) != 0)
            return -1;
        if (b == DALY_BASLIK)
            bulundu = 1;
    }
    if (!bulundu)
        return -2;
    cevap[0] = b;
    for (int i = 1; i < 13; i++)
        if (io->al_bayt(io->ctx, &cevap[i], DALY_ZAMAN_MS) != 0)
            return -1;

    if (cevap[1] != DALY_ADRES || cevap[2] != komut)
        return -2;
    if (topla8(cevap, 12) != cevap[12])
        return -2;
    return 0;
}
```

Bu kod, Bölüm 39.5'teki test ikizlerinden **fake** türüdür: gerçek bir donanım yerine, önceden hazırlanmış baytları veren bir nesne. Testte, bozuk bir sağlamanın `-2`, komut uyuşmazlığının `-2`, yarım çerçevenin `-1` döndüğünü ve gürültü baytlarından sonra senkronun yeniden kurulduğunu sınadım. Bu testler arşivdeki host testinde WSL üzerinde AddressSanitizer ve UBSan ile çalıştırıldı; hiçbir uyarı ya da hata çıkmadı.

Aynı kod, STM32 için derlenebilir. `arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -Os` ile derlendiğinde Daly sürücüsünün nesne dosyasının metin (kod) bölümü 200 bayt, CRC-16 48 bayt, COBS 176 bayt, halka tampon 72 bayt ve telemetri çerçeve kodlayıcısı 170 bayt çıkar. Veri ve BSS bölümleri sıfırdır, çünkü bu modüller global durum tutmaz. Bu sayılar, kodun gömülü bir hedefe sığdığını gösterir; kesin boyut, bağlayıcı ayarlarına ve seçilen libc'ye göre değişir.

Bir uyarı: `printf` ailesinin float biçimlendirmesi gömülü libc'de (newlib-nano) varsayılan olarak bağlanmaz. Aşağıdaki sembol kontrolü bunu gösterir: `-u _printf_float` bağlayıcı bayrağı olmadan `_printf_float` sembolü yoktur, bu bayrakla bağlanınca kod boyutu yaklaşık 5 KB'tan 19 KB'a çıkar. Bu, EV Dashboard'un `main.c` dosyasındaki `%f` kullanımı için kritik bir sorudur (45.11).

Son olarak kesme bağlamında bir not. Daly sürücüsündeki zaman aşımı bekleyen `HAL_UART_Receive` çağrıları, ana döngüyü bloke eder. Gerçek bir sistemde bu çağrıları kesmeye dayalı bir alımla ve halka tamponla değiştirmek, zaman aşımı süresince işlemciyi serbest bırakır. Bu tasarım seçimi, yanıt süresi ile çevrim süresi arasındaki dengeyi değiştirir.


## 45.11 Vaka çalışması: EV Dashboard veri hattı

Bu bölümün en somut kısmı Mert'in kendi projesidir: Teknofest 2026 elektrikli araç takımının EV Dashboard'u. Sistemin protokol omurgası şöyledir. Daly BMS, batarya gerilimini, akımını, SOC'unu, sıcaklığını ve hücre gerilimlerini 13 baytlık UART çerçeveleriyle verir. Kelly motor sürücüsü hız verisini UART ile verir. Vites, sinyal ve far durumları STM32'nin GPIO pinlerinden okunur. STM32 bütün bunları bir JSON satırında toplayıp 200 ms'de bir UART3 üzerinden Raspberry Pi 5'e yollar. Pi'de iki servis çalışır: `telemetri.py` veriyi RFD900X telsiz modülü üzerinden yer istasyonuna iletir, `kadran.py` ise WebSocket ile tarayıcıdaki dashboard'a yayınlar.

Şekil 45.10 bu akışı gösterir. Bu bölümde kodu okurken dikkat edeceğin nokta şudur: her iki uçta, yani BMS ile STM32 arasında ve STM32 ile Pi arasında, **alınan baytın doğruluğunu hiçbir yerde denetlemiyoruz**. Bu, sistemin çalıştığı günlerde iyi görünür; ama gürültü, kablo gevşekliği ya da bir kesintiden sonra sessiz yanlış değerler üretir.

![Şekil 45.10: EV Dashboard veri akışı. BMS ve motor sürücüsü UART ile STM32'ye bağlanır; STM32 JSON satırını UART3 üzerinden Pi 5'e yollar; Pi iki servisle telsize ve tarayıcıya dağıtır.](gorseller/b45_ev_akis.png)

### Bulgular

Aşağıdaki tablo, kodu satır satır okuyup her bulguyu bir kanıtla eşleştirir. Kanıt türü üç sınıftan biridir: **kod incelemesi** (satır mantığından çıkan), **kaynak karşılaştırması** (ESPHome daly_bms.cpp'nin resmi olmayan ama açık kaynaklı Daly sürücüsü ile), ya da **simülasyon** (arşivdeki programlar). Kaynak dosyalar salt okunurdur ve değiştirilmemiştir; satır numaraları `stm32/main.c` ve `rpi/*.py` dosyalarına aittir.

| No | Konum | Bulgu | Kanıt |
|---|---|---|---|
| B1 | main.c, 47–57 ve 66–69 | Daly yanıtında başlık (0xA5), adres (0x01), komut eşleşmesi ve sağlama denetimi yok. Yanıt doğrudan alan olarak okunuyor. | Kod incelemesi; 45.4 örneği |
| B2 | main.c, 75–77 | 0x95 (hücre) yanıtında kare numarası (bayt 4) ve ilk hücrenin üst baytı gerilim sanılıyor. Sonuç 0,268 V; doğru değer 3,300 V. Ayrıca "en düşük hücre" hesaplanmıyor; tek karede yalnızca 3 hücre var. | ESPHome kaynağı (hücre 1: bayt 5–6); simülasyon |
| B3 | main.c, 62–78 ve 155–166 | Zaman aşımında eski değer korunur; yaşı belli olmaz. Hiçbir bayrak yok. | Kod incelemesi |
| B4 | main.c, 90 | Yorum "RPM -> km/h" diyor, ama dönüşüm yok; ham RPM değeri hız olarak yollanıyor. Dönüşüm, tekerlek çevresi ve dişli oranı gerektirir. | Kod incelemesi |
| B5 | main.c, 98–109 | Hiçbir vites pini aktif değilse vites `'D'` oluyor. Kablo kopması sürüş modu olarak görünür. | Kod incelemesi |
| B6 | main.c, 123–131 | `snprintf` ile `%f` kullanılıyor. Gömülü libc'de float biçimlendirmesi bağlayıcı bayrağına bağlıdır; bayrak yoksa `volt` ve `cell` alanları bozulur. | Sembol kontrolü (45.10); proje bağlayıcı ayarı dosyada yok |
| B7 | main.c, 137–141; telemetri.py, 60–65 | JSON satırında sıra no, sağlama ya da uzunluk alanı yok. Bozulan bir rakam geçerli JSON kalır. | Simülasyon (aşağıdaki tablo) |
| B8 | telemetri.py, 77–79 | JSON geçerli ama bir nesne değilse (örneğin `5`), `veri.get(...)` bir `AttributeError` fırlatır; yalnızca `SerialException` yakalandığı için servis durur. | Simülasyon: `'int' object has no attribute 'get'` |
| B9 | telemetri.py, 67–71 | 5 Hz sınırı gelen paketleri atarak uygulanır. 190 ms aralıkla gelen 10 pakette 5 tanesi iletildi. Tam 200 ms aralıkta kayan nokta ve jitter yüzünden bazı paketler atıldı. STM32 periyodu 200 ms'den uzun olduğu için filtre çoğunlukla etkisizdir, ama bir garanti değildir. | Simülasyon |
| B10 | kadran.py, 43–57 | Yayın sırasında bir istemci bağlanır ya da ayrılırsa `RuntimeError: Set changed size during iteration` oluşur. Hata `seri_oku` üzerinden tüm servisi düşürür. `kadran.service` (Restart=always, RestartSec=3) hizmeti üç saniye sonra yeniden başlatır; tüm tarayıcılar bu sürede kopar. | Simülasyon (gerçek `yayinla` kodu) |
| B11 | telemetri.py, 18; kadran.py, 8 | İki servis de `/dev/ttyAMA2` hattını açar. Aynı anda çalışırlarsa her bayt yalnızca birine gider; veri bölünür. `baslat.sh` yalnızca tarayıcıyı başlatır, hangi servisin çalışacağı kurulumda belirlenmeli. | Kod incelemesi; Linux seri port semantiği (genel bilgi) |
| B12 | main.c, 47–57 | Daly UART hızı dosyada yok (`MX_USART1_UART_Init` ayrı dosyada). Sürücünün 9600 mı başka bir hızda mı çalıştığı doğrulanmalı. | Kod incelemesi |

Üç bulgu özellikle üzerinde durmaya değer. Birincisi **B2**: bu bir yorumlama hatasıdır; doğru uzunluk ve ofset bilgisine sahipsen düzeltmek kolaydır, ama hatanın fark edilmemiş olması, B1'in bir sonucudur. Doğrulanmamış bir yanıtın alanları yanlış anlamlandırıldığında hata sessizce kalır. İkincisi **B7 ve B10**: sessiz bozulma ile servis çökmesi, sağlamlık ve hata izolasyonu konusunun iki yüzüdür. Üçüncüsü **B3**: zaman aşımı ve yaş bilgisi yokken bir sensör durduğunda sistem eski veriyi taze gibi gösterir. Bir EV'de bu, sürücünün yanlış bir batarya yüzdesine güvenmesi demektir.

Aşağıdaki simülasyon, B7'yi sayısal olarak gösterir. Her kare 15 baytlık sabit bir yük (hız, batarya, gerilim, menzil, sıcaklık, hücre, vites ve sinyaller) taşır. Bir JSON satırı ile 21 baytlık ikili çerçeve aynı veriyi taşır. İkisine de bit başına eşit olasılıkla ters çevirme uygulanır; 20000 kare üzerinden kabul edilen yanlış değerler sayılır. Sabit tohum 45 kullanıldı; simülasyon programı arşivdedir.

| Bit hata olasılığı (BER) | CRC-çerçeve: yanlış kabul | CRC-çerçeve: red | JSON: yanlış kabul | JSON: red |
|---|---|---|---|---|
| 1 × 10⁻⁴ | 0 | 357 | 707 | 1178 |
| 1 × 10⁻³ | 0 | 3074 | 3647 | 8687 |
| 3 × 10⁻³ | 0 | 7947 | 2536 | 16358 |

Tablonun önemli yanı, JSON'un "yanlış kabul" sütunudur: 1 × 10⁻³ gibi orta bir hata oranında 20000 karenin 3647'si geçerli JSON olarak kabul edilip yanlış değer taşır. CRC hattında bu sayı sıfırdır; bozuk kareler reddedilir. Bedeli, kırmızı sütundaki reddetmelerdir: CRC hattı daha çok kareyi atar. Bu takas, bir telemetride genellikle doğrudur: eksik bir kare, yanlış bir kareden daha az zararlıdır, çünkü yer istasyonu bir sonrakini bekleyebilir.

### Sağlamlaştırılmış çerçeve önerisi

Önerilen çerçeve, bu bölümdeki parçaları birleştirir: sürüm alanı (Bölüm 31.5), sıra numarası (boşluk ve yinelenen tespiti), sabit uzunlukta ikili yük (JSON'daki ondalık biçimlendirme ve ayrıştırma sorunları yok, boyut küçük), CRC-16 (bütünlük) ve COBS (çerçeve sınırı).

| Alan | Boyut | Açıklama |
|---|---|---|
| SÜRÜM | 1 bayt | Protokol sürümü (şu an 1) |
| SIRA | 1 bayt | 0–255 arası döngüsel sıra numarası |
| YÜK | 15 bayt | spd (u16), bat (u8), volt×10 (u16), range (u16), btemp (i8), tmp (i8), cell mV (u16), gear (ASCII), sigL, sigR, beam (u8) |
| CRC16 | 2 bayt | CRC-16/CCITT-FALSE, SÜRÜM + SIRA + YÜK üzerinde, büyük uç |
| Ayraç | 1 bayt | 0x00 (COBS kodlamasından sonra) |

Çerçeve 21 bayttır. Aynı veri JSON satırı olarak ortalama 118,9 bayt tutar (ölçüm: 2000 rastgele yük). 5 Hz yayında JSON yaklaşık 595 bayt/s, ikili çerçeve yaklaşık 105 bayt/s üretir. Telsiz modülünün hava hızı ayrı bir ayardır ve burada bu oranın doğrudan bir sonucu değildir; ama daha az bayt, daha az çarpışma ve daha kısa gecikme demektir.

Aşağıdaki C kodu STM32 tarafındaki kodlayıcıdır. Yük, struct dolgusuna güvenmeden baytlara tek tek yazılır; bu, derleyiciden ve hedef mimariden bağımsız bir düzen sağlar (Bölüm 2.7 ve 1.5).

```c
/* telemetri_cerceve.h: EV telemetri cercevesi (surum+sira+yuk+CRC16).
 * Cerceve: COBS kodlu, sonunda 0x00. Toplam 21 bayt. */
#ifndef TELEMETRI_CERCEVE_H
#define TELEMETRI_CERCEVE_H
#include <stddef.h>
#include <stdint.h>

#define TEL_SURUM      1u
#define TEL_YUK_BOYU  15u

typedef struct {
    uint16_t spd;       /* km/h */
    uint8_t  bat;       /* % */
    uint16_t volt_x10;  /* 0.1 V birimi */
    uint16_t range;     /* km */
    int8_t   btemp;     /* C */
    int8_t   tmp;       /* C */
    uint16_t cell_mv;   /* mV */
    uint8_t  gear;      /* 'P' 'R' 'N' 'D' */
    uint8_t  sigL;
    uint8_t  sigR;
    uint8_t  beam;
} tel_yuk_t;

/* Yuku 15 bayt little-endian yazar (struct dolgusundan bagimsiz). */
void tel_yuk_yaz(const tel_yuk_t *y, uint8_t cikis[TEL_YUK_BOYU]);

/* Cerceveyi uretir. Donus: uzunluk (0x00 dahil) ya da -1. */
int tel_kodla(const tel_yuk_t *y, uint8_t sira,
              uint8_t *cikis, size_t kapasite);

#endif
```

Kodun devamı şöyledir:

```c
/* telemetri_cerceve.c: cerceve kodlayici (STM32 tarafi). */
#include "telemetri_cerceve.h"
#include "cobs.h"
#include "crc16.h"

void tel_yuk_yaz(const tel_yuk_t *y, uint8_t b[TEL_YUK_BOYU])
{
    b[0]  = (uint8_t)(y->spd & 0xFF);
    b[1]  = (uint8_t)(y->spd >> 8);
    b[2]  = y->bat;
    b[3]  = (uint8_t)(y->volt_x10 & 0xFF);
    b[4]  = (uint8_t)(y->volt_x10 >> 8);
    b[5]  = (uint8_t)(y->range & 0xFF);
    b[6]  = (uint8_t)(y->range >> 8);
    b[7]  = (uint8_t)y->btemp;        /* int8 -> bit deseni */
    b[8]  = (uint8_t)y->tmp;
    b[9]  = (uint8_t)(y->cell_mv & 0xFF);
    b[10] = (uint8_t)(y->cell_mv >> 8);
    b[11] = y->gear;
    b[12] = y->sigL;
    b[13] = y->sigR;
    b[14] = y->beam;
}
```

Kodun devamı şöyledir:

```c
int tel_kodla(const tel_yuk_t *y, uint8_t sira,
              uint8_t *cikis, size_t kapasite)
{
    uint8_t ham[2 + TEL_YUK_BOYU + 2];      /* 19 bayt */
    uint8_t kod[sizeof ham + 2];            /* COBS icin pay */
    uint16_t crc;
    int n;

    ham[0] = TEL_SURUM;
    ham[1] = sira;
    tel_yuk_yaz(y, &ham[2]);
    crc = crc16_ccitt(ham, 2 + TEL_YUK_BOYU);
    ham[17] = (uint8_t)(crc >> 8);          /* CRC: big-endian */
    ham[18] = (uint8_t)(crc & 0xFF);

    n = cobs_kodla(ham, sizeof ham, kod, sizeof kod);
    if (n < 0 || (size_t)n + 1 > kapasite)
        return -1;
    for (int i = 0; i < n; i++)
        cikis[i] = kod[i];
    cikis[n] = 0x00;
    return n + 1;
}
```

Aşağıdaki demo, Python'daki başvuru çerçevesiyle aynı yükü kodlar. Çıktıdaki 21 bayt, 45.3'teki COBS ve 45.4'teki CRC ile hesaplanmıştır; Python ölçümünde kullanılan çerçeve ile birebir aynıdır.

```c
/* ornek_tel.c: telemetri cercevesi (21 bayt) uretir. */
#include <stdio.h>
#include "telemetri_cerceve.h"

int main(void)
{
    tel_yuk_t y = {12, 87, 523, 143, 25, -3, 3300, 'D', 1, 0, 0};
    uint8_t kare[32];
    int n = tel_kodla(&y, 7, kare, sizeof kare);

    printf("uzunluk=%d\n", n);
    for (int i = 0; i < n; i++)
        printf("%02x%c", kare[i], i == n - 1 ? '\n' : ' ');
    return 0;
}
```

```term
$ gcc -std=c11 ornek_tel.c telemetri_cerceve.c cobs.c crc16.c; ./a.out
uzunluk=21
04 01 07 0c 05 57 0b 02 8f 07 19 fd e4 0c 44 01 01 03 bd cb 00
```

Pi tarafındaki çözücü, bu çerçeveyi ters sırayla uygular: sonlandırıcıya kadar oku, COBS çöz, uzunluk 19 mu kontrol et, CRC'yi doğrula, sürümü denetle, sırayı önceki sıra ile karşılaştır (boşluk ya da yineleme varsa say) ve yükü aç. Zaman aşımı kuralı da eklenmelidir: son geçerli çerçeveden 500 ms geçtiyse dashboard veriyi "bayat" işaretlemelidir. Bu, B3'ün ve B10'un da çözümüdür. Pi tarafındaki çözücüyü yazmak, Kendin Yap bölümündeki ilk projedir.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'teki altı adımı izler. Her birinde adımlar ayrı başlıklarla işaretlenmiştir ve son adımda elle iz sürme tablosu bulunur. Zorluk sırası ★, ★★, ★★, ★★★ şeklindedir.

### Örnek 1 (★): 0x4B baytını bir UART hattında çiz ve örnekle

**Adım 1 — Anla.** Hat 8N1 (8 veri biti, parite yok, 1 durdurma biti) çalışıyor. Verici 0x4B baytını gönderiyor. Alıcının saati, vericinin saatinden %6 yavaş (d = +0,06). Soru: alıcı baytı doğru okur mu? Okursa her bit nerede örneklenir? Okumazsa hangi bit yanlış olur?

**Adım 2 — Örnekle.** `0x4B = 0100 1011`. UART LSB önce gönderir: bit 0 = 1, bit 1 = 1, bit 2 = 0, bit 3 = 1, bit 4 = 0, bit 5 = 0, bit 6 = 1, bit 7 = 0. Çerçeve: `0 | 1 1 0 1 0 0 1 0 | 1` (başlangıç, veri, durdurma). Toplam 10 bit penceresi, indeksleri 0–9.

**Adım 3 — Kaba çöz.** Verici k. biti `[k, k+1)` aralığında tutar (birim: bir bit süresi). Alıcı k. biti `t_k = (k + 0.5) · (1 + d)` anında örnekler. Sapma yoksa her örnek kendi penceresinin ortasındadır. Sapma varsa örnek kayar; kayma k ile birlikte artar. Hangi k'da örnek pencereden çıkar?

**Adım 4 — Örüntü.** Kayma `(k + 0.5) · d` kadardır. Örnek, pencerenin sonunu geçer ve bir sonraki pencereye düşerse hata oluşur: `(k + 0.5)(1 + d) ≥ k + 1`. d = 0,06 için bu `(k + 0,5) · 0,06 ≥ 0,5`, yani `k ≥ 0,5/0,06 − 0,5 ≈ 7,83`. Bu, k = 8 ve k = 9 için hata demektir. Ama dikkat: k = 9 durdurma biti olduğundan ve bir sonraki pencere boşta (1) olduğundan, durdurma bitindeki hata görünmez. Bayt bozulması k = 8 ile olur, çünkü o bit 0 iken bir sonraki pencerede 1 okunur.

**Adım 5 — İyileştir.** Yapılabilecek iki şey var. Birincisi, saat sapmasını azaltmak: iki tarafın saatini harici bir kristalle sabitlemek ya da baud hızını bölen değerle tam tutturmak (genel bilgi: bazı UART çevre birimleri 16 kat aşırı örnekleme yapar, böylece örnek anı bit süresinin 1/16'sı kadar hassas olur). İkincisi, çerçeveyi bu hatadan bağımsız kılmak: Bölüm 45.3'teki COBS + CRC ile bozuk bayt reddedilir ve yanlış değer taşınmaz.

**Adım 6 — Doğrula.** Her k için örnek anını, pencereyi ve okunan biti tabloya yazalım. `d = 0` ve `d = +0,06` karşılaştırılıyor.

| k | t_k (d = 0) | t_k (d = +0,06) | Pencere | Hat biti | Okunan (d = +0,06) |
|---|---|---|---|---|---|
| 0 (başlangıç) | 0,50 | 0,53 | [0, 1) | 0 | 0 |
| 1 | 1,50 | 1,59 | [1, 2) | 1 | 1 |
| 2 | 2,50 | 2,65 | [2, 3) | 1 | 1 |
| 3 | 3,50 | 3,71 | [3, 4) | 0 | 0 |
| 4 | 4,50 | 4,77 | [4, 5) | 1 | 1 |
| 5 | 5,50 | 5,83 | [5, 6) | 0 | 0 |
| 6 | 6,50 | 6,89 | [6, 7) | 0 | 0 |
| 7 | 7,50 | 7,95 | [7, 8) | 1 | 1 |
| 8 | 8,50 | **9,01** | [8, 9) | 0 | **1** (pencere dışı) |
| 9 (dur) | 9,50 | **10,07** | [9, 10) | 1 | 1 |

Okunan bayt `1 1 0 1 0 0 1 1` olur ve değeri `0xCB`'dir. Yani d = +0,06'da 0x4B, 0xCB olarak okunur. Simülasyonda bunu sınadığımızda da aynı sonuç çıktı; tolerans taraması d = +5,88 üst sınırını bulmuştu, dolayısıyla +6 bu sınırın dışındadır.

::: ipucu
Bu örnek, tolerans sınırının neden **bir yüzde değil, bir bayt bazında** olduğunu gösterir. Sınırın altında her bayt doğru okunur; üstünde yalnızca belirli bit desenleri (son veri biti 0 olan baytlar) bozulur. Bu yüzden sınır testini yalnızca tek bir baytla yapmak yanıltıcı olur.
:::

**Bunu AI'sız yazabilir misin?** Son veri biti 1, diğer bitleri 0 olan bir bayt (`0x80`) düşün. Sapma negatif olduğunda hangi `k` değerinde hata oluşur? Bu, `0x4B` örneğindeki hesabın tersi yönüdür; formülü türetip bir tabloyla doğrula.

### Örnek 2 (★★): Bir I2C okuma işleminin bit izi

**Adım 1 — Anla.** Ana, 7 bitlik adresi `0x50` olan uyduya yazar: önce yazmaç adresi `0x10`, sonra tekrarlanan START ile okuma yapar ve iki bayt (`0x5A`, `0x6B`) alır. İzi, her bitin ne olduğunu ve her ACK/NACK'in nerede verildiğini gösterecek şekilde yazmamız istenir.

**Adım 2 — Örnekle.** Adres baytları: yazma için `0x50 << 1 | 0 = 0xA0`, okuma için `0x50 << 1 | 1 = 0xA1`. Bunların ikili gösterimi `1010 0000` ve `1010 0001`dir. Yazmaç adresi `0x10 = 0001 0000`. Veriler: `0x5A = 0101 1010`, `0x6B = 0110 1011`.

**Adım 3 — Kaba çöz.** İşlem sırası: START, adres yazma (8 bit, ACK), yazmaç (8 bit, ACK), tekrarlanan START, adres okuma (8 bit, ACK), veri 1 (8 bit, ACK ana tarafından), veri 2 (8 bit, NACK ana tarafından), STOP. Burada ACK'i kimin verdiğine dikkat et: adresten sonraki ACK uydudan, okunan verilerden sonraki ACK anadan gelir.

**Adım 4 — Örüntü.** Her baytta sekiz veri biti MSB önce gider, dokuzuncu bit ACK slotudur. Okumada veri biti uydu tarafından SDA'ya konur; ana yalnızca SCL yüksekken okur. Son okunan bayttan sonra ana NACK gönderir ve STOP çıkarır. Yazmadan okumaya geçişte STOP beklenmez; tekrarlanan START kullanılır.

**Adım 5 — İyileştir.** Okuma izinin her baytını, uydu tarafında hangi yazmaç adresinden geldiğiyle birlikte yaz. Bu örnekte okunan iki bayt `0x10` ve `0x11` yazmaçlarındadır; uydunun yazmaç işaretçisi her veri baytında bir artar. Böylece 'hangi bayt hangi konumdan geldi' sorusu izden doğrudan cevaplanır.

**Adım 6 — Doğrula.** Aşağıdaki tablo, her adımın SDA'da ne göründüğünü ve kimin sürdüğünü gösterir (ACK = SDA 0; NACK = SDA 1).

| Sıra | Gönderen | İçerik | Bitler (MSB önce) | SDA'da ne görünür | Yanıt |
|---|---|---|---|---|---|
| 1 | Ana | START | — | SCL yüksekken SDA düşer | — |
| 2 | Ana | Adres yazma `0xA0` | 1010 0000 | Ana sürer | Uydu ACK (SDA = 0) |
| 3 | Ana | Yazmaç `0x10` | 0001 0000 | Ana sürer | Uydu ACK |
| 4 | Ana | Tekrarlanan START | — | SCL yüksekken SDA düşer | — |
| 5 | Ana | Adres okuma `0xA1` | 1010 0001 | Ana sürer | Uydu ACK |
| 6 | Uydu | Veri 1 `0x5A` | 0101 1010 | Uydu sürer (ana okur) | Ana ACK (SDA = 0) |
| 7 | Uydu | Veri 2 `0x6B` | 0110 1011 | Uydu sürer | Ana NACK (SDA = 1) |
| 8 | Ana | STOP | — | SCL yüksekken SDA yükselir | — |

Tablo, simülasyon modelinin olay sırasıyla aynıdır (START, ACK, ACK, tekrarlanan START, ACK, OKU, OKU, STOP). Bu örnekte uydunun `0x10` ve `0x11` konumlarında önceden `0x5A` ve `0x6B` bulunduğunu varsayıyoruz; ana bu iki baytı okur.

**Bunu AI'sız yazabilir misin?** Aynı işlemi, ana yalnızca **bir** bayt okuyacak şekilde değiştir. Son okunan bayttan sonra SDA ne olmalı? Hangi sıra numarasında STOP gelir? Ve bu bir bayt okumada yazmaç adresi neden yine de gönderilmelidir?

### Örnek 3 (★★): Üç CAN düğümünün tahkimi

**Adım 1 — Anla.** Üç düğüm aynı anda 11 bitlik kimliklerle başlıyor: A `0x123`, B `0x0A5`, C `0x3F0`. Hangi düğüm kazanır? Hangi bitte hangisi kaybeder? Kaybettikten sonra hangisi hatta yazmayı sürdürür?

**Adım 2 — Örnekle.** İkili gösterimler (11 bit, MSB önce): `0x123 = 001 0010 0011`, `0x0A5 = 000 1010 0101`, `0x3F0 = 011 1111 0000`. Her mesajın başında bir SOF biti (0) vardır, ardından kimlik gelir.

**Adım 3 — Kaba çöz.** Her bitte hattın değeri, gönderen tüm düğümlerin AND'idir (baskın 0). Bir düğüm 1 gönderir ve hat 0 okursa kaybeder. İlk bit SOF'tur ve üç düğümün de 0'ı var, bu yüzden tahkim orada başlar.

**Adım 4 — Örüntü.** Bitleri karşılaştır: SOF (indeks 0): üçü de 0. ID10 (indeks 1): üçü de 0. ID9 (indeks 2): A 0, B 0, C 1. C 1 gönderir, hat 0 olur; C kaybeder. ID8 (indeks 3): A 1, B 0. A 1 gönderir, hat 0; A kaybeder. Geriye B kalır.

**Adım 5 — İyileştir.** Kazananın kendini tanıması için ayrı bir mekanizmaya gerek yoktur; tahkim kendi içinde kazananı seçer. Tasarım açısından önemli olan, düğümlerin öncelik tablosunu kimlik seçimiyle kurmaktır: kritik mesajlara en küçük kimlikleri ver.

**Adım 6 — Doğrula.** Aşağıdaki tablo, programın çıktısıyla aynı sonucu verir: `ornek_can.py` çıktısında `bit 2` satırında `0x3F0`, `bit 3` satırında `0x123` kaybeder ve kazanan `0x0A5`'tir.

| İndeks | Bit (A) | Bit (B) | Bit (C) | Hat | Kaybeden |
|---|---|---|---|---|---|
| 0 (SOF) | 0 | 0 | 0 | 0 | — |
| 1 (ID10) | 0 | 0 | 0 | 0 | — |
| 2 (ID9) | 0 | 0 | **1** | 0 | C |
| 3 (ID8) | **1** | 0 | (kaybetti) | 0 | A |

**Bunu AI'sız yazabilir misin?** `0x3F0` yerine `0x3F1` kullansaydın tahkim sonucu değişir mi? Hangi bitte? Dolgu biti kimlik bitlerinin arasına girdiğinde tahkim karşılaştırması hangi bitleri karşılaştırır?

### Örnek 4 (★★★): Daly BMS paketini elle kur, bozulmuş paketi yakala

**Adım 1 — Anla.** Daly BMS'ten gelen 0x90 yanıtı 13 bayttır. Bu örnekte iki şeyi yapacağız: yanıtın sağlamasını elle hesaplayacağız, sonra iki gerilim baytının yer değiştiği bir paketi hem toplama sağlamasıyla hem CRC-16 ile denetleyeceğiz. Ayrıca `main.c`'nin 0x95 çözümlemesindeki hatayı göreceğiz.

**Adım 2 — Örnekle.** Daly yanıtında baytlar şöyle: 0–3 başlık (`A5 01 90 08`), 4–5 gerilim (×0,1 V), 6–7 kullanılmıyor, 8–9 akım (ofsetli), 10–11 SOC (×0,1 %), 12 sağlama. Gerilim 52,3 V ise ham değer `523 = 0x020B`. Yani bayt 4 = `02`, bayt 5 = `0B`.

**Adım 3 — Kaba çöz.** Sağlama, bayt 0'dan 11'e kadar olan baytların toplamının alt 8 biti. Yanıtı kurmak için toplamı hesaplayacağız: `A5 + 01 + 90 + 08 + 02 + 0B + 00 + 00 + 74 + B3 + 03 + 6A`. Ardından gerilim baytlarını yer değiştirip yeniden hesaplayacağız.

**Adım 4 — Örüntü.** Toplama, bayt sırasına duyarsızdır: iki baytı yer değiştirmek toplamı değiştirmez. Bu yüzden sağlama, gerilim baytlarının yer değişimini yakalayamaz. CRC-16 ise sıraya duyarlıdır; bu yüzden aynı hatayı yakalar. Yani sorun bir "toplama" sorunudur, bir "veri" sorunu değildir.

**Adım 5 — İyileştir.** Doğrulanmamış bir yanıtı kabul etmemek için üç adım eklenir: (a) başlık (0xA5), adres (0x01) ve komut eşleşmesi denetlenir, (b) sağlama hesaplanır, (c) aralık denetimi yapılır (gerilim makul bir aralıkta mı?). CRC, Daly'nin kendi sağlamasının yerine geçmez; ancak BMS yanıtını STM32 ile Pi arasında taşırken kendi çerçevemizde kullanılabilir.

**Adım 6 — Doğrula.** Aşağıdaki tablo, programın çıktısıyla birebir uyuşur (`ornek_daly.py`).

| Alan | Orijinal (hex) | Yer değiştirmiş (hex) | Açıklama |
|---|---|---|---|
| Bayt 4–5 | 02 0B | 0B 02 | Gerilim ham değeri |
| Gerilim | 52,3 V | 281,8 V | 0x0B02 = 2818; ÷10 |
| Toplam (alt 8 bit) | DF | DF | Aynı; toplama yakalamaz |
| CRC-16 (12 bayt) | BC50 | CE95 | Farklı; CRC yakalar |
| Sağlama baytı (12) | DF | DF | Değişmedi |

Aynı paketin 0x95 hücre yanıtı için: `A5 01 95 08 01 0C E4 0C D7 0C F0 00 13`. Bayt 4 kare numarası (1). Hücre 1 bayt 5–6: `0C E4` = 3300 mV = 3,300 V. `main.c` ise `((bayt4 << 8) | bayt5) / 1000` hesaplar: `(0x01 << 8 | 0x0C) = 268`, yani 0,268 V. Program çıktısında `main.c hucre = 0.268 V` ve `dogru hucre1 = 3.300 V` satırları bu farkı gösterir.

**Bunu AI'sız yazabilir misin?** İstek çerçevesinin (`A5 40 90 08 00...`) sağlaması `0x7D`'dir; bunu elle doğrula. Sonra bayt 8–9 akım değerini `−12,5 A` için (ofsetli) yeniden hesapla ve sağlamayı güncelle. Son olarak, yanıtın adres baytını `0x02` yapıp sağlamayı yeniden hesaplarsan, `daly_sorgu`'nun hangi dönüş kodunu vereceğini söyle.

## Kendin Yap Projeleri

::: dikkat
Bu projeleri **yapay zekâ aracı olmadan** yapacaksın. Bölüm metnini, şekilleri ve arşivdeki kodu okuyabilirsin; ama kodu yazarken bir aracın öneri vermesine izin verme. Bir sorunda takıldığında önce kendi notlarına ve dokümana dön; hâlâ çözülmüyorsa ipucunu oku, sonra tekrar dene.
:::

### Proje 1 (★★): EV telemetri hattını sağlamlaştır

**Amaç.** EV Dashboard'un STM32'den Pi'ye giden JSON hattını, 45.11'deki sağlamlaştırılmış çerçeveye geçirmek. STM32 tarafındaki kodlayıcı, bu bölümde verilen `telemetri_cerceve.c` dosyasıdır. Senin işin Pi tarafındaki çözücüyü, sıra takibini ve bayatlık denetimini yazmak.

**Beklenen davranış.** Pi, her seri sonlandırıcıya kadar bir kare okur, COBS çözer ve CRC'yi doğrular. Yalnızca geçerli kareler işlenir. Sıra numarası bir önceki kareye göre atlamışsa kayıp sayısı artar; aynı sıra iki kez gelirse yinelenen sayısı artar. Son geçerli kareden 500 ms geçtiyse veri "bayat" işaretlenir. Bozuk bir kare, servisi düşürmeden atlanır.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Çözücüyü üç parçaya böl: kareyi ayırma (sonlandırıcıya kadar tampon), COBS çözme ve doğrulama, yükü açma. Yük açma için `struct` modülünün `<HBHHbbHBBBB` biçimini kullanabilirsin; bu biçim C'deki düzenle birebir eşleşir. Kayıp sayacını ve bayatlık zamanlayıcısını ayrı bir sınıfta tut. Test için Bölüm 39'daki sahte (fake) yaklaşımı kullan: gerçek seri port yerine baytları bir listeden veren bir nesne.

**Başarı kriterleri.**
1. Gürültü testinde (BER = 1 × 10⁻³, 20000 kare, sabit tohum 45) yanlış kabul edilen kare sayısı 0 olmalı.
2. 100 kare bilerek atıldığında kayıp sayacı tam 100 göstermeli; sıra numarası 255'ten 0'a sardığında da doğru çalışmalı.
3. Son geçerli kareden 500 ms sonra "bayat" işareti verilmeli; yeni bir kare gelince işaret kalkmalı.
4. Servis, JSON olmayan, uzunluğu yanlış ve geçersiz COBS içeren kareler karşısında çökmemeli.

### Proje 2 (★★★): I2C protokol çözücü

**Amaç.** Bir bit düzeyi I2C izini (her satır: zaman, SCL, SDA) alıp bunu START, STOP, adres, R/W, veri baytları ve ACK/NACK olarak çözen bir program yazmak. Bu, bir mantık analizörünün protokol çözücüsünün en küçük hâlidir (45.9).

**Beklenen davranış.** Çözücü, SCL yükselirken SDA değişirse START ya da STOP tanır (SCL yüksekken SDA'nın düşmesi START, yükselmesi STOP). SCL yükseldiğinde SDA'yı okuyup sekiz bit toplar, dokuzuncu bitin ACK olup olmadığını bildirir. Tekrarlanan START'ı yeni bir işlem başlatmadan ayırt eder.

**Önerilen yaklaşım (ipucu).** Her adımın durumunu (beklemede, bit toplama, ACK bekleme) bir değişkenle izle. Girdi olarak bir liste ya da CSV kullanabilirsin; girdiyi kendin üret: bu bölümdeki şekil 45.6'nın bit düzeyi karşılığını bir kenar kenar yazmak iyi bir alıştırmadır. Bir hata (ACK yokluğu, yarım bayt) gelirse çözücü hata durumuna geçmeli ve yeniden senkron olmalıdır.

**Başarı kriterleri.**
1. Yalnızca yazma yapan bir işlem (adres + iki bayt) doğru adres, doğru bayt ve doğru ACK bilgisiyle çözülmeli.
2. Tekrarlanan START içeren bir yazma-oku işlemi, iki ayrı çerçeve olarak değil tek bir işlem olarak görünmeli (aynı işlemin parçaları).
3. Hiçbir aygıtın ACK vermediği bir adres NACK olarak raporlanmalı.
4. Rastgele bozulmuş bir izde çözücü takılı kalmamalı; bir STOP'ta yeniden başlamalı.

## Ek Alıştırmalar

1. **★** 0x55 baytını 8N1 UART'ta gönder: `0101 0101` LSB önce hangi çerçeveyi üretir? Bit 0'dan başlayarak 10 bitlik diziyi yaz.
2. **★** Bir UART hattı 115200 bps'de çalışıyor. Tek bir bit süresi kaç µs'dir? 8N1 ile bir bayt kaç µs sürer?
3. **Mülakat ★★** İki tarafın saatleri birbirinden zıt yönde %2 sapıyor: toplam sapma %4. 8N1 çerçevesi güvende mi? Hangi sınıra göre karar verdin?
4. **★★** SPI'de CPOL = 1 ve CPHA = 1 kipi hangi kenarda veri hazırlar, hangi kenarda okur? Bir tablo çiz.
5. **★★** Dört uydu tek bir SPI hattına bağlanacak. CS hattı sayısı ile zincirleme (daisy chain) yapısını karşılaştır. Hangisi daha az pin kullanır, hangisi daha yavaş olur?
6. **★★** I2C'de bir ana 0x50 adresine yazarken 0x51'e de yazmaya çalışırsa tahkimde hangi bit belirleyici olur? Neden?
7. **★★** I2C hattında iki çekme direncini paralel bağlarsan etkin direnç ne olur? Bu, hızlı moda geçişte ne anlama gelir?
8. **★★★** CAN'de iki düğüm aynı kimlikle mesaj gönderirse ne olur? Tahkim bu durumu çözebilir mi? (İpucu: veri alanı ve CRC'ye bak.)
9. **Mülakat ★★★** Toplama sağlaması ile CRC-8 (poli 0x07) arasında bir karşılaştırma yap. Hangi hata türlerinde CRC-8 toplamadan üstün, hangilerinde eşit?
10. **Mülakat ★★** "Bir I2C hattında SDA 0'da kilitlendi. Hangi adımları izlersin ve neden?" sorusunu, 9 saat darbesi kuralını da kullanarak cevapla.
11. **Mülakat ★★★** "Kesme tabanlı bir UART alıcısında halka tampon kullanırken hangi yarış koşulu oluşabilir? Tek üretici tek tüketici olduğunda nasıl önlenir?" sorusunu yaz.
12. **Mülakat ★★** "CRC bütünlük sağlar mı, kimlik doğrulaması sağlar mı?" sorusunu iki cümlede yanıtla ve bir örnek ver.


## Kod Okuma Egzersizi

Bu egzersizde gerçek bir kaynak olarak Mert'in EV Dashboard projesini okuyacaksın. Kesitler kaynak dosyadan birebir alınmıştır; kod kartındaki satır numaraları yalnızca kesit içindir, dosyadaki gerçek numaralar kesitin başlığında verilmiştir. Dosyalar salt okunurdur; bu egzersiz bir inceleme egzersizidir, düzeltme değil. Bölüm 45.11'deki bulgularla karşılaştırmadan önce her kesiti kendi başına oku. Kaynakta tek satır olan bazı uzun satırlar kitap dizgisi için sarılmıştır; sarılan devam satırları dört boşlukla başlar.

**Kesit 1: `stm32/main.c`, satır 47–57 (Daly BMS'ten tek sorgu).**

```c
HAL_StatusTypeDef Daly_VeriOku(uint8_t komut, uint8_t *cevap)
{
    uint8_t istek_paketi[13] = {0xA5, 0x40, komut, 0x08,
    0,0,0,0,0,0,0,0, 0};
    uint8_t saglama = 0;

    for (int i = 0; i < 12; i++) saglama += istek_paketi[i];
    istek_paketi[12] = saglama;

    HAL_UART_Transmit(&bms_hatti, istek_paketi, 13, 100);
    return HAL_UART_Receive(&bms_hatti, cevap, 13, 200);
}
```

**Kesit 2: `stm32/main.c`, satır 62–78 (batarya ve hücre ayrıştırma).**

```c
void Daly_BataryaGuncelle(void)
{
    uint8_t gelen[13];

    if (Daly_VeriOku(DALY_KOMUT_SARJ, gelen) == HAL_OK) {
        arac.voltaj  = ((gelen[4] << 8) | gelen[5]) / 10.0f;
        arac.batarya = ((gelen[10] << 8) | gelen[11]) / 10;
    }

    if (Daly_VeriOku(DALY_KOMUT_SICAKLIK, gelen) == HAL_OK) {
        arac.bat_sicaklik = gelen[4] - 40;   /* Daly offset
    duzeltmesi */
    }

    if (Daly_VeriOku(DALY_KOMUT_HUCRE, gelen) == HAL_OK) {
        arac.hucre = ((gelen[4] << 8) | gelen[5]) / 1000.0f;
    }
}
```

**Kesit 3: `stm32/main.c`, satır 83–93 (Kelly motor sürücüsü).**

```c
void Kelly_MotorGuncelle(void)
{
    uint8_t istek[4] = {0x8A, 0x01, 0x00, 0x8B};
    uint8_t gelen[8] = {0};

    HAL_UART_Transmit(&motor_hatti, istek, 4, 100);
    if (HAL_UART_Receive(&motor_hatti, gelen, 8, 200) == HAL_OK) {
        arac.hiz            = (gelen[1] << 8) | gelen[2];   /* RPM ->
    km/h */
        arac.motor_sicaklik = gelen[4];
    }
}
```

**Kesit 4: `stm32/main.c`, satır 123–131 (JSON satırı).**

```c
void JSON_Olustur(void)
{
    snprintf(json_tampon, sizeof(json_tampon),
        "{\"spd\":%u,\"bat\":%u,\"volt\":%.1f,\"range\":%u,"
        "\"btemp\":%d,\"tmp\":%d,\"cell\":%.2f,\"gear\":\"%c\","
        "\"sigL\":%u,\"sigR\":%u,\"beam\":\"%s\"}\n",
        arac.hiz, arac.batarya, arac.voltaj, arac.menzil,
        arac.bat_sicaklik, arac.motor_sicaklik, arac.hucre,
    arac.vites,
        arac.sol_sinyal, arac.sag_sinyal, arac.far);
```

**Kesit 5: `rpi/telemetri.py`, satır 53–79 (STM32 okuma ve iletim döngüsü).**

```python
    while True:
        # STM32'den bir satir oku (JSON paketi)
        ham_veri = stm32.readline()

        if not ham_veri:
            continue

        try:
            metin = ham_veri.decode("utf-8").strip()
            veri  = json.loads(metin)
        except (UnicodeDecodeError, json.JSONDecodeError) as hata:
            logging.warning(f"Bozuk paket: {hata}")
            continue

        # Yayin frekansini sinirla (5 Hz)
        simdi = time.time()
        if simdi - son_gonderim < aralik:
            continue
        son_gonderim = simdi

        try:
            telemetriyeGonder(rfd, veri)
            logging.info(f"-> RFD900X: hiz={veri.get('spd')} "
                         f"bat={veri.get('bat')}%
    vites={veri.get('gear')}")
        except serial.SerialException as hata:
            logging.error(f"Telsiz yazma hatasi: {hata}")
            time.sleep(1)
```

**Kesit 6: `rpi/kadran.py`, satır 43–57 (WebSocket yayını).**

```python
async def yayinla(veri: dict):
    """Gelen veriyi tum bagli dashboard istemcilerine gonderir."""
    if not istemciler:
        return

    mesaj  = json.dumps(veri, ensure_ascii=False)
    kopuk  = set()

    for soket in istemciler:
        try:
            await soket.send(mesaj)
        except websockets.ConnectionClosed:
            kopuk.add(soket)

    istemciler.difference_update(kopuk)
```

**Sorular — cevaplamadan geçme:**

1. Kesit 1'deki `HAL_UART_Receive`, yanıtın kaç baytını bekliyor? Başlık (0xA5), adres ve komut eşleşmesi ile sağlama bu kodda denetleniyor mu? Denetlemiyorsa, hangi gerçek durum (örneğin tek bir bayt kaybı) bu fonksiyonu yanlış bir değerle `HAL_OK` döndürmesine yol açar? Yanıtını 45.4'teki yer değişimi örneğiyle bağla.
2. Kesit 2'de 0x95 (hücre) yanıtı `(gelen[4] << 8) | gelen[5]` ile çözülüyor. Bayt 4 bu yanıtta ne anlama gelir? ESPHome'un çözümünde hücre 1 hangi baytlardadır? Bu iki farklılık, bu satırın ürettiği değeri neye çevirir?
3. Kesit 3 "RPM -> km/h" yorumunu taşıyor. Kod bir dönüşüm yapıyor mu? Hız alanında hangi birim saklanır? Bu dönüşümü yapmak için hangi iki fiziksel bilgiye, bu dosyada olmayan hangi değerlere ihtiyaç duyarsın?
4. Kesit 2 ve `Daly_VeriOku`nun zaman aşımı değerlerini kullanarak, bir BMS tamamen sustuğunda `Daly_BataryaGuncelle` çağrısının en kötü süresini hesapla. Bu süre, ana döngünün 200 ms periyodunu nasıl etkiler? Bu sürede STM32 hangi veriyi hâlâ yayınlar ve bu veri yaşlı mı yeni mi görünür?
5. Kesit 4'teki `%f` biçimi gömülü bir hedefte güvenli olması için bağlayıcıda hangi bayrağa ihtiyaç duyar? Bu bayrağın varlığını ve yokluğunu, sembol tablosu üzerinden hangi komutla kontrol edersin? (45.10'daki deneyi tekrar et.)
6. Kesit 5'te JSON satırı geçerli ama bir nesne değilse (örneğin tek bir sayı), `veri.get` hangi satırda çağrılır? Bu satır, `try` bloğunun hangi `except` ile korunduğu düşünüldüğünde servisi neden düşürür? Kesit 6'daki `yayinla`'nın aynı türden bir kırılganlığı olup olmadığını, istemci kümesi üzerinde yapılan değişikliklere bakarak açıkla.

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
