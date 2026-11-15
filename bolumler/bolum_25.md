%% kisim_no: VI
%% kisim_ad: İşletim Sistemi & Mimari
%% bolum_no: 25
%% baslik: Bellek Hiyerarşisi

## Giriş: İşlemcinin en çok beklediği yer

Bölüm 1'de bir programın belleğini text, data, heap ve stack olarak çizdik. Bölüm 2'de `malloc` ile heap'ten yer istedik. Bölüm 7'de aynı `O(n)` toplamı iki farklı sırayla yapınca dizinin bağlı listeden neden hızlı olduğunu ölçtük ve sebebini "cache" diye bıraktık. Bu bölümde o kutunun içini açıyoruz.

Bugünkü işlemcinin hızı ile belleğin hızı arasındaki fark, bilgisayar mimarisinin en büyük sorunudur. Bir toplama işlemi birkaç ondalık nanosaniye sürerken, ana bellekten bir değer okumak yüz nanosaniyeyi aşabilir. Yani işlemci çoğu zaman yapacak işi değil, belleğin cevabını bekler. Bu farkı kapatmak için mühendisler belleği bir hiyerarşi olarak kurdu: küçük ve çok hızlı katmanlar, büyük ve yavaş katmanların önüne yerleştirildi. Programın hızı, hangi verinin hangi katmanda durduğuna çok bağlıdır.

Bu bilgi mülakatta sık sorulur: "önbellek nedir", "neden dizi bağlı listeden hızlı", "TLB ne işe yarar", "sayfa hatası ile önbellek kaçırması arasındaki fark nedir". Savunma sanayiinde de aynı konu karşına çıkar: gerçek zamanlı bir yazılımın en kötü süresi (WCET) önbellek kaçırmalarından etkilenir; gömülü bir işlemcide bellek koruması ile sanal bellek farklı mekanizmalardır (bu bölümün sonunda göreceğiz). MertOS'ta yazdığın sayfa tablosu ve heap yöneticisi bu bölümün gerçek bir uygulamasıdır.

::: not
Bu bölümde çok sayıda ölçüm var ve her biri bir makineye aittir. Sayıları ezberleme; kendi makinende aynı programları çalıştır ve kendi eğrini çiz. Bu bölümdeki değerler AMD Ryzen 7 6800H, WSL2 üzerinde Linux 6.6 çekirdeği, gcc 13.3 ve `-O2` ile alındı. Bir çalıştırmadan diğerine değerler yüzde 10-20 oynayabilir; önemli olan eğrinin şeklidir.
:::

## 25.1 Hiyerarşi: neden tek bir hızlı bellek yok?

En hızlı bellek, işlemcinin içindeki yazmaçlardır. Yazmaç bir saat döngüsünde erişilir, ama sayısı birkaç düzinedir ve her biri birkaç bayt tutar. Bir sonraki katman önbelleklerdir: L1, L2 ve L3. Onlar da SRAM'dir; yani hızlıdırlar ama bir bitlik yerleri pahalıdır ve çip üzerinde yer kaplarlar. Daha ileride DRAM, yani ana bellek vardır. Her bit için bir kapasitör ve bir transistör kullanır; ucuzdur, büyük olabilir, ama erişmesi yavaştır. En dışta ise SSD ve ağ gelir.

Neden tek bir büyük ve hızlı bellek yapılmıyor? İki sebep var. Birincisi maliyet ve fiziktir: hızlı bellek büyüdükçe hem enerji hem de sinyal yolu uzar, ışık hızı bile bir döngüde bir çipin büyük bir kısmını gezemez. İkincisi ekonomidir: 16 MB SRAM ile 16 GB DRAM aynı fiyata alınamaz. Mimari bu iki gerçeğe bir cevap olarak katmanları ayırır ve her katmanın yakın bir üstünü yedek olarak tutar.

Aşağıdaki tabloda bu makinede ölçtüğümüz ve bilinen değerleri ayırdık. "Ölçüm" yazanları bu bölümdeki C programlarıyla kendimiz aldık; "genel bilgi" yazanlar ise bu bölümde doğrulamadığımız, literatürde yaygın yaklaşık değerlerdir.

| Katman | Kapasite (bu makine) | Gecikme | Kaynak |
|---|---|---|---|
| Yazmaçlar | onlarca bayt | ~0,3 ns | genel bilgi (bir saat döngüsü) |
| L1 önbellek | 32 KB, çekirdek başına | 0,82 ns | ölçüm (Şekil 25.4) |
| L2 önbellek | 512 KB | ~2,5 ns | ölçüm (Şekil 25.4) |
| L3 önbellek | 16 MB, paylaşımlı | ~9-11 ns | ölçüm, 1-4 MB dizi |
| DRAM | 15 GB | 110-130 ns | ölçüm, 64 MB ve üstü |
| SSD (NVMe) | terabayt ölçeği | ~100 µs | genel bilgi |
| Ağ (aynı veri merkezi) | sınırsız | ~0,5 ms | genel bilgi |

Tablodaki en önemli oran, L1 ile DRAM arasındadır: yaklaşık 130 kat. Bu, bir programın hızını anlamak için "işlem sayısını say" yaklaşımının neden tek başına yetmediğinin en somut kanıtıdır. Bölüm 12'de Big-O'nun işlemleri saydığını ve onların maliyetini eşit varsaydığını gördük; bu tablo o varsayımın ne kadar yanlış olabileceğini gösterir.

Hiyerarşinin işe yaraması iki yerelliğe dayanır. **Zamansal yerellik**: az önce erişilen veriye kısa sürede tekrar erişilir (bir döngü değişkeni gibi). **Uzamsal yerellik**: bir adrese erişildiğinde komşu adreslere de erişilir (bir dizinin elemanları gibi). Önbellek bu iki varsayıma göre tasarlanır. Varsayım tutmazsa, yani program verisini rastgele dolaşırsa, katmanların hiçbiri yardım etmez. Bölüm 7'deki satır-sütun deneyinin bütün açıklaması budur.

![Şekil 25.1: Bellek hiyerarşisi. Üstte küçük ve hızlı katmanlar, altta büyük ve yavaş katmanlar. Gecikme sütunundaki ölçüm değerleri bu makineye aittir.](gorseller/b25_piramit.png)

## 25.2 Önbellek satırı: veri tek tek değil, blok blok gelir

Önbellek, belleği tek bayt tek bayt değil, sabit boyutlu bloklar hâlinde tutar. Bu bloğa **önbellek satırı (cache line)** denir. Bu makinede satır 64 bayttır. Değeri Linux'un sysfs arayüzünden ve `getconf` ile doğruladık. 

Bu bilgiyi her önbellek düzeyi için sysfs'ten okuyan küçük bir kabuk betiği, `getconf` ile de ek değerleri alır. Betik, her düzeyin boyutunu, yol sayısını (associativity), küme sayısını ve satır boyunu yazdırır:

```bash
#!/bin/bash
for i in 0 1 2 3; do
  d=/sys/devices/system/cpu/cpu0/cache/index$i
  echo "L$(cat $d/level) $(cat $d/type)" \
       "size=$(cat $d/size)" \
       "ways=$(cat $d/ways_of_associativity)" \
       "sets=$(cat $d/number_of_sets)" \
       "line=$(cat $d/coherency_line_size)" \
       "shared=$(cat $d/shared_cpu_list)"
done
getconf -a | grep -iE "DCACHE|L2_CACHE|L3_CACHE|PAGESIZE"
```

Betiğin çıktısı:

```term
$ bash cacheinfo.sh
L1 Data size=32K ways=8 sets=64 line=64 shared=0-1
L1 Instruction size=32K ways=8 sets=64 line=64 shared=0-1
L2 Unified size=512K ways=8 sets=1024 line=64 shared=0-1
L3 Unified size=16384K ways=16 sets=16384 line=64 shared=0-15
PAGESIZE                           4096
LEVEL1_DCACHE_SIZE                 32768
LEVEL1_DCACHE_ASSOC                8
LEVEL1_DCACHE_LINESIZE             64
LEVEL2_CACHE_SIZE                  524288
LEVEL2_CACHE_ASSOC                 8
LEVEL2_CACHE_LINESIZE              64
LEVEL3_CACHE_SIZE                  16777216
LEVEL3_CACHE_ASSOC                 16
LEVEL3_CACHE_LINESIZE              64
```

Bu çıktıdan üç sayı çıkar. L1 veri önbelleği 32 KB, 8 yollu ve 64 kümelidir: 64 × 8 × 64 = 32 768 bayt. L2 512 KB, 8 yollu, 1024 kümelidir. L3 16 MB, 16 yollu, 16384 kümelidir. Üç seviyede de satır 64 bayttır. Yani satır boyu bir mimari kararıdır ve program bunu değiştiremez; ama programın bu boyuta göre düzenlenmesi performansı doğrudan etkiler.

Bir bellek adresi, önbelleğin içinde hangi satıra ve hangi kümeye düştüğünü üç parçaya bölünerek anlatılır: **ofset**, **küme** ve **etiket (tag)**. Ofset, satırın içindeki bayt konumudur; 64 baytlık satır için 6 bit gerekir ($2^6 = 64$). Küme, adresin hangi kümeye düştüğünü söyler; 64 küme için yine 6 bit gerekir. Geri kalan üst bitler etikettir ve satırı benzersiz kılar. Bu bölünmeyi aşağıdaki şekilde ve Örnek 1'de elle yapacağız.

![Şekil 25.2: 48 bitlik sanal adresin önbellek tarafından bölünmesi. Örnek adres 0x7F3A12C4B5E8, bu önbellekte 23. kümenin 40. baytına denk gelir.](gorseller/b25_adres_bolunme.png)

Kümelerin ve satırların sayısı ile kapasite arasındaki ilişki basittir: kapasite = küme sayısı × yol sayısı × satır boyu. Bu ilişkiden bir sonuç çıkar: küme sayısı 2'nin kuvveti olduğu için, kümeyi seçen bitler adresin belirli bitleridir. İki adres bu bitlerde aynıysa aynı kümeye düşer. Bölüm 25.6'da bu gerçeğin nasıl performans kaybına dönüştüğünü ölçeceğiz.

## 25.3 Yerleştirme, çıkarma ve yazma politikaları

Bir adres önbelleğe geldiğinde üç soru sorulur. Hangi kümeye? Bu kümede hangi yola? Yol doluysa kim atılacak?

İlk soruyu yukarıdaki adres bölünmesi cevaplar: küme, adresin küme bitlerinden hesaplanır. İkinci sorunun cevabı önbellek organizasyonuna bağlıdır. **Doğrudan eşlemeli** (direct-mapped) önbellekte her küme tek yoldan oluşur: bir adres yalnızca bir yere gidebilir, arama tek karşılaştırmadır, ama iki adres aynı kümeye düşerse birbirini atar. **Tam ilişkili** (fully associative) önbellekte tek küme vardır ve her satır her yere gidebilir: çakışma yoktur, ama her erişimde bütün etiketler karşılaştırılmalıdır, bu da büyük önbellekte pahalıdır. **Küme ilişkili** (set-associative) tasarım ikisinin arasındadır ve gerçek işlemcilerde neredeyse hep budur: bu makinenin L1'i 8 yollu, L3'ü 16 yollu.

![Şekil 25.3: Küme ilişkili önbellek (64 küme, 8 yol). Adresin küme bitleri bir kümeyi seçer; etiket, o kümenin sekiz yolunda aranır. Hücre değerleri örnek amaçlıdır.](gorseller/b25_kume_iliskili.png)

Üçüncü soru çıkarma (eviction) politikasıdır. En iyi politika, en uzun süre kullanılmayacak satırı atmaktır; ama gelecekteki erişimi bilemeyiz. Pratikte en yaygın yaklaşım **LRU** (Least Recently Used), yani en uzun süredir kullanılmayanı atmaktır. Tam LRU bir yol için bile sıra bilgisi tutar; 8 yol için bu sıralama bilgisi saat döngüsü içinde güncellenebilmelidir, bu yüzden gerçek donanım genellikle yaklaşık bir sıra (pseudo-LRU) tutar. Burada yazacağımız simülatör tam LRU kullanır, çünkü davranışı tahmin etmesi kolaydır ve bölüm sonundaki alıştırmalar bunu test edecek.

Yazma tarafında iki temel politika var. **Write-through** her yazmayı hemen alt seviyeye de iletir. **Write-back** yazmayı önce önbellekte tutar, satır atılırken değişmişse (kirli bit, dirty bit) alt seviyeye yazar. Write-back daha az bellek trafiği üretir ve modern işlemcilerde yaygındır. Yazma kaçırmasında satırı önbelleğe getirme kararı da bir politikadır (write-allocate). Simülatörümüz yalnızca okumaları sayar; yazma politikalarının etkisini Bölüm 27'de çok çekirdekli tutarlılıkla birlikte göreceğiz.

Çok seviyeli önbelleklerde bir seviyedeki verinin diğerinde de olup olmadığı ayrı bir sorudur. **Kapsayıcı** (inclusive) bir L3, içindeki her satırın L1 ve L2'de de bulunmasını garanti eder; **dışlayıcı** (exclusive) bir L3 ise aynı satırı iki yerde tutmaz. Bu tercihlerin hangisinin bu makinede kullanıldığını bu bölümde doğrulamadık; genel bilgi olarak bilinen her iki politika da farklı işlemcilerde görülür.

Şimdi bu kararların hepsini tek bir simülatörde toplayalım. `onbellek.c` 32 KB, 8 yollu, 64 satırlı bir önbelleği taklit eder. Yol ve küme sayısı `-DYOL=` ve `-DKUME=` ile değiştirilebilir; böylece aynı kodla doğrudan eşlemeli ve tam ilişkili sürümleri de derleyeceğiz. Program iki modda çalışır: tek tek adresleri yazdırır ya da N×N bir matrisin tarama desenini simüle eder.

```c
/* onbellek.c - kume iliskili, LRU'lu bir onbellek simulatoru.
 * Varsayilan: 32 KB, 8 yol, 64 bayt satir -> 64 kume.
 * YOL ve KUME derleme aninda degistirilebilir:
 *   -DYOL=1 -DKUME=512   dogrudan eslemeli (ayni 32 KB)
 *   -DYOL=512 -DKUME=1   tam iliskili (ayni 32 KB)
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 onbellek.c -o onbellek
 * Kullanim:
 *   ./onbellek adres 0x1234 0xabcd ...
 *   ./onbellek matris N satir|sutun
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define SATIR 64
#ifndef YOL
#define YOL 8
#endif
#ifndef KUME
#define KUME 64
#endif

typedef struct {
    int gecerli;
    uint64_t etiket;
    uint64_t son;               /* son kullanim zamani (LRU) */
} Girdi;

static Girdi onb[KUME][YOL];
static uint64_t saat;
static long isabet, kacirma;

/* Tek bir erisim. Donus: 1 isabet, 0 kacirma. */
```

Kod, önbelleği bir `Girdi` dizisi olarak tutar. Her girdinin geçerli bayrağı, etiketi ve bir son kullanım zamanı vardır. `saat` sayacı her erişimde artar; LRU kararı, en küçük son kullanım zamanına sahip girdiyi seçerek verilir.

```c
static int erisim(uint64_t adr)
{
    uint64_t kume = (adr / SATIR) % KUME;
    uint64_t etiket = adr / SATIR / KUME;
    saat++;
    for (int y = 0; y < YOL; y++) {
        Girdi *g = &onb[kume][y];
        if (g->gecerli && g->etiket == etiket) {
            g->son = saat;
            isabet++;
            return 1;
        }
    }
    kacirma++;
    int sec = 0;                /* bos yer ya da en eski girdi */
    for (int y = 0; y < YOL; y++) {
        if (!onb[kume][y].gecerli) { sec = y; break; }
        if (onb[kume][y].son < onb[kume][sec].son) sec = y;
    }
    onb[kume][sec].gecerli = 1;
    onb[kume][sec].etiket = etiket;
    onb[kume][sec].son = saat;
    return 0;
}

static void adres_modu(int n, char **arg)
{
    printf("yol=%d kume=%d satir=%d\n", YOL, KUME, SATIR);
    printf("adres        etiket    kume ofset sonuc\n");
    for (int i = 0; i < n; i++) {
        uint64_t adr = strtoull(arg[i], NULL, 0);
        uint64_t ofs = adr % SATIR;
        uint64_t kume = (adr / SATIR) % KUME;
        uint64_t etiket = adr / SATIR / KUME;
        int s = erisim(adr);
        printf("0x%08llx 0x%06llx %5llu %4llu %s\n",
               (unsigned long long)adr, (unsigned long long)etiket,
               (unsigned long long)kume, (unsigned long long)ofs,
               s ? "ISABET" : "KACIRMA");
    }
}
```

`erisim` fonksiyonu tek bir adresi işler. Önce adresin kümesini ve etiketini hesaplar (`adr / SATIR % KUME` ve `adr / SATIR / KUME`). Sonra kümedeki yolları tarar; etiket eşleşirse isabet (hit) sayılır ve son kullanım zamanı güncellenir. Eşleşme yoksa kaçırma (miss) sayılır ve yeni etiket bir boş yola ya da en eski yola yazılır. Bu fonksiyon, bu bölümün geri kalanındaki bütün ölçümlerin temelidir.

```c

/* N x N int matrisinin tek gecisi; taban 0x10000, eleman 4 bayt. */
static void matris_modu(long n, int satir_once)
{
    uint64_t taban = 0x10000;
    for (long a = 0; a < n; a++)
        for (long b = 0; b < n; b++) {
            long i = satir_once ? a : b;
            long j = satir_once ? b : a;
            erisim(taban + (uint64_t)(i * n + j) * 4);
        }
    long toplam = isabet + kacirma;
    printf("N=%ld %-5s erisim=%ld isabet=%ld kacirma=%ld oran=%.3f\n",
           n, satir_once ? "satir" : "sutun", toplam, isabet, kacirma,
           (double)kacirma / (double)toplam);
}

int main(int argc, char **argv)
{
    if (argc >= 3 && strcmp(argv[1], "adres") == 0) {
        adres_modu(argc - 2, argv + 2);
        return 0;
    }
    if (argc == 4 && strcmp(argv[1], "matris") == 0 &&
        (strcmp(argv[3], "satir") == 0 ||
         strcmp(argv[3], "sutun") == 0)) {
        matris_modu(atol(argv[2]), strcmp(argv[3], "satir") == 0);
        return 0;
    }
    fprintf(stderr,
            "kullanim: %s adres <hex>... | matris N satir|sutun\n",
            argv[0]);
    return 1;
}
```

Program adresleri komut satırından alır ve her biri için kümeyi, ofseti ve sonucu yazdırır. Matris modu, N×N bir `int` matrisini `0x10000` adresinden başlayıp bellekte satır sırasıyla (`satir`) ya da sütun sırasıyla (`sutun`) dolaşır ve kaçırma oranını basar. Önce tek bir adresi çözelim:

```term
$ ./onbellek adres 0x7F3A12C4B5E8
yol=8 kume=64 satir=64
adres        etiket    kume ofset sonuc
0x7f3a12c4b5e8 0x7f3a12c4b    23   40 KACIRMA
```

Çıktı, Şekil 25.2'deki elle hesabı doğrular: etiket `0x7f3a12c4b`, küme 23, ofset 40. Bu adres tek başına bir kaçırmadır, çünkü önbellek boştur.

## 25.4 Ölçümle hiyerarşiyi keşfetmek: işaretçi kovalama

Önbellek boyutlarını ve gecikmelerini kataloglardan okuyabilirsin, ama en güvenilir yol ölçmektir. Bunun için bir yöntem gerekir: ölçtüğümüz erişimler birbirine bağımlı olmalı. Neden? Modern işlemci bağımsız yükleri paralel olarak sürdürebilir (buna bellek düzeyi paralelliği denir). Bölüm 12'de rastgele indeksle bir diziyi topladığımızda ortalama erişim başına yaklaşık 6 ns çıkmıştı; bu, işlemcinin birden çok kaçırmayı aynı anda beklediğinin işaretidir. Gecikmeyi ölçmek için ise her yükleme bir önceki yüklemenin sonucuna bağlanmalıdır. Buna **işaretçi kovalama** (pointer chasing) denir.

Yöntem şöyledir. Bellekte `n` tane 64 baytlık düğüm ayırıyoruz. Her düğümün ilk 8 baytı bir sonraki düğümün adresini tutar. Düğümlerin zincir sırası rastgele olmalı; yoksa donanım ön getirici (prefetcher) ardışık adresleri önceden getirir ve gecikmeyi ölçemeyiz. Rastgele ama tek bir döngü oluşturan bir sıra için Sattolo algoritmasını kullanıyoruz: bu algoritma her düğümü tam olarak bir kez ziyaret eden tek bir döngü üretir. Ölçüm, zincirde `2^22` adım yürür ve süreyi bu adım sayısına böler. Her boyut için beş deneme yapılır, medyan alınır.

```c
#define _POSIX_C_SOURCE 199309L
/* kovalama.c - isaretci kovalama ile onbellek basamaklari.
 * Her dugum bir onbellek satiri (64 bayt) boyutundadir ve bir
 * sonraki dugumun adresini tutar. Dugumler rastgele bir sirada
 * dizilir; her yukleme bir oncekinin sonucuna bagimlidir, bu
 * yuzden islemci yukleri paralel calistiramaz.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 kovalama.c -o kovalama
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

#define SATIR 64                 /* onbellek satir boyu */
#define ADIM (1u << 22)          /* olcum icin yukleme sayisi */
#define DENEME 5                 /* medyan icin deneme sayisi */

static uint64_t tohum = 88172645463325252ULL;   /* sabit tohum */

static uint64_t rastgele(void)                  /* xorshift64 */
{
    tohum ^= tohum << 13;
    tohum ^= tohum >> 7;
    tohum ^= tohum << 17;
    return tohum;
}

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + (double)t.tv_nsec;
}
```

Önce başlıklar ve yardımcılar. `_POSIX_C_SOURCE` satırı önemlidir: `-std=c11` ile derlerken `clock_gettime` gibi POSIX fonksiyonlarının görünmesi için bu makro gerekir. Bu makro olmadan derleyici `clock_gettime` için örtük bildirim uyarısı verir ve derleme başarısız olur. Bu, gerçek projelerde sık düşülen bir tuzaktır.

```c
static void *cikis;              /* derleyici donguyu silmesin diye */

static int karsilastir(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

/* Bir boyut icin ns/erisim degerinin medyanini dondurur. */
static double olc(size_t boyut)
{
    size_t n = boyut / SATIR;
    char *bolge = aligned_alloc(SATIR, n * SATIR);
    size_t *sira = malloc(n * sizeof *sira);
    if (!bolge || !sira) { perror("malloc"); exit(1); }

    for (size_t i = 0; i < n; i++) sira[i] = i;
    /* Sattolo karistirmasi: tek dongu uretir */
    for (size_t i = n - 1; i > 0; i--) {
        size_t j = rastgele() % i;
        size_t t = sira[i]; sira[i] = sira[j]; sira[j] = t;
    }
    for (size_t k = 0; k < n; k++) {             /* tek bir dongu */
        void **d = (void **)(bolge + sira[k] * SATIR);
        *d = bolge + sira[(k + 1) % n] * SATIR;
    }

    double sonuc[DENEME];
    for (int r = 0; r < DENEME; r++) {
        void *q = bolge + sira[0] * SATIR;
        double t0 = simdi_ns();
        for (size_t s = 0; s < ADIM; s++)
            q = *(void *volatile *)q;
        double t1 = simdi_ns();
        cikis = q;
        sonuc[r] = (t1 - t0) / ADIM;
    }
    qsort(sonuc, DENEME, sizeof sonuc[0], karsilastir);
    free(bolge);
    free(sira);
    return sonuc[DENEME / 2];
}
```

`olc` fonksiyonu bir boyut için bölgeyi ayırır, Sattolo ile rastgele tek döngüyü kurar ve zinciri `volatile` olmayan bir işaretçiyle dolaşırsa ne olacağını gösterir. Dikkat: ilk sürümde döngü `q = *(void **)q;` biçimindeydi. Sonuç, bütün boyutlar için 0,000 ns çıktı. Sebep şuydu: `q`'nun son değeri yalnızca `cikis`'a yazılıyordu ve derleyici ara yüklerin bir etkisi olmadığını görüp döngüyü tamamen silmişti. Ölçümde sıfır süre görmek, döngünün hiç çalışmadığının işaretidir. Çözüm, yükü `volatile` yapmaktır: `q = *(void *volatile *)q;`. Bu değişiklik, her yüklemeyi gerçekten bellekten yaptırır.

```c
int main(void)
{
    printf("boyut_bayt,ns_erisim\n");
    for (unsigned k = 12; k <= 28; k++) {
        size_t boyutlar[2] = { (size_t)1 << k,
                               3 * ((size_t)1 << (k - 1)) };
        for (int i = 0; i < 2; i++) {
            if (k == 28 && i == 1) continue;      /* 384 MB'a cikma */
            printf("%zu,%.3f\n", boyutlar[i], olc(boyutlar[i]));
            fflush(stdout);
        }
    }
    return 0;
}
```

`main` boyutları 4 KB'dan 256 MB'a kadar iki katına çıkan bir ölçekte gezer. Her adımda hem `2^k` hem de `3 × 2^(k-1)` boyutunu ölçtük; böylece eğride basamaklar daha yumuşak görünür. Tüm sonuçlar `boyut_bayt,ns_erisim` biçiminde CSV olarak yazılır ve bu CSV Şekil 25.4'ü üretir.

Ölçümden seçtiğimiz noktalar aşağıda. Tam tabloyu `engine/veri/b25_kovalama.csv` dosyasında bulabilirsin.

| Dizi boyutu | ns / erişim | Yorum |
|---|---|---|
| 16 KB | 0,81 | L1 içinde |
| 32 KB | 0,85 | L1 sınırında |
| 64 KB | 2,47 | L1 dışı, L2 içinde |
| 256 KB | 2,96 | L2 içinde |
| 1 MB | 9,10 | L2 dışı, L3 içinde |
| 4 MB | 12,74 | L3 içinde |
| 8 MB | 71,24 | geçiş bölgesi |
| 16 MB | 90,99 | L3 nominal boyutu |
| 64 MB | 110,02 | DRAM |
| 256 MB | 125,97 | DRAM |

![Şekil 25.4: İşaretçi kovalama ile ölçülen erişim gecikmesi (log ölçekte boyut). Üç basamak (L1, L2, L3) ve DRAM plato değerleri görülür. Kesikli çizgiler nominal önbellek boyutlarını gösterir.](gorseller/b25_kovalama_basamak.png)

Eğri üç basamağa ayrılır. Ölçüm, 32 KB'a kadar yaklaşık 0,8 ns'de düz kalır; bu L1 gecikmesidir ve 4,7 GHz boost hızında yaklaşık dört saat döngüsüne denk gelir (saat hızı varsayımı, genel bilgi). 48 KB ile 256 KB arasında 2,5 ns civarında düzlenir; bu L2'dir. Bir sonraki basamak 1 ile 4 MB arasındadır ve 9 ile 11 ns civarındadır; bu L3'tür. Sonra 6 ile 8 MB arasında keskin bir sıçrama olur ve DRAM düzeyi 110 ile 130 ns arasında kalır.

Dikkatli bir okur iki şeyi fark etmelidir. Birincisi: L3 nominal olarak 16 MB'tır, ama eğri 6 MB civarında yükselmeye başlıyor. Bunun bir nedeni, L3'ün bu sistemde paylaşımlı olmasıdır: WSL2 sanal makinesinde ve ana bilgisayarda çalışan diğer iş yükleri aynı L3'ü kullanır. İkincisi ve daha olası bir neden TLB'nin kapsama alanıdır: rastgele dolaşımda her düğüm farklı bir sayfadaysa, 8 MB 2048 adet 4 KB sayfaya denk gelir ve bu, işlemcinin ikinci seviye TLB'sinin kapasitesine yakındır (kesin sayı işlemciye göre değişir, genel bilgi). TLB'nin etkisini Bölüm 25.12'de ayrıca ölçeceğiz. Bu iki açıklamayı ayırt etmek için `perf stat` ile L3 ve TLB kaçırma sayaçlarını okumak gerekir; bu bölümde bunu yapmadık ve kesin neden konusunda emin değiliz.

Son olarak Bölüm 12 ile bağlantıyı kuralım. Bölüm 12'deki rastgele erişim ölçümünde 16 777 216 eleman için 102,56 ms ölçülmüştü; bu, erişim başına yaklaşık 6,1 ns demektir. Şimdi aynı makinede rastgele DRAM erişimi, bağımlı yüklerle, 110 ns ile 130 ns arasında. Aradaki yaklaşık yirmi kat fark, bağımsız yüklerin paralel sürdürülmesinden gelir: Bölüm 12'de işlemci birden çok kaçırmayı aynı anda beklemişti, burada ise her yükleme bir öncekini beklemek zorundaydı. Yani "rastgele erişim ne kadar yavaş" sorusunun cevabı, programın bağımlılık yapısına bağlıdır.

## 25.5 Adım taraması: satır boyunu ölçmek

Kovalama eğrisi bize boyutları verdi; şimdi bir önbellek satırının boyutunu ölçmeye bakalım. Yöntem basittir: büyük bir dizide sabit sayıda erişim yap, ama her erişimler arası adımı (stride) değiştir. Adım 4 bayt ise bir satırın on altı elemanı tek bir getirmeyle gelir ve erişim başına maliyet düşüktür. Adım 64 bayt ise her erişim yeni bir satıra düşer ve erişim başına maliyet satır getirme maliyetine yaklaşır. Eğrinin kırıldığı yer satır boyunu gösterir.

Bu deneyde erişimler bağımlı değildir; dizi zaten sırayla gezilir ve donanım ön getiricisi ardışık satırları önceden getirir. Yani ölçtüğümüz şey gecikme değil, bellekten satır getirme hızıdır. Bu bir ayrımdır ve sonuçların yorumunda önemlidir.

```c
#define _POSIX_C_SOURCE 199309L
/* satir.c - adim taramasi ile onbellek satir boyunu bulmak.
 * 64 MB'lik bir dizide her erisim, s bayt ileridedir ve toplam
 * erisim sayisi sabittir. s < 64 iken bir satir birden fazla
 * erisimle paylasilir; s >= 64 iken her erisim yeni bir satir
 * getirir. Egri 64'te duzlesiyorsa satir boyu 64 bayttir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 satir.c -o satir
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define BOYUT (64u << 20)        /* 64 MB, 2'nin kuvveti */
#define ERISIM (1u << 22)
#define DENEME 5

static volatile unsigned char *dizi;
static volatile unsigned char cikis;

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + (double)t.tv_nsec;
}

static int karsilastir(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

```

64 MB'lık dizi L3'ten büyük olduğu için adımlı erişim gerçekten ana belleğe gider. `volatile` kullanmamızın sebebi, derleyicinin `toplam` döngüsünü sonuçsuz diye atmasını engellemektir. Adım, `(idx + s) & (BOYUT - 1)` ile sarılır; BOYUT 2'nin kuvveti olduğu için maske bir mod işleminden çok daha ucuzdur ve dizinin sonunda başa döner.

```c
static double olc(size_t s)
{
    double sonuc[DENEME];
    for (int r = 0; r < DENEME; r++) {
        unsigned toplam = 0;
        size_t idx = 0;
        double t0 = simdi_ns();
        for (size_t i = 0; i < ERISIM; i++) {
            toplam += dizi[idx];
            idx = (idx + s) & (BOYUT - 1);
        }
        double t1 = simdi_ns();
        cikis = (unsigned char)toplam;
        sonuc[r] = (t1 - t0) / ERISIM;
    }
    qsort(sonuc, DENEME, sizeof sonuc[0], karsilastir);
    return sonuc[DENEME / 2];
}
```

`olc` her adım için beş ölçüm alır ve medyanı döndürür. Ölçümden önce `memset` ile tüm dizinin sayfaları gerçekten ayrılır; yoksa ilk erişimlerde sayfa hataları zamanlamayı bozar. Bu, Bölüm 25.10'da göreceğimiz talep üzerine sayfalamanın ölçümlere nasıl girdiğinin basit bir örneğidir.

```c
int main(void)
{
    dizi = malloc(BOYUT);
    if (!dizi) { perror("malloc"); return 1; }
    /* sayfa hatalari olcume girmesin diye once dokunulur */
    memset((void *)dizi, 1, BOYUT);

    printf("adim_bayt,ns_erisim\n");
    for (size_t s = 1; s <= 512; s *= 2)
        printf("%zu,%.3f\n", s, olc(s));
    free((void *)dizi);
    return 0;
}
```

`main` adımları 1'den 512'ye kadar ikişer katına çıkarır ve sonucu CSV olarak yazar. Çıktı:

```term
$ ./satir
adim_bayt,ns_erisim
1,0.451
2,0.460
4,0.460
8,0.505
16,0.695
32,1.164
64,1.995
128,3.170
256,3.164
512,3.903
```

Eğri, Şekil 25.5'te gösterilmiştir. Adım 1'den 8'e kadar gecikme neredeyse düzdür: her satır 64/s erişim sağladığı için satır getirme maliyeti erişimlere yayılır. Adım 8'den 64'e iki katına çıktıkça gecikme de kabaca artar. 64'te eğri kırılmalıdır, ama ölçümde kırılma yumuşaktır: 64'ten 128'e kadar hâlâ yükselir, 256'da düzleşir gibi görünür ve 512'de yeniden artar. Bu fark büyük olasılıkla donanım ön getiricinin (prefetcher) bitişik satırı da çekmesinden ve sayfa sınırı etkilerinden kaynaklanır; bu bölümde bunu ayrıca doğrulamadık (genel bilgi). Bu yüzden satır boyunu bu eğriden tek başına okumak yanıltıcı olabilir; kesin kanıt, sysfs'teki `coherency_line_size` değeridir: 64.

![Şekil 25.5: Adım taraması. Adım 64 bayta yaklaştıkça erişim başına maliyet artar; kesik çizgi sysfs'ten gelen satır boyudur.](gorseller/b25_satir_tarama.png)

Bu deneyin mülakatta sorulan sürümü şudur: "Bir diziyi 64 baytlık adımlarla dolaşırsan ne olur?" Cevap, her erişimin yeni bir satır getirdiği ve belleğin bant genişliğinin o adımlarla sınırlandığıdır. Bu, Bölüm 7'de dizi ile bağlı liste arasındaki farkın bir yüzüdür.

## 25.6 Çakışma kayıpları: 2'nin kuvveti adımı

Kümeleri seçen bitler adresin belirli bitleridir. Bu gerçeğin bir sonucu şudur: adımı 2'nin büyük bir kuvveti yaparsan, bütün erişimler aynı kümeye düşebilir. Bu duruma **çakışma kaçırması** (conflict miss) denir. Kapasite yeterliyken bile yol sayısından fazla satır aynı kümeye düşerse birbirini atar.

Bu fikri bir ölçümde gösterelim. `catisma.c` K düğümü adım kadar aralıklarla yerleştirir ve bunlardan bir halka kurar: her düğüm sonrakini gösterir. Halka bağımlı yüklerle dolaşılır, yani ölçülen şey gecikmedir. Üç adım deneyeceğiz: 64 bayt (her düğüm farklı kümede), 4096 bayt (bütün düğümler aynı kümede) ve 4160 bayt (4096 + 64, düğümler kümelere dağılır). Her biri için K = 8, 9 ve 16 deneyeceğiz. K = 8, L1'in yol sayısıdır.

```c
#define _POSIX_C_SOURCE 199309L
/* catisma.c - ayni kumeye dusen satirlarin catisma kaybi.
 * K dugum, adim kadar aralikla dizilir ve bir halka olusturur:
 * her dugum sonrakini gosterir. Adim 4096 bayt ise tum dugumler
 * ayni L1 kumesine duser; L1 8 yol oldugu icin K > 8 olunca
 * halkanin her turu L1'den kacar. Adim 4160 (4096 + 64) dugumleri
 * kumelere dagitir ve catisma olusmaz.
 * Erisimler birbirine bagimli oldugu icin olculen sure gecikmedir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 catisma.c -o catisma
 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define ADIM_SAYI (1u << 22)     /* her olcumde toplam yukleme */
#define DENEME 5

static void *cikis;

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + (double)t.tv_nsec;
}

static int karsilastir(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

```

Yardımcı fonksiyonlar bir önceki ölçüm programına çok benzer. Asıl farkı halkanın kurulmasında ve okumada: `olc` her düğümün işaretçisini bir sonrakine bağlar ve döngü `q = *(void *volatile *)q;` ile ilerler.

```c
static double olc(char *bolge, size_t adim, size_t k)
{
    for (size_t j = 0; j < k; j++) {        /* halka kur */
        void **d = (void **)(bolge + j * adim);
        *d = bolge + ((j + 1) % k) * adim;
    }
    double sonuc[DENEME];
    for (int r = 0; r < DENEME; r++) {
        void *q = bolge;
        double t0 = simdi_ns();
        for (unsigned s = 0; s < ADIM_SAYI; s++)
            q = *(void *volatile *)q;
        double t1 = simdi_ns();
        cikis = q;
        sonuc[r] = (t1 - t0) / ADIM_SAYI;
    }
    qsort(sonuc, DENEME, sizeof sonuc[0], karsilastir);
    return sonuc[DENEME / 2];
}
```

`olc` halkayı kurar ve `ADIM_SAYI` yükleme için süreyi ölçer. Her ölçüm için toplam yükleme sabittir, böylece farklı K değerleri aynı toplam iş için karşılaştırılabilir.

```c
int main(void)
{
    char *bolge = aligned_alloc(4096, 1u << 20);
    if (!bolge) { perror("malloc"); return 1; }
    size_t adimler[3] = { 64, 4096, 4160 };
    size_t kler[3] = { 8, 9, 16 };
    printf("adim_bayt,satir_sayisi,ns_erisim\n");
    for (int a = 0; a < 3; a++)
        for (int b = 0; b < 3; b++)
            printf("%zu,%zu,%.3f\n", adimler[a], kler[b],
                   olc(bolge, adimler[a], kler[b]));
    free(bolge);
    return 0;
}
```

`main` üç adımın ve üç K'nın bütün kombinasyonlarını dolaşır. Sonuç:

```term
$ ./catisma
adim_bayt,satir_sayisi,ns_erisim
64,8,0.832
64,9,0.834
64,16,0.826
4096,8,0.816
4096,9,2.343
4096,16,2.267
4160,8,0.868
4160,9,0.820
4160,16,0.821
```

Sonuçları okuyalım. Adım 64 ve 4160'ta K ne olursa olsun gecikme 0,82 ile 0,87 ns arasındadır: bütün düğümler L1'e sığar ve kümeler dengeli dağılır. Adım 4096'da K = 8 hâlâ L1'de kalır (0,82 ns), çünkü 8 düğüm 8 yola sığar. K = 9 olduğunda gecikme 2,34 ns'ye çıkar: düğüm sayısı yol sayısını bir aştığı için LRU halkanın her turunda en eski düğümü atar ve bir sonraki turda o düğüm L1'de yoktur. Düğüm L2'den gelir, yani 2,5 ns civarı L2 gecikmesidir. K = 16 için de aynı durum geçerlidir (2,27 ns).

Bu deneyden çıkan kural şudur: aynı kümeye giden satır sayısı yol sayısını aşarsa, önbellek kapasitesi yeterli olsa bile erişim bir alt düzeye düşer. Bu, Bölüm 25.3'te küme ilişkili tasarımın bir bedelidir. Bu kuralın pratikteki sonucu, 2'nin kuvveti boyutlu tamponlar ve satır uzunluklarıdır; bir matrisin satır genişliğinin 2'nin kuvveti olması sütun taramasını çakışmalı hâle getirebilir. Bunu sonraki bölümde matris örneğinde göreceğiz.

## 25.7 Önbelleğe dostu algoritma: blok (tiled) matris çarpımı

Bölüm 7'de bir matrisi satır ve sütun sırasıyla dolaşmanın farkını görmüştük. Burada aynı fikri bir adım daha ileri götüreceğiz: matris çarpımında hem `A`'nın hem `B`'nin erişim desenini düzenleyerek önbelleği en iyi kullanmak. Üç erişim düzeni karşılaştırıyoruz.

**ijk** sırası çarpımın en doğrudan yazılışıdır: her `C[i][j]` için `A`'nın bir satırını ve `B`'nin bir sütununu okur. `B`'nin sütun okuması, bellekte her adımda bir satır (`N * 8` bayt) atlamak demektir. **ikj** sırası iç iki döngüyü değiştirir: `A[i][k]` tek bir skaler olur ve `B`'nin satırı ile `C`'nin satırı bellek sırasında gezilir. Bu sıra hem önbellek dostudur hem de iç döngünün, derleyicinin SIMD ile vektörleştirebileceği bir biçim almasını sağlar (genel bilgi; `gcc -O2 -fopt-info-vec` ile kontrol edilebilir). **Blok** sürümde matris 32 × 32'lik kutulara bölünür; her kutu üç kutunun (A, B ve C'nin birer kutusu) toplamda L1'e sığacağı kadar küçüktür ve kutu içindeki veri, kutu tamamlanana kadar önbellekte kalır.

```c
#define _POSIX_C_SOURCE 199309L
/* matris.c - ayni O(n^3) carpimin uc erisim duzeni.
 * ijk : B'yi sutun sutun okur (her adim N*8 bayt atlar).
 * ikj : B'yi satir satir okur (bellek sirasi).
 * blok: 32x32 kutularla calisir; kutular L1'e sigar.
 * Sonuclar tam sayi oldugu icin toplamlar birebir karsilastirilir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 matris.c -o matris
 */
#include <stdio.h>
#include <string.h>
#include <time.h>

#define N 1024
#define BL 32
#define DENEME 3

static double A[N][N], B[N][N], C[N][N];   /* global: yigin degil */

```

Matrisler 1024 × 1024 `double` değerlerdir; her biri 8 MB tutar, yani toplam 24 MB. Bu, L3'ten büyüktür; önbellek etkisi bu yüzden görünür olur. Sonuçlar tam sayı olduğu için üç yöntemin toplamı birebir eşleşmelidir; bu, ölçümün yanlış bir yolla hızlanmadığının kontrolüdür.

```c
static double simdi_s(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

static void ijk(void)
{
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            double s = 0;
            for (int k = 0; k < N; k++)
                s += A[i][k] * B[k][j];
            C[i][j] = s;
        }
}

static void ikj(void)
{
    for (int i = 0; i < N; i++)
        for (int k = 0; k < N; k++) {
            double a = A[i][k];
            for (int j = 0; j < N; j++)
                C[i][j] += a * B[k][j];
        }
}

static void blok(void)
{
    for (int ii = 0; ii < N; ii += BL)
        for (int kk = 0; kk < N; kk += BL)
            for (int jj = 0; jj < N; jj += BL)
                for (int i = ii; i < ii + BL; i++)
                    for (int k = kk; k < kk + BL; k++) {
                        double a = A[i][k];
                        for (int j = jj; j < jj + BL; j++)
                            C[i][j] += a * B[k][j];
                    }
}
```

Üç çarpım fonksiyonu yan yana. `ikj` ve `blok` aynı iç döngüyü kullanır; fark, blok sürümde üç döngü daha bulunmasıdır. `ijk` ise `s` adında bir toplayıcı kullanır, yani iç döngü bir indirgemedir. Kayan nokta toplamanın sırası değiştirilemediği için derleyici bu döngüyü `-O2` ile tipik olarak vektörleştirmez.

```c
static double toplam(void)
{
    double s = 0;
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            s += C[i][j];
    return s;
}

static void calistir(const char *ad, void (*f)(void))
{
    double sn[DENEME], ss = 0;
    for (int r = 0; r < DENEME; r++) {
        memset(C, 0, sizeof C);
        double t0 = simdi_s();
        f();
        sn[r] = simdi_s() - t0;
    }
    ss = toplam();
    /* medyan: 3 denemenin ortancasi */
    double a = sn[0], b = sn[1], c = sn[2], m;
    if ((a <= b && b <= c) || (c <= b && b <= a)) m = b;
    else if ((b <= a && a <= c) || (c <= a && a <= b)) m = a;
    else m = c;
    printf("%-6s %8.3f s   toplam=%.0f\n", ad, m, ss);
}

int main(void)
{
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            A[i][j] = (i * j) % 7 + 1;
            B[i][j] = (i + j) % 5 + 1;
        }
    calistir("ijk", ijk);
    calistir("ikj", ikj);
    calistir("blok", blok);
    return 0;
}
```

`calistir` her yöntemi üç kez çalıştırır, `C`'yi her seferinde sıfırlar ve medyan süreyi yazdırır. Son çıktı bütün `C` toplamını da gösterir; üç satırda da aynı sayı görünmelidir.

```term
$ ./matris
ijk       5.644 s   toplam=11490899958
ikj       0.441 s   toplam=11490899958
blok      0.295 s   toplam=11490899958
```

Sonuçlar Şekil 25.6'da gösterilmiştir. Son çalıştırmada `ijk` 5,64 s sürerken `ikj` 0,44 s ve `blok` 0,30 s sürdü. Aynı programın ilk çalıştırmasında `ijk` 6,62 s, `blok` 0,37 s ölçülmüştü; yani `ijk`'ye göre blok sürümün kazancı iki çalıştırmada da 18 ile 19 kat arasındaydı. Bu oran, Bölüm 12'de aldığımız 32 katlık oranla aynı ilkeye dayanır: erişim sırası önbellek kullanımını belirler. Fark, bu kez matris çarpımında ve iki düzenlemenin birlikte uygulanmasıyla ortaya çıkar.

![Şekil 25.6: N = 1024 için üç çarpım yöntemi. Sütun okumalı ijk en yavaş; satır okumalı ikj yaklaşık on üç kat hızlı; blok sürüm birkaç kat daha da hızlıdır.](gorseller/b25_matris.png)

Dikkatli bir okur iki sayıyı ayırmalıdır. `ijk`'den `ikj`'ye geçiş kazancın çoğunu verir (13 ile 15 kat arası, iki çalıştırmada). Bunun ana nedeni erişim sırasıdır ve derleyicinin iç döngüyü vektörleştirebilmesidir. `ikj`'den `blok`'a geçiş daha küçük bir kazanç (1,2 ile 1,5 kat arası) verir. Bunun nedeni, `ikj`'nin de `B`'nin tamamını her `i` için yeniden okuması ve bu yüzden 8 MB'lık `B`'nin L3'e sığmamasıdır: blok sürüm aynı kutuyu tekrar tekrar kullanarak bu yeniden okumayı azaltır. Bu kazancın `N` ile nasıl değiştiğini bu bölümde ölçmedik; `N = 1024` yalnızca bir örnektir. Alıştırmalarda bu ölçümü sana bırakıyoruz.

Blok boyutu da bir karardır. 32 × 32 `double` kutusunun üç tane olması 24 KB eder ve L1'in 32 KB'ına sığar. Kutu daha büyük olursa L1'den taşar, daha küçük olursa döngü yükü artar. Bu seçim için ideal bir değer yoktur; işlemciye ve veri tipine göre ölçülerek bulunur.

## 25.8 Sanal bellek: adres bir sözleşmedir

Program bir adres kullandığında, o adres fiziksel RAM'deki gerçek bir yer değildir. Bir sanal adrestir ve işletim sistemi ile donanımın birlikte uyguladığı bir sözleşmenin parçasıdır. İşlemcinin içindeki **MMU** (bellek yönetim birimi) her erişimde sanal adresi fiziksel adrese çevirir. Çeviri bulunamazsa ya da izin ihlal edilirse işlemci bir **sayfa hatası** (page fault) istisnası üretir ve işletim sistemi kodu bu durumu çözer ya da süreci sonlandırır.

Bu sözleşmenin dört pratik faydası vardır. **Yalıtım**: her sürecin kendi adres uzayı vardır ve bir süreç diğerinin belleğini doğrudan göremez. **Büyük ve sürekli bir adres uzayı**: fiziksel bellek parçalı olabilir, ama süreç ona bitişik bir bölge gibi bakar. **Paylaşım**: aynı fiziksel sayfa iki sürecin adres uzayında eşlenebilir; kütüphane kodu bunun en yaygın örneğidir ve RAM'de tek kopya tutulur. **Koruma**: her sayfanın okuma, yazma ve çalıştırma izinleri vardır; kod sayfası yazılamaz, veri sayfası çalıştırılamaz. Bunun bir örneğini Bölüm 25.9'da PTE bitlerinde göreceğiz.

Sayfa, sanal ve fiziksel adres uzayının eşlendiği en küçük birimdir. Bu makinede boyutu 4096 bayttır:

```term
$ getconf PAGESIZE
4096
```

Sayfa boyutu 2'nin kuvveti olduğu için bir sanal adresin ofseti, adresin alt 12 bitidir. Geri kalan üst bitler sayfa numarasıdır ve çeviri yalnızca bu numarayı değiştirir. Bu yüzden ofset çeviride değişmez; bir sayfanın içindeki bayt konumu korunur. Çevirinin fiziksel çerçevesi ise bir sayfa tablosundan gelir.

## 25.9 Dört seviyeli sayfa tablosu

x86-64 mimarisinde sanal adres 48 bittir (en yüksek 16 bit çeviride kullanılmaz, işaret genişlemesi yapılır). Bu 48 bit beş parçaya bölünür: dört seviyeli tablonun her biri için 9 bit ve sayfa ofseti için 12 bit. Her tablo 512 girdi içerir ve her girdi 8 bayttır; yani bir tablo tam olarak 4 KB, yani bir sayfadır. Bu, tablonun kendisinin de bellekte bir sayfa tutması ve sayfa tablosunun sayfa tablosu gibi davranması anlamına gelir.

Çeviri şöyle işler. CR3 yazmacı en üstteki PML4 tablosunun fiziksel adresini tutar. Sanal adresin bit 47-39'u PML4'te bir girdi seçer; bu girdi bir sonraki tablonun (PDPT) fiziksel adresini verir. Bit 38-30 PDPT'de, bit 29-21 PD'de, bit 20-12 PT'de bir girdi seçer. PT'deki girdi, sonunda fiziksel çerçevenin adresini verir; bit 11-0 ise çerçeve içindeki ofsettir. Dört tablo okuması, en kötü durumda dört ek bellek erişimi demektir (son veri erişimi buna eklenir). Bu yüzden her çeviriyi önbelleğe almak gerekir: bu iş TLB'nin (Bölüm 25.12) görevidir.

Her girdinin 64 bitinde adres ve bayraklar birlikte bulunur. Adres bitleri 12'den 51'e kadardır (sayfa hizalı olduğu için alt 12 bit boştur). Bayrak bitlerinin anlamı, Mert'in MertOS çekirdeğindeki VMM başlığında da aynı konumlarda tanımlanmıştır (alıntıda satır sonu yorumları bir üst satıra alındı; sabitler ve değerler aynen korundu):

```cpp
    // Sayfa bellekte
    static constexpr uint64_t PRESENT      = (1ULL << 0);
    // Yazılabilir
    static constexpr uint64_t WRITABLE     = (1ULL << 1);
    // User-space erişim
    static constexpr uint64_t USER         = (1ULL << 2);
    // Write-through cache
    static constexpr uint64_t WRITE_THRU   = (1ULL << 3);
    // Cache devre dışı
    static constexpr uint64_t NO_CACHE     = (1ULL << 4);
    // CPU set eder
    static constexpr uint64_t ACCESSED     = (1ULL << 5);
    // CPU set eder (PT için)
    static constexpr uint64_t DIRTY        = (1ULL << 6);
    // 2MB/1GB huge page
    static constexpr uint64_t HUGE         = (1ULL << 7);
    // TLB'de tut
    static constexpr uint64_t GLOBAL       = (1ULL << 8);
    static constexpr uint64_t NO_EXECUTE   = (1ULL << 63);  // NX bit
```

Dikkat edilecek üç bayrak vardır. **Present (P)**, girdinin geçerli olduğunu söyler; 0 ise sayfa bellekte değildir ve erişim sayfa hatasına yol açar. **Writable (R/W)** yazmaya izin verir; **NX** (bit 63) çalıştırmayı yasaklar, yani veri sayfalarında kod çalıştırılamaz. Bu son bit, yığın taşması saldırılarının zorlaştırılmasında kritiktir (Bölüm 32'de güvenlik tarafını göreceğiz). **HUGE** (bit 7, PS) ise bir PD girdisini doğrudan 2 MB'lık bir sayfaya işaret ettirir; bu, çeviri zincirinin bir seviye kısalması demektir ve Bölüm 25.12'de ölçeceğiz.

Aşağıdaki şekil, Bölüm 25.9'da kullanacağımız örnek adresin dört seviyeli yürüyüşünü gösterir. Değerleri elle hesapladık ve aşağıdaki kod ile doğruladık.

![Şekil 25.7: Dört seviyeli sayfa tablosu yürüyüşü. Her seviye 9 bitlik bir indeksle bir sonraki tablonun adresini bulur; son seviyede çerçeve ve 12 bitlik ofset birleşir. Değerler, 0x5AD9861362A0 adresi için bu çalıştırmada ölçülen heap adresinden alınmıştır.](gorseller/b25_sayfa_yuruyusu.png)

Şimdi bu hesabı bir programla doğrulayalım. `adres_uzayi.c` üç farklı bölgeden birer adres alır (kod, veri, heap, mmap ve yığın), her biri için dört indeksi hesaplar ve sonra `/proc/self/maps` dosyasını da okur. Önce programın başlangıcı:

```c
/* adres_uzayi.c - surecin sanal adres haritasi,
 * 4 seviyeli sayfa tablosu indeksleri.
 * Her bolumden bir adres alir, 48 bitlik adresin sayfa tablosu
 * indekslerine boler ve /proc/self/maps'i (kisaltilmis) yazar.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 adres_uzayi.c -o adr
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int veri_baslangic = 7;              /* .data */
int veri_bss;                        /* .bss  */
const char *metin = "merhaba";       /* .rodata'daki dize */

static void indeks(const char *ad, uintptr_t va)
{
    printf("%-7s %016llx %3llu %4llu %4llu %4llu\n", ad,
           (unsigned long long)va,
           (unsigned long long)((va >> 39) & 0x1FF),
           (unsigned long long)((va >> 30) & 0x1FF),
           (unsigned long long)((va >> 21) & 0x1FF),
           (unsigned long long)((va >> 12) & 0x1FF));
}
```

Bu bölümde `_GNU_SOURCE` tanımlıyoruz; `/proc` dosyalarında kullandığımız bazı fonksiyonlar için gerekli. `veri_baslangic` başlangıç değeri olan bir global olduğu için `.data`'da, `veri_bss` ise `.bss`'te yaşar. `indeks` fonksiyonu adresin dört indeksini `(va >> 39) & 0x1FF` gibi kaydırma ve maske işlemleriyle hesaplar; bu, Bölüm 1'de gördüğümüz bit işlemlerinin doğrudan bir uygulamasıdır.

```c
static void harita(void)
{
    FILE *f = fopen("/proc/self/maps", "r");
    char satir[512];
    if (!f) { perror("maps"); return; }
    while (fgets(satir, sizeof satir, f)) {
        unsigned long a, b;
        char izin[8];
        sscanf(satir, "%lx-%lx %7s", &a, &b, izin);
        char *yol = satir;
        for (int k = 0; k < 5; k++) {          /* 5 alan atla */
            yol = strchr(yol, ' ');
            while (yol && *yol == ' ') yol++;
        }
        if (yol) yol[strcspn(yol, "\n")] = '\0';
        char *ad = (yol && *yol) ? strrchr(yol, '/') : NULL;
        printf("%012lx-%012lx %s %s\n", a, b, izin,
               ad ? ad + 1 : (yol && *yol ? yol : "(anonim)"));
    }
    fclose(f);
}
```

`harita` fonksiyonu `/proc/self/maps` dosyasını satır satır okur. Her satırda adres aralığını ve izinleri alır, yol alanını ise beşinci boşluktan sonra bulur. Yol boşsa bölge anonimdir, yani bir dosyaya bağlı değildir. Çıktıyı kısa tutmak için yalnızca dosya adının son kısmını yazdırıyoruz.

```c
int main(void)
{
    int yerel = 0;
    char *yigin_ayri = malloc(100);
    char *buyuk = malloc(1u << 20);      /* 1 MB: mmap ile gelir */

    printf("bolge    sanal adres      PML4 PDPT   PD   PT\n");
    indeks("kod", (uintptr_t)&harita);
    indeks("rodata", (uintptr_t)metin);
    indeks("data", (uintptr_t)&veri_baslangic);
    indeks("bss", (uintptr_t)&veri_bss);
    indeks("heap", (uintptr_t)yigin_ayri);
    indeks("mmap", (uintptr_t)buyuk);
    indeks("yigin", (uintptr_t)&yerel);

    printf("\n/proc/self/maps:\n");
    harita();
    free(yigin_ayri);
    free(buyuk);
    return 0;
}
```

`main` her bölgeden bir adres seçer, indeksleri yazdırır ve haritayı basar. Bu çalıştırmanın ilk kısmı şöyle:

```term
$ ./adr
bolge    sanal adres      PML4 PDPT   PD   PT
kod     00005ad974c53460 181  357  422   83
rodata  00005ad974c540cd 181  357  422   84
data    00005ad974c56010 181  357  422   86
bss     00005ad974c56024 181  357  422   86
heap    00005ad9861362a0 181  358   48  310
mmap    0000751cadc47010 234  114  366   71
yigin   00007ffe197bd564 255  504  203  445
```

Heap satırındaki değerleri elle doğrulayalım. Sanal adres `0x5AD9861362A0`. PML4 indeksi bit 47-39'dan gelir ve 181'dir. PDPT indeksi 358, PD indeksi 48, PT indeksi 310 ve ofset `0x2A0 = 672`'dir. Şekil 25.7 aynı değerleri kullanır. Ofset satırın son üç hanesi olarak da okunabilir: `2A0` ilk 12 bitin içindedir ve adresin son üç hex hanesiyle eşleşir.

Bu çıktıda üç ilginç gözlem var. Birincisi, kod, rodata, data ve bss aynı PML4, PDPT ve PD girdisini paylaşıyor; yani küçük bir program için sayfa tablosunun üst seviyeleri çok az yer kaplar. İkincisi, yığın adresi (`0x7ffe...`) PML4 indeksi 255'te, yani adres uzayının en üst bölgesinde. Üçüncüsü, `mmap` adresi ile heap adresi arasında çok büyük bir mesafe var: heap ve kod ilk 512 GB'de (PML4=181), `mmap` bölgesi ise farklı bir PML4 girdisinde (234). Bu, glibc'nin büyük istekleri neden ayrı bir bölgeye koyduğunu ve Linux'un bölgeleri neden seyrek dağıttığını anlamanın başlangıcıdır; Bölüm 25.11'de haritanın tamamına bakacağız.

## 25.10 Talep üzerine sayfalama ve sayfa hatası

Bir sanal sayfa eşlenmiş olabilir ama bellekte olmayabilir. İşletim sistemi bir süreç başlatırken yığın ve heap için büyük bölgeler ayırır, ama bu bölgelerin hiçbir fiziksel çerçeveye bağlı olmadığı sayfalar olabilir. İlk erişimde sayfa tablosundaki P biti 0'dır, işlemci sayfa hatası istisnası üretir, çekirdek boş bir çerçeve bulur, sayfayı sıfırlar, tabloyu günceller ve komutu yeniden çalıştırır. Bu süreç **talep üzerine sayfalama** (demand paging) olarak adlandırılır: bellek, gerçekten kullanıldığında gelir.

Sayfa hataları iki sınıfa ayrılır. **Küçük hata** (minor fault) bellekte zaten bulunan bir sayfaya ulaşmak için çekirdeğin tabloyu düzeltmesidir; sıfırlanmış yeni bir sayfa ya da paylaşılan bir sayfanın eşlenmesi bu sınıftadır. **Büyük hata** (major fault) sayfanın diskten okunmasını gerektirir: takas (swap) alanından ya da dosyadan. Büyük hatanın maliyeti milisaniye mertebesine çıkabilir ve bu, küçük hatanın maliyetinden çok daha büyüktür (genel bilgi).

Bu davranışı `/proc/self/pagemap` ile gözlemleyebiliriz. Bu dosya, her sanal sayfa için bir 64 bitlik girdi verir ve bit 63 sayfanın bellekte olup olmadığını (present) söyler. Fiziksel çerçeve numarası (PFN) ise çekirdek bunu yalnızca yetkili süreçlere gösterdiği için bu programda görünmez; bizim için present biti yeterlidir.

```c
/* talep.c - talep uzerine sayfalama (demand paging) gozlemi.
 * mmap ile 16 sayfalik sanal bolge ayirir. Hicbir sayfaya
 * dokunmadan /proc/self/pagemap icindeki "present" bitini okur.
 * Sonra yalnizca 4. sayfaya yazar ve degisimi gozlemler.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 talep.c -o talep
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/resource.h>

#define SAYFA 4096
#define SAYI 16

static long kucuk_hata(void)
{
    struct rusage u;
    getrusage(RUSAGE_SELF, &u);
    return u.ru_minflt;
}

/* Sanal adresin sayfa tablosu girdisi "present" mi? */
static int mevcut(int fd, char *va)
{
    uint64_t e = 0;
    off_t ofs = ((uintptr_t)va / SAYFA) * 8;
    if (pread(fd, &e, sizeof e, ofs) != sizeof e) return -1;
    return (int)((e >> 63) & 1);
}

```

`mevcut` fonksiyonu sayfa tablosu girdisine dolaylı olarak bakar: sanal adresi sayfa numarasına çevirir, `pagemap`'te o girdinin 8 baytını `pread` ile okur ve en yüksek biti döndürür. `kucuk_hata` ise `getrusage` ile süreç için küçük hata sayacını okur. Sayaç, `RUSAGE_SELF` seçeneğiyle süreç genelinde toplamı verir.

```c
static void goster(const char *etiket, int fd, char *bolge)
{
    printf("%s", etiket);
    for (int i = 0; i < SAYI; i++)
        printf("%d", mevcut(fd, bolge + i * SAYFA));
    printf("\n");
}

int main(void)
{
    int fd = open("/proc/self/pagemap", O_RDONLY);
    char *bolge = mmap(NULL, SAYI * SAYFA, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (fd < 0 || bolge == MAP_FAILED) { perror("hata"); return 1; }

    goster("dokunmadan once : ", fd, bolge);

    long h0 = kucuk_hata();
    bolge[3 * SAYFA] = 42;                 /* 4. sayfaya ilk yazma */
    long h1 = kucuk_hata();
    goster("4. sayfaya yazma: ", fd, bolge);
    printf("kucuk hata (1 yazma): %ld\n", h1 - h0);

    h0 = kucuk_hata();
    for (int i = 0; i < SAYI; i++)
        bolge[i * SAYFA] = 1;              /* kalan sayfalar */
    printf("kalan 15 sayfa      : %ld kucuk hata\n",
           kucuk_hata() - h0);
    goster("hepsi dokundu    : ", fd, bolge);

    munmap(bolge, SAYI * SAYFA);
    close(fd);
    return 0;
}
```

`main` 16 sayfalık bir bölge ayırır ve hiçbir sayfaya dokunmadan bitleri okur. Sonra yalnızca dördüncü sayfaya yazar ve farkı gözlemler. Kalan on beş sayfaya dokunulduğunda kaç küçük hata olduğunu da sayar.

```term
$ ./talep
dokunmadan once : 0000000000000000
4. sayfaya yazma: 0001000000000000
kucuk hata (1 yazma): 1
kalan 15 sayfa      : 15 kucuk hata
hepsi dokundu    : 1111111111111111
```

Çıktı beklenen davranışı gösterir. İlk satırda hiçbir sayfa bellekte değil. Dördüncü sayfaya tek bir yazma yaptığımızda yalnızca o sayfa `1` olur ve tam bir küçük hata sayılır. Kalan on beş sayfaya dokunulunca on beş küçük hata daha oluşur ve bütün bölge bellektedir. Bu, sayfanın birinci erişimde çekirdek tarafından getirildiğinin doğrudan kanıtıdır.

Bu mekanizmanın bir sonucu fork ve kopyalama-yazarken (copy-on-write) davranışıdır: `fork` sonrası ebeveyn ve çocuk sayfaları ilk başta aynı fiziksel çerçeveyi paylaşır ve yazma koruması ile işaretlenir; yazıldığında bir sayfa hatası oluşur ve çekirdek sayfayı kopyalar. Bunu Bölüm 26'da süreç oluşturma sırasında ayrıntılı göreceğiz. Dosya eşlemeleri ve sayfa önbelleği ise Bölüm 28'in konusudur.

## 25.11 Süreç adres uzayı: /proc/self/maps

Bir sürecin adres uzayının bütün haritası `/proc/self/maps` dosyasında durur. Yukarıdaki program, bu dosyanın yalnızca yol kısmını kısaltarak yazdırıyordu. Çıktının bu kısmı şöyledir:

```term
/proc/self/maps:
5ad974c52000-5ad974c53000 r--p adr
5ad974c53000-5ad974c54000 r-xp adr
5ad974c54000-5ad974c55000 r--p adr
5ad974c55000-5ad974c56000 r--p adr
5ad974c56000-5ad974c57000 rw-p adr
5ad986136000-5ad986157000 rw-p [heap]
751cada00000-751cada28000 r--p libc.so.6
751cada28000-751cadbb0000 r-xp libc.so.6
751cadbb0000-751cadbff000 r--p libc.so.6
751cadbff000-751cadc03000 r--p libc.so.6
751cadc03000-751cadc05000 rw-p libc.so.6
751cadc05000-751cadc12000 rw-p (anonim)
751cadc47000-751cadd4b000 rw-p (anonim)
751cadd52000-751cadd54000 rw-p (anonim)
751cadd54000-751cadd55000 r--p ld-linux-x86-64.so.2
751cadd55000-751cadd80000 r-xp ld-linux-x86-64.so.2
751cadd80000-751cadd8a000 r--p ld-linux-x86-64.so.2
751cadd8a000-751cadd8c000 r--p ld-linux-x86-64.so.2
751cadd8c000-751cadd8e000 rw-p ld-linux-x86-64.so.2
7ffe1979f000-7ffe197c0000 rw-p [stack]
7ffe197d1000-7ffe197d5000 r--p [vvar]
7ffe197d5000-7ffe197d7000 r-xp [vdso]
```

Her satır bir **bölge** (VMA, virtual memory area) tanımlar: aralık, izinler (r: okunur, w: yazılır, x: çalıştırılır, p: özel) ve kaynak. Şekil 25.8 bu bölgeleri adres sırasına göre çizer; adreslerin yüksekliğe orantılı olmadığını unutma, bölgeler eşit yükseklikte gösterilmiştir.

![Şekil 25.8: Bir sürecin sanal adres uzayı (bu çalıştırmadan). En alttaki bölgeler programın kendisi, en üstteki bölgeler çekirdeğin paylaştığı alanlardır. Bölge yükseklikleri eşittir; boyutlar orantılı değildir.](gorseller/b25_adres_haritasi.png)

Okunması gereken birkaç şey var. `adr` ile işaretli beş satır, programın kod (r-xp), salt okunur veriler (r--p) ve yazılabilir veri (rw-p) bölümleridir; bunlar Bölüm 1'deki text, rodata ve data'nın gerçek karşılıklarıdır. `[heap]` satırı, `malloc`'un küçük istekleri için kullandığı alandır ve programın hemen arkasında gelir. Anonim bir bölge olan 1 MB'lık `malloc` isteği ise ayrı bir eşlemedir: glibc büyük istekleri `mmap` ile ayırır (varsayılan eşik 128 KB'dır, genel bilgi).

`libc.so.6` ve `ld-linux-x86-64.so.2` paylaşımlı kütüphanelerdir. Her birinin kod ve veri bölümleri farklı izinlerle ayrı bölgelerde durur; kütüphanelerin arkasındaki anonim bölgeler, `.bss` gibi çalışma zamanı verileri için ayrılmış alanlardır (genel bilgi). `[stack]` yığındır; yığın büyüdükçe bu bölge aşağı doğru genişler. En üstteki `[vvar]` ve `[vdso]`, çekirdeğin kullanıcı alanına açtığı zaman ve sistem çağrısı hızlandırma sayfalarıdır.

Bu adresler her çalıştırmada değişir. İki ayrı çalıştırmada aynı program farklı taban adreslerle yüklendi; bunun sebebi adres alanı yerleşiminin rastgeleleştirilmesidir (ASLR, genel bilgi). Bu yüzden hata ayıklarken adresleri sabit bir değer gibi düşünme; yalnızca bölgelerin göreli düzenine güven.

## 25.12 TLB: çeviriyi önbelleğe almak

Her bellek erişimi için dört seviyeli tabloyu yürümek pahalıdır. Bu yüzden işlemci çevirilerin sonuçlarını küçük bir önbellekte tutar: **TLB** (translation lookaside buffer). TLB'de sanal sayfa numarası ile fiziksel çerçeve numarası eşleşmesi durur. İsabet olursa çeviri neredeyse bedavadır. Kaçırma olursa donanım sayfa tablosunu yürür (page walk), sonucu TLB'ye yazar ve erişime devam eder. Bu yürüyüşün süresi, sayfa tablosu girdilerinin nerede bulunduğuna bağlıdır: girdiler önbellekteyse birkaç nanosaniye, DRAM'deyse onlarca nanosaniye sürebilir (ayrıntılar işlemciye göre değişir, genel bilgi).

TLB'nin etkisini ölçmek için bir tuzak var: adresleri değiştirdiğinde önbellek davranışı da değişir. Bu yüzden deneyde üç düzeni karşılaştırıyoruz ama her birinde aynı sayıda satır (16 384) kullanıyoruz. Sıkı düzen 1 MB'lık bir bölgede: 256 sayfa. Seyrek düzen her düğümü ayrı bir sayfaya koyar: 16 384 sayfa. Son düzen seyrekle aynıdır ama 2 MB huge page üzerinde çalışır: 32 sayfa.

Bu deney şu sonucu verir: her üç düzende de 16 384 önbellek satırı kullanılır, dolayısıyla L1 ve L2 kaçırmaları benzerdir; fark TLB ve sayfa tablosu yürüyüşünden gelmelidir.

```c
/* tlb.c - TLB etkisini, onbellek yukunu sabit tutarak olcmek.
 * Uc duzen, ayni sayida dugum (16384) ve ayni rastgele dongu:
 *   sikli  : dugumler 1 MB'lik bolgede (256 sayfa)
 *   seyrek : her dugum ayri sayfada (16384 sayfa, 64 MB)
 *   buyuk  : seyrek ile ayni, ama 2 MB huge page uzerinde
 * Uc duzende de 16384 onbellek satiri kullanilir; fark TLB'den gelir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 tlb.c -o tlb
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/resource.h>

#define DUGUM 16384
#define ADIM (1u << 21)
#define DENEME 5
#define SAYFA 4096
#define IKI_MB (2u << 20)
#define BOYUT (64u << 20)

static uint64_t tohum = 88172645463325252ULL;

static uint64_t rastgele(void)
{
    tohum ^= tohum << 13;
    tohum ^= tohum >> 7;
    tohum ^= tohum << 17;
    return tohum;
}

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + (double)t.tv_nsec;
}

```

Başlıklar ve yardımcılar. `IKI_MB` 2 MB'lık hizalama için kullanılır; huge page ancak fiziksel ve sanal adresi 2 MB'a hizalı bir bölgede çalışır.

```c
static long kucuk_hata(void)
{
    struct rusage u;
    getrusage(RUSAGE_SELF, &u);
    return u.ru_minflt;
}

static void *cikis;

/* Dugum p'nin bolge icindeki ofseti. */
static size_t yer(size_t p, int sayfali)
{
    if (!sayfali) return p * 64;                     /* sikli */
    return p * SAYFA + ((p >> 8) & 63) * 64;        /* seyrek */
}

static int karsilastir(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}
```

`kucuk_hata` sayaç okur. `yer` fonksiyonu düğümün bölge içindeki ofsetini verir: sıkı düzende `p * 64`, seyrek düzende `p * 4096 + ((p >> 8) & 63) * 64`. Seyrek düzendeki ofset, her düğümü ayrı bir sayfaya koyar ama satırın kümesini de dağıtır; bu ayrıntı aşağıdaki tuzakta açıklanıyor.

```c
static double olc(char *bolge, int sayfali, long *hata)
{
    size_t *ord = malloc(DUGUM * sizeof *ord);
    for (size_t i = 0; i < DUGUM; i++) ord[i] = i;
    for (size_t i = DUGUM - 1; i > 0; i--) {         /* Sattolo */
        size_t j = rastgele() % i;
        size_t t = ord[i]; ord[i] = ord[j]; ord[j] = t;
    }
    long h0 = kucuk_hata();
    for (size_t k = 0; k < DUGUM; k++) {
        void **d = (void **)(bolge + yer(ord[k], sayfali));
        *d = bolge + yer(ord[(k + 1) % DUGUM], sayfali);
    }
    *hata = kucuk_hata() - h0;

    double sonuc[DENEME];
    for (int r = 0; r < DENEME; r++) {
        void *q = bolge + yer(ord[0], sayfali);
        double t0 = simdi_ns();
        for (size_t s = 0; s < ADIM; s++)
            q = *(void *volatile *)q;
        double t1 = simdi_ns();
        cikis = q;
        sonuc[r] = (t1 - t0) / ADIM;
    }
    qsort(sonuc, DENEME, sizeof sonuc[0], karsilastir);
    free(ord);
    return sonuc[DENEME / 2];
}
```

`olc` düğümleri Sattolo ile karıştırır, bölgeyi kurar ve ölçümü yapar. Bölgeyi kurarken kaç küçük hata olduğunu kaydeder: seyrek ve huge düzende bu sayı sayfa sayısına yaklaşmalıdır. Ölçüm, medyan alınmış `ADIM` yüklemesinin süresidir.

```c
static void huge_bilgi(void)
{
    FILE *f = fopen("/proc/self/smaps_rollup", "r");
    char satir[256];
    if (!f) return;
    while (fgets(satir, sizeof satir, f))
        if (strncmp(satir, "AnonHugePages", 13) == 0)
            printf("  %s", satir);
    fclose(f);
}

int main(void)
{
    char *sikli = aligned_alloc(SAYFA, 1u << 20);
    char *seyrek = aligned_alloc(SAYFA, BOYUT);
    char *buyuk = aligned_alloc(IKI_MB, BOYUT);
    if (!sikli || !seyrek || !buyuk) { perror("alloc"); return 1; }
    madvise(buyuk, BOYUT, MADV_HUGEPAGE);   /* THP: 2 MB sayfa iste */

    long h1, h2, h3;
    double n1 = olc(sikli, 0, &h1);
    double n2 = olc(seyrek, 1, &h2);
    double n3 = olc(buyuk, 1, &h3);

    printf("duzen    sayfa  ns/erisim  kucuk_hata\n");
    printf("sikli      256 %9.2f %10ld\n", n1, h1);
    printf("seyrek   16384 %9.2f %10ld\n", n2, h2);
    printf("buyuk       32 %9.2f %10ld\n", n3, h3);
    printf("buyuk icin /proc/self/smaps_rollup:\n");
    huge_bilgi();
    free(sikli); free(seyrek); free(buyuk);
    return 0;
}
```

`huge_bilgi` `/proc/self/smaps_rollup` dosyasından `AnonHugePages` satırını okur; bu, gerçekten kaç kilobaytın 2 MB sayfa ile desteklendiğini gösterir. `main` üç bölgeyi ayırır, huge düzen için `madvise(..., MADV_HUGEPAGE)` çağrısıyla çekirdeğe 2 MB sayfa isteği bildirir ve sonuçları tablo hâlinde yazdırır. Sistemin THP (Transparent Huge Pages) ayarı şudur:

```term
$ cat /sys/kernel/mm/transparent_hugepage/enabled
always [madvise] never
```

`[madvise]` seçeneği, huge page'in yalnızca uygulamanın açıkça istediği bölgelerde kullanılacağı anlamına gelir. Programımız tam olarak bunu yapıyor. Sonuçlar:

```term
$ ./tlb
duzen    sayfa  ns/erisim  kucuk_hata
sikli      256      9.14        256
seyrek   16384     20.60      16384
buyuk       32     17.65         32
buyuk icin /proc/self/smaps_rollup:
  AnonHugePages:     65536 kB
```

![Şekil 25.9: Aynı önbellek yükü, farklı sayfa düzenleri. Seyrek düzen (her düğüm ayrı sayfada) TLB kaçırmaları nedeniyle yavaşlar; 2 MB huge page bu maliyetin bir kısmını geri kazandırır.](gorseller/b25_tlb.png)

Üç sonucu ayrı ayrı okuyalım. Sıkı düzen 9,14 ns, seyrek düzen 20,60 ns sürdü: fark yaklaşık 11,5 ns. Bu fark, her erişimde TLB kaçırılmasının ve sayfa tablosu yürüyüşünün maliyetidir; önbellek davranışı iki düzende aynıdır, çünkü ikisi de 16 384 satıra dokunur. Seyrek düzeni 2 MB huge page'e taşıyınca süre 17,65 ns'ye düşüyor. Böylece TLB kaçırmalarının maliyetinin yaklaşık 2,9 ns'lik bir kısmı huge page ile kazanılıyor.

Geriye kalan yaklaşık 8,5 ns (huge düzen ile sıkı düzen arasındaki fark) bu ölçümle açıklanamadı. Olası nedenler arasında düzenlerin fiziksel yerleşiminin ve L2/L3 kümelerinin farklılığı var; bunu ayırt etmek için `perf` ile L2 ve TLB kaçırma sayaçlarını okumak gerekir ve bu bölümde yapmadık. Bu nedenle bu kalan farkı, huge page'in tam sihri olarak yorumlamıyoruz.

::: dikkat
Bu deneyin ilk sürümünde seyrek düzen `p % 64` ofseti kullanıyordu. Huge page ile çalıştırınca süre 94 ns'ye fırladı. Sebep, huge page içinde fiziksel adresin düşük 21 bitinin sanal adresle aynı kalmasıydı: düğümlerin L3 kümesi (bit 6-19) yalnızca 256 değer aldığı için 16 384 satır 256 kümeye yığılıyordu ve L3 taşıyordu. Yani "huge page daha kötü" sonucu aslında bir düzen hatasıydı. Ofseti `(p >> 8) & 63` olarak değiştirince kümeler dengelendi ve sonuç anlamlı hâle geldi. Ölçüm yaparken düzeninin ölçtüğün şeyi değiştirmediğini her zaman kontrol et.
:::

Bu sonuçların mülakattaki karşılığı şudur: sanal bellekte her erişimin iki maliyeti vardır, önbellek kaçırması ve çeviri kaçırması. Büyük ve dağınık bir veri yapısı, ikisini birlikte tetikleyebilir. Huge page'ler çeviri kaçırmalarını azaltır, ama önbelleğin kendisini değiştirmez. Veritabanları ve yüksek performanslı sistemler bu yüzden büyük tamponları huge page ile ayırmaya eğilimlidir (genel bilgi).

## 25.13 Bellek ayırıcılar: glibc ptmalloc

Bölüm 2'de `malloc` ve `free`'yi bir sözleşme olarak tanıtmıştık: istenen boyutta bir blok ver, bitince geri al. Bu sözleşmenin uygulaması işletim sistemi değil, C kütüphanesidir. Linux'ta glibc kullanıldığında ayırıcı `ptmalloc` adı verilen bir algoritmadır. Çekirdekten büyük bloklar (varsayılan olarak 128 KB ve üstü `mmap` ile) ve bir ana bellek alanı (`brk`) alır, sonra bu alanı kendi serbest listeleri ile böler.

Ayırıcının temel birimi **parça** (chunk) adını alır. Her parçanın başında bir başlık vardır: önceki parçanın boyutu ve kendi boyutu. Kullanıcı işaretçisi başlığın hemen sonrasındadır. Başlığın ilk alanı, parça boşsa önceki parçanın boyutunu tutar; dolu parçalarda bu alan önceki parçanın kullanıcı verisinin bir parçası olarak kullanılır. Bu, bir ayrıntıdır ama mülakatta karşına çıkar: glibc, boşa giden bayt sayısını en aza indirmek için bu alanı üst parçanın verisiyle paylaştırır.

Parça boyutu, isteğe 8 bayt başlık eklenip 16'ya yuvarlanarak bulunur; en küçük parça 32 bayttır. Bu makinede bu kurallar şöyle görünür. Aşağıdaki program her istek için iki ardışık `malloc` çağrısı yapar ve iki adres arasındaki farkı parça boyutu olarak alır. Hiçbir blok serbest bırakılmadığı için bloklar üst parçadan sırayla gelir ve bu fark gerçek parça boyutunu verir.

```c
/* malloc_boyut.c - glibc'nin ayirdigi gercek blok boyutlari.
 * Her istek icin 2 ardisik malloc yapilir. Ikinci adresin
 * birincisinden farki, glibc'nin bu istek icin harcadigi parca
 * boyutudur (baslik dahil). Hicbir blok serbest birakilmaz; bu
 * sayede bloklar ust parcadan (top chunk) sirayla gelir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 malloc_boyut.c -o mb
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <malloc.h>

int main(void)
{
    size_t istekler[] = { 1, 8, 16, 17, 24, 25, 40, 64, 100, 1000 };
    size_t n = sizeof istekler / sizeof istekler[0];

    printf("istek  kullanilabilir  parca(zincir)\n");
    for (size_t i = 0; i < n; i++) {
        char *a = malloc(istekler[i]);
        char *b = malloc(istekler[i]);
        if (!a || !b) { perror("malloc"); return 1; }
        size_t kull = malloc_usable_size(a);
        size_t parca = (uintptr_t)b - (uintptr_t)a;
        printf("%5zu %12zu %14zu\n", istekler[i], kull, parca);
    }
    return 0;
}
```

Program, `malloc_usable_size` ile kullanıcının gerçekten kullanabildiği bayt sayısını ve iki adres farkından gelen parça boyutunu yazdırır. Sonuç:

```term
$ ./malloc_boyut
istek  kullanilabilir  parca(zincir)
    1           24             32
    8           24             32
   16           24             32
   17           24             32
   24           24             32
   25           40             48
   40           40             48
   64           72             80
  100          104            112
 1000         1000           1008
```

Tablo birkaç kuralı ortaya koyar. İstek 1 ile 17 arasında olduğunda parça 32 bayt, kullanılabilir alan 24 bayttır. İstek 25 olduğunda parça 48 bayta sıçrar ve kullanılabilir alan 40 olur: 25 baytın yanında 8 baytlık başlık paylaşımı ve 16'ya yuvarlama birlikte çalışır. İstek 1000'de kullanılabilir alan 1000 bayttır ve parça 1008'dir. Her satırda kullanılabilir alan = parça − 8 ilişkisi tutar. Bu ilişkinin kaynağı glibc'nin `memsize` makrosudur; Kod Okuma bölümünde kaynağını göreceğiz.

![Şekil 25.10: glibc'de malloc(25) için parça düzeni. Parça 48 bayttır; kullanıcı 40 bayta erişebilir, çünkü son 8 bayt bir sonraki parçanın önceki boyut alanı ile örtüşür.](gorseller/b25_malloc_parca.png)

Bu tablo iki tür israfı gösterir. **İç israf** (internal fragmentation), isteğin yuvarlanması ve başlık yüzünden kullanılmayan bayttır: istek 25 için 15 bayt ek alan. **Dış israf** (external fragmentation) ise serbest bloklar arasında kalan, ama hiçbir istek için yeterince büyük olmayan boşluklardır. İç israf istek boyutunun dağılımına bağlıdır; dış israf, ayırma ve serbest bırakma sırasının karmaşıklığına. İkisi birlikte uzun süre çalışan sunucularda bellek kullanımının şişmesinin ana sebebidir.

Gerçek glibc daha karmaşıktır ve bu bölümde tam hâlini incelemiyoruz: iş parçacığı başına **arena**'lar, boyuta göre **bin**'ler (hızlı, küçük, büyük ve sınıflandırılmamış listeler) ve glibc 2.26'dan beri her iş parçacığına ait kısa bir **tcache** (genel bilgi). Bunların amacı, yaygın küçük ayırma ve serbest bırakma çiftlerinin kilitsiz ve hızlı yapılmasıdır. Bunu anlamak için Bölüm 26 ve 27'deki iş parçacığı ve senkronizasyon kavramlarına ihtiyacın olacak.

## 25.14 Kendi ayırıcın: sabit boyutlu blok havuzu

Her ayırıcı her iş yükü için iyi değildir. Gömülü ve gerçek zamanlı sistemlerde iki soru daha önemlidir: istek süresi üst sınırla sınırlı mı, ve bellek kullanımı önceden bilinen bir miktarı aşabilir mi? Bu sorulara en basit cevap **sabit boyutlu blok havuzu** (pool) ile verilir. Havuzda hep aynı boyutta bloklar vardır, bu yüzden ayırma ve serbest bırakma tek bir işaretçi işlemidir ve dış israf oluşmaz.

Tasarım iki fikre dayanır. Birincisi, boş blokların listesi bloklarının içinde tutulur: boş bir bloğun ilk 8 baytı bir sonraki boş bloğun adresidir. Bu sayede ayrı bir liste belleği gerekmez. İkincisi, liste başta tutulur ve LIFO davranır: son serbest bırakılan blok ilk ayrılır. LIFO, yakın zamanda kullanılmış bir bloğun büyük olasılıkla hâlâ önbellekte olmasını sağlar; yani zamansal yerellikten yararlanır.

```c
#define _POSIX_C_SOURCE 199309L
/* ayirici.c - sabit boyutlu blok havuzu (pool) ayirici.
 * Serbest bloklar, bloklarin ICINDE tutulan bir bagli listede durur:
 * bos bir blogun ilk 8 bayti bir sonraki bos blogun adresidir.
 * Derleme : gcc -O2 -Wall -Wextra -std=c11 ayirici.c -o ayirici
 * ASan ile: gcc -O1 -g -fsanitize=address,undefined ayirici.c
 * Kullanim: ./ayirici test  |  ./ayirici olc
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define BLOK 64              /* blok boyu; en az sizeof(void *) */
#define ADET 4096            /* havuzdaki blok sayisi */

typedef struct {
    unsigned char *bellek;   /* ADET * BLOK bayt, tek parca */
    void *bos;               /* serbest listenin basi */
    size_t kullanilan;
} Havuz;
```

Başlıklar ve iki sabit. `BLOK` 64 bayttır, en az bir işaretçi sığmalıdır; `ADET` havuzdaki blok sayısıdır. `Havuz` yapısı tek bir büyük bellek parçasını, liste başını ve kullanım sayacını tutar. Tüm bloklar tek bir `malloc` ile ayrılır; yani havuzun kendisi bir kez ayrılır ve sonra hiç büyümez.

```c
static int havuz_kur(Havuz *h)
{
    h->bellek = malloc((size_t)ADET * BLOK);
    if (!h->bellek) return 0;
    h->bos = NULL;
    h->kullanilan = 0;
    /* tersten doldur: 0. blok listenin basinda olsun */
    for (size_t i = ADET; i-- > 0; ) {
        void *b = h->bellek + i * BLOK;
        *(void **)b = h->bos;
        h->bos = b;
    }
    return 1;
}

static void *havuz_ayir(Havuz *h)
{
    void *b = h->bos;
    if (!b) return NULL;                 /* havuz dolu */
    h->bos = *(void **)b;
    h->kullanilan++;
    return b;
}

static int havuz_birak(Havuz *h, void *p)
{
    uintptr_t adr = (uintptr_t)p;
    uintptr_t taban = (uintptr_t)h->bellek;
    if (adr < taban || adr >= taban + (uintptr_t)ADET * BLOK)
        return 0;                        /* bu havuza ait degil */
    if ((adr - taban) % BLOK != 0)
        return 0;                        /* blok sinirinda degil */
    *(void **)p = h->bos;
    h->bos = p;
    h->kullanilan--;
    return 1;
}
```

`havuz_kur` blokları tersten dolaşır ve her birini listenin başına ekler; böylece 0. blok listenin başında kalır. `havuz_ayir` listenin başını alır ve bir sonrakine ilerler; boş liste `NULL` döndürür. `havuz_birak` ise bir işaretçinin havuza ait olduğunu iki kontrolle doğrular: adres aralık içinde mi ve blok sınırına mı hizalı. Bu kontroller, havuzun dışındaki bir işaretçiyi listeye sokmayı engeller; ama çift serbest bırakmayı yakalamaz. Bunu Örnek 4'te yapacağımız deneyde açıkça göreceğiz.

```c
static uint32_t tohum = 2463534242u;     /* xorshift32, sabit tohum */

static uint32_t rastgele(void)
{
    tohum ^= tohum << 13;
    tohum ^= tohum >> 17;
    tohum ^= tohum << 5;
    return tohum;
}

static int test(void)
{
    Havuz h;
    if (!havuz_kur(&h)) return 1;
    static void *canli[ADET];
    static unsigned char desen[ADET];
    size_t n = 0, en_fazla = 0;
    const long ADIM = 2000000;

    for (long adim = 0; adim < ADIM; adim++) {
        if (n < ADET && (n == 0 || rastgele() % 2 == 0)) {
            void *p = havuz_ayir(&h);
            if (!p) {
                printf("HATA: bos blok yok, n=%zu\n", n);
                return 1;
            }
            unsigned char d = (unsigned char)rastgele();
            memset(p, d, BLOK);
            canli[n] = p;
            desen[n] = d;
            n++;
            if (n > en_fazla) en_fazla = n;
        } else {
            size_t k = rastgele() % n;
            unsigned char *c = canli[k];
            for (size_t i = sizeof(void *); i < BLOK; i++)
                if (c[i] != desen[k]) {
```

`rastgele` küçük bir xorshift32 üreteçtir ve sabit tohumla başlar; testin ve ölçümün tekrarlanabilir olması için bu gereklidir. `test` fonksiyonu rastgele ayır ve bırak dizisi üretir: her adımda ya yeni bir blok alır ya da rastgele seçilmiş bir canlı bloğu bırakır. Her blok, ayrıldığı anda rastgele bir bayt değeriyle doldurulur. Bırakılmadan önce ilk 8 bayt dışındaki tüm baytların hâlâ aynı değer olup olmadığına bakılır; böylece başka bir bloğun yazmasının bu bloğu bozup bozmadığını yakalarız.

```c
                    printf("HATA: blok bozuldu, adim=%ld\n", adim);
                    return 1;
                }
            if (!havuz_birak(&h, c)) {
                printf("HATA: birakma reddedildi, adim=%ld\n", adim);
                return 1;
            }
            canli[k] = canli[n - 1];
            desen[k] = desen[n - 1];
            n--;
        }
        if (h.kullanilan != n) {
            printf("HATA: sayim uyusmuyor, adim=%ld\n", adim);
            return 1;
        }
    }
    /* listeyi say: serbest blok sayisi ADET - n olmali */
    size_t bos = 0;
    for (void *b = h.bos; b; b = *(void **)b) bos++;
    if (bos != ADET - n) { printf("HATA: liste bozuk\n"); return 1; }
    printf("test gecti: %ld adim, en fazla dolu blok = %zu\n",
           ADIM, en_fazla);
    free(h.bellek);
    return 0;
}
```

Test her adımda iki değişmezi kontrol eder: havuzun kullanım sayacı canlı blok sayısıyla eşit olmalı ve sonunda serbest liste tam olarak `ADET - n` uzunlukta olmalıdır. Herhangi bir uyuşmazlık hata mesajı verir ve test başarısız olur. Test'i normal ve ASan + UBSan ile iki kez çalıştırdık. ASan'ı `-fsanitize=address,undefined` ile derleyerek kullandık; bu derleme, Bölüm 6'da gördüğümüz sanitizer'ın aynısıdır.

```term
$ ./ayirici test
test gecti: 2000000 adim, en fazla dolu blok = 2571
```

Aynı testi sanitizer ile derlediğimizde:

```term
$ ./ayirici_asan test
test gecti: 2000000 adim, en fazla dolu blok = 2571
```

İki sonuç da temiz. ASan, bloklar arasında bir taşma ya da sarkan işaretçi kullanımı görmedi ve sızıntı denetimi (LeakSanitizer) de bir sızıntı bildirmedi. Bu, testin gücünü kanıtlamaz; yalnızca bu kadar rastgele dizinin sorunsuz geçtiğini gösterir. Yine de bu tür bir testi her kod değişikliğinden sonra çalıştırmak, havuzu güvenilir kılan şeydir.

```c
static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + (double)t.tv_nsec;
}

/* Ayni is yukunu havuzla ve malloc ile yapip ns/islem dondurur. */
static double olc(int havuz_mi)
{
    static void *canli[ADET];
    const long ISLEM = 10000000;
    Havuz h;
    if (havuz_mi && !havuz_kur(&h)) return -1;
    tohum = 2463534242u;
    size_t n = 0;
    double t0 = simdi_ns();
    for (long i = 0; i < ISLEM; i++) {
        if (n < ADET && (n == 0 || rastgele() % 2 == 0)) {
            canli[n++] = havuz_mi ? havuz_ayir(&h) : malloc(BLOK);
        } else {
            size_t k = rastgele() % n;
            if (havuz_mi) havuz_birak(&h, canli[k]);
            else free(canli[k]);
            canli[k] = canli[--n];
        }
    }
    double t1 = simdi_ns();
    for (size_t k = 0; k < n; k++) {     /* temizlik */
        if (havuz_mi) havuz_birak(&h, canli[k]);
        else free(canli[k]);
    }
    if (havuz_mi) free(h.bellek);
    return (t1 - t0) / ISLEM;
}
```

Ölçüm fonksiyonu aynı rastgele iş yükünü iki kez çalıştırır: bir kez havuzla, bir kez `malloc` ve `free` ile. Her ikisinde de 10 milyon işlem yapılır ve sadece ayırma/serbest bırakma kısmı zamanlanır. Canlı blok sayısı 4096'yı geçmez, yani havuzun kapasitesi yeter.

```c
int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "test") == 0)
        return test();
    if (argc == 2 && strcmp(argv[1], "olc") == 0) {
        printf("havuz : %6.2f ns/islem\n", olc(1));
        printf("malloc: %6.2f ns/islem\n", olc(0));
        return 0;
    }
    fprintf(stderr, "kullanim: %s test | olc\n", argv[0]);
    return 1;
}
```

`main` iki modu seçer: `test` doğruluk testini, `olc` zamanlamayı çalıştırır. Ölçüm çıktısı:

```term
$ ./ayirici olc
havuz :   5.39 ns/islem
malloc:   9.23 ns/islem
```

Bu rastgele iş yükünde havuz ortalama 5,4 ns, `malloc`/`free` ise 9,2 ns sürdü. Yani yaklaşık 1,7 kat hızlı. Kazancın bir kısmı, havuzun her işlemde kontrol ve başlık maliyetinin olmamasından gelir; bir kısmı da sabit boyuttan sağlanan öngörülebilirlikten. Ama dikkat: bu, havuzun her zaman `malloc`'tan hızlı olduğu anlamına gelmez. Yalnızca tek boyutlu, sabit bir iş yükü için tasarlanmış bir çözümdür ve glibc'nin tcache'i zaten çok hızlı küçük ayırmalar yapar; burada kazanç, 64 baytlık blokların rastgele sırada ayrılıp bırakılmasında ortaya çıkıyor.

Havuzun sınırlarını da bilmek gerekir. Boyutu sabittir, yani 64 bayttan büyük bir istek yapılamaz. Yapısında bir sınır kontrolü, bir çift serbest bırakma tespiti ya da bir kullanım sonrası kontrolü yoktur. Sayfa tablosu ya da iş parçacığı güvenliği de yoktur. Gömülü bir sistemde bunların her biri ayrı bir karar gerektirir. Bir yığın (arena ya da bump allocator) ise daha da basit bir stratejidir: bir işaretçiyi ileri kaydırır, hiçbir bloğu tek tek serbest bırakmaz; tüm arenayı bir kerede sıfırlar. Bu, ayrıştırıcı ya da bir istek işleyicisi gibi "işlem bitince her şeyi at" kalıbında çok hızlı ve parçalanmasız bir ayırıcıdır.

## 25.15 Bellek hatalarının sınıflandırılması

Bellek hataları birkaç sınıfta toplanır ve her sınıfın bir belirtisi vardır. Bu sınıflandırma, hangi aracın hangi hatayı yakalayacağını bilmek için gereklidir.

| Hata | Belirti | Yakalayan araç ve önlem |
|---|---|---|
| Sızıntı (leak) | Bellek zamanla şişer, `free` eksiktir | LeakSanitizer (ASan ile), valgrind |
| Kullanım sonrası (use-after-free) | Serbest bırakılmış blok okunur ya da yazılır | ASan; havuzda ek bayrak kontrolü |
| Çift serbest bırakma (double free) | Aynı blok iki kez listeye girer | ASan ve glibc; havuzda tespit yok (Örnek 4) |
| Taşma (overflow) | Dizinin sonrasına yazılır | ASan; `-fstack-protector` (yığın için) |
| Başlatılmamış okuma | Çöp değer okunur | valgrind; MSan (clang) |

Bölüm 6'da ASan ve valgrind'i kullanmayı öğrendik; burada gördüğün test, aynı araçlarla bir ayırıcıyı denetlemenin nasıl yapılacağını gösterir. Dikkat edilmesi gereken nokta şudur: bir sanitizer yalnızca çalıştırdığın yolda hatayı görür. Bu yüzden rastgele iş yükleri ve kenar durumları, sanitizer'ın kapsamını gerçekten genişletir.

## 25.16 NUMA (kısaca)

Çok soketli sunucularda her işlemcinin kendi bellek denetleyicisi ve kendine yakın bir bellek bankası vardır. Bir işlemci, başka soketin belleğine eriştiğinde gecikme artar. Bu tür mimariye NUMA (Non-Uniform Memory Access) denir. Yerel ve uzak bellek arasındaki fark, sunucu donanımına göre değişir ve genel bilgi olarak yerel erişimin uzak erişimden belirgin biçimde hızlı olduğu bilinir.

Bu makinede tek bir düğüm (`node0`) görünüyor, yani NUMA etkisi ölçülemez. Ama mülakatta sorulduğunda cevabın şu iki parçası olmalı: (1) bellek sayfasının hangi düğümde yaşadığı, ilk erişim yapan iş parçacığının düğümüne göre belirlenir (first-touch politikası, genel bilgi); (2) iş parçacığını ve belleği birlikte yerleştirmek, bu yüzden veri yapılarını başlatan iş parçacığı önemlidir.

## 25.17 Gerçek dünya: MertOS'ta sayfalama ve heap

Bu bölümde yazdığımız kodların birçoğu Mert'in MertOS çekirdeğinde zaten var. Çekirdeğin kendi sayfalama ve heap kodunu okuyarak bu bölümün kavramlarını gerçek bir sistemde görebilirsin. Aşağıdaki üç alıntı yalnızca okunmuştur; her biri dosya yolu ve satır aralığıyla verilmiştir. Kitap sütun genişliğine sığsın diye satır sonu yorumları bir üst satıra alındı; kod sözcükleri ve değerler değişmedi.

İlk alıntı, çekirdeğin başlangıcında kurduğu ilk sayfa tablosudur. Önce `entry.asm`'de 2 MB huge page'lerle bir kimlik eşlemesi (sanal = fiziksel) kurulur. Döngü, her girdiye `Present | Writable | Huge Page` bayraklarını yazar:

```asm
    mov ecx, 0
.map_pd:
    mov eax, 0x200000           ; 2MB
    ; EAX = ecx * 2MB (max: 2047 * 2MB = 0xFFE00000, 32-bit'e sığar)
    mul ecx
    or  eax, 0b10000011         ; Present | Writable | Huge Page
    ; 4 tablo ardışık → tek döngüyle tümü doldurulur
    mov [edi + ecx * 8], eax
    inc ecx
```

Bu tasarım, Bölüm 25.9'daki PS (huge) bitinin ve Bölüm 25.12'deki TLB kazancının pratik bir uygulamasıdır: 4 GB'lık belleği 4 KB sayfalarla eşleseydik yaklaşık bir milyon girdi gerekirdi; 2 MB girdilerle 2048 girdi yeter ve çeviri zincirini bir seviye kısaltır. Bu, çekirdeğin başlangıcını sadeleştiren makul bir seçimdir.

İkinci alıntı, çekirdeğin `VMM::mapPage` fonksiyonundan. Burada bir hata var. Bir PD girdisi zaten 2 MB huge page ise ve üstüne 4 KB'lık bir eşleme istenirse, fonksiyon eşlemeyi yapmadan `true` döndürüyor:

```cpp
    // PD: 2MB huge page mi var? Varsa küçük sayfayla çakışma
    uint64_t& pd_entry = pd[pdIndex(virt_addr)];
    if ((pd_entry & PageFlags::PRESENT) &&
        (pd_entry & PageFlags::HUGE)) {
        // Huge page bölgesine 4KB map atılıyor → entry.asm'nin
        // identity mapping'i burada zaten kapsıyor olabilir.
        // Şimdilik güvenli: varsa üzerine yazma
        return true;
    }
```

Yorum, bu durumun `entry.asm`'nin kimlik eşlemesi tarafından "zaten kapsandığını" varsaydığını söylüyor. Bu varsayım her zaman doğru değil: çağıran taraf eşlemenin yapıldığını sanır, oysa yapılmamıştır. Böyle bir hata sonradan sessiz bir bellek erişimi hatasına dönüşebilir; doğru davranış `false` döndürmek ya da bir `assert` ile durmak olurdu. Bu, Bölüm 6'da anlattığımız "erken patla" ilkesinin tam uygulamasıdır.

Üçüncü alıntı, heap yöneticisinin blok başlığıdır. Yorum başlığın 48 bayt olduğunu söylüyor. Alanları sayınca ise `uint32_t` iki tane (8 bayt) ve işaretçi dört tane (32 bayt) var: toplam 40 bayt. Bunu bir C++ derleyicisiyle doğruladık: aynı alan tanımlarını ayrı bir dosyaya kopyalayıp `sizeof` değerini yazdırdık ve sonuç 40 çıktı. Yorum yanlış, ama bu hata yalnızca belge hatasıdır: `HEADER_SIZE` sabiti `sizeof(BlockHeader)` ile hesaplandığı için kod doğru bir değer kullanıyor.

```cpp
    struct BlockHeader {
        uint32_t     magic;      // MAGIC_FREE veya MAGIC_USED
        uint32_t     payload;    // Kullanıcı veri boyutu (hizalanmış)
        BlockHeader* phys_prev;  // Fiziksel bellekte önceki blok
        BlockHeader* phys_next;  // Fiziksel bellekte sonraki blok
        // Sadece free iken geçerli:
        BlockHeader* free_prev;  // Free list'te önceki
        BlockHeader* free_next;  // Free list'te sonraki
    };
    // Header boyutu = 48 byte (6 x pointer/uint = 6x8 = 48,
    // uint32 x 2 = 8 -> toplam 48)
```

Bu üç alıntıdan çıkan ders şudur: çekirdek kodunda bile sayfa tablosu ve heap'in kavramları, yorumların ve sabitlerin doğru olup olmadığını kontrol etmeyi gerektirir. Bir yorumun sayısal iddiasını, sınanabilir bir ifadeye dönüştürüp derleyiciyle ölç.

Son olarak gömülü bir mikrodenetleyici ile karşılaştıralım. Bir Cortex-M çekirdeğinde MMU genellikle yoktur; yerine bölge tabanlı bir **MPU** (Memory Protection Unit) bulunur. MPU, belirli adres bölgelerine erişim izni tanımlar, ama sanal adres çevirisi yapmaz: adresler fiziksel adreslerdir. Bu yüzden bir gömülü sistemde talep üzerine sayfalama ve takas yoktur, bellek düzeni derleme ve bağlama zamanında belirlenir, dinamik ayırma çoğu zaman yasaklanır (genel bilgi). Bazı Cortex-M7 tabanlı mikrodenetleyicilerde önbellek bulunur (genel bilgi); bu durumda DMA ile okunan bir tampon ile önbellek arasında tutarlılık sorunu çıkar ve bunu bir yazılım kararıyla (önbelleği boşaltmak ya da tamponu hizalamak) çözmek gerekir. Bu konu Bölüm 43'te ele alınacak.

## Çözümlü Örnekler

Aşağıdaki dört örneği Bölüm 5'teki altı adımla çözüyoruz: anla, örnekle, kaba çöz, örüntü bul, iyileştir, doğrula. Her örneğin sonunda bir varyasyon var; onu önce kâğıtta çöz, sonra kontrol et.

### Örnek 1 (★): Bir önbellek izinde isabet ve kaçırmalar

Önbellek 32 KB, 8 yollu ve 64 baytlık satırlıdır (64 küme). Başlangıçta boştur ve LRU politikasını kullanır. Sırayla şu on iki adres geliyor: `0x140`, `0x1140`, `0x2140`, `0x3140`, `0x4140`, `0x5140`, `0x6140`, `0x7140`, `0x8140`, `0x140`, `0x147`, `0x2140`. Her erişimin ISABET mi KACIRMA mı olduğunu ve erişim sonunda 5 numaralı kümede hangi etiketlerin durduğunu bul.

**Adım 1 — Anla.** Önemli olan iki şey: her adresin kümesi ve etiketi, ve her kümenin en fazla sekiz etiket tutabilmesi. Kümeyi `(adres / 64) % 64`, etiketi `adres / 4096` ile buluyoruz. Sekiz yol olduğu için bir kümede dokuzuncu farklı etiket geldiğinde bir şey atılmalıdır.

**Adım 2 — Örnekle.** `0x140 = 320`. Ofset `320 % 64 = 0`, küme `(320 / 64) % 64 = 5`, etiket `320 / 4096 = 0`. `0x1140 = 4416`: ofset 0, küme `(4416 / 64) % 64 = 69 % 64 = 5`, etiket 1. Yani iki adres de 5. kümeye düşüyor ama etiketleri farklı. Dizideki bütün adresler `0x?140` biçiminde, yani aynı küme; etiket ise onaltılık sayıdaki üst basamaktan okunur.

**Adım 3 — Kaba çöz.** Her adres için: kümeyi bul, o kümede aynı etiket var mı bak, varsa isabet ve son kullanımı güncelle; yoksa kaçırma, bir boş yer ya da en eski girdiyi yeni etiketle değiştir. Bu, simülatörün yaptığı şeyin elle uygulanmasıdır.

**Adım 4 — Örüntü.** Dokuz farklı etiket aynı kümeye geliyor ve küme yalnızca sekiz yol tutuyor. İlk sekiz adres kümeyi doldurur. Dokuzuncu adres en eski etiketi (`0`) atar. Sonra `0x140` (etiket `0`) geldiğinde o satır yok, dolayısıyla kaçırma olur ve bu kez en eski `1` atılır. Ardından `0x147` aynı satırı (etiket `0`) isabetle bulur, çünkü `0x147` ile `0x140` aynı 64 baytlık satırda. `0x2140` ise etiket `2`'yi bulur; etiket `2` henüz atılmamıştır.

**Adım 5 — İyileştir.** Burada iyileştirilecek bir kod yok, ama bir karar var: LRU sıralamasında isabet, bir girdinin "en yeni" konumuna taşınır. Bu, `0x147`'nin etiket `0`'ı, `0x2140`'ın ise etiket `2`'yi en yeni konuma getirdiği anlamına gelir. Sonuç olarak, bir sonraki kaçırmada atılacak girdi, bu iki isabetten sonra değişir. Bunu gözden kaçırmak, bir sonraki erişimi yanlış tahmin etmene yol açar.

**Adım 6 — Doğrula.** Elle yürüttüğümüz iz tablosu:

| No | Adres | Etiket | Sonuç | Küme 5 (en eski → en yeni) |
|---|---|---|---|---|
| 1 | `0x140` | 0 | KAÇIRMA | [0] |
| 2 | `0x1140` | 1 | KAÇIRMA | [0, 1] |
| 3 | `0x2140` | 2 | KAÇIRMA | [0, 1, 2] |
| 4 | `0x3140` | 3 | KAÇIRMA | [0, 1, 2, 3] |
| 5 | `0x4140` | 4 | KAÇIRMA | [0 … 4] |
| 6 | `0x5140` | 5 | KAÇIRMA | [0 … 5] |
| 7 | `0x6140` | 6 | KAÇIRMA | [0 … 6] |
| 8 | `0x7140` | 7 | KAÇIRMA | [0 … 7] (dolu) |
| 9 | `0x8140` | 8 | KAÇIRMA | [1 … 8] (0 atıldı) |
| 10 | `0x140` | 0 | KAÇIRMA | [2 … 8, 0] (1 atıldı) |
| 11 | `0x147` | 0 | ISABET | [2 … 8, 0] |
| 12 | `0x2140` | 2 | ISABET | [3 … 8, 0, 2] |

Tabloyu simülatörle karşılaştıralım. Adres dizisini `iz1.txt` dosyasına tek satır olarak yazdık: `0x140 0x1140 0x2140 0x3140 0x4140 0x5140 0x6140 0x7140 0x8140 0x140 0x147 0x2140`. Simülatör bütün dizi için kümeyi, etiketi, ofseti ve sonucu yazdırır:

```term
$ ./onbellek adres $(cat iz1.txt)
yol=8 kume=64 satir=64
adres        etiket    kume ofset sonuc
0x00000140 0x000000     5    0 KACIRMA
0x00001140 0x000001     5    0 KACIRMA
0x00002140 0x000002     5    0 KACIRMA
0x00003140 0x000003     5    0 KACIRMA
0x00004140 0x000004     5    0 KACIRMA
0x00005140 0x000005     5    0 KACIRMA
0x00006140 0x000006     5    0 KACIRMA
0x00007140 0x000007     5    0 KACIRMA
0x00008140 0x000008     5    0 KACIRMA
0x00000140 0x000000     5    0 KACIRMA
0x00000147 0x000000     5    7 ISABET
0x00002140 0x000002     5    0 ISABET
```

Simülatörün sonuçları elle tablomuzla birebir aynı: ilk on erişimin tamamı kaçırma, 11. ve 12. erişimler isabet. Bu örnekten alınacak ders, LRU'nun "en eski" kararının yalnızca erişim sırasına bağlı olduğu ve bir isabetin bu sırayı değiştirdiğidir.

**Bunu AI'sız yazabilir misin?** Aynı diziyi tekrar çalıştır, ama son adresi `0x2140` yerine `0x1140` yap. Etiket 1, adım 10'da atılmış olduğundan bu erişim kaçırma olur. Hangi etiket atılır ve son durum tablo nasıl değişir? Önce elle yaz, sonra simülatörle kontrol et.

### Örnek 2 (★★): Sanal adresi sayfa tablosu indekslerine bölmek

Sanal adres `0x7F3A12C4B5E8`. (a) Dört seviyenin indekslerini ve sayfa ofsetini bul. (b) Bu adres için en fazla kaç yeni sayfa tablosu sayfası gerekir: (i) 4 KB'lık bir sayfayı ilk kez eşlerken, (ii) 2 MB'lık bir huge page eşlerken?

**Adım 1 — Anla.** 48 bitlik adres beş parçaya ayrılır: bit 47-39 (PML4), 38-30 (PDPT), 29-21 (PD), 20-12 (PT) ve 11-0 (ofset). Her indeks 9 bit, yani 0-511 arası bir değer. CR3 zaten PML4 tablosunu gösterir; yani PML4 girdisi her zaman vardır, eksik olabilecek tablolar PDPT, PD ve PT'dir.

**Adım 2 — Örnekle.** Önce ilk iki bayta bakalım: `0x7F3A`. Hex'te her basamak 4 bittir. `0x7F3A` = `0111 1111 0011 1010`. Adresin 48 biti: `0x7F3A12C4B5E8`. Bit 47-39 bölgesi en üstteki 9 bittir: `0111 1111 0` (0x7F3A'nın ilk 9 biti), yani 254.

**Adım 3 — Kaba çöz.** Her indeks için: `(adres >> kaydırma) & 0x1FF`, ofset için `adres & 0xFFF`. Kaydırmalar sırasıyla 39, 30, 21 ve 12.

**Adım 4 — Örüntü.** Her seviye kendi 9 bitini kullanır ve ofset 12 bit olduğu için 9 + 9 + 9 + 9 + 12 = 48. Yeni tablo gereksinimi ise şöyle: bir 4 KB sayfayı eşlemek için PDPT, PD ve PT'nin her biri yoksa yaratılır (üç yeni sayfa); bir 2 MB sayfa için PD girdisi doğrudan veriyi gösterir, yani yalnızca PDPT ve PD gerekir (iki yeni sayfa); 1 GB için yalnızca PDPT (bir yeni sayfa). Her yeni tablo bir sayfa olduğu için bu sayılar bellek kullanımına doğrudan çevrilir.

**Adım 5 — İyileştir.** Hesabı kaydırma ve maske işlemleriyle yaptık. Bu, bir sayfa tablosu yürüyüşünün donanımda yaptığının aynısıdır; yazılımda da aynı işlemler çekirdeğin `VMM` sınıfında `pml4Index`, `pdptIndex` gibi fonksiyonlarla yapılır. Bu yüzden bu bit kaydırmalarını bir fonksiyona koymak ve test etmek hem okunabilirliği hem doğruluğu artırır.

**Adım 6 — Doğrula.** Sonuçları bir Python betiğiyle kontrol edelim. Betik indeksleri hesaplar, sonra bunları birleştirerek özgün adrese dönüp dönmediğine bakar:

```python
# Sanal adresi 4 seviyeli sayfa tablosu indekslerine boler,
# sonra geri birlestirip ozgun adresle karsilastirir.
adres = 0x7F3A12C4B5E8
pml4 = (adres >> 39) & 0x1FF
pdpt = (adres >> 30) & 0x1FF
pd = (adres >> 21) & 0x1FF
pt = (adres >> 12) & 0x1FF
ofset = adres & 0xFFF
print("PML4=%d PDPT=%d PD=%d PT=%d ofset=%d"
      % (pml4, pdpt, pd, pt, ofset))
geri = (pml4 << 39) | (pdpt << 30) | (pd << 21) | (pt << 12) | ofset
print("geri birlestirme dogru:", geri == adres)
girdi = 1 << 9
print("tablo girdisi:", girdi, "girdi boyutu: 8 bayt")
print("tablo boyutu:", girdi * 8, "bayt")
```

```term
$ python ornek2_kontrol.py
PML4=254 PDPT=232 PD=150 PT=75 ofset=1512
geri birlestirme dogru: True
tablo girdisi: 512 girdi boyutu: 8 bayt
tablo boyutu: 4096 bayt
```

Elle hesap ve betik aynı sonucu veriyor: PML4 254, PDPT 232, PD 150, PT 75 ve ofset 1512 (`0x5E8`). Birleştirme testi de True döndü. Tablo girdisi sayısı 512, girdi boyutu 8 bayt, yani tablo 4096 bayt eder.

**Bunu AI'sız yazabilir misin?** Adres `0x0000_0040_0000_0000` (yani 256 GB) için dört indeksi elle bul ve hangi seviyelerde yeni tablo gerekeceğini söyle. İpucu: bu adres PML4 ve PDPT'nin hangi girdilerine düşer?

### Örnek 3 (★★): Matris taramasında kaçırma oranını tahmin etmek

Önbellek 32 KB, 8 yollu, 64 baytlık satırlıdır. Bir `int` (4 bayt) matrisi satır sırasıyla ve sütun sırasıyla taranıyor. (a) `N = 64` ve `N = 128` için kaçırma oranını tahmin et. (b) Tahminini simülatörle doğrula. (c) Önbelleği tam ilişkili ya da doğrudan eşlemeli yaparsan oranlar nasıl değişir?

**Adım 1 — Anla.** Kaçırma oranı = kaçırma sayısı / toplam erişim. Zorunlu (ilk erişim) kaçırmalar, her satırın bir kez getirilmesinden gelir. Ek kaçırmalar ise çakışmadan (aynı kümeye fazla satır) gelir.

**Adım 2 — Örnekle.** `N = 4` olsaydı matris 16 `int` = 64 bayt olurdu, yani tek bir satır. Satır ve sütun taraması aynı satıra dokunur: bir kaçırma ve 15 isabet, her iki yönde de. Düzen önemli değildir, çünkü her şey tek satırda. Bu, düzen farkının yalnızca matris bir önbelleğe sığmadığında ortaya çıktığını gösterir.

**Adım 3 — Kaba çöz.** Satır taraması: her satır 16 `int` taşır, yani satırı bir kez getirip 16 erişim yaparız. Oran `1/16 = 0,0625`. Bu, matris bütünüyle önbelleğe sığsa da sığmasa da satır taramasında geçerlidir.

**Adım 4 — Örüntü.** `N = 128` için satır uzunluğu 512 bayttır. Eleman `(i, j)`'nin adresi `taban + (128 i + j) × 4`; bunun satır numarası `(128 i + j) / 16 = 8 i + j / 16` ve küme numarası `(8 i + j / 16) mod 64`. Sütun taramasında `j` sabit, `i` değişiyor. Küme `8 i mod 64` ile belirlenir ve `i mod 8` değerleri yalnızca sekiz farklı küme verir. Her bir kümeye `i`'nin 8 ile ayrışan 16 değeri düşer: 16 farklı satır, 8 yol. Döngüsel taramada her satır bir sonraki turdan önce atılır, yani her erişim kaçırır. Sütun taraması `N = 128` için oranı 1,0 olmalıdır. `N = 64` için matris 16 KB'dır ve sığar: her satır yalnızca bir kez getirilir, oran 0,0625.

**Adım 5 — İyileştir.** Bu sorunun standart çözümü, satır uzunluğunu 2'nin kuvveti olmaktan çıkarmaktır: satır başına birkaç ek eleman (padding) eklemek küme dağılımını değiştirir. Bunu tahmin etmek için küme hesabını yeni satır uzunluğuyla yeniden yapman yeterlidir. Blok (tiled) çarpım ise erişim desenini değiştirir; Bölüm 25.7'de bunu ölçtük.

**Adım 6 — Doğrula.** Tahminlerimizi simülatör çıktısıyla karşılaştıralım:

| Düzen | Tahmin (N=64) | Ölçüm | Tahmin (N=128) | Ölçüm |
|---|---|---|---|---|
| satır (8 yollu) | 0,0625 | 0,062 | 0,0625 | 0,062 |
| sütun (8 yollu) | 0,0625 | 0,062 | 1,000 | 1,000 |

Komutlar ve çıktılar:

```term
$ for m in satir sutun; do ./onbellek matris 64 $m; done
N=64 satir erisim=4096 isabet=3840 kacirma=256 oran=0.062
N=64 sutun erisim=4096 isabet=3840 kacirma=256 oran=0.062
```

```term
$ for m in satir sutun; do ./onbellek matris 128 $m; done
N=128 satir erisim=16384 isabet=15360 kacirma=1024 oran=0.062
N=128 sutun erisim=16384 isabet=0 kacirma=16384 oran=1.000
```

Tam ilişkili (tek küme, 512 yol) sürümü `gcc -O2 -std=c11 -DYOL=512 -DKUME=1 onbellek.c -o onb_full` ile, doğrudan eşlemeli (512 küme, 1 yol) sürümü `-DYOL=1 -DKUME=512` ile derledik. Aynı kaynak dosyadan üretilen iki sürümün çıktısı:

```term
$ ./onb_full matris 128 sutun
N=128 sutun erisim=16384 isabet=15360 kacirma=1024 oran=0.062
```

```term
$ ./onb_dm matris 128 sutun
N=128 sutun erisim=16384 isabet=0 kacirma=16384 oran=1.000
```

Tam ilişkili önbellekte sütun taraması 0,062'ye düşer: çalışma kümesi 128 satırdır ve 512 satırlık önbelleğe sığar, yalnızca zorunlu kaçırmalar kalır. Doğrudan eşlemeli önbellekte oran 1,000'dır: iki satır aynı kümeye düştüğünde birbirini atar. Bu, çakışma kayıplarının yol sayısına ne kadar duyarlı olduğunu gösterir.

**Bunu AI'sız yazabilir misin?** `N = 128` yerine her satırı 132 eleman yap (satır başına dört `int` ekle). Yeni satır uzunluğu 528 bayt. Sütun taramasında hangi kümelere erişildiğini yeniden hesapla. Kaç küme kullanılır ve her küme kaç farklı satır alır? Tahminini simülatörle kontrol etmek için matris modunun taban adresini ve satır genişliğini değiştirmen gerekir.

### Örnek 4 (★★★): Sabit boyutlu blok havuzu ve çift serbest bırakma

Oyun motoru bir kare içinde 64 baytlık nesneleri sürekli ayırıp serbest bırakıyor. Nesneler tek boyutlu, sayıları üst sınırlı ve ayırma süresi öngörülebilir olmalı. Bir havuz (pool) yaz: ayırma ve bırakma O(1) olsun, ayrı bir takip yapısı gerekmesin. Ardından çift serbest bırakmayı (aynı bloğu iki kez bırakmayı) tespit edip edemediğini sına.

**Adım 1 — Anla.** Bütün bloklar aynı boyutta. Boş bloklar bir liste oluşturabilir, ama liste belleği ayrıca ayırmamalı: boş blok kendi içinde bir sonrakinin adresini taşıyabilir. Ayırma listenin başını almaktır, bırakma bloğu başa koymaktır. Çift serbest bırakma, aynı bloğun iki kez listeye girmesidir ve listeyi bozar.

**Adım 2 — Örnekle.** Dört bloklu küçük bir havuzda listenin başından başlayarak iz sürelim. Aşağıdaki program, bu örnekteki işlem dizisini çalıştırıp her adımdaki durumu yazdırır:

```c
/* izdogrula.c - 4 bloklu bir havuzda serbest liste izi.
 * Derleme: gcc -O1 -Wall -Wextra -std=c11 izdogrula.c -o izdogrula
 */
#include <stdio.h>
#include <stdlib.h>

#define BLOK 64
#define ADET 4

typedef struct {
    unsigned char *bellek;
    void *bos;                  /* serbest listenin basi */
    size_t kullanilan;
} Havuz;

static void havuz_kur(Havuz *h)
{
    h->bellek = malloc((size_t)ADET * BLOK);
    h->bos = NULL;
    h->kullanilan = 0;
    for (size_t i = ADET; i-- > 0; ) {
        void *b = h->bellek + i * BLOK;
        *(void **)b = h->bos;
        h->bos = b;
    }
}

static void *havuz_ayir(Havuz *h)
{
    void *b = h->bos;
    if (!b) return NULL;
    h->bos = *(void **)b;
    h->kullanilan++;
    return b;
}

static int havuz_birak(Havuz *h, void *p)
{
    *(void **)p = h->bos;       /* sinir/cift birakma kontrolu yok */
    h->bos = p;
    h->kullanilan--;
    return 1;
}

static int blok_no(Havuz *h, void *p)
{
    if (!p) return -1;
    return (int)(((unsigned char *)p - h->bellek) / BLOK);
}

static void yaz(Havuz *h, const char *ad, void *p)
{
    printf("%-14s blok=%2d  bos_bas=%2d\n",
           ad, blok_no(h, p), blok_no(h, h->bos));
}

int main(void)
{
    Havuz h;
    havuz_kur(&h);
    void *b0 = havuz_ayir(&h); yaz(&h, "ayir", b0);
    void *b1 = havuz_ayir(&h); yaz(&h, "ayir", b1);
    havuz_birak(&h, b0); yaz(&h, "birak(B0)", b0);
    void *c = havuz_ayir(&h); yaz(&h, "ayir", c);
    havuz_birak(&h, b1); yaz(&h, "birak(B1)", b1);
    void *d = havuz_ayir(&h); yaz(&h, "ayir", d);
    void *e = havuz_ayir(&h); yaz(&h, "ayir", e);
    void *f = havuz_ayir(&h); yaz(&h, "ayir", f);
    void *g = havuz_ayir(&h); yaz(&h, "ayir (bos)", g);
    havuz_birak(&h, e); yaz(&h, "birak(B2)", e);
    havuz_birak(&h, e); yaz(&h, "birak(B2) 2.", e);
    void *x = havuz_ayir(&h); yaz(&h, "ayir", x);
    void *y = havuz_ayir(&h); yaz(&h, "ayir", y);
    printf("ayni blok iki kez verildi mi? %s\n",
           x == y ? "EVET" : "hayir");
    free(h.bellek);
    return 0;
}
```

Program `havuz_birak`'ı bilerek sadeleştirdi: sınır ve çift bırakma kontrolü yok. Çıktı şöyle:

```term
$ ./izdogrula
ayir           blok= 0  bos_bas= 1
ayir           blok= 1  bos_bas= 2
birak(B0)      blok= 0  bos_bas= 0
ayir           blok= 0  bos_bas= 2
birak(B1)      blok= 1  bos_bas= 1
ayir           blok= 1  bos_bas= 2
ayir           blok= 2  bos_bas= 3
ayir           blok= 3  bos_bas=-1
ayir (bos)     blok=-1  bos_bas=-1
birak(B2)      blok= 2  bos_bas= 2
birak(B2) 2.   blok= 2  bos_bas= 2
ayir           blok= 2  bos_bas= 2
ayir           blok= 2  bos_bas= 2
ayni blok iki kez verildi mi? EVET
```

Çıktıdaki `bos_bas` alanı, her adımdan sonra listenin başındaki bloğun numarasıdır (-1 boş liste). İlk iki ayırma 0 ve 1'i verir; B0 bırakıldığında liste başı yeniden 0 olur ve sonraki ayırma 0'ı geri verir. Dördüncü blok tükendikten sonra beşinci ayırma `NULL` döner.

**Adım 3 — Kaba çöz.** Basit çözüm, her ayırmada boş bloğu aramaktır; bu `O(n)` olur. Bir sonraki çözüm her blok için bir bit tutan bitmap'tir; ama boş biti bulmak için bitleri taramak yine doğrusal bir maliyet taşır. Bizim istediğimiz, ayırma ve bırakmanın sabit zamanda olmasıdır; bu yüzden listeye ihtiyacımız var.

**Adım 4 — Örüntü.** Listenin başı ayırmada çıkar, bırakmada girer: bu bir yığın (stack) davranışıdır, LIFO. Her işlem bir işaretçi değişimi ve bir yükleme içerir. Ayrıca yakın zamanda bırakılan blok en sıcak bloktur (zamansal yerellik); LIFO bunu kendiliğinden verir.

**Adım 5 — İyileştir.** Bu tasarımda iki eksik var. Birincisi, bırakılan işaretçinin havuzun içinde ve blok sınırında olduğunu kontrol eden doğrulama, `ayirici.c`'de vardır ama bu izde kasıtlı olarak yok. İkincisi, çift bırakma tespiti. Çift bırakmayı yakalamanın basit bir yolu, her bloğa bir "boş" bayrağı eklemek ya da bir bit dizisi tutmaktır. Bu bir bellek maliyeti getirir ama hatayı erken yakalar.

**Adım 6 — Doğrula.** Elle izlediğimiz adımlar ve programın çıktısı aynı sonucu veriyor:

| Adım | İşlem | Dönen blok | Liste başı | Liste (baştan) |
|---|---|---|---|---|
| 1 | ayır | B0 | B1 | B1 → B2 → B3 |
| 2 | ayır | B1 | B2 | B2 → B3 |
| 3 | bırak(B0) | - | B0 | B0 → B2 → B3 |
| 4 | ayır | B0 | B2 | B2 → B3 |
| 5 | bırak(B1) | - | B1 | B1 → B2 → B3 |
| 6 | ayır | B1 | B2 | B2 → B3 |
| 7 | ayır | B2 | B3 | B3 |
| 8 | ayır | B3 | NULL | boş |
| 9 | ayır | NULL | NULL | boş (dolu) |
| 10 | bırak(B2) | - | B2 | B2 → NULL |
| 11 | bırak(B2), ikinci | - | B2 | B2 → B2 (döngü) |
| 12 | ayır | B2 | B2 | B2 → B2 (döngü) |
| 13 | ayır | B2 | B2 | B2 → B2 (döngü) |

Adım 11'de B2 kendi kendisini gösteren bir döngü oluşuyor. 12 ve 13. ayırmalar aynı B2'yi iki kez veriyor. Bu, veri bozulmasının sessiz kaynağıdır. Sayaç da bozulur: çift bırakma `kullanilan` değerini iki kez azaltır, yani hata hem listeyi hem sayacı etkiler.

Peki asıl havuzun testi bu hatayı yakalar mı? Hayır: `ayirici test` yalnızca her bloğu tek kez bırakır, çift bırakma üretmez. Bu, testin kapsamında bir boşluk, ve bu boşluğu bulmak bu örneğin asıl amacıdır. Testlere, bilerek çift bırakma üreten bir adım ekleyip hatanın yakalandığını görmek iyi bir alıştırmadır.

**Bunu AI'sız yazabilir misin?** Havuza her bloğun boş olup olmadığını tutan bir bit dizisi ekle. Ayırmada ilgili biti dolu yap; bırakmada biti kontrol et ve blok zaten boşsa `0` döndür. Bu değişikliği yaz, izi yeniden çalıştır. Hangi adımda `EVET` yerine `hayir` görüyorsun, ve neden tam olarak o adımda?

## Kendin Yap Projeleri

::: dikkat
Bu iki projede yapay zekâ aracına kod yazdırma. Bölüm 6'daki kuralın aynısı geçerli: önce kendin dene, takıldığında kavramı sor, cevabı değil. Önceki bölümlerdeki `onbellek.c` ve `ayirici.c` dosyalarını bu bölümde yazdın; onları başlangıç noktası olarak kullanabilirsin, ama kod sende değilse öğrenme de sende olmaz. Bitirdikten sonra kendi kodunu bu bölümün çözümleriyle karşılaştır; farkın nedenini anlamadan geçme.
:::

### Proje 1 (★★): Yapılandırılabilir önbellek simülatörü

**Amaç.** `onbellek.c`'yi, boyutu, yol sayısını, satır boyunu ve çıkarma politikasını (LRU ya da FIFO) komut satırından seçilebilen bir simülatöre dönüştür. Girdi olarak bir adres dizisi dosyası kabul etsin ve her erişim için isabet ya da kaçırma yazsın; sonunda toplam isabet oranını versin.

**Beklenen davranış.** Komut şöyle çalışmalı:

`./sim -boyut 32768 -yol 8 -satir 64 -politika lru iz.txt`

İz dosyası, her satırda bir onaltılık adres içersin (`0x` ile ya da olmadan). Çıktı, her erişim için kümeyi, etiketi ve sonucu yazsın; sonunda `isabet`, `kacirma` ve oran değerlerini yazsın. Geçersiz parametre verildiğinde anlamlı bir hata mesajı ve sıfır olmayan çıkış kodu dönsün.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Küme sayısını `boyut / (satir × yol)` ile hesapla ve 2'nin kuvveti olup olmadığını kontrol et. FIFO için her girdiye bir "yerleştirilme sırası" ver: LRU'daki son kullanım zamanı yerine yalnızca yerleşme anını tut. Bu fark, Bölüm 25.3'te tarif edilen küçük bir değişikliktir ama davranışı büyük ölçüde değiştirir. İz dosyası için satır okuyucuyu `fgets` ile yaz ve `strtoull`'un taban parametresinin 0 olduğunda `0x` önekini tanıdığını hatırla.

**Başarı kriterleri.**
- Örnek 3'teki `matris 128 sutun` izi (16 384 adres) hem bu simülatörde hem `onbellek.c`'de aynı oranı (1,000) verir.
- Tam ilişkili (`-yol` = küme sayısı, `-kume` = 1) yapılandırma, sütun taramasında 0,062 verir.
- Rastgele bir iz üzerinde LRU ve FIFO arasındaki oran farkını ölçtüğünde sonucu iki kez çalıştırıp aynı çıkar.
- `-fsanitize=address,undefined` ile derlendiğinde temiz geçer.
- Simülatör, 1 000 000 adresli bir izi bir saniyenin altında işler (bu, makineye göre değişebilir; amacı büyüklük mertebesini görmek).

### Proje 2 (★★★): Kendi malloc'un: serbest liste, birleştirme ve sınır etiketleri

**Amaç.** Bölüm 25.13'teki glibc davranışını anlamak için kendi genel amaçlı ayırıcını yaz. Değişken boyutlu istekleri karşılayan, serbest blokları bir bağlı listede tutan ve komşu serbest blokları birleştiren (coalescing) küçük bir `my_malloc` ve `my_free` olsun. Sonuçlarını glibc ile karşılaştır.

**Beklenen davranış.** `my_malloc(n)` en az `n` bayt kullanılabilir bir işaretçi döndürsün ve 16 bayta hizalı olsun. `my_free(p)` bloğu serbest listeye koysun ve komşu serbest bloklarla birleştirsin. Çift serbest bırakma ve sınır dışı işaretçi tespit edilsin (hata durumunda program durdurulsun ya da hata kodu dönsün). Rastgele bir ayırma ve bırakma dizisinde hiçbir bellek hatası ve sızıntı olmasın.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Bir sınır etiketi (boundary tag) tasarla: her blokta başta ve sonda boyut ve bir "kullanımda" bayrağı olsun. Böylece bir bloğun hem önceki hem sonraki komşusu sabit zamanda bulunur. Bölüm 25.17'de MertOS'un heap başlığını gördün; onun `phys_prev`/`phys_next` işaretçileriyle farkını düşün. Parçalanmayı ölçmek için rastgele bir iş yükünde kullanılmayan (serbest ama küçük) bayt oranını ve en büyük boş bloğu raporla. Bölüm 25.13'teki `malloc_boyut` programının benzerini yaz: aynı istekler için kendi parça boyutlarını göster ve glibc ile yan yana koy.

**Başarı kriterleri.**
- Rastgele 100 000 ayır/bırak işleminde (sabit tohum) ASan ve UBSan temiz geçer; sızıntı raporu yoktur.
- Bitişik iki serbest blok bırakıldığında tek bir büyük serbest blok oluşur (bir test ile gösterilmiş olmalı).
- Her istek için kullanılabilir boyut, istekten büyük ya da eşit ve 16 katıdır.
- Aynı iş yükünde glibc ile hız (ns/işlem) ve parçalanma (en büyük boş blok / toplam boş alan) karşılaştırması yapılmış ve yorumlanmıştır.
- Çift serbest bırakma testi, programın hata verdiğini gösterir.

### Ek Alıştırmalar

Aşağıdaki alıştırmalar cevapsız. Önce kâğıtta ya da boş bir dosyada düşünerek çöz; kodu yazdıktan sonra kontrol et. Ölçüm gerektiren sorularda makinende ölç ve sonucu bu bölümdeki değerlerle karşılaştır.

1. ★ Bir `int` dizisi 64 baytlık sınırda başlıyor. Satır başına kaç eleman düşer? 100 elemanlık sıralı bir toplamda kaç önbellek kaçırması beklersin? Cevabını `onbellek.c` ile doğrula.
2. ★ `getconf LEVEL1_DCACHE_LINESIZE` ve sysfs'teki `coherency_line_size` aynı değeri verir. Bu değerlerin neden aynı kaynaktan geldiğini ve hangisinin programın bakış açısından "gerçek" olduğunu açıkla.
3. ★★ Bölüm 25.4'teki kovalama programını kendi makinende çalıştır ve eğrini çiz. L1, L2 ve L3 basamaklarını işaretle; L3'ün nominal boyutuyla ölçülen geçişi arasındaki farkı yaz.
4. ★★ 4 KB sayfalı bir sistemde 1 GB'lık tek bir dizi ayırıyorsun ve her sayfasına bir kez yazıyorsun. Sayfa tabloları için yaklaşık ne kadar bellek gerekir? (İpucu: PT sayısı, 8 bayt girdi, üst seviyeler.)
5. ★★ Bir süreç 3 GB'lık bir sanal bölge ayırıyor ve sadece her 4 KB'ın başına bir bayt yazıyor. Kaç küçük hata beklersin? Sonra `talep.c`'yi bu düzene uyarlayıp ölç.
6. ★★ `madvise(p, n, MADV_DONTNEED)` çağrısından sonra bir sayfaya tekrar dokunmanın bir küçük hata mı yoksa büyük hata mı olduğunu tahmin et. Ardından `talep.c`'yi bu çağrıyı içerecek şekilde değiştirip sayaçla doğrula.
7. ★★ `ayirici.c`'deki havuzu iki boyutlu bir sınıfa dönüştür: 32 bayt ve 128 bayt blok havuzları, istek boyutuna göre seçilsin. Hangi boyutun hangi sınıfa gideceğini nasıl belirlersin? (Mülakat)
8. ★★ Blok matris çarpımında blok boyutunu 16, 32, 64 ve 128 olarak değiştir. Hangi değerde süre minimum olur ve bunu L1 boyutuyla nasıl ilişkilendirirsin?
9. ★★★ `N = 1024` `int` matrisinde sütun taramasını önbellek dostu hâle getirmek için satır başına padding ekle. Kaçırma oranını simülatörle ölç ve padding miktarına göre nasıl değiştiğini tablo hâlinde göster. (Mülakat)
10. ★★★ FIFO ve LRU, aynı 9 etiketli döngüde nasıl davranır? Bunu elle yürüt, sonra `onbellek.c`'ye FIFO ekleyerek doğrula. FIFO'nun bazı girdilerde daha fazla yol eklendiğinde daha çok kaçırma yapabildiğini (Belady anomalisi, genel bilgi) bu deneyle gösterebilir misin?
11. ★★★ Bir Python listesinin her elemanı ayrı bir nesneye işaret eder. Bunun tıpkı işaretçi kovalama gibi bağımlı yüklere yol açtığını açıkla. Basit bir toplamda `list` ile `array.array` arasındaki farkı ölç ve sonucu bu bölümdeki kovalama sonuçlarıyla ilişkilendir. (Mülakat)
12. ★★★ Bir `struct`'ın alanlarını yeniden sıralamanın bellek kullanımına ve önbellek kaçırmalarına etkisini tahmin et. Bölüm 27'de göreceğin false sharing'in bu konuyla ilişkisini şimdiden düşün. (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: glibc 2.39 sürümündeki `malloc/malloc.c` dosyası (6049 satır). Dosya şu adresten alındı: `https://raw.githubusercontent.com/bminor/glibc/glibc-2.39/malloc/malloc.c`.

Aşağıdaki kesitlerde kod sözcükleri ve sırası değiştirilmedi. Tek değişiklik, satır sonundaki bazı yorumların bir üst satıra alınması ve birkaç uzun makro satırının sarılmasıdır; bunu yalnızca 70 sütunluk kitap düzenine sığmak için yaptık. Kesitlerin kaynak satır numaraları verilmiştir.

`struct malloc_chunk` (satır 1136-1146) parçanın bellek düzenini tanımlar. Yapının adı ve alanları bir bakıma yanıltıcıdır; yorumda bu açıkça söylenir ("misleading but accurate").

```c
struct malloc_chunk {

  /* Size of previous chunk (if free).  */
  INTERNAL_SIZE_T      mchunk_prev_size;
  /* Size in bytes, including overhead. */
  INTERNAL_SIZE_T      mchunk_size;

  struct malloc_chunk* fd;
  /* double links -- used only if free. */
  struct malloc_chunk* bk;

  /* Only used for large blocks: pointer to next larger size.  */
  struct malloc_chunk* fd_nextsize;
  /* double links -- used only if free. */
  struct malloc_chunk* bk_nextsize;
};
```

`MIN_CHUNK_SIZE` ve `MINSIZE` makroları (satır 1296-1301) en küçük parçanın boyutunu belirler. İsteği parçaya çeviren `request2size` (satır 1314-1318) ise ayırmanın kalbidir.

```c
#define MIN_CHUNK_SIZE (offsetof(struct malloc_chunk, fd_nextsize))

#define MINSIZE  \
  (unsigned long)(((MIN_CHUNK_SIZE + MALLOC_ALIGN_MASK) \
                   & ~MALLOC_ALIGN_MASK))

#define request2size(req)                                         \
  (((req) + SIZE_SZ + MALLOC_ALIGN_MASK < MINSIZE)  ?             \
   MINSIZE :                                                      \
   ((req) + SIZE_SZ + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK)
```

`musable` (satır 5233-5243) `malloc_usable_size`'ın gövdesidir. Kullanılabilir boyutu, parçanın durumuna göre hesaplar.

```c
static size_t
musable (void *mem)
{
  mchunkptr p = mem2chunk (mem);

  if (chunk_is_mmapped (p))
    return chunksize (p) - CHUNK_HDR_SZ;
  else if (inuse (p))
    return memsize (p);

  return 0;
```

Bu kesitte geçen `memsize(p)` makrosu (satır 1447-1450) mtag kapalıyken ve parça mmap ile ayrılmamışsa `chunksize(p) - CHUNK_HDR_SZ + SIZE_SZ` değerini döndürür; `CHUNK_HDR_SZ` 16, `SIZE_SZ` 8 olduğundan bu, parçanın boyutundan 8 çıkarmaktır. mmap parçası için ise ekleme yapılmaz ve 16 çıkarılır (Soru 4). Bu, Bölüm 25.13'teki ölçümde gördüğümüz "kullanılabilir = parça − 8" kuralının kaynağıdır.

**Sorular — cevaplamadan geçme:**

1. `mchunk_prev_size` alanı yorumda yalnızca önceki parça boş ("if free") iken anlamlı diye yazılmıştır. Bu alan dolu parçalar için neden ayrılmıştır, ve kullanılabilir boyutu hesaplarken bu durumdan nasıl yararlanılır?
2. `MIN_CHUNK_SIZE` neden `offsetof(struct malloc_chunk, fd_nextsize)` ile tanımlanmış ve neden `bk_nextsize` değil? Bir parça boşken hangi alanlara ihtiyaç vardır?
3. `request2size` içinde `req + SIZE_SZ + MALLOC_ALIGN_MASK` ifadesi üç farklı iş yapar. Her birini ayrı ayrı açıkla ve neden `MINSIZE` ile karşılaştırıldığını söyle.
4. `musable` mmap ile ayrılmış parçalar için `chunksize(p) - CHUNK_HDR_SZ` döndürür, yani 8 değil 16 çıkarır. Bu farkın sebebini bulmak için mmap parçası ile normal parça arasındaki komşuluk ilişkisini düşün.
5. `inuse(p)` bir sonraki parçanın `PREV_INUSE` bayrağına bakar. Bu bayrak olmadan birleştirme (coalescing) neden zorlaşır?
6. Kendi `havuz`'unda (Bölüm 25.14) başlık yok ve boyut sabit. Bu iki tasarım arasında bellek ve hız açısından bir denge kur. Hangi iş yükünde glibc'nin başlık maliyeti kabul edilebilir, hangisinde değildir?

## Bölüm Özeti

Bu bölümde bellek hiyerarşisini bir mimari gerçek olarak kurduk ve her katmanı ölçümle doğruladık:

- Hiyerarşi, hızlı ama küçük ve yavaş ama büyük katmanların bir yığınıdır; program hızı hangi verinin hangi katmanda durduğuna bağlıdır. Yerellik ilkesi bu yapıyı mümkün kılar.
- Önbellek satırı 64 bayttır. Adres, etiket, küme ve ofset olarak bölünür; küme ilişkili tasarımda çakışma kayıpları yol sayısına bağlıdır.
- İşaretçi kovalama ile ölçtüğümüz basamaklar: L1 yaklaşık 0,8 ns, L2 yaklaşık 2,5 ns, L3 yaklaşık 10 ns, DRAM 110-130 ns. Ölçüm, bağımlı ve bağımsız yüklerin farkını da açığa çıkarır.
- Adım taraması satır boyunun 64 bayt olduğunu sysfs ile birlikte doğrular; 2'nin kuvveti adımlar çakışma kaybına yol açar.
- Blok matris çarpımı, erişim düzeni ve blok boyutu ile önbellek kullanımını iyileştirir; ijk'den blok sürüme kazanç iki çalıştırmada 18 ile 19 kat arasındaydı.
- Sanal bellek, dört seviyeli sayfa tablosu ile çalışır. Talep üzerine sayfalama, sayfa hatalarının iki sınıfını (küçük ve büyük) ayırır. TLB kaçırmaları ayrı bir maliyettir ve huge page bunu azaltır.
- glibc ayırıcısı parça başlığı ve 16 bayta hizalama ile çalışır; kullanılabilir alan parçadan 8 bayt küçüktür. Sabit boyutlu havuz ise O(1) ve başlıksız, ama çift serbest bırakmayı kendisi yakalamaz.
- Gerçek sistemlerde (MertOS) sayfa tablosu ve heap, bu kavramların doğrudan uygulamasıdır; ancak yorumların ve belgelerin de ölçümle doğrulanması gerekir.

**Sonraki bölümde:** Bölüm 26 (Process & Thread) ile bu bölümün kopyalama-yazarken (copy-on-write) ve sayfa tablosu fikirlerini, süreç oluşturma (`fork`, `exec`) ve iş parçacığı bağlamında göreceğiz. Bağlam değişiminin TLB ve önbellek üzerindeki etkisi de orada ayrıca ölçülecek.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Önbellek kaçırması ile sayfa hatası arasındaki farkı açıkla. Hangisi donanım tarafından, hangisi işletim sistemi tarafından çözülür ve her birinin maliyeti tipik olarak neye benzer?
2. L1 önbelleğin yol sayısı neden genellikle 8 ya da 12 gibi küçük bir değerdir? Yol sayısını artırmanın hangi bedelleri vardır?
3. 1024 × 1024 bir `int` matrisinde sütun taraması ile satır taraması arasında hangisinin daha çok kaçırma yapacağını ve bunun neden öyle olduğunu tahmin et. Önbelleğin boyutu değişirse cevabın nasıl değişir?
4. Huge page'ler TLB kaçırmalarını azaltır ama önbellek kaçırmalarını azaltmaz. Bu iki kavramı bir programda hangi desenle birbirinden ayırt edersin?
5. Bir ayırıcıda çift serbest bırakmayı nasıl tespit edersin? Bu tespitin bellek ve zaman maliyeti ne olur ve üretimde bu maliyeti ne zaman ödemezsin?
6. Gömülü bir sistemde dinamik bellek ayırmanın neden yasaklandığını, parçalanma ve zaman üst sınırı açısından açıkla. Bu kararın bir istisnası olabilir mi?
7. Bağlı liste ile dizi arasındaki seçimi yalnızca Big-O ile yapmak neden yanıltıcıdır? Hangi ölçüm bu seçimi değiştirebilir?
8. Bir programın yavaşlığını gördüğünde önce hangi üç şeyi ölçersin ve her biri hangi katmanı ayırt etmene yardım eder?
:::
