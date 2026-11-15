%% kisim_no: XIII
%% kisim_ad: Sinyal & Paralel
%% bolum_no: 53
%% baslik: Paralel & Eşzamanlı Programlama

## Giriş: Hızlanmanın bedava olmadığı yer

Bugünkü işlemciler saat hızını artırarak değil, çekirdek sayısını artırarak hızlanıyor. Bu bölümde ölçtüğümüz makine bir AMD Ryzen 7 6800H: 8 fiziksel çekirdek ve her çekirdekte iki mantıksal iş parçacığı, yani işletim sistemine görünen 16 "işlemci". Dizüstü bir bilgisayarda bile tek bir programın yalnızca bir çekirdeği kullanması, makinenin yarısından fazlasını boşa harcamak demek.

Ama "dört çekirdek var, programım dört kat hızlanır" varsayımı çoğu zaman yanlıştır. Bir işin bir kısmı her zaman sıralı kalır; çekirdekler aynı belleği paylaşınca birbirlerini bekler; veriyi çekirdekler arasında taşımak da zaman alır. Bölüm 26'da süreçleri ve iş parçacıklarını, Bölüm 27'de yarış koşullarını ve kilitleri gördük. Bu bölümde soru değişiyor: işi nasıl böleriz, bölünce ne kadar kazanırız ve neden beklenen kazancı alamayız?

Bu soru mühendislikte doğrudan karşına çıkar. Bir İHA'nın görüntü işleme hattında kare başına ayrılan süre, bir radar sinyalinin işlenmesi ya da bir uçuş kontrol döngüsünün son tarihi, işin hangi çekirdeğe, hangi sırayla ve hangi bekleme ile dağıtıldığına bağlıdır. Savunma sanayiinde "işlemci sayısını artırdık, sistem hızlandı mı?" sorusunun cevabını ölçmeden veremezsin; genel bilgi olarak, bu tür sistemlerde gerçek zamanlı kısıt ihlali çoğu zaman ortalama hızda değil, en kötü durumdaki gecikmede ortaya çıkar.

Mülakatlarda da bu konu sık sorulur: "Amdahl yasası nedir?", "bu kodu dört çekirdekte çalıştırınca neden üç kat hızlanmadı?", "bir veri yapısını kilitsiz nasıl paylaşırsın?" Bu bölümü bitirdiğinde bu soruların her birine bir ölçümle cevap verebilmelisin.

Bu bölümün yaklaşımı, Kısım XIII'ün öbür yarısı olan Bölüm 52'deki sinyal işleme ve Bölüm 19'daki böl ve fethet fikriyle aynı: önce bir model kur, sonra modeli bir programla sına, sonra farkı açıkla. Her iddiayı bir ölçüm ile destekledik; kodların tamamı kitapta ve sabit tohum (`seed 53`) kullanılıyor.

::: not
Bu bölümdeki her sayı bir programın çıktısıdır. Ölçüm makinesi: AMD Ryzen 7 6800H (8 çekirdek, 16 iş parçacığı), 15 GB RAM, WSL2 içinde Ubuntu 24.04 ve gcc 13.3 (C programları); Windows 11 üzerinde CPython 3.12.10 ve NumPy (OpenBLAS 0.3.30, Python programları). Diğer süreçler aynı makinede çalışırken ölçüm yapıldı; her ölçüm birkaç kez tekrarlanıp medyanı alındı. Tekrarlar arasında değerler yaklaşık %10 oynadı; bu yüzden tablolardaki sayılardan tam değer değil, düzen ve eğilim okuyun.
:::

## 53.1 Eşzamanlılık ve paralellik

Bu iki kelime günlük konuşmada karışır, ama mühendislikte ayrı şeylerdir. Rob Pike'ın bu ayrımı sık anılır (genel bilgi): **eşzamanlılık** (concurrency), birden çok işi aynı anda *yönetebilme* yapısıdır; **paralellik** (parallelism) ise birden çok işi aynı anda *çalıştırmaktır*. Eşzamanlı bir program tek çekirdekte de çalışabilir; işler sırayla, kısa dilimler hâlinde ilerler ve hepsi bir sürede ilerlemiş görünür. Paralel çalışma ise en az iki fiziksel yürütme birimi gerektirir.

Bir mutfak benzetmesi işe yarar. Tek bir aşçı iki yemeği aynı anda pişiriyor gibi görünür: soğanı kavururken fırındaki tepsiyi kontrol eder, sonra sosa döner. Bu eşzamanlılıktır; iş yönetimi vardır, ama tek bir el çalışır. İki aşçı aynı anda iki yemek pişirirse bu paralelliktir. Eşzamanlılık bir *tasarım* sorusudur ("hangi işler bağımsız, hangi bekleme nerede?"); paralellik ise bir *çalıştırma* özelliğidir ("bu makinede gerçekten aynı anda mı çalışıyor?").

Şekil 53.1, iki durumu yan yana gösteriyor. Üstte tek çekirdekte iki görev dönüşümlü çalışıyor; alttaki iki çekirdekte ise her görev kendi çekirdeğinde tamamlanıyor.

![Şekil 53.1: Üstte tek çekirdekte dönüşümlü (eşzamanlı) çalışma, altta iki çekirdekte gerçek paralel çalışma.](gorseller/b53_esz_par.png)

Bu ayrım neden önemli? Çünkü her iki durumda da sorunlar farklıdır. Eşzamanlılıkta asıl tehlike **yarış koşulu** ve **kilitlenmedir** (Bölüm 27); bunları tek çekirdekte bile yaşarsın. Paralellikte ise yeni bir soru gelir: bu işi bölersem gerçekten ne kadar hızlanırım? Bölüm 27'deki yarışları çözmek programı doğru yapar, ama hızlandırmaz. Bu bölümün konusu ikinci sorudur. Tabloda iki kavramın farkını toparlayalım:

| Soru | Eşzamanlılık | Paralellik |
|---|---|---|
| Ne yönetilir? | Birden çok görev, bekleme ve olaylar | Aynı anda yürüyen hesap |
| Gereken donanım | Tek çekirdek de yeterli | En az iki yürütme birimi |
| Tipik hata | Yarış, kilitlenme, açlık | Yük dengesizliği, bellek çekişmesi |
| Bu kitapta | Bölüm 26, 27, 28, 31 | Bu bölüm (53) |

## 53.2 Donanım sınıflandırması: Flynn'den bu makineye

1966'da Michael Flynn, bilgisayar mimarilerini veri ve komut akışlarının sayısına göre dört sınıfa ayırdı (genel bilgi). Bu sınıflar bugün de kullanılır; ama modern işlemcilerin çoğu tek bir sınıfa girmez, birkaçını birden içerir.

- **SISD** (tek komut, tek veri): klasik tek çekirdekli, skaler işlemci. Bir komut bir değer üzerinde çalışır.
- **SIMD** (tek komut, çok veri): aynı komut bir vektör register'ındaki birçok değer üzerinde aynı anda çalışır. Bölüm 24.8'de SSE ve AVX2 ile yapılan vektör işlemlerini gördük; bu, tek çekirdek içinde bir paralelliktir.
- **MISD** (çok komut, tek veri): pratikte nadir; hata toleransı için bazı yedekli sistemlerde görülür. Bu kitapta ayrıntıya girmiyoruz.
- **MIMD** (çok komut, çok veri): birbirinden bağımsız çekirdeklerin her biri kendi komut akışını ve veri kümesini yürütür. Bugünkü çok çekirdekli işlemcilerin ve sunucuların çoğu buna girer.

Bu sınıflandırmada bir boşluk var: GPU'lar binlerce iş parçacığını tek bir komut akışıyla yönetir. Bunu NVIDIA "SIMT" (single instruction, multiple threads) diye adlandırır; ayrıntısı Bölüm 53.11'de. Tablo olarak özetleyelim:

| Sınıf | Komut akışı | Veri akışı | Örnek |
|---|---|---|---|
| SISD | Tek | Tek | Klasik skaler çekirdek |
| SIMD | Tek | Çok (vektör) | AVX2 ile 8 `float` toplama |
| MIMD | Çok | Çok | 8 çekirdekli Ryzen, sunucu |
| SIMT | Tek (warp) | Çok (iş parçacığı) | GPU çekirdeği (Bölüm 53.11) |

Şimdi kendi makinemize bakalım. Aşağıdaki çıktı, WSL2 içinde çalıştırdığımız `lscpu` komutunun işlemci özetidir; işletim sisteminin gördüğü çekirdek ve iş parçacığı sayısı bu şekilde okunur.

```term
$ lscpu | egrep "Model name|^CPU\(s\)|Thread|Core"
CPU(s): 16
Model name: AMD Ryzen 7 6800H with Radeon Graphics
Thread(s) per core: 2
Core(s) per socket: 8
```

"Thread(s) per core: 2" satırı, her fiziksel çekirdeğin iki mantıksal iş parçacığı (AMD'de SMT, Intel'de Hyper-Threading) sunduğunu gösterir. Bu iki mantıksal iş parçacığı bir fiziksel çekirdeğin hesap birimlerini paylaşır. İki iş parçacığı birbirinden bağımsız bellek bekleyen işler yapıyorsa SMT kazanç sağlar; ikisi de aynı hesap birimini yoğun kullanıyorsa kazanç azdır. Bu fark Bölüm 53.3'te ölçümde görünecek.

GPU bilgisi de ilgimizi çekiyor. `nvidia-smi` ile sorguladığımızda makinede bir NVIDIA GeForce RTX 3060 Laptop GPU ve 6144 MiB bellek olduğunu gördük. Bu bölümde GPU üzerinde kod çalıştırmadık; GPU'yu yalnızca kavramsal olarak, Bölüm 53.11'de ele alıyoruz.
## 53.3 Performans yasaları: Amdahl, Gustafson ve ölçüm

Bir işi p çekirdeğe böldüğünde hızlanmanın üst sınırı nedir? Bu sorunun iki klasik cevabı vardır ve ikisi de aynı gerçeğe dayanır: işin bir kısmı paralelleştirilemez. Bu kısım **seri kesir** (serial fraction) olarak adlandırılır ve `s` ile gösterilir. İşin geri kalanı `1 - s` oranında paralelleştirilebilir.

### Amdahl yasası: sabit iş, güçlü ölçekleme

Gene Amdahl 1967'de, tek bir sabit büyüklükteki iş için şu oranı yazdı (genel bilgi):

`S(p) = T1 / Tp = 1 / (s + (1 - s) / p)`

Burada `T1` işin tek çekirdekte süresi, `Tp` p çekirdekte süresidir. Formülün sezgisi basit: süre iki parçadan oluşur; seri kısım `s·T1` her zaman aynı kalır, paralel kısım `(1-s)·T1 / p` kadar küçülür. p ne kadar büyük olursa olsun, seri kısım sabit bir taban oluşturur. p sonsuza giderken hızlanma `1/s` değerine yaklaşır. Yani seri kesri %10 olan bir işte, kaç çekirdek alırsan al, 10 kattan fazla hızlanamazsın.

Bu yasa mülakatta en sık kullanılan "neden hızlanmadı?" cevabıdır. Ama yasayı ezberlemek yetmez; sınırını ölçmek gerekir. Bunun için seri kesri bilerek ayarladığımız bir C programı yazdık.

### Gustafson yasası: iş çekirdek sayısıyla büyürse

Amdahl'ın varsayımı sabit işti. Gerçek hayatta çoğu zaman tersini yaparız: çekirdek sayısı arttıkça daha büyük bir problem çözeriz (daha yüksek çözünürlüklü görüntü, daha uzun simülasyon). 1988'de John Gustafson bu durum için farklı bir ölçü önerdi (genel bilgi). Paralel çalıştırmanın süresi `T_p` üzerinden seri kesir `s` alınırsa ölçeklenmiş hızlanma şöyledir:

`Sw(p) = s + (1 - s) * p`

Bu formülde seri kısım sabit kalır, paralel kısım p kat büyüyen iş için p kat çalışır. Böylece hızlanma çekirdek sayısıyla doğrusal artar; eğim `1-s` ile belirlenir. Amdahl sabit işte bir tavan çizer, Gustafson büyüyen işte bir eğim çizer. İki yasa çelişmez; farklı soruları yanıtlar.

Bu iki yaklaşım iki tür ölçeklemeye karşılık gelir:

- **Güçlü ölçekleme** (strong scaling): iş sabit, çekirdek sayısı artar. Soru: "Bu işi daha hızlı bitirebilir miyim?" Amdahl'ın alanı.
- **Zayıf ölçekleme** (weak scaling): her çekirdeğe düşen iş sabit, toplam iş çekirdek sayısıyla büyür. Soru: "Daha büyük bir problemi aynı sürede çözebilir miyim?" Gustafson'ın alanı.

### Ölçüm programı: `olcek.c`

Her iki yasayı da gerçek bir programla deniyoruz. Program bir işi üç parçaya ayırır: seri bir kısım ve `BIRIM = 4096` paralel birim. Her birim, bellek kullanmayan bir tamsayı karma döngüsüdür; yani iş tamamen ALU'da yapılır ve bellek bant genişliği darboğazı burada devreye girmez. Bu seçim bilinçlidir: önce saf hesabın ölçeklemesini görmek, sonra bellek etkisini Bölüm 53.9'da eklemek istiyoruz.

Programın çekirdeği olan `kur` fonksiyonu ile başlıyoruz. Döngünün her adımı bir önceki sonuca bağlıdır; bu, derleyicinin döngüyü paralel ya da vektörleştirerek kısaltmasını engeller.

```c
/* b53_olcek.c - Amdahl (guclu) ve Gustafson (zayif) olcegi.
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_olcek.c -o olcek
 * Kullanim: ./olcek guclu 0.10     (sabit toplam is, seri kesir 0.10)
 *           ./olcek zayif 0.10     (is p ile buyur, seri kesir 0.10)
 * Cikti: CSV. Medyan sure saniye cinsinden.
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NG 400000000UL   /* guclu: toplam iterasyon */
#define N0 100000000UL   /* zayif: 1 birimlik temel is */
#define BIRIM 4096       /* guclu: paralel birim sayisi */
#define ZKOK 256         /* zayif: is parcacigi basina birim */
#define TEKRAR 5

static unsigned long out[BIRIM];
static volatile unsigned long sink;

/* Tamsayi karma dongusu: bellek kullanmaz, yalnizca ALU. */
static unsigned long kur(unsigned long n, unsigned long tohum) {
    unsigned long s = tohum;
    for (unsigned long i = 0; i < n; i++)
        s = (s * 31UL + i) ^ (s >> 7);
    return s;
}
```

Aşağıdaki parça, seri kısmı ve paralel birimleri çalıştıran `kos` fonksiyonudur. Seri kısım yalnızca bir iş parçacığında çalışır. Paralel döngü `#pragma omp parallel for` ile p iş parçacığına bölünür; her birim kendi `out[b]` yuvasına yazar, böylece iş parçacıkları aynı konuma yazmaz ve yarış oluşmaz (Bölüm 27'deki yarış tanımına göre temiz bir paralel döngü).

```c
/* Once seri kisim (tek is parcacigi), sonra p parcacikla birim. */
static double kos(unsigned long seri, unsigned long birim,
                  int nb, int p) {
    double t0 = omp_get_wtime();
    sink = kur(seri, 1);
    #pragma omp parallel for num_threads(p) schedule(static)
    for (int b = 0; b < nb; b++)
        out[b] = kur(birim, (unsigned long)b);
    unsigned long t = 0;
    for (int b = 0; b < nb; b++) t ^= out[b];
    sink ^= t;
    return omp_get_wtime() - t0;
}

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static double medyan(double *v, int n) {
    qsort(v, n, sizeof v[0], karsilastir);
    return v[n / 2];
}
```

Ana program iki mod sunar. `guclu` modunda toplam iş sabittir ve seri kesir `s` ile ayarlanır. `zayif` modunda ise her iş parçacığı 256 birim alır; toplam iş p ile büyür ve seri kısım sabit tutulur. Zayıf modda, ölçeklenmiş hızlanma için aynı işi bir kez de tek iş parçacığında çalıştırıp süreyi karşılaştırırız.

```c
int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "kullanim: %s guclu|zayif s\n", argv[0]);
        return 1;
    }
    int zayif = strcmp(argv[1], "zayif") == 0;
    double s = atof(argv[2]);
    int pler[] = {1, 2, 4, 6, 8, 10, 12, 14, 16};
    int np = (int)(sizeof pler / sizeof pler[0]);
    printf("# mod=%s seri=%.2f tekrar=%d\n", argv[1], s, TEKRAR);
    if (!zayif) {
        double t1 = 0;
        printf("p,medyan_s,hizlanma,verim\n");
        for (int k = 0; k < np; k++) {
            double t[TEKRAR];
            unsigned long seri = (unsigned long)(s * NG);
            unsigned long birim =
                (unsigned long)((1.0 - s) * NG / BIRIM);
            for (int r = 0; r < TEKRAR; r++)
                t[r] = kos(seri, birim, BIRIM, pler[k]);
            double m = medyan(t, TEKRAR);
            if (pler[k] == 1) t1 = m;
            printf("%d,%.4f,%.3f,%.3f\n", pler[k], m, t1 / m,
                   t1 / m / pler[k]);
        }
    } else {
        printf("p,medyan_tp_s,medyan_tseq_s,");
        printf("olceklenmis_hizlanma,verim\n");
        unsigned long seri = (unsigned long)(s * N0);
        int nb_taban = ZKOK;
        for (int k = 0; k < np; k++) {
            int p = pler[k];
            int nb = nb_taban * p;     /* is p ile buyur */
            unsigned long birim =
                (unsigned long)((1.0 - s) * N0 / ZKOK);
            double tp[TEKRAR], ts[TEKRAR];
            for (int r = 0; r < TEKRAR; r++) {
                tp[r] = kos(seri, birim, nb, p);   /* paralel */
                ts[r] = kos(seri, birim, nb, 1);  /* tek iplik */
            }
```

Dosyanın son satırları ana fonksiyonun kapanışıdır:

```c
            double mp = medyan(tp, TEKRAR), ms = medyan(ts, TEKRAR);
            printf("%d,%.4f,%.4f,%.3f,%.3f\n", p, mp, ms, ms / mp,
                   ms / mp / p);
        }
    }
    return 0;
}
```

Programı WSL2 içinde `gcc -O2 -std=c11 -fopenmp` ile derledik ve her p değeri için 5 tekrar alıp medyanı kullandık. Platform notu: Linux'ta (WSL2 dahil) `long` ve `unsigned long` 8 bayttır, Windows'ta (LLP64) ise 4 bayttır. Programlarımız karma hesabını `unsigned long` ile yaptığı için aynı kodu Windows'ta derlersen taşma davranışı değişir ve sonuçlar farklı çıkar. Bu yüzden tüm C ölçümlerini WSL2 içinde, Linux (LP64) modelinde yaptık. Seri kesir için `s = 0` (saf paralel) ve `s = 0,10` çalıştırdık. Aşağıda `guclu` modunun iki çıktısını ve `zayif` modunun çıktısını görüyorsun:

```term
$ ./olcek guclu 0.0
# mod=guclu seri=0.00 tekrar=5
p,medyan_s,hizlanma,verim
1,0.3714,1.000,1.000
2,0.1908,1.946,0.973
4,0.1006,3.692,0.923
6,0.0691,5.378,0.896
8,0.0555,6.689,0.836
10,0.0451,8.236,0.824
12,0.0384,9.670,0.806
14,0.0339,10.958,0.783
16,0.0401,9.254,0.578
```

```term
$ ./olcek guclu 0.10
# mod=guclu seri=0.10 tekrar=5
p,medyan_s,hizlanma,verim
1,0.3709,1.000,1.000
2,0.2052,1.807,0.904
4,0.1263,2.937,0.734
6,0.1009,3.677,0.613
8,0.0873,4.248,0.531
10,0.0780,4.752,0.475
12,0.0716,5.178,0.431
14,0.0675,5.492,0.392
16,0.0747,4.962,0.310
```

```term
$ ./olcek zayif 0.10
# mod=zayif seri=0.10 tekrar=5
p,medyan_tp_s,medyan_tseq_s,olceklenmis_hizlanma,verim
1,0.0938,0.0931,0.993,0.993
2,0.0945,0.1766,1.869,0.935
4,0.0979,0.3456,3.531,0.883
6,0.0985,0.5067,5.144,0.857
8,0.1035,0.6773,6.543,0.818
10,0.1065,0.8371,7.859,0.786
12,0.1080,1.0091,9.348,0.779
14,0.1145,1.1898,10.391,0.742
16,0.1310,1.3409,10.235,0.640
```

Ölçümü tahminle karşılaştırmadan önce tablo okuma becerisi gerekir. `hizlanma` sütunu `T1 / Tp` oranıdır, `verim` ise `hizlanma / p`. Verim 1,0 ise çekirdeğin tamamı işe yarıyor; verim p arttıkça düşüyorsa paralel olmayan bir kayıp var demektir.

Tablo ile Amdahl tahminini yan yana koyalım. Seri kesir `s = 0,10` için Amdahl formülü p = 2, 4, 8 ve 16 değerlerinde sırasıyla 1,82; 3,08; 4,71 ve 6,40 verir. Ölçülen değerler 1,81; 2,94; 4,25 ve 4,96. Küçük p'de tahmin ile ölçüm birbirine çok yakın; p büyüdükçe ölçüm tahminin altında kalıyor. Bu fark, Amdahl'ın modelinde olmayan bir maliyetin işaretidir: iş parçacıklarını başlatma, birim sonuçlarını birleştirme ve (sonraki bölümlerde göreceğimiz) bellek ve kaynak çekişmesi.

Bu farkı tek bir sayıya indirgemek için **Karp–Flatt metriği** kullanılır (genel bilgi). Ölçülen hızlanmadan etkin seri kesri geri hesaplar:

`e(p) = (1/S(p) - 1/p) / (1 - 1/p)`

Eğer model doğruysa `e(p)` her p için tasarlanan `s` değerine yakın çıkmalıdır. Bizde `s = 0,10` için p = 4 ile 14 arasında `e(p)` 0,119 ile 0,126 arasında kaldı; p = 16'da 0,148'e çıktı. Yani etkin seri kesir, tasarladığımızdan yaklaşık 0,02 büyük; bu fazlalık paralel döngünün başlatma ve birleştirme maliyetinden gelir. p = 16'da artış ise bir sonraki paragrafta anlatılan SMT ve arka plan yükünün etkisidir.

Şekil 53.2, teorik eğrileri ve ölçüm noktalarını yan yana koyuyor. Sol panelde güçlü ölçekleme eğrileri Amdahl'ın tavanına yaklaşıyor; sağ panelde zayıf ölçekleme noktaları Gustafson doğrusuna yakın ama ondan hafifçe aşağıda.

![Şekil 53.2: Solda güçlü ölçekleme (Amdahl) ve sağda zayıf ölçekleme (Gustafson); eğriler teorik, noktalar ölçüm.](gorseller/b53_amdahl_gustafson.png)

Zayıf ölçeklemede ölçülen `olceklenmis_hizlanma` p = 8 için 6,54; Gustafson formülü `s = 0,10` ile 7,3 verir. Fark, serisel kesrin ölçeklenmiş koşuda `s`'ten biraz farklı olmasından ve paralel kısmın bellek etkisinden gelir. Şekil 53.3 verimi gösteriyor: güçlü ölçeklemede verim p = 8'e kadar hızla düşmüyor, ama `s = 0,10` eğrisinde ise p büyüdükçe verim belirgin biçimde düşüyor (p = 8'de 0,53).

![Şekil 53.3: Solda üç ölçeklemenin verimi (p = 8'de dikey çizgi, fiziksel çekirdek sayısı); sağda Karp–Flatt ile ölçülen seri kesir.](gorseller/b53_olcum_verim.png)

Son olarak SMT konusuna dönelim. Güçlü ölçekleme eğrisi `s = 0` için p = 14'te 10,96 kata çıkıyor; sekiz fiziksel çekirdeğe rağmen. Bu, `kur` döngüsünün her iterasyonunun bir önceki sonuca bağlı olmasından kaynaklanıyor: bir iş parçacığı çarpma ve xor gecikmesini beklerken, aynı çekirdeğin ikinci mantıksal iş parçacığı boş hesap birimlerini kullanabiliyor. Bu bir yorumdur; SMT'nin etkisini ayrı bir deneyle doğrulamadık. Yine de bu, Bölüm 24'teki boru hattı ve gecikme anlayışının doğrudan bir sonucudur: gecikme bağımlı işte SMT yardım eder, hesap birimi bağımlı işte etmez. Yük 16 iş parçacığına çıktığında hem düşüş hem arka plan yükü devreye girer; sonuç olarak en yüksek hızlanma 14 iş parçacığında görüldü.

::: ipucu
Amdahl'ı kullanırken iki hatadan kaçın. Birincisi, `s`'yi koddan tahmin etmek yerine ölçmek: yalnızca seri kısmın süresini ölç ve toplama böl. İkincisi, yasayı paralel iş parçacığı sayısının "sınırsız" olduğu varsayımıyla kullanmak: gerçek sistemde bellek bant genişliği (Bölüm 53.9), kilitler ve SMT sınırı, teorik tavanı çok daha erken keser.
:::
## 53.4 İş–açıklık modeli ve Brent teoremi

Amdahl yasası bir işin seri kesrini bilmeyi ister. Ama bir algoritmayı tasarlarken genelde seri kesri hesaplamaz, paralelliğin yapısını düşünürüz. Bunun için daha genel bir dil kullanılır: **iş–açıklık** (work–span) modeli (genel bilgi, Blumofe ve Leiserson'un çalışmalarından bilinen bir çerçeve).

Model iki ölçüye dayanır. **İş** `T1`, işi tek işlemcide yapmanın toplam maliyetidir: işin bütün düğümlerinin sayısı. **Açıklık** (span) `T∞`, sonsuz sayıda işlemci olsa bile değişmeyen en uzun bağımlılık zincirinin uzunluğudur; yani işin "paralelleştirilemeyen omurgası". İşi bir yönlü çevrimsiz graf (DAG) olarak düşünürsek, `T1` tüm düğümlerin sayısı, `T∞` ise graftaki en uzun yolun uzunluğudur.

Buradan bir **paralellik** ölçüsü çıkar:

`paralellik = T1 / T∞`

Bu oran, en fazla kaç işlemcinin işe yarayacağının bir üst sınırını verir. Paralellik 2,3 ise dört işlemci almak boşa harcamaktır; en fazla iki buçuk işlemcinin anlamlı katkısı olur.

Brent teoremi, p işlemcide çalışma süresinin bir üst sınırını verir (genel bilgi):

`Tp <= T1 / p + T∞`

Sezgisi şudur: süre, işin p'ye bölünmüş hâli (`T1/p`) artı kritik yolun zorunlu maliyeti (`T∞`) kadardır. Bu formül Amdahl'ın yapısal bir karşılığıdır: `T∞`, seri kesrin "zorunlu" payının genelleştirilmiş hâlidir. Ama dikkat: Brent bir üst sınır verir, gerçek süre bellek ve zamanlayıcı maliyetleri yüzünden genelde biraz daha uzundur.

Somut bir örnek için 8 elemanlı bir dizinin toplamını ele alalım. Şekil 53.4'te her kutu bir toplamadır, yapraklar girdi elemanlarıdır. Seri toplama 7 toplama yapar, yani `T1 = 7`. Ağaçta en uzun yol 3 toplamadan geçer, yani `T∞ = 3`. Paralellik `7/3 ≈ 2,3` olur. Bu rakam, bu küçük örnekte dört işlemciye dayanmanın yetersiz olduğunu gösterir.

![Şekil 53.4: 8 elemanlı toplamın iş–açıklık DAG'ı. Yedi toplama toplam iştir (T1 = 7); en uzun yol üç seviyedir (T∞ = 3).](gorseller/b53_is_aciklik.png)

Bu modelin gücü, paralelliği *yapısal* olarak görmesidir. Birleştirme sıralamasında (Bölüm 19'dan) iş `Θ(n log n)`dir. Birleştirme adımı seri yapılırsa açıklık `Θ(n)` olur; ana birleşim tek başına `n` adım sürer ve paralellik yalnızca `Θ(log n)` kalır. Birleşimi de paralel yaparsan açıklık `O(log² n)`'e iner (genel bilgi, Bölüm 19.12'de bu sonuca atıf yapmıştık). Bölüm 53.5'teki ve Örnek 4'teki paralel birleştirme sıralamasının açıklığını bu model üzerinden hesaplayacağız.

## 53.5 Ayrıştırma kalıpları

İş–açıklık modeli bir algoritmanın *ne kadar* paralel olabileceğini söyler. Pratikte iş genelde birkaç tekrar eden kalıba oturur. Bu kalıpları tanırsan yeni bir problemi bile hızlıca paralelleştirebilirsin.

- **Veri paralelliği (map).** Her eleman bağımsız bir işlemden geçer: bir görüntünün her pikseli, bir sensör dizisinin her örneği. Açıklık sabit kalır, paralellik veri boyutu kadardır. Bu, GPU'ların en çok sevdiği kalıptır (Bölüm 53.11).
- **Görev paralelliği (task parallelism).** Farklı işlevler farklı iş parçacıklarında çalışır: bir İHA'da görüntü toplama, hedef tespiti ve telemetri kaydı birbirinden bağımsız olabilir. Paralellik, bağımsız görevlerin sayısıyla sınırlıdır; biri çok yavaşsa diğerleri onu hızlandırmaz.
- **Boru hattı (pipeline).** İş aşamalara ayrılır ve her aşama farklı bir çekirdekte çalışır; aşamalar arasında kuyruk bulunur. Sürekli akışta verim, en yavaş aşamanın hızıyla belirlenir; bu, Bölüm 41.8'de gördüğümüz kuyruk ve geri basınç (backpressure) fikrinin doğrudan uygulamasıdır.
- **İndirgeme (reduction).** Bir operatörle (toplam, maksimum, en küçük) diziyi tek değere indirirsin. Doğrusal bir zincir yerine ağaçla yaparsan açıklık `log n` seviyeye düşer. Şekil 53.5, 8 elemanlı bir toplamı yedi sıralı adım yerine üç seviyede bitiriyor.

![Şekil 53.5: Ağaçla indirgeme. Her seviyedeki toplamalar bağımsızdır; 8 eleman üç seviyede (log2 8 = 3) toplanır.](gorseller/b53_indirgeme.png)

- **Tarama (scan, önek toplamı).** Her çıktı elemanı, kendisine kadar olan tüm girdilerin toplamıdır. İndirgeme gibi görünür ama her ara sonucu da üretmek gerekir; seri çözüm basittir, paralel çözüm ise daha az basit. Guy Blelloch'un dışlayıcı tarama algoritması, işi iki süpürme ile yapar: önce yukarı doğru bir indirgeme ağacı, sonra aşağı doğru bir dağıtım (genel bilgi). Şekil 53.6, 8 elemanlı bir örnekte bu iki süpürmeyi adım adım gösteriyor. Her satır bir süper adımın sonucudur; kodu ve izini Örnek 2'de görüyorsun.

![Şekil 53.6: Blelloch taramasında üst satırlar yukarı süpürme, alt satırlar aşağı süpürme. Son satır dışlayıcı önek toplamıdır.](gorseller/b53_blelloch.png)

Blelloch taramasının iş–açıklık değeri şöyledir. Toplam toplama sayısı `2(n - 1)` eder; yani iş hâlâ doğrusaldır (`O(n)`), ama sıralı taramanın `n - 1` toplamasının iki katını yapar. Açıklık ise `2 log2 n` süper adımdır. Paralellik `(2(n-1)) / (2 log2 n)` gibi davranır; büyük `n` için yaklaşık `n / log2 n` olur. Bu tam olarak paralel tarama algoritmalarının değer önerisidir: iki kat iş pahasına logaritmik açıklık.

- **Stencil.** Her çıktı elemanı kendi komşuluğunun bir fonksiyonudur: 2B konvolüsyon, ısı denklemi, görüntü bulanıklaştırma. Veri paralelliğinin bir türüdür ama komşuluk nedeniyle sınır elemanlarında paylaşılan veri oluşur. Bunu Kendin Yap Projesi 1'de kullanacağız.
- **Böl ve yönet + fork-join.** Bölüm 19'da anlattığımız böl ve yönet şablonu doğal bir paralel yapıdır: iki alt problem bağımsızdır, `fork` ile ikiye ayrılır, `join` ile birleşir. Birleştirme sıralamasının paralel hâli Örnek 4'te ölçülecek.

Bu kalıpların hepsi tek bir ilkeye dayanır: **bağımsız iş ne kadar çoksa ve bağımlılık zinciri ne kadar kısaysa, o kadar çok çekirdek işe yarar.** Bağımlılığı görmeden paralelleştirmeye çalışmak, Bölüm 27'deki yarış koşullarının tam kaynağıdır.
## 53.6 Yük dengeleme: statik, dinamik ve iş çalma

Bir paralel döngünün süresi, en geç biten iş parçacığı tarafından belirlenir. Bu yüzden iş parçacıkları eşit *iş* aldığında değil, eşit *süre* çalıştığında iyi sonuç verir. Eşit olmayan iş, paralel programların en sık karşılaşılan sorunudur ve buna **yük dengesizliği** (load imbalance) denir.

Bir döngüyü iş parçacıklarına dağıtmanın üç temel yolu vardır:

- **Statik zamanlama.** İterasyonlar baştan parçalara ayrılır; her iş parçacığı kendi parçasını çalıştırır. Dağıtım maliyeti düşüktür, ama iterasyonların maliyeti eşit değilse bir iş parçacığı geride kalır.
- **Dinamik zamanlama.** İterasyonlar küçük parçalar (`chunk`) hâlinde bir kuyrukta durur; boşta kalan iş parçacığı bir sonraki parçayı alır. Dengesizliği azaltır, ama her parça için kuyruk erişimi maliyeti ekler.
- **Guided (kılavuzlu) zamanlama.** Dinamiğin bir varyantıdır: parçalar başta büyük, sonda küçüktür. Böylece hem erişim sayısı azalır hem de sonda dengesizlik küçülür (genel bilgi, OpenMP tanımı).

İş çalma (work stealing) ise dinamik kuyruğun dağıtık bir hâlidir. Her iş parçacığının kendi kuyruğu vardır; işi biten bir iş parçacığı, başka birinin kuyruğunun ucundan iş "çalar". Bölüm 8'de bu fikrin adını ilk kez andık; burada ölçecek kadar somut hâle getiriyoruz. Cilk, Intel TBB ve OpenMP görevleri gibi sistemler bu modeli kullanır (genel bilgi).

Dengesiz iş yükünü ölçmek için `zamanlama.c` programını yazdık. 512 iş var; `i`. iş `(i + 1) * 2000` adımlık bir karma döngüsü: iş maliyeti doğrusal artıyor. Bu, gerçek hayatta sık görülen bir durumdur (ağaç dolaşımı, artan boyutlu matris satırları, sonuçları gittikçe ağırlaşan arama). Her iş bir `th[i]` (hangi iş parçacığı) ve `ts[i]`, `te[i]` (başlangıç ve bitiş zamanı) kaydeder; böylece zaman çizelgesini çizebiliriz.

```c
/* b53_zamanlama.c - statik, dinamik, guided (dengesiz is).
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_zamanlama.c -o zamanlama
 * Kullanim: ./zamanlama <thread>      (ornek: ./zamanlama 8)
 * Is i, (i+1) * BIRIM adimlik bir karma dongusudur: is maliyeti
 * dogrusal artar. Statik bolme son iş parçacigini yukler.
 * Ilk kosunun zaman cizelgesi: engine\veri\b53_gantt.csv
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M 512            /* is (iterasyon) sayisi */
#define BIRIM 2000       /* i. is: (i+1)*BIRIM adim */
#define TEKRAR 5
#define GANTT "b53_gantt.csv"

static volatile unsigned long sink;
static int th[M];
static double ts[M], te[M];

static void yuk(long n) {
    unsigned long s = 1;
    for (long k = 0; k < n; k++)
        s = s * 31UL + (unsigned long)k;
    sink += s;
}
```

Aşağıdaki parça, iş maliyetini ve tek bir zamanlama koşusunu kaydeden fonksiyonları içerir. `omp_set_schedule` çalışma zamanındaki zamanlama türünü seçer; böylece tek bir `schedule(runtime)` satırı üç farklı davranışı sınar.

```c
/* Calisma suresini dondurur; th/ts/te zaman cizelgesini doldurur. */
static double kos(omp_sched_t tur, int p) {
    omp_set_schedule(tur, tur == omp_sched_dynamic ? 8 : 0);
    double t0 = omp_get_wtime();
    #pragma omp parallel for num_threads(p) schedule(runtime)
    for (int i = 0; i < M; i++) {
        ts[i] = omp_get_wtime() - t0;
        yuk((long)(i + 1) * BIRIM);
        te[i] = omp_get_wtime() - t0;
        th[i] = omp_get_thread_num();
    }
    return omp_get_wtime() - t0;
}

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}
```

Ana program her zamanlamayı beş kez çalıştırır, medyanı alır ve ilk koşunun zaman çizelgesini `b53_gantt.csv` dosyasına yazar.

```c
int main(int argc, char **argv) {
    int p = argc > 1 ? atoi(argv[1]) : 8;
    omp_sched_t turler[3] = {omp_sched_static, omp_sched_dynamic,
                             omp_sched_guided};
    const char *ad[3] = {"statik", "dinamik8", "guided"};
    FILE *g = fopen(GANTT, "w");
    if (!g) { perror("gantt"); return 1; }
    fprintf(g, "zamanlama,is,thread,baslangic_ms,bitis_ms\n");
    double t1 = kos(omp_sched_static, 1);   /* tek is referansi */
    printf("# M=%d BIRIM=%d thread=%d tekrar=%d\n", M, BIRIM, p,
           TEKRAR);
    printf("# tek_is_parcacigi_s=%.4f ideal_s=%.4f\n", t1, t1 / p);
    printf("zamanlama,medyan_s,hizlanma\n");
    for (int k = 0; k < 3; k++) {
        double t[TEKRAR];
        for (int r = 0; r < TEKRAR; r++) {
            t[r] = kos(turler[k], p);
            if (r == 0)
                for (int i = 0; i < M; i++)
                    fprintf(g, "%s,%d,%d,%.3f,%.3f\n",
                            ad[k], i, th[i],
                            ts[i] * 1e3, te[i] * 1e3);
        }
        qsort(t, TEKRAR, sizeof t[0], karsilastir);
        printf("%s,%.4f,%.2f\n", ad[k], t[TEKRAR / 2],
               t1 / t[TEKRAR / 2]);
    }
    fclose(g);
    return 0;
}
```

Programı WSL2'de `gcc -O2 -fopenmp` ile derleyip sekiz iş parçacığıyla çalıştırdık:

```term
$ ./zamanlama 8
# M=512 BIRIM=2000 thread=8 tekrar=5
# tek_is_parcacigi_s=0.1833 ideal_s=0.0229
zamanlama,medyan_s,hizlanma
statik,0.0453,4.04
dinamik8,0.0281,6.53
guided,0.0251,7.29
```

Tek iş parçacığında iş 0,183 saniye sürdü; sekiz çekirdeğe ideal bölünmüş süre 0,023 saniye olurdu. Statik zamanlama 0,045 saniye ile yalnızca 4,04 kat hızlandırdı; son iş parçacığı en ağır parçayı aldığı için geri kalanlar beklemek zorunda kaldı. Dinamik (parça 8) 6,53 kat, guided 7,29 kat hızlandırdı. Şekil 53.7 aynı koşunun zaman çizelgesini gösteriyor: statikte son iş parçacığının çubukları sağa doğru uzanırken, dinamik ve guided'da çubuklar neredeyse aynı bitişte duruyor.

![Şekil 53.7: Statik, dinamik (parça 8) ve guided zamanlamada p = 8 iş parçacığının zaman çizelgesi. Her çubuk bir iş; çubuklar arası boşluk bekleme demek.](gorseller/b53_zamanlama_gantt.png)

Bu sonuçta iki ders var. Birincisi, dengesiz iş için statik bölme ciddi bir kayıptır; bu kayıp, dinamik ya da guided ile büyük ölçüde geri alınabilir. İkincisi, guided'ın dinamik 8'den daha iyi çıkması, başta büyük parçaların erişim maliyetini düşürmesinden ve sonda küçük parçalarla dengeyi toplamasından gelir. Ama parça boyutunu sezgiyle seçmek riskli; doğru değeri ölçerek bulursun.

::: dikkat
Dinamik zamanlamanın parça boyutu çok küçük seçilirse kuyruk erişimi iş yükünün önüne geçer. Bunu Örnek 4'te eşik seçiminde ve 53.8'deki `chunksize` deneyinde ayrıca göreceğiz: çok küçük parça, hesabın kendisinden daha pahalıya gelir.
:::

## 53.7 C'de paralellik: OpenMP ve pthreads

C'de paralel programlamanın iki yaygın yolu vardır. **pthreads** (POSIX iş parçacıkları) Bölüm 26'da tanıdığımız düşük seviyeli API'dir: iş parçacığını kendin oluşturur, işi kendin bölersin, kendin birleştirirsin. **OpenMP** ise derleyiciye pragma'lar verirsin, derleyici iş parçacığı yönetimini ve döngü bölmesini üstlenir. Derlemek için `gcc -fopenmp` yeterlidir.

Bir OpenMP döngüsünün tipik hâli şöyledir; bu parça bir örnek kalıptır, tam program değildir:

```c
double toplam = 0.0;
#pragma omp parallel for reduction(+:toplam) schedule(static)
for (long i = 0; i < n; i++)
    toplam += x[i];
```

Bu beş satırda dört kavram var. `parallel for`, döngüyü iş parçacıklarına böler. `reduction(+:toplam)`, her iş parçacığına kendi kısmi toplamını verir ve sonunda bunları birleştirir; böylece tek bir paylaşılan `toplam` değişkenine yarış koşulu oluşmaz. `schedule(static)` zamanlama türünü seçer (53.6). Döngü içindeki `i` her iş parçacığında özel (private) olur; `x` ve `n` ise paylaşılan (shared) okunur.

Reduction'ın doğru çalıştığını görmek için iki yaklaşımın farkını bilmek gerekir. Paylaşılan bir değişkene doğrudan yazarsan, iki iş parçacığının aynı anda okuyup yazması bir kayıp güncellemeye yol açar; bunu Örnek 3'te kasıtlı olarak göreceğiz. `reduction` bunu önler, çünkü her iş parçacığı kendi kopyasına yazar. Kısmi toplamların birleşme sırası ise iş parçacığı sayısına bağlı olabilir; bu, 53.10'da ayrıca konu olacak.

Şimdi aynı işi pthreads ile el ile bölmeyi deneyelim ve iki yaklaşımı karşılaştıralım. Program 10^8 elemanlık bir işi (küçük bir karma hesabı) sekiz iş parçacığına bölüyor. İş küçük olmadığı için iş parçacığı oluşturma maliyeti hesabın içinde kaybolur; ama önce bu maliyeti ayrıca ölçüyoruz. Program iki şeyi ölçer: boş bir işle sekiz iş parçacığının oluşturulup birleştirilmesi (olusturma_birlestirme) ve gerçek işin üç yolla çalıştırılması (sıralı, pthreads, OpenMP). Sonuçlar XOR ile birleştirildiği için her yolun sonucu aynı olmalıdır; bu bir doğruluk kontrolüdür.

```c
/* b53_pthread.c - pthreads ile elle bolme, OpenMP ve is parcacigi
 * olusturma maliyeti.
 * Derleme: gcc -O2 -std=c11 -pthread -fopenmp b53_pthread.c -o pth
 * Kullanim: ./pth <thread>          (ornek: ./pth 8)
 * Is: her i icin kucuk bir karma hesabi; sonuc XOR ile birlesir
 * (XOR degisme siralidan bagimsizdir, bu yuzden dogrulama tam olur).
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 100000000UL
#define TEKRAR 5
#define OVH_TEKRAR 2000

static unsigned long hesapla(unsigned long i) {
    unsigned long s = i + 1;
    for (int k = 0; k < 4; k++) s = (s * 31UL) ^ (s >> 7);
    return s;
}

struct is { unsigned long lo, hi, sonuc; };

static void *calis(void *arg) {
    struct is *x = arg;
    unsigned long s = 0;
    for (unsigned long i = x->lo; i < x->hi; i++) s ^= hesapla(i);
    x->sonuc = s;
    return NULL;
}
```

Aşağıdaki parça elle bölmeyi yapan `elle` fonksiyonudur. Her iş parçacığına bir `struct is` aralığı verilir, sonuçlar `is[k].sonuc` alanına yazılır; ortak bir değişkene yazılmadığı için yarış yoktur.

```c
static unsigned long elle(int p) {   /* pthreads ile bolme */
    pthread_t th[64];
    struct is is[64];
    unsigned long pay = N / (unsigned long)p;
    for (int k = 0; k < p; k++) {
        is[k].lo = k * pay;
        is[k].hi = (k == p - 1) ? N : (k + 1) * pay;
        pthread_create(&th[k], NULL, calis, &is[k]);
    }
    unsigned long toplam = 0;
    for (int k = 0; k < p; k++) {
        pthread_join(th[k], NULL);
        toplam ^= is[k].sonuc;
    }
    return toplam;
}

static unsigned long openmp(int p) {         /* OpenMP statik bolme */
    unsigned long toplam = 0;
    #pragma omp parallel for num_threads(p) schedule(static) \
            reduction(^:toplam)
    for (unsigned long i = 0; i < N; i++) toplam ^= hesapla(i);
    return toplam;
}

static unsigned long sirali(void) {
    unsigned long toplam = 0;
    for (unsigned long i = 0; i < N; i++) toplam ^= hesapla(i);
    return toplam;
}

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}
```

Ana program ölçümleri yapar ve sonuçları yazdırır:

```c
int main(int argc, char **argv) {
    int p = argc > 1 ? atoi(argv[1]) : 8;
    /* 1. Olusturma + birlestirme maliyeti (is: sifir iş). */
    double ov[OVH_TEKRAR];
    for (int r = 0; r < OVH_TEKRAR; r++) {
        pthread_t th[64];
        struct is bos = {0, 0, 0};
        double t0 = omp_get_wtime();
        for (int k = 0; k < p; k++)
            pthread_create(&th[k], NULL, calis, &bos);
        for (int k = 0; k < p; k++)
            pthread_join(th[k], NULL);
        ov[r] = omp_get_wtime() - t0;
    }
    qsort(ov, OVH_TEKRAR, sizeof ov[0], karsilastir);
    printf("# thread=%d N=%lu\n", p, N);
    printf("olusturma_birlestirme_medyan_us=%.1f\n",
           ov[OVH_TEKRAR / 2] * 1e6);
    /* 2. Hesap: sirali, pthreads, OpenMP. */
    double tr[TEKRAR], to[TEKRAR], ts[TEKRAR];
    unsigned long r1 = 0, r2 = 0, r3 = 0;
    for (int r = 0; r < TEKRAR; r++) {
        double t0 = omp_get_wtime();
        r1 = sirali();
        ts[r] = omp_get_wtime() - t0;
        t0 = omp_get_wtime();
        r2 = elle(p);
        tr[r] = omp_get_wtime() - t0;
        t0 = omp_get_wtime();
        r3 = openmp(p);
        to[r] = omp_get_wtime() - t0;
    }
    qsort(ts, TEKRAR, sizeof ts[0], karsilastir);
    qsort(tr, TEKRAR, sizeof tr[0], karsilastir);
    qsort(to, TEKRAR, sizeof to[0], karsilastir);
    printf("surum,medyan_s,hizlanma,ayni_sonuc\n");
    printf("sirali,%.4f,1.00,-\n", ts[TEKRAR / 2]);
    printf("pthreads,%.4f,%.2f,%s\n", tr[TEKRAR / 2],
           ts[TEKRAR / 2] / tr[TEKRAR / 2],
           r2 == r1 ? "evet" : "HAYIR");
```

```c
    printf("openmp,%.4f,%.2f,%s\n", to[TEKRAR / 2],
           ts[TEKRAR / 2] / to[TEKRAR / 2],
           r3 == r1 ? "evet" : "HAYIR");
    return 0;
}
```

Çıktı:

```term
$ ./pth 8
# thread=8 N=100000000
olusturma_birlestirme_medyan_us=341.0
surum,medyan_s,hizlanma,ayni_sonuc
sirali,0.1426,1.00,-
pthreads,0.0484,2.95,evet
openmp,0.0355,4.02,evet
```

Bu çıktı iki şey gösteriyor. Birincisi, bir kez sekiz iş parçacığı oluşturup birleştirmek yaklaşık 0,34 milisaniye sürdü. Bu, 0,14 saniyelik işin yaklaşık binde ikisi kadar bir paydır; yani büyük iş için oluşturma maliyeti önemsiz, küçük iş için ise kritik olur. Bu yüzden iş parçacıklarını her işte yeniden yaratmak yerine bir havuzda tutmak (OpenMP'nin yaptığı gibi) yaygın bir tasarımdır.

İkincisi, üç yolun sonucu aynı (`ayni_sonuc = evet`), ama hızları farklı. Elle bölmeli pthreads sürümü 2,95 kat, OpenMP 4,02 kat hızlandırdı. Bu farkın nedenini bu ölçümle ayırt etmedik. Oluşturma maliyeti farkı açıklamıyor (her çağrıda 0,34 ms, toplam 48 ms içinde küçük). Olası bir neden derleyicinin iki döngü gövdesini farklı biçimde optimize etmesi olabilir; ama bunu doğrulamadık. Bu, mühendislikte önemli bir alışkanlığı gösteriyor: iki sürümün neden farklı hızda olduğunu, nedenini ölçmeden söyleme.

## 53.8 Python'da paralellik ve sayısal kütüphaneler

Python'da paralellik iki katmanda düşünülmelidir. Birinci katmanda CPython'un GIL'i (Bölüm 26.12) saf Python bayt kodunun aynı anda yalnızca bir iş parçacığında çalışmasına izin verir. Bölüm 26'da bunu ölçtük: CPU-bağlı iş iş parçacıklarıyla hızlanmadı, dört süreçle yaklaşık 3,5 kat hızlandı. Ayrıca Bölüm 27.18'de `x += 1` ifadesinin bir bayt kodu komutu olmadığını ve GIL'in kullanıcı kodundaki yarışları kendiliğinden önlemediğini gördük.

İkinci katman, NumPy gibi C kütüphaneleridir. NumPy'nin hesap çekirdekleri (örneğin BLAS çağrıları) büyük işlerde GIL'i bırakır ve OpenBLAS gibi kütüphaneler kendi iş parçacıklarını kullanır (genel bilgi). Bu yüzden bir matris çarpımı Python tarafında basit görünse de sekiz çekirdeği kullanabilir. Bölüm 48.14'te BLAS ve LAPACK katmanlarını tanıtmıştık; burada onların iş parçacığı sayısına bağlılığını ölçüyoruz.

Süreç havuzları (`ProcessPoolExecutor`, `multiprocessing.Pool`) GIL sorununu her süreçte ayrı bir yorumlayıcı açarak çözer. Ama bedeli vardır: süreç başlatma, işlerin ve sonuçların **serileştirilmesi** (pickle) ve süreçler arası iletişim. Windows'ta süreçler `spawn` yöntemiyle başlatılır; yani her süreç ana modülü baştan içe aktarır. Bu yüzden `__main__` korumasını unutursan program yinelenen süreçler açmaya çalışır.

Aşağıdaki `pool.py` programı üç soruyu ölçer: (1) `chunksize` (her süreç çağrısına kaç işin birden gönderileceği) süreyi nasıl değiştirir, (2) iş ne kadar büyük olmalı ki havuz kazandırsın, (3) büyük bir diziyi argüman olarak göndermek ile süreç içinde üretmek arasında ne fark var.

```python
# -*- coding: utf-8 -*-
"""b53_pool.py - surec havuzu: chunksize, serilestirme, is buyuklugu.

Calistirma: python -I b53_pool.py
Windows'ta multiprocessing 'spawn' kullanir: ana kod MUTLAKA
if __name__ == "__main__" blogu icinde olmali.
Cikti: engine\\veri\\b53_pool.csv (deney, parametre, tekrar, sure_s)
"""
import csv
import statistics
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HAVUZ = 8
TEKRAR = 3
CIKTI = "b53_pool.csv"

def hafif(x):
    return (x * x) % 1000003

def agir(n):
    s = 0
    for k in range(n):
        s += k * k % 7
    return s

def dizi_ile(dizi):
    return float(dizi.sum())

def uret_ile(args):
    tohum, boyut = args
    return float(np.random.default_rng(tohum).random(boyut).sum())
```

Ölçümün ana gövdesi her deneyi `olc` fonksiyonuyla tekrarlar ve medyan alır. Havuz başlatma süresini ayrı ölçeriz; çünkü Windows'ta sekiz süreç açmak başlı başına bir maliyettir.

```python
def olc(fn, girdi, ex, chunk):
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        list(ex.map(fn, girdi, chunksize=chunk))
        zs.append(time.perf_counter() - t0)
    return statistics.median(zs)

if __name__ == "__main__":
    satirlar = []

    def kaydet(deney, parametre, sure):
        satirlar.append((deney, parametre, sure))
        print(f"{deney:<12s} {str(parametre):<14s} {sure:8.4f} s")

    # 0. Havuz kurulum maliyeti (Windows: yeni yorumlayici acilir).
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
            list(ex.map(hafif, range(HAVUZ)))
        zs.append(time.perf_counter() - t0)
    kaydet("kurulum", "8 surec", statistics.median(zs))
```

Sonraki parça `chunksize` deneyini ve iş büyüklüğü deneyini içerir. `Pool.map` için varsayılan `chunksize` formülünü de burada hesaplayıp karşılaştırıyoruz.

```python
    # 1. chunksize etkisi: 100000 hafif is.
    N = 100000
    girdi = list(range(N))
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        sum(hafif(x) for x in girdi)
        zs.append(time.perf_counter() - t0)
    seri_ref = statistics.median(zs)
    kaydet("seri", N, seri_ref)
    varsayilan, kalan = divmod(N, HAVUZ * 4)     # Pool.map formulu
    if kalan:
        varsayilan += 1
    with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
        list(ex.map(hafif, range(HAVUZ)))         # isinma
        for c in (1, 10, 100, 1000, 10000, varsayilan):
            kaydet("chunksize", c, olc(hafif, girdi, ex, c))

    # 2. Is buyuklugu: 200 agir is, her biri 200000 dongu.
    agir_girdi = [200000] * 200
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        for n in agir_girdi:
            agir(n)
        zs.append(time.perf_counter() - t0)
    kaydet("agir_seri", "200x200000", statistics.median(zs))
    with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
        list(ex.map(agir, [1000] * HAVUZ))
        kaydet("agir_surec", "200x200000",
               olc(agir, agir_girdi, ex, 4))
```

En son parça serileştirme deneyi ve dosyaya yazma adımıdır.

```python
    # 3. Serilestirme: 8 MB dizi argumanla mi, surecte mi?
    boyut = 1000000
    tohumlar = list(range(50))
    diziler = [np.random.default_rng(t).random(boyut)
               for t in tohumlar]
    with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
        list(ex.map(uret_ile, [(0, 10)] * HAVUZ))
        kaydet("arg_dizi", "50x8MB",
               olc(dizi_ile, diziler, ex, 1))
        kaydet("surec_uret", "50 tohum",
               olc(uret_ile, [(t, boyut) for t in tohumlar], ex, 1))
    # Dogruluk: iki yol da ayni toplamlari vermeli.
    ref = [float(d.sum()) for d in diziler]
    with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
        a = list(ex.map(dizi_ile, diziler))
        b = list(ex.map(uret_ile, [(t, boyut) for t in tohumlar]))
    print("dogruluk (arg):", a == ref, " (uret):", b == ref)

    with open(CIKTI, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["deney", "parametre", "tekrar", "sure_s"])
        for deney, parametre, sure in satirlar:
            w.writerow([deney, parametre, TEKRAR, f"{sure:.6f}"])
    print("CSV:", CIKTI)
```

Programın çıktısı:

```term
$ python -I b53_pool.py
kurulum      8 surec          0.5008 s
seri         100000           0.0082 s
chunksize    1               42.9431 s
chunksize    10               1.8623 s
chunksize    100              0.1958 s
chunksize    1000             0.0400 s
chunksize    10000            0.0244 s
chunksize    3125             0.0258 s
agir_seri    200x200000       2.3397 s
agir_surec   200x200000       0.4066 s
arg_dizi     50x8MB           0.3053 s
surec_uret   50 tohum         0.0500 s
dogruluk (arg): True  (uret): True
CSV: b53_pool.csv
```

Sonuçların ilk okuması şaşırtıcı olabilir: 100000 hafif iş için `chunksize = 1` ile 43 saniye sürdü, oysa seri hesap 0,008 saniyedir. Nedeni, her işin süreç sınırını geçip sıraya girmesi, bir kez pickle edilmesi ve geri dönmesidir; iş ne kadar hafifse, bu yük hesabın kendisinden kat kat pahalıdır. `chunksize` 10000'e çıkınca süre 0,024 saniyeye indi, yani hâlâ seri hesabın üç katı. Bu, hafif işte süreç havuzunun doğru araç olmadığını gösterir.

İş büyüdüğünde tablo değişiyor. Her biri 200000 döngü olan 200 iş seri olarak 2,34 saniye sürdü; sekiz süreçle 0,41 saniyeye indi, yani 5,75 kat. Bu, GIL'in CPU-bağlı işte engellediği paralelliğin süreçlerle geri kazanıldığını gösterir.

Serileştirme deneyi, pahalı taşımanın etkisini gösterir. 50 tane 8 MB'lık diziyi argüman olarak göndermek 0,305 saniye sürdü; aynı diziyi her süreç kendi tohumundan üretince 0,050 saniye sürdü (6,1 kat). Sonuçlar iki yolda da aynı (`dogruluk ... True`). Ders açık: süreçlere büyük veri göndermek yerine, mümkünse veriyi süreç içinde üret ya da paylaşılan bellek kullan (Bölüm 26'daki paylaşılan bellek).

Bu deneyde `chunksize = 3125` olan varsayılan değer (Pool.map formülü, Kod Okuma'da göreceğiz) 0,026 saniye verdi; yani yüz binlik iş için bu formül makul bir seçimdir. Ama formülün her iş boyutu için optimal olduğunu söylemiyor; yalnızca çok küçük parçalardan kaçınmayı sağlıyor.

Son olarak NumPy'nin iş parçacığı sayısını ölçelim. `b53_blas.py`, 2048×2048 bir `float64` matris çarpımını her iş parçacığı sayısı için ayrı bir süreçte çalıştırır. `OPENBLAS_NUM_THREADS` ortam değişkeni, kütüphane yüklenmeden önce ayarlanmalıdır; bu yüzden her ölçüm alt süreçte yapılır.

```python
# -*- coding: utf-8 -*-
"""b53_blas.py - NumPy matmul: OpenBLAS is parcacigi sayisina bagli.

Calistirma: python -I b53_blas.py
Her thread sayisi icin ayri bir surec acilir; OPENBLAS_NUM_THREADS
ortam degiskeni, kutuphane yuklenmeden once ayarlanmalidir.
Cikti: engine\\veri\\b53_blas.csv (p, medyan_s, gflops, hizlanma)
"""
import csv
import os
import statistics
import subprocess
import sys

N = 2048
TEKRAR = 5

def cocuk():
    """Alt surec: matmul'i olcer, sonucun ozetini yazar."""
    import time
    import numpy as np
    rng = np.random.default_rng(53)
    a = rng.standard_normal((N, N))
    b = rng.standard_normal((N, N))
    c = a @ b                              # isinma
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        c = a @ b
        zs.append(time.perf_counter() - t0)
    print(statistics.median(zs), f"{float(np.abs(c).sum()):.12e}")
```

```python
def ana():
    rows = []
    for p in (1, 2, 4, 8, 16):
        env = dict(os.environ, OPENBLAS_NUM_THREADS=str(p))
        out = subprocess.run(
            [sys.executable, "-I", __file__, "--cocuk"],
                             env=env, capture_output=True, text=True,
                             check=True).stdout.split()
        t, ozet = float(out[0]), out[1]
        rows.append((p, t, ozet))
        print(f"p={p:2d} medyan={t:.4f} s  "
              f"gflops={2*N**3/t/1e9:7.1f}  ozet={ozet}")
    t1 = rows[0][1]
    with open("b53_blas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["p", "medyan_s", "gflops", "hizlanma", "ozet"])
        for p, t, ozet in rows:
            w.writerow([p, f"{t:.6f}", f"{2*N**3/t/1e9:.2f}",
                        f"{t1/t:.3f}", ozet])
    print("CSV: b53_blas.csv")

if __name__ == "__main__":
    if "--cocuk" in sys.argv:
        cocuk()
    else:
        ana()
```

Çıktı:

```term
$ python -I b53_blas.py
p= 1 medyan=0.3192 s  gflops=   53.8  ozet=1.514080575280e+08
p= 2 medyan=0.1667 s  gflops=  103.0  ozet=1.514080575280e+08
p= 4 medyan=0.0909 s  gflops=  188.9  ozet=1.514080575280e+08
p= 8 medyan=0.0717 s  gflops=  239.5  ozet=1.514080575280e+08
p=16 medyan=0.0617 s  gflops=  278.5  ozet=1.514080575280e+08
CSV: b53_blas.csv
```

Matris çarpımı yaklaşık 1,7·10^10 kayan nokta işlemi (2n³) yapar. Tek iş parçacığında 53,8 GFLOPS, on altı iş parçacığında 278,5 GFLOPS elde ettik; hızlanma 5,17 kat. Dikkat et: sekiz çekirdekte 239,5 GFLOPS, on altıda 278,5; yani SMT'nin ek iş parçacıkları sekiz fiziksel çekirdekten sonra kazancı sınırlı biçimde artırıyor. Tüm çalıştırmalarda sonuç özeti (`ozet`) aynı kaldı; iş parçacığı sayısı değişse de matris çarpımının sonucu değişmedi, ama toplamların birleşme sırası farklı olabilir; bu, 53.10'un konusudur.

Bu sonuçtan çıkan pratik ders şudur: NumPy kodunda kendi döngülerini yazmadığın sürece paralellik zaten bir ölçüde var. Ama kendi döngülerini (ör. Python `for` döngüsü içinde küçük matris işleri) yazıyorsan, BLAS'ın iş parçacığı havuzunu bir kez açıp her işi onunla yapmak ve gereksiz `OPENBLAS_NUM_THREADS` artışından kaçınmak gerekir. Aynı makinede birden çok Python süreci (ör. havuz) BLAS'ı da kendi iş parçacıklarıyla çalıştırırsa aşırı abonelik (oversubscription) oluşur; bu tuzağı 53.9'da anlatıyoruz.

::: not
`asyncio` G/Ç-bağlı işlerde (ağ, dosya, sensör bekleme) çok etkilidir; Bölüm 31.8'de olay döngüsü olarak gördük. Ama CPU-bağlı bir işi `asyncio` görevlerine koymak tek bir iş parçacığında çalışır ve hızlandırmaz: olay döngüsü tek bir işi aynı anda yürütür. CPU-bağlı işte doğru araç süreç havuzu ya da C kütüphanesidir.
:::
## 53.9 Paralel performans tuzakları

Şimdiye kadar hesabı ölçtük ve hesap birimlerinin ölçeklenmesini gördük. Gerçek programlarda ise hesap çoğu zaman bellekten beklemekle geçer. Bu bölümde beş tuzağı sırayla ele alıyoruz: bellek bant genişliği, aritmetik yoğunluk (roofline), önbellek çekişmesi (false sharing), kilit çekişmesi ve aşırı abonelik. Son ikisi, dengesiz iş ve bariyer maliyetleriyle birlikte paralel performansı sınırlayan başlıca nedenlerdir.

### Bellek bant genişliği: çekirdekler aynı kapıdan geçer

Her çekirdek belleğe ulaşmak için aynı bellek denetleyicisini ve aynı DRAM kanallarını kullanır. Çekirdek sayısını artırmak hesabı çoğaltır ama bellek yolunu çoğaltmaz. Bunu ölçmek için STREAM benzeri bir "triad" kullandık: `a[i] = b[i] + q * c[i]`. Her eleman için iki okuma ve bir yazma yapılır; STREAM sayımına göre 24 bayt. Dizilerin her biri 268 MB'tır, yani 16 MB'lık L3 önbelleğe sığmaz; hesap bellekte yapılır.

`b53_bant.c`, p = 1'den 16'ya kadar her iş parçacığı sayısını beş kez çalıştırır ve medyanı alır. İlk dokunuş (first touch) için diziler paralel doldurulur; böylece sayfalar iş parçacıklarının kullandığı yerde eşlenir (Bölüm 25'teki sayfa eşleme anlayışı).

```c
/* b53_bant.c - STREAM benzeri triad: bellek bant genisligi olcegi.
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_bant.c -o bant
 * Kullanim: ./bant
 * Triad: a[i] = b[i] + q * c[i]. STREAM sayimi: element basina
 * 24 bayt (2 okuma + 1 yazma, 8 bayt double). Gercekte yazma
 * oncesi satir okunduguna gore trafik daha fazladir (write-allocate).
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

#define N (1UL << 25)    /* 2^25 double = 256 MB */
#define TEKRAR 5

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}
```

Triad döngüsünün kendisi, ölçüm bölümünde yer alır:

```c
int main(void) {
    double *a = malloc(N * sizeof *a);
    double *b = malloc(N * sizeof *b);
    double *c = malloc(N * sizeof *c);
    if (!a || !b || !c) {
        fputs("bellek yetersiz\n", stderr);
        return 1;
    }
    const double q = 3.0;
    /* Ilk dokunus: sayfalar 16 is parcacigi tarafindan eslenir. */
    #pragma omp parallel for num_threads(16) schedule(static)
    for (long i = 0; i < (long)N; i++) {
        a[i] = 0.0;
        b[i] = 1.0;
        c[i] = 2.0;
    }
    printf("# N=%lu (her dizi %.0f MB), tekrar=%d\n",
           N, N * 8.0 / 1e6, TEKRAR);
    printf("p,medyan_gbs,min_gbs,max_gbs\n");
    for (int p = 1; p <= 16; p++) {
        double gb[TEKRAR];
        for (int r = 0; r < TEKRAR; r++) {
            double t0 = omp_get_wtime();
            #pragma omp parallel for num_threads(p) schedule(static)
            for (long i = 0; i < (long)N; i++)
                a[i] = b[i] + q * c[i];
            double dt = omp_get_wtime() - t0;
            gb[r] = 24.0 * (double)N / dt / 1e9;
        }
        qsort(gb, TEKRAR, sizeof gb[0], karsilastir);
        printf("%d,%.2f,%.2f,%.2f\n", p, gb[TEKRAR / 2], gb[0],
               gb[TEKRAR - 1]);
    }
    /* Dogrulama: a[i] = 1 + 3*2 = 7 olmali. */
    printf("dogrulama: a[0]=%.1f a[N-1]=%.1f\n", a[0], a[N - 1]);
    free(a); free(b); free(c);
    return 0;
}
```

Programın çıktısı:

```term
$ ./bant
# N=33554432 (her dizi 268 MB), tekrar=5
p,medyan_gbs,min_gbs,max_gbs
1,18.70,17.33,19.10
2,26.63,25.83,27.34
3,29.52,28.86,29.81
4,29.16,28.31,30.02
5,30.40,30.09,31.43
6,31.19,30.73,31.41
7,31.02,30.75,31.91
8,31.41,31.38,32.39
9,31.41,31.10,31.93
10,31.18,28.86,31.69
11,30.01,29.57,30.97
12,31.78,30.55,32.16
13,31.67,31.20,31.94
14,32.02,31.79,32.25
15,31.43,31.31,31.98
16,31.72,31.41,31.99
dogrulama: a[0]=7.0 a[N-1]=7.0
```

Tek iş parçacığı 18,7 GB/s bant genişliğine ulaştı. İki iş parçacığı 26,6 GB/s'e çıktı, altı iş parçacığında 31 GB/s civarına geldi ve bundan sonra düz bir tavan gördük: p = 14'te 32,0 GB/s ölçtük, p = 11'de ise 30,0 GB/s ile geçici bir düşüş oldu. Şekil 53.8 bu doyumu gösteriyor. Bu tavan makinenin bellek sisteminin pratik sınırıdır; teorik bant genişliğini bu makinenin bellek spesifikasyonundan doğrulamadık, bu yüzden değeri ölçülmüş tavan olarak okumalısın.

![Şekil 53.8: Triad bant genişliği iş parçacığı sayısına göre. Altı iş parçacığından sonra eğri 31–32 GB/s civarında doyuyor; gölge min–maks aralığıdır.](gorseller/b53_bant_doyma.png)

Bu sonuç, paralel tasarımda sık yapılan bir hatayı gösterir: bellek-bağlı bir işe çekirdek eklemek, belleği bekleyen iş parçacıklarının sayısını artırır, ama tavanı yükseltmez. Doyumdan sonra daha fazla iş parçacığı yalnızca çekişme ve bağlam değişimi maliyeti ekler. Ayrıca STREAM sayımı yazma öncesi okumayı (write-allocate) hesaba katmaz; gerçek trafik 24 bayttan fazladır, dolayısıyla gerçek bant genişliği ölçülen değerden biraz yüksektir.

### Aritmetik yoğunluk ve roofline modeli

Bir çekirdeğin performansı iki tavana bağlıdır: bellek bant genişliğinin çarpı aritmetik yoğunluğu ve işlemcinin tepe hesap hızı. **Aritmetik yoğunluk** (arithmetic intensity), bayt başına kaç kayan nokta işlem yapıldığıdır (flop/bayt). Samuel Williams ve arkadaşlarının 2009'da tanıttığı **roofline** modeli bu iki tavanı tek bir grafikte birleştirir (genel bilgi):

`P = min(tepe hesap, bant genişliği × I)`

Burada `I` aritmetik yoğunluktur. Düşük `I`'da grafik bellek eğrisini izler (bellek-bağlı); yüksek `I`'da yatay tepe hesap çizgisine ulaşır (hesap-bağlı). İki eğrinin kesiştiği nokta, "köşe" (ridge point) olarak adlandırılır: `tepe / bant`.

Bizim ölçümlerimizde tepe hesap, matris çarpımının p = 16'daki 278,5 GFLOPS değeri; bant ise triad'ın doyum tavanı 32,0 GB/s. Köşe `278,5 / 32,0 ≈ 8,7 flop/bayt` çıkıyor. Şekil 53.9'da iki kernel'i işaretledik:

- **Triad**: her eleman için 2 flop ve 24 bayt, yani `I = 2/24 ≈ 0,083`. Model tavanı `0,083 × 32 ≈ 2,7 GFLOPS`: bellek-bağlı, hesap birimleri boşta.
- **Matris çarpımı** (2048×2048): `I ≈ 2n³ / (3n²·8) ≈ 171` flop/bayt. Köşenin çok sağında, hesap-bağlı; ölçülen 278,5 GFLOPS tepe hesap tavanına dayanıyor.

![Şekil 53.9: Roofline modeli. Eğik çizgi bellek tavanı, yatay çizgi hesap tavanı; kesişim köşedir. Triad bellek-bağlı, matris çarpımı hesap-bağlı.](gorseller/b53_roofline.png)

Roofline'ın pratik kullanımı şudur: bir kernel'in performansını artırmadan önce hangi tavana bağlı olduğunu bilmelisin. Bellek-bağlı bir kernel'e daha hızlı bir hesap birimi koymak işe yaramaz; onun yoğunluğunu artırmak (veriyi yeniden kullanmak, blok bölmek) gerekir. Bölüm 25.7'deki blok matris çarpımı tam da bu yoğunluğu artırma fikrine dayanır.

### Önbellek çekişmesi (false sharing)

İki iş parçacığı farklı değişkenleri yazsa bile, o değişkenler aynı önbellek satırındaysa (x86'da 64 bayt) satır çekirdekler arasında gidip gelir. Bunu Bölüm 27.14'te ölçtük ve sahte paylaşımın yazma yoğun döngülerde ciddi bir yavaşlamaya yol açtığını gördük. Burada yeni bir ölçüm eklemiyoruz; kuralı tekrar etmek yeterli: paralel iş parçacıklarının yazdığı değişkenleri birbirinden en az bir önbellek satırı kadar uzak tut (`alignas(64)` ya da dolgu).

### Kilit çekişmesi

Bir kilit, iş parçacıkları arasındaki sıra için gereklidir, ama aynı kilide sık sık giren çok sayıda iş parçacığı, kilidi beklemekle zaman harcar. Bu, paralelliğin en sık görülen sahte kazancıdır: iş parçacığı sayısı artar, ama hepsi aynı kapıda bekler. Örnek 3'te histogramı üç yöntemle yazdığımızda bu olgu açıkça görülecek: her elemanı ortak bir sayaca atomik olarak yazmak, sıralı sürümden bile yavaş çıktı.

### Aşırı abonelik (oversubscription)

Çekirdeklerden fazla iş parçacığı çalıştırmak ayrı bir sorundur. İşletim sistemi bu iş parçacıklarını zaman diliminde değiştirmek (bağlam değişimi) zorunda kalır; Bölüm 26.9'da bu maliyetin ne olduğunu gördük. Aşırı abonelik özellikle iki paralel kütüphane birlikte çalıştığında ortaya çıkar: bir OpenMP havuzu 8 iş parçacığı açar, BLAS da kendi 16 iş parçacığını açarsa sistemde 128'e yakın hazır iş parçacığı olabilir (genel bilgi). Bu yüzden kütüphanelerin iş parçacığı sayısını ayrı ayrı sınırlamak (`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`) iyi bir alışkanlıktır. Bu deneyi bu bölümde ölçmedik; kuralı ve nedenini bilmek yeterlidir.

### Yük dengesizliği ve bariyerler

53.6'da dengesiz işin statik bölmeyi nasıl bozduğunu gördük. Benzer biçimde, her aşamanın sonunda tüm iş parçacıklarının beklediği **bariyer** (barrier) noktaları da toplam süreyi uzatır: en yavaş iş parçacığı bitmeden hiçbiri devam edemez. Bariyerlerin maliyeti, iş–açıklık modelinde (53.4) açıklığa eklenen bir terimdir: her bariyer, kritik yoldaki en yavaş işi zorunlu kılar.

## 53.10 Paralel doğruluk: birleşme sırası ve Kahan toplamı

Paralel bir programın doğru olması için iki şeye bakarız: yarış olmamalı (Bölüm 27) ve sonuç sıralı referansla uyuşmalı. İkincisi beklediğinden zordur, çünkü **kayan nokta toplamasının birleşme sırası değiştirir.** Bölüm 1.5'te IEEE-754 sayılarının yuvarlamalı olduğunu gördük. Aynı sayılar farklı sırayla toplanınca, ara yuvarlamalar farklı olduğu için sonuç da farklı olabilir. Paralel toplamada sıra, iş parçacığı sayısına bağlı değişir; yani sonuç p'ye bağlıdır.

Bunu ölçmek için `toplam.c` programı 10 milyon `float` değeri (xorshift, tohum 53) hem düz hem de Kahan telafili toplamla toplar. Her toplamı p parçaya böler, parça toplamlarını sırayla birleştirir. Bu, p iş parçacığının aynı işi yaptığı durumun matematiksel karşılığıdır.

Kahan toplamı, küçük katkıların kaybını bir telafi değişkeninde tutar (genel bilgi, W. Kahan). Her adımda `y = x - c`, `t = s + y`, `c = (t - s) - y` hesaplanır; bu kayıp bitleri bir sonraki adıma taşır.

```c
/* b53_toplam.c - kayan nokta toplamasi: parca sayisi, birlesme sirasi
 * ve Kahan (telafili) toplam.
 * Derleme: gcc -O2 -std=c11 b53_toplam.c -o toplam
 * (-ffast-math KULLANMA: Kahan'i derleyici silerdi.)
 * Veri: xorshift32 tohum 53; N = 10^7 float, degerler [0,1).
 * Parcalar ayri ayri toplanir, sonra SIRAYLA birlestirilir: bu,
 * p is parcaciginin ayni islemi matematiksel olarak yapmasidir.
 */
#include <stdio.h>
#include <stdlib.h>

#define N 10000000

static float veri[N];
static unsigned int xs = 53u;

static float rastgele(void) {
    xs ^= xs << 13;
    xs ^= xs >> 17;
    xs ^= xs << 5;
    return (float)(xs / 4294967296.0);
}

/* Duz float toplam. */
static float duz(const float *x, long n) {
    float s = 0.0f;
    for (long i = 0; i < n; i++) s += x[i];
    return s;
}
```

Ana fonksiyon, referansı `long double` ile hesaplar ve p değerlerinde iki toplamı karşılaştırır:

```c
/* Kahan: c, kaybedilen dusuk bitleri geri besler. */
static float kahan(const float *x, long n) {
    float s = 0.0f, c = 0.0f;
    for (long i = 0; i < n; i++) {
        float y = x[i] - c;
        float t = s + y;
        c = (t - s) - y;
        s = t;
    }
    return s;
}

int main(void) {
    for (long i = 0; i < N; i++) veri[i] = rastgele();
    /* Referans: long double ile seri toplam (yakl. dogru). */
    long double acc = 0.0L;
    for (long i = 0; i < N; i++) acc += veri[i];
    double ref = (double)acc;
    printf("referans (long double) = %.3f\n", ref);
    printf("p,duz_float,hata_duz,kahan_parca,hata_kahan\n");
    int pler[] = {1, 2, 3, 4, 6, 8, 12, 16};
    for (int k = 0; k < 8; k++) {
        int p = pler[k];
        float dt = 0.0f, kt = 0.0f;
        long pay = N / p;
        for (int j = 0; j < p; j++) {
            long lo = j * pay;
            long hi = (j == p - 1) ? N : lo + pay;
            /* Parca toplamlari sirayla birlestirilir. */
            dt += duz(veri + lo, hi - lo);
            kt += kahan(veri + lo, hi - lo);
        }
        printf("%d,%.3f,%.3e,%.3f,%.3e\n", p, dt,
               (dt - ref) / ref, kt, (kt - ref) / ref);
    }
    return 0;
}
```

Çıktı:

```term
$ ./toplam
referans (long double) = 5000005.233
p,duz_float,hata_duz,kahan_parca,hata_kahan
1,5000258.000,5.055e-05,5000005.000,-4.664e-08
2,5000176.000,3.415e-05,5000005.000,-4.664e-08
3,4999961.500,-8.747e-06,5000005.000,-4.664e-08
4,4999968.000,-7.447e-06,5000005.000,-4.664e-08
6,5000003.000,-4.466e-07,5000005.500,5.336e-08
8,5000043.000,7.553e-06,5000005.000,-4.664e-08
12,4999983.500,-4.347e-06,5000005.000,-4.664e-08
16,4999999.000,-1.247e-06,5000005.500,5.336e-08
```

Düz `float` toplam, p = 1'de referansa göre `5,1·10^-5` bağıl hata yaptı; p = 2'de hata değişti, p = 3'te işaret değiştirdi. Sonuç, parça sayısına göre 4 999 961 ile 5 000 258 arasında dalgalandı. Yani aynı veri ve aynı algoritma, farklı iş parçacığı sayısında farklı bir sayı verdi. Kahan toplamı ise her p için referansa göre `5·10^-8` mertebesinde kaldı. Kahan'ın bu kadar tutarlı olmasının nedeni, her parçada hatayı küçük tutmasıdır; ama telafi de bir kayan nokta işlemi olduğu için, Kahan'ın bile bütünüyle "tam" olmadığını unutma.

Bu deneyin mühendislik sonucu üç maddedir. Birincisi, paralel sonuçları sıralı referansla **tam eşitlik** yerine **tolerans** ile karşılaştır; ama toleransı verinin ölçeğine göre seç (buradaki göreli hata ile mutlak hata farklıdır). İkincisi, mümkünse toplamayı deterministik bir sırada yap (sabit parça ve sabit birleşim sırası), böylece aynı p için her çalıştırma aynı sonucu verir. Üçüncüsü, kritik sayısal hesaplarda (ör. sensör füzyonu ya da kalman filtresi) toplama hatasını Kahan ya da daha yüksek hassasiyetle azalt.

Bu bölümdeki diğer paralel doğruluk kontrolleri de aynı ilkeye dayanır: Örnek 4'teki birleştirme sıralamasında paralel sonuç, seri sonuçla bayt bayt karşılaştırılır; pthreads ile OpenMP sürümlerinin sonucu XOR ile birleştiği için tam eşitlik beklenir. Tam sayılarda (ve XOR'da) birleşme sırası sonucu değiştirmez; kayan noktada değiştirir.

## 53.11 GPU'ya giriş: SIMT ve bellek hiyerarşisi

Bu bölümde GPU üzerinde kod çalıştırmadık; ayrıntısı Bölüm 76'da, CUDA temelleriyle birlikte gelecek. Burada, paralel düşünceyi bir adım ileri taşıyan mimari farkı kavramsal olarak kuruyoruz. Bu makinede `nvidia-smi` çıktısı şöyleydi:

```term
$ nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
name, memory.total [MiB], driver_version
NVIDIA GeForce RTX 3060 Laptop GPU, 6144 MiB, 616.64
```

Bu bilgi, makinede bir NVIDIA GPU'nun sürücüyle birlikte çalıştığını doğrular; GPU'nun 6 GB belleği ve sürücü sürümü, hangi boyutta veriyi tek seferde tutabileceğini gösterir. Ama GPU'nun gerçek hızını ölçmeden bir şey söyleyemeyiz.

CPU ile GPU arasındaki temel fark, hangi sorunu optimize ettiklerindedir. CPU birkaç güçlü çekirdekten oluşur; her çekirdeğin büyük önbellekleri, dal tahmini ve sıra dışı yürütmesi vardır, yani tek bir iş parçacığının gecikmesini düşürmeye odaklanır. GPU ise yüzlerce hatta binlerce daha basit hesap birimini bir arada tutar ve gecikmeyi, çok sayıda hafif iş parçacığını birbirinin yerine geçirerek gizler: bir grup bellek beklerken diğer grup hesap yapar.

NVIDIA bu modeli **SIMT** (single instruction, multiple threads) diye adlandırır (genel bilgi). Temel birim **warp**'tır: genel olarak 32 iş parçacığı aynı komutu aynı anda yürütür (genel bilgi). Bir warp içinde iş parçacıkları farklı dallara giderse, her dal sırayla yürütülür ve diğerleri beklenir (dal ayrışması). Bu, SIMD'nin (Bölüm 24.8) çok iş parçacıklı hâlidir: aynı komut, çok veri, ama veri başına bir iş parçacığı görünümü ile.

Bellek hiyerarşisi de farklıdır. GPU'da her iş parçacığının yazmaçları, bir blok içinde paylaşılan (shared) bellek, en sonda da büyük ama yavaş global bellek vardır. Paylaşılan bellek, CPU'daki önbellek gibi çalışır ama programcı tarafından yönetilir. Bölüm 25'te önbellek satırlarını ve TLB'yi gördüğümüz düşünce burada da geçerlidir: veriyi tekrar kullanmadığın sürece global belleğin bant genişliği darboğaz olur.

![Şekil 53.10: CPU ve GPU mimarisinin kavramsal karşılaştırması. Solda az sayıda büyük çekirdek ve büyük önbellekler, sağda çok sayıda SM ve yüksek bant genişlikli global bellek.](gorseller/b53_cpu_gpu.png)

GPU'ya ne zaman değer? Üç koşul aranır. Birincisi, iş veri paralelliğine (map, stencil, büyük matris işleri) uygun olmalıdır. İkincisi, aritmetik yoğunluk yüksek olmalıdır (53.9'daki roofline): bayt başına çok işlem yapılmıyorsa GPU'nun bant avantajı kazanç vermez. Üçüncüsü, veri transferi maliyeti hesaba katılmalıdır: GPU ile CPU arasındaki veri aktarımı (PCIe üzerinden) çoğu zaman hesabın kendisinden pahalı olabilir. Bir hesabı GPU'ya taşıyıp sonuçları her adımda CPU'ya geri kopyalarsan, kazanç transfer maliyetinde kaybolur.

Bu üç koşulun ölçülmesi gerekir; bu bölümde bunu yaptık: CPU bant ve hesap tavanlarını ölçtük (53.9). GPU tavanlarını bu makinede ölçmedik; bu yüzden GPU hakkında verdiğimiz sayılar kavramsaldır ve genel bilgidir.

## 53.12 Dağıtık paralellik ve gerçek zamanlı bağlam

Tek bir makinenin içindeki paralellik ortak belleği paylaşır. Birden çok makineye yayılan işte paylaşım yoktur; veri mesajla taşınır. Bu, **mesaj geçirme** (message passing) modelinin temelidir. En yaygın standart **MPI**'dir (Message Passing Interface, genel bilgi): her süreç kendi belleğine sahiptir ve `Send`/`Recv` benzeri çağrılarla veri alışverişi yapar. Ağ gecikmesi ve bant genişliği, tek makinedeki bellek erişiminden kat kat yavaş olduğu için, mesaj sayısını ve boyutunu azaltmak burada ana tasarım hedefidir.

Bu modelde yarış koşulunun yerini başka bir hata alır: kilit yerine bekleme döngüleri, ölü kilit yerine karşılıklı mesaj bekleme (deadlock). Bölüm 41'de dağıtık sistem tasarımını gördük; Bölüm 19.12'de ise MapReduce fikrine değindik: büyük veriyi parçalara bölüp her parçayı bağımsız işlemek ve sonuçları birleştirmek, dağıtık paralelliğin en sade örneğidir (genel bilgi).

Gömülü ve gerçek zamanlı bağlamda iki şey ekstra önemlidir. Birincisi **deterministik zamanlama**: çok çekirdekli bir MCU'da (ör. çok çekirdekli bir MCU ya da bir uçuş bilgisayarı) bir görevin en kötü durumdaki yürütme süresi (WCET) kanıtlanabilmelidir; paylaşılan önbellek ve bellek çekişmesi bu süreyi belirsizleştirir (genel bilgi). İkincisi **doğrulama**: paralel bir yazılımın her zamanlamada doğru çalıştığını testle tam olarak kanıtlamak zordur. Savunma sanayiinde bu yüzden paralellik, sıralı bir referans, yarış denetleyicileri (Bölüm 27'deki ThreadSanitizer gibi araçlar) ve ölçülmüş zamanlama sınırlarıyla birlikte ele alınır. Bu, Bölüm 78'de ele alınacak doğrulama ve sertifikasyon konusunun paralel tarafıdır (genel bilgi).

Bu bölümün ana fikri böylece bir zincire bağlanıyor: bir işi bölebilirsin, bölme yapısı iş–açıklık modeliyle sınırlanır, ölçüm bu sınırı doğrular, bellek ve senkronizasyon tavanlarını ancak ölçerek bulursun ve sonuç doğruluğunu paralel sırada da kanıtlamak zorundasın.
## Çözümlü Örnekler

Dört örnek, zorluk sırasıyla ★, ★★, ★★, ★★★ olarak artar. Her örnek Bölüm 5'teki altı adımı izler. Doğrulama adımında elle iz sürme tablosu bulunur; kendi sonucunu bir tabloya dökmeden doğru kabul etme.

### Örnek 1 (★): Seri kesri %10 olan işte 8 ve 64 çekirdek

**Problem.** Bir işin %10'u paralelleştirilemiyor. 8 çekirdek ve 64 çekirdek için en fazla ne kadar hızlanma beklenir? Bu tahmini ölçümle karşılaştır.

**Adım 1 — Anla.** Girdi: seri kesir `s = 0,10` ve çekirdek sayısı `p`. Çıktı: hızlanma `S(p)`. Kenar durumu: `p = 1` için `S = 1` olmalı. `p`'nin sonsuza gitmesi halinde `S` ne olur? Bu, yasanın sınırıdır.

**Adım 2 — Örnekle.** `p = 2`, `p = 8` ve `p = 64` ile ilk bakış: `S(2)` yaklaşık 1,8 çıkmalı, `S(8)` 4,7 civarı, `S(64)` ise 9'a yakın olmalı. Sezgi, `s = 0,10` olduğu için tavanın 10 olduğunu söylüyor.

**Adım 3 — Kaba çöz.** Doğrudan formül: `S(p) = 1 / (s + (1 - s)/p)`. Her p için paydayı hesaplayıp tersini almak yeter. Bu, en kaba ama güvenilir yöntemdir.

**Adım 4 — Örüntü.** Payda `0,10 + 0,90/p` biçimindedir. `p` büyüdükçe `0,90/p` sıfıra yaklaşır ve payda `0,10`'a yaklaşır. Bu örüntü tavanın `1/s` olduğunu gösterir. Kazanç, `p`'nin ikiye katlanmasıyla azalan bir getiri verir.

**Adım 5 — İyileştir.** Bu formülü tek satırda yazmak yeterli; ama seri kesrin *ölçümünü* tahmin yerine yap. Ölçülen hızlanmadan Karp–Flatt ile `e(p)` hesapla. Bu adım, modelin varsayımlarının gerçek makinede tutup tutmadığını gösterir.

**Adım 6 — Doğrula.** Elle iz tablosu (paydayı ve tersini hesapla):

| p | Payda `0,10 + 0,90/p` | Teorik `S(p)` | Ölçülen `S(p)` (Bölüm 53.3) |
|---|---|---|---|
| 1 | 0,10 + 0,900 = 1,000 | 1,000 | 1,000 |
| 2 | 0,10 + 0,450 = 0,550 | 1,818 | 1,807 |
| 4 | 0,10 + 0,225 = 0,325 | 3,077 | 2,937 |
| 8 | 0,10 + 0,1125 = 0,2125 | 4,706 | 4,248 |
| 16 | 0,10 + 0,05625 = 0,15625 | 6,400 | 4,962 |
| 64 | 0,10 + 0,0140625 = 0,1140625 | 8,767 | ölçmedik |

Teorik değerler p = 8 için 4,71 ve p = 64 için 8,77 çıktı. Bu, 8 çekirdekte yaklaşık 4,7 kat, 64 çekirdekte ise 8,8 kat bir üst sınır demektir. Ölçülen p = 8 değeri 4,25 idi, yani teorinin yaklaşık %90'ı; p = 16'da fark büyüdü (4,96 / 6,40). Karp–Flatt ile p = 8 için `e ≈ 0,126` bulunur; yani etkin seri kesir tasarlanan `0,10`'dan yaklaşık 0,026 büyük. Bu farkın bir kısmı SMT ve paralel döngü maliyetinden gelir (Bölüm 53.3).

**Bunu AI'sız yazabilir misin?** Seri kesri `0,25` olan bir işin 4 ve 32 çekirdekte hızlanmasını hesapla. Sonra ölçümle doğrulayacağın bir deney tasarla: iki ayrı bölümü olan ve ikinci bölümünün süresini bilerek ayarladığın bir programla `S(p)` ölç ve Karp–Flatt ile `e(p)`'yi çıkar.

### Örnek 2 (★★): 8 elemanlık dizide Blelloch önek toplamı

**Problem.** `[3, 1, 7, 0, 4, 1, 6, 3]` dizisinin dışlayıcı önek toplamını (exclusive scan) Blelloch yöntemiyle hesapla. Her süper adımın sonucunu göster ve paralel adım sayısını ile toplama sayısını doğrula.

**Adım 1 — Anla.** Girdi `a` (uzunluğu `n = 8`), çıktı `c` öyle ki `c[i] = a[0] + ... + a[i-1]` ve `c[0] = 0`. Kenar durumu: `n = 1` (çıktı `[0]`), ve `n` iki kuvveti değilse Blelloch'un tanımı değişir; biz `n` iki kuvveti olan durumla çalışıyoruz.

**Adım 2 — Örnekle.** Küçük bir örnek: `[a, b]` için çıktı `[0, a]`. Burada yukarı süpürme sağ konuma `a + b` yazar, kökü (sağ konumu) sıfırlarsın; aşağı süpürme sol konuma kökün değerini (0), sağ konuma ise eski sol değeri (`a`) yazar. Bu iki adımı 8 elemana genelleştireceğiz.

**Adım 3 — Kaba çöz.** Sıralı yöntem her elemanı sırayla toplar: `n - 1` toplama. Bu doğru ama sıralıdır: açıklığı `n - 1`. Paralel yol, yukarı süpürme (ağaç indirgemesi) ve aşağı süpürme (dağıtma) olmak üzere iki kez `log2 n` seviye yapar.

**Adım 4 — Örüntü.** Yukarı süpürmede her seviye `d = 1, 2, 4` için `x[k + 2d - 1] += x[k + d - 1]` yapılır (k, 2d'nin katları). Kök `x[n-1]` sıfırlanır. Aşağı süpürmede `d = 4, 2, 1` için sol çocuğa ebeveynin değeri kopyalanır, sağ çocuğa ise eski sol değer eklenir. Toplam toplama sayısı her iki süpürmede `n - 1` olduğundan `2(n - 1)`.

**Adım 5 — İyileştir.** Kodda her süper adımı bir liste olarak kaydederek izi görünür kıl. Kod tam olarak bu planı izler. Doğrulama için rastgele dizilerde sıralı referans ile karşılaştır.

**Adım 6 — Doğrula.** Elle iz tablosu (yukarı süpürmeden sonra aşağı süpürme; her satır bir süper adım):

| Adım | `d` | Dizinin durumu |
|---|---|---|
| Başlangıç | | `[3, 1, 7, 0, 4, 1, 6, 3]` |
| Yukarı | 1 | `[3, 4, 7, 7, 4, 5, 6, 9]` |
| Yukarı | 2 | `[3, 4, 7, 11, 4, 5, 6, 14]` |
| Yukarı | 4 | `[3, 4, 7, 11, 4, 5, 6, 25]` |
| Kök sıfırlanır | | `[3, 4, 7, 11, 4, 5, 6, 0]` |
| Aşağı | 4 | `[3, 4, 7, 0, 4, 5, 6, 11]` |
| Aşağı | 2 | `[3, 0, 7, 4, 4, 11, 6, 16]` |
| Aşağı | 1 | `[0, 3, 4, 11, 11, 15, 16, 22]` |

Son satır, sıralı referans olan `0, 3, 4, 11, 11, 15, 16, 22` ile birebir aynıdır. Elle iz tablosunda kök sıfırlandığını ve son satırda `x[7] = 22` olduğunu kontrol et: `3+1+7+0+4+1+6 = 22`. Bu, tarama tanımıyla uyumludur. Aşağıdaki program, aynı iz ve 2'den 1024'e kadar rastgele doğrulamayı yazdırır:

```python
# -*- coding: utf-8 -*-
"""b53_scan.py - Blelloch dislayici tarama (exclusive prefix sum).

Calistirma: python -I b53_scan.py
Her yukari/asagi super adimi, ayni seviyedeki bagimsiz toplamalardan
olusur; bunlar paralel calistirilabilir. Adim sayisi = 2 log2(n).
"""
import random
from itertools import accumulate

def blelloch(a):
    """Dislayici onek toplami. Doner: (sonuc, islem, izler)."""
    n = len(a)
    x = list(a)
    izler = []
    islem = 0
    # Yukari super (indirgeme): her seviyede 2d'lik bloklarin sonu.
    d = 1
    while d < n:
        for k in range(0, n, 2 * d):
            x[k + 2 * d - 1] += x[k + d - 1]
            islem += 1
        izler.append(("yukari", d, list(x)))
        d *= 2
    x[n - 1] = 0                       # kok sifirlanir
    # Asagi super (dagitma): toplamlar yeniden yayilir.
    d = n // 2
    while d >= 1:
        for k in range(0, n, 2 * d):
            t = x[k + d - 1]
            x[k + d - 1] = x[k + 2 * d - 1]
            x[k + 2 * d - 1] += t
            islem += 1
        izler.append(("asagi", d, list(x)))
        d //= 2
    return x, islem, izler
```

```python
def dogrula(n, tohum):
    """Rastgele dizilerde Blelloch'u seri referansla sinar."""
    rnd = random.Random(tohum)
    for _ in range(50):
        a = [rnd.randint(-100, 100) for _ in range(n)]
        ref = list(accumulate(a, initial=0))[:-1]
        sonuc, _, _ = blelloch(a)
        if sonuc != ref:
            return False
    return True

if __name__ == "__main__":
    a = [3, 1, 7, 0, 4, 1, 6, 3]
    sonuc, islem, izler = blelloch(a)
    print("girdi :", a)
    for tur, d, durum in izler:
        print(f"{tur:6s} d={d}  {durum}")
    print("cikti :", sonuc)
    print("sirali:", list(accumulate(a, initial=0))[:-1])
    print()
    print("n     toplama   2(n-1)  adim(2log2n)  dogru")
    for k in range(1, 11):
        n = 2 ** k
        arr = list(range(1, n + 1))
        _, islem, _ = blelloch(arr)
        adim = 2 * k
        print(f"{n:<5d} {islem:<9d} {2*(n-1):<7d} {adim:<13d}"
              f" {dogrula(n, 53)}")
```

Çıktı:

```term
$ python -I b53_scan.py
girdi : [3, 1, 7, 0, 4, 1, 6, 3]
yukari d=1  [3, 4, 7, 7, 4, 5, 6, 9]
yukari d=2  [3, 4, 7, 11, 4, 5, 6, 14]
yukari d=4  [3, 4, 7, 11, 4, 5, 6, 25]
asagi  d=4  [3, 4, 7, 0, 4, 5, 6, 11]
asagi  d=2  [3, 0, 7, 4, 4, 11, 6, 16]
asagi  d=1  [0, 3, 4, 11, 11, 15, 16, 22]
cikti : [0, 3, 4, 11, 11, 15, 16, 22]
sirali: [0, 3, 4, 11, 11, 15, 16, 22]

n     toplama   2(n-1)  adim(2log2n)  dogru
2     2         2       2             True
4     6         6       4             True
8     14        14      6             True
16    30        30      8             True
32    62        62      10            True
64    126       126     12            True
128   254       254     14            True
256   510       510     16            True
512   1022      1022    18            True
1024  2046      2046    20            True
```

Çıktıdaki tablo, her `n` için toplama sayısının `2(n - 1)` ile ve süper adım sayısının `2 log2 n` ile tam uyuştuğunu gösteriyor. Ayrıca her `n` için 50 rastgele dizinin tamamı sıralı referansla eşleşti. Bu, algoritmanın *doğru* olduğunun kanıtı değildir ama tanımın doğru uygulandığının güçlü bir kontrolüdür.

**Bunu AI'sız yazabilir misin?** Aynı algoritmayı `n = 4` için elle yap ve kökü sıfırlamadan önceki durumu yaz. Sonra kökü sıfırlamayı unutan bir sürümün çıktısının neden tamamen yanlış olduğunu açıkla.

### Örnek 3 (★★): Histogram: yarış, atomik ve yerel birleştirme

**Problem.** 20 milyon bayt değerini (0 ile 15 arasında, xorshift, tohum 53) 16 kovalı bir histograma sayan paralel bir program yaz. Üç sürümü karşılaştır: (a) yarışlı, (b) atomik, (c) yerel + birleştirme. Her sürümün hızını ve doğruluğunu ölç.

**Adım 1 — Anla.** Girdi: `veri[0..N-1]`, çıktı: `h[0..15]` öyle ki `h[k]` değerinin kaç kez görüldüğünü tutar. Doğruluk ölçütü: kova toplamı `N` olmalı ve her kova sıralı referansla eşleşmeli. Kenar durumu: aynı kovaya çok sayıda iş parçacığı yazarsa çekişme yüksektir.

**Adım 2 — Örnekle.** Küçük örnek: iki iş parçacığı, dizi `[5, 5]` (her iki değer aynı kovaya). Beklenen: `h[5] = 2`. Yarışlı sürümde iki iş parçacığı `h[5]`'i aynı anda okursa her ikisi de `0 + 1 = 1` yazar; sonuç `1` olur.

**Adım 3 — Kaba çöz.** Sıralı sürüm tek döngü: `h[veri[i]]++`. Paralel kaba sürüm: `#pragma omp parallel for` ile aynı döngüyü böl. Bu, yarış yaratır: `h[k]++` bir okuma-artırma-yazma dizisidir ve araya başka bir iş parçacığı girebilir.

**Adım 4 — Örüntü.** Yarış sadece aynı kovaya yazarken ortaya çıkar. Kova sayısı az (16) olduğu için çekişme çok yüksek olacak. Düzeltmenin iki yolu var: kovaya yazmayı atomik yapmak (paylaşımı sürdürür) ya da her iş parçacığına kendi histogramını verip sonunda birleştirmek (paylaşımı ortadan kaldırır).

**Adım 5 — İyileştir.** Üç sürüm yaz: `yaris` (kasıtlı yarış, sadece gösterim), `atomik` (`#pragma omp atomic`), `yerel` (her iş parçacığı kendi `my[]` dizisi; birleştirme `critical` içinde, bir kez). Sıralı referans da ölçülür.

**Adım 6 — Doğrula.** Elle iz tablosu (iki iş parçacığı, aynı kova `k`, değer `h[k] = 5`):

| Zaman | İş parçacığı A | İş parçacığı B | `h[k]` (paylaşılan) |
|---|---|---|---|
| t1 | `h[k]` oku: 5 | | 5 |
| t2 | | `h[k]` oku: 5 | 5 |
| t3 | `h[k] = 5 + 1` yaz | | 6 |
| t4 | | `h[k] = 5 + 1` yaz | 6 (kayıp!) |

İki artış yapıldı ama sonuç yalnızca bir artış kadar. Ölçülen sonuçla karşılaştır: aşağıdaki çıktıda yarışlı sürümün kova toplamı 20 000 000 olmalıydı, ama yaklaşık yarısı kaybolmuş.

```c
/* b53_histogram.c - histogram: yaris, atomic ve yerel + birlestirme.
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_histogram.c -o hist
 * Kullanim: ./hist <thread>      (ornek: ./hist 8)
 * Veri: xorshift32, tohum 53. Kova sayisi 16 (cok cekisme icin az).
 * Surum 1 (yaris) KASITLI olarak tanimsiz davranis icerir; yalnizca
 * kayip guncellemeyi gostermek icindir.
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 20000000L
#define KOVA 16
#define TEKRAR 3

static unsigned char veri[N];
static long h0[KOVA], h1[KOVA], h2[KOVA], h3[KOVA];

static unsigned int xs = 53u;
static unsigned int xorshift(void) {
    xs ^= xs << 13;
    xs ^= xs >> 17;
    xs ^= xs << 5;
    return xs;
}

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static void sifirla(long *h) { memset(h, 0, KOVA * sizeof *h); }
```

```c
static void yaris(void) {
    sifirla(h1);
    #pragma omp parallel for
    for (long i = 0; i < N; i++)
        h1[veri[i]]++;   /* KASITLI YARIS: kayip guncelleme */
}

static void atomik(void) {
    sifirla(h2);
    #pragma omp parallel for
    for (long i = 0; i < N; i++) {
        #pragma omp atomic
        h2[veri[i]]++;
    }
}

static void yerel(void) {
    sifirla(h3);
    #pragma omp parallel
    {
        long my[KOVA];
        memset(my, 0, sizeof my);  /* yerel kutu */
        #pragma omp for
        for (long i = 0; i < N; i++)
            my[veri[i]]++;
        #pragma omp critical       /* birlestirme, bir kez */
        for (int k = 0; k < KOVA; k++)
            h3[k] += my[k];
    }
}

static void sirali(void) {
    sifirla(h0);
    for (long i = 0; i < N; i++) h0[veri[i]]++;
}
```

```c
static int dogru(const long *ref, const long *h) {
    int hata = 0;
    for (int k = 0; k < KOVA; k++)
        if (ref[k] != h[k]) hata++;
    return hata;
}

static double olc(void (*f)(void), int p) {
    double t[TEKRAR];
    omp_set_num_threads(p);
    for (int r = 0; r < TEKRAR; r++) {
        double t0 = omp_get_wtime();
        f();
        t[r] = omp_get_wtime() - t0;
    }
    qsort(t, TEKRAR, sizeof t[0], karsilastir);
    return t[TEKRAR / 2];
}

int main(int argc, char **argv) {
    int p = argc > 1 ? atoi(argv[1]) : 8;
    for (long i = 0; i < N; i++)
        veri[i] = (unsigned char)(xorshift() % KOVA);
    /* Sirali referans: dogruluk icin ve hiz tabani icin */
    double tsira = olc(sirali, 1);
    long toplam_ref = 0;
    for (int k = 0; k < KOVA; k++) toplam_ref += h0[k];
    printf("# N=%ld kova=%d thread=%d tekrar=%d\n",
           N, KOVA, p, TEKRAR);
    printf("surum,medyan_s,kova_toplami,yanlis_kova\n");
    printf("sirali,%.4f,%ld,0\n", tsira, toplam_ref);

    double ts = olc(yaris, p);
    long toplam1 = 0;
    for (int k = 0; k < KOVA; k++) toplam1 += h1[k];
    printf("yaris,%.4f,%ld,%d\n", ts, toplam1, dogru(h0, h1));
```

```c
    double ta = olc(atomik, p);
    long toplam2 = 0;
    for (int k = 0; k < KOVA; k++) toplam2 += h2[k];
    printf("atomik,%.4f,%ld,%d\n", ta, toplam2, dogru(h0, h2));

    double ty = olc(yerel, p);
    long toplam3 = 0;
    for (int k = 0; k < KOVA; k++) toplam3 += h3[k];
    printf("yerel,%.4f,%ld,%d\n", ty, toplam3, dogru(h0, h3));
    printf("referans_toplam=%ld\n", toplam_ref);
    return 0;
}
```

Sekiz iş parçacığıyla çalıştırınca:

```term
$ ./hist 8
# N=20000000 kova=16 thread=8 tekrar=3
surum,medyan_s,kova_toplami,yanlis_kova
sirali,0.0057,20000000,0
yaris,0.0782,10667496,16
atomik,0.1977,20000000,0
yerel,0.0014,20000000,0
referans_toplam=20000000
```

Tablonun okunması: `yaris` süresi 0,078 s ile sıralı sürümün 0,0057 s'sinden on kat yavaş, ve kova toplamı 10 667 496: kayıp güncelleme var ve sonuç yanlış. `atomik` doğru ama 0,198 s ile **sıralı sürümden yaklaşık 35 kat yavaş**: her artış, hepsinin aynı önbellek satırını almasını gerektirir. `yerel` hem doğru (toplam 20 000 000, yanlış kova 0) hem hızlı (0,0014 s, sıralıya göre yaklaşık 4 kat): paylaşım yoktur, birleşim yalnızca 16 değerlik bir toplamadır. Yarışlı sürümün kayıp miktarı çalıştırmadan çalıştırmaya değişir; bu da yarışın sonucunun öngörülemez olduğunu gösterir.

**Bunu AI'sız yazabilir misin?** Yerel sürümü, her iş parçacığının kendi kovasını `malloc` ile ayırdığı ve birleştirmeyi bir `reduction` ile yapan bir versiyona çevir. Hangisi daha az bellek kullanır, hangisi kova sayısı 65 536 olunca daha iyi olur? Bu soruyu kağıt üzerinde yanıtla, sonra ölç.

### Örnek 4 (★★★): Paralel birleştirme sıralamasının iş–açıklık analizi ve eşik seçimi

**Problem.** `n = 2^24` tam sayıyı sekiz iş parçacığıyla sıralayan bir birleştirme sıralaması yaz. Birleştirme adımı seri kalsın. Eşik (cutoff), görev oluşturmayı durduran küçük alt dizinin boyutu. Bu eşiğin hız ve doğruluğa etkisini ölç ve iş–açıklık modeline göre açıkla.

**Adım 1 — Anla.** Girdi: `ilk[0..n-1]`, çıktı: sıralı `a`. Doğruluk: paralel çıktı, seri çıktıyla bayt bayt eşleşmeli (birleştirme kararlıdır). Kenar durumları: `eşik = n` olduğunda tüm iş seri çalışır; `eşik = 1` olduğunda görev patlar.

**Adım 2 — Örnekle.** Küçük örnek: `[4, 1, 3, 2]`. Ortadan ikiye bölünür: `[4, 1]` ve `[3, 2]`. İkisi sıralanır: `[1, 4]` ve `[2, 3]`. Birleştirme: `[1, 2, 3, 4]`. Paralel olarak iki yarım bağımsız sıralanabilir; birleştirme ise bekler.

**Adım 3 — Kaba çöz.** Her seviyede bütün elemanları taşıyan bir birleştirme var, toplam iş `n log2 n`. Her seviyeyi iki görevle paralelleştirirsen (fork-join), ama birleştirmeyi seri tutarsan, kritik yol her seviyedeki birleştirmeyi içerir.

**Adım 4 — Örüntü.** Kritik yolda üst düzey birleştirme `n`, bir alt seviye `n/2` vb. adım sürer. Toplam açıklık `n + n/2 + n/4 + ... ≈ 2n`. Paralellik `T1 / T∞ ≈ n log2 n / 2n = (log2 n) / 2`. `n = 2^24` için bu yaklaşık 12'dir. Brent sınırı `T8 ≤ T1/8 + T∞`: `T1 = 24n`, `T∞ = 2n` (birim: karşılaştırma-taşıma) alınırsa `T8 ≤ 3n + 2n = 5n`, yani en fazla `24n / 5n ≈ 4,8` kat hızlanma.

**Adım 5 — İyileştir.** Eşik seçimi: küçük eşik çok görev (yük ve zamanlama maliyeti), büyük eşik az görev (dengesizlik) demektir. Sezgisel bir hedef: yaprak sayısı `n / eşik` iş parçacığı sayısının onlarca katı olsun, ama her yaprak görev maliyetinden çok daha uzun sürsün. Bunu bir deneyle ölçeriz.

**Adım 6 — Doğrula.** Önce küçük bir elle iz: iki sıralı yarı `[1, 4, 6, 7]` ve `[2, 3, 5, 8]` birleştirilir:

| Adım | Sol baş | Sağ baş | Seçilen | Çıktı |
|---|---|---|---|---|
| 1 | 1 | 2 | 1 | `[1]` |
| 2 | 4 | 2 | 2 | `[1, 2]` |
| 3 | 4 | 3 | 3 | `[1, 2, 3]` |
| 4 | 4 | 5 | 4 | `[1, 2, 3, 4]` |
| 5 | 6 | 5 | 5 | `[1, 2, 3, 4, 5]` |
| 6 | 6 | 8 | 6 | `[1, ..., 6]` |
| 7 | 7 | 8 | 7 | `[1, ..., 7]` |
| 8 | bitti | 8 | 8 | `[1, 2, 3, 4, 5, 6, 7, 8]` |

Eşitlikte sol taraf önce gelir (`a[j] < a[i]` koşulu); bu kararlılığın kaynağıdır. Şimdi programı çalıştır (kod, birleştirme ve görev yapısını içerir):

```c
/* b53_mergesort.c - paralel birlestirme siralamasi: gorev + esik.
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_mergesort.c -o msort
 * Kullanim: ./msort <thread>        (ornek: ./msort 8)
 * Birlestirme seri yapilir: T_inf = O(n) (metinde anlatilir).
 * Dogruluk: her paralel sonuc, seri siralamanin birebir kopyasiyla
 * karsilastirilir (kararli birlestirme: esitlikte sol taraf once).
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N (1L << 24)     /* 16.7 milyon int */
#define TEKRAR 3

static long ESIK;

static void birlestir(int *a, int *t, long lo, long mid, long hi) {
    long i = lo, j = mid, k = lo;
    while (i < mid && j < hi)
        t[k++] = (a[j] < a[i]) ? a[j++] : a[i++];
    while (i < mid) t[k++] = a[i++];
    while (j < hi) t[k++] = a[j++];
    memcpy(a + lo, t + lo, (size_t)(hi - lo) * sizeof *a);
}

static void sirali(int *a, int *t, long lo, long hi) {
    if (hi - lo < 2) return;
    long mid = lo + (hi - lo) / 2;
    sirali(a, t, lo, mid);
    sirali(a, t, mid, hi);
    birlestir(a, t, lo, mid, hi);
}
```

```c
/* Esik altinda seri, uzerinde iki gorev. */
static void paralel(int *a, int *t, long lo, long hi) {
    if (hi - lo <= ESIK) {
        sirali(a, t, lo, hi);
        return;
    }
    long mid = lo + (hi - lo) / 2;
    #pragma omp task shared(a, t)
    paralel(a, t, lo, mid);
    #pragma omp task shared(a, t)
    paralel(a, t, mid, hi);
    #pragma omp taskwait
    birlestir(a, t, lo, mid, hi);
}

static unsigned int xs = 53u;
static unsigned int xorshift(void) {
    xs ^= xs << 13;
    xs ^= xs >> 17;
    xs ^= xs << 5;
    return xs;
}

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}
```

```c
int main(int argc, char **argv) {
    int p = argc > 1 ? atoi(argv[1]) : 8;
    int *ilk = malloc(N * sizeof *ilk);
    int *a = malloc(N * sizeof *a);
    int *t = malloc(N * sizeof *t);
    int *ref = malloc(N * sizeof *ref);
    if (!ilk || !a || !t || !ref) return 1;
    for (long i = 0; i < N; i++) ilk[i] = (int)(xorshift() >> 2);
    memcpy(ref, ilk, N * sizeof *ilk);
    double tr[TEKRAR];
    for (int r = 0; r < TEKRAR; r++) {
        memcpy(a, ilk, N * sizeof *ilk);
        double t0 = omp_get_wtime();
        sirali(a, t, 0, N);
        tr[r] = omp_get_wtime() - t0;
    }
    memcpy(ref, a, N * sizeof *a);  /* seri sonuc referans */
    qsort(tr, TEKRAR, sizeof tr[0], karsilastir);
    double tseri = tr[TEKRAR / 2];
    printf("# N=%ld thread=%d tekrar=%d\n", N, p, TEKRAR);
    printf("esik,medyan_s,hizlanma,dogru\n");
    printf("seri,%.4f,1.00,evet\n", tseri);
    long esikler[] = {1L << 8, 1L << 12, 1L << 16, 1L << 20, N};
    for (int k = 0; k < 5; k++) {
        ESIK = esikler[k];
        double tp[TEKRAR];
        int dogru = 1;
        for (int r = 0; r < TEKRAR; r++) {
            memcpy(a, ilk, N * sizeof *ilk);
            double t0 = omp_get_wtime();
            #pragma omp parallel num_threads(p)
            #pragma omp single
            paralel(a, t, 0, N);
            tp[r] = omp_get_wtime() - t0;
            if (memcmp(a, ref, N * sizeof *a) != 0) dogru = 0;
        }
        qsort(tp, TEKRAR, sizeof tp[0], karsilastir);
        printf("%ld,%.4f,%.2f,%s\n", ESIK, tp[TEKRAR / 2],
               tseri / tp[TEKRAR / 2], dogru ? "evet" : "HAYIR");
    }
```

```c
    free(ilk); free(a); free(t); free(ref);
    return 0;
}
```

Sekiz iş parçacığıyla çalıştırdığımızda:

```term
$ ./msort 8
# N=16777216 thread=8 tekrar=3
esik,medyan_s,hizlanma,dogru
seri,1.4015,1.00,evet
256,0.3655,3.83,evet
4096,0.3473,4.04,evet
65536,0.3376,4.15,evet
1048576,0.3535,3.96,evet
16777216,1.3684,1.02,evet
```

Ölçüm, modelle uyumludur. Seri süre 1,40 saniye; en iyi eşik (65 536 ve 4 096 civarı) yaklaşık 4,0–4,15 kat hızlandırdı. Model 4,8 kat üst sınır veriyordu; ölçüm bunun altında, birleştirmenin bellek bant genişliğine bağlılığı (53.9) ve görev maliyeti nedeniyle. Eşik `256`'da hız 3,83 kat ve `1 048 576`'da 3,96 kattı: plato geniş. Eşik `n`'de (yalnızca seri) hız 1,02, yani paralellik tamamen kayboldu. Tüm çalıştırmalarda sonuç seri referansla birebir eşleşti (`dogru = evet`).

Bu ölçümden çıkan sonuç: eşik seçimi kritik değil ama tamamen yok sayılamaz. Birkaç yüz ile birkaç yüz binler arasında düz bir plato var; asıl büyük kayıp eşiğin `n` ya da `1` olduğu uç durumlarda. Pratik kural: `n / eşik` yaprak sayısı iş parçacığı sayısının onlarca katına ulaşsın, yaprak işi görev maliyetinden belirgin büyük olsun.

**Bunu AI'sız yazabilir misin?** Birleştirmeyi de paralel yapan (iki sıralı diziyi bölüp paralel birleştiren) bir sürüm düşün. Açıklık `O(log² n)`'e nasıl iner? Bu soruyu bir ağaçla çiz, sonra kendi sürümünün dağıtım adımını elle izle.
## Kendin Yap Projeleri

::: dikkat
Bu iki projede bir yapay zekâ aracına, kod üreteci ya da otomatik tamamlamaya başvurma. Amaç, paralel programın nasıl bölündüğünü, nerede beklediğini ve neden hızlandığını ya da hızlanmadığını kendi elinle ölçerek görmek. Her iki projede de ölçümünü tablo olarak raporla; tablo yoksa başarı sayılmaz.
:::

### Proje 1 (★★): Paralel 2B konvolüsyon ve hız raporu

**Amaç.** 2 boyutlu bir sentetik görüntüye 3×3 bir konvolüsyon filtresi uygulayan dört sürüm yazmak: sıralı C, OpenMP, Python `multiprocessing` ve NumPy vektörleştirilmiş. Sonuçları doğrulamak, hızlanmayı ölçmek ve seri kesri Amdahl'a uydurarak tahmin etmek.

**Beklenen davranış.** Girdi: `4096 × 4096` `float32` bir görüntü (`numpy.random.default_rng(53)` ile üretilmiş, sabit tohum). Kenar pikselleri için sıfır dolgu (zero padding) kullan. Her sürüm aynı çıktıyı vermeli; her biri 1, 2, 4, 8 ve 16 iş parçacığı (ya da süreç) için süre ölçmeli.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Konvolüsyon bir stencil'dir: her çıktı pikseli, komşularına bağlıdır. Paralelleştirmenin en doğal yolu satırları bloklara bölmektir. Bloklar arasında bir satır kadar "halo" (sınır) verisi paylaşılır; bu veri yalnızca okunur, yazılmadığı için yarış oluşmaz. OpenMP sürümünde `schedule(static)` ile başla, sonra dinamik ile karşılaştır. Python sürümünde Bölüm 53.8'deki chunksize deneyini hatırla: satır başına değil, blok başına iş gönder. NumPy sürümünde kaydırmalı toplamları vektör olarak yaz.

**Başarı kriterleri (ölçülebilir).**
1. Dört sürümün çıktıları, sıralı referansla en fazla `1e-5` mutlak farkla eşleşir (`max|fark|` ile raporla).
2. Sekiz iş parçacığında OpenMP sürümü sıralıya göre en az 4 kat hızlanır. Bu bir hedef; ölçümün sonucu ne olursa olsun, sayıyı raporla.
3. Ölçülen hızlanmalardan Karp–Flatt ile `e(p)` hesapla; `p = 4..8` arasındaki değerlerin ortalamasını yaz ve bunun ne anlama geldiğini bir paragrafta açıkla.
4. Bir hız (`S(p)`) ve bir verim (`E(p) = S/p`) grafiği üret; grafiğin altında hangi kısmın bellek-bağlı, hangisinin hesap-bağlı göründüğünü yaz (53.9'daki roofline ile karşılaştır).

### Proje 2 (★★★): İş çalma ile görev havuzu

**Amaç.** C ve pthreads ile küçük bir görev havuzu yazmak. Her iş parçacığının kendi çift uçlu kuyruğu (deque) olsun: iş parçacığı kendi kuyruğunun sonundan görev alır, boşta kalan iş parçacığı başka bir kuyruğun başından **çalar**. Aynı dengesiz iş yükünü statik bölmeyle de çalıştır ve karşılaştır.

**Beklenen davranış.** Görevler şöyle olsun: `N = 20000` görev, her görev `i` için maliyeti rastgele ama sabit tohumla (53) `[1, 5000]` arasında bir karma döngüsü. Bazı görevler görev üretebilsin (ağaç benzeri): bir görev iki alt görev ekleyebilir, toplam görev sayısı ölçülebilir olsun. Her görev tam bir kez yürütülmeli; program sonunda yürütülen görev sayısı `N` (ya da üretilen toplam) ile eşleşmeli.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Kuyruk başına bir `pthread_mutex_t` ile başla; bu basit ve doğrudur. Sonra bir kuyruğu kilitsiz yapmayı deneyebilirsin, ama bu, Bölüm 27.15'teki Treiber yığını ve ABA problemi gibi ince konulara girer: önce kilitli sürümü tamamen doğrula. Çalma işlemi için kuyrukların uçlarını farklı kilitle korumak gerekir. Doğruluğu ThreadSanitizer ile denetle (Bölüm 27.17): derlemede `-fsanitize=thread` kullan ve uyarı çıkmadığını rapora ekle. Karşılaştırma için statik bölme: görevleri `N/p` parçaya ayır.

**Başarı kriterleri (ölçülebilir).**
1. Her görev tam bir kez yürütülür: her görev için bir sayaç dizisi tut ve sonunda tüm sayaçların 1 olduğunu doğrula.
2. ThreadSanitizer hiçbir veri yarışı raporlamaz.
3. Sekiz iş parçacığında, dengesiz yükte iş çalma sürümü statik bölmeye göre en az %30 daha kısa sürede bitirir. Bu hedefi bir kez ölç; tutmazsa nedenini (kilit çekişmesi, görev boyutu, bellek) raporla.
4. Çalma sayısını (kaç kez bir kuyruktan başka bir kuyruğa geçildiğini) say ve raporla. Bu sayı, dengesizliğin büyüklüğü hakkında ne söyler?

## Ek Alıştırmalar

Aşağıdaki problemler kademelidir. Cevabı yazmadan önce bir tahmin yap, sonra kendi hesabınla karşılaştır. Mülakat etiketli olanlar whiteboard formatında çözülmeli.

1. ★ Seri kesri `0,20` olan bir işin 16 çekirdekte Amdahl hızlanmasını hesapla. Bu sonuç, "16 çekirdek" kararına ne diyor?
2. ★ Seri kesri `0,05` olan bir işi 8 kat büyüterek 8 çekirdekte çalıştırıyorsun. Gustafson ölçeklenmiş hızlanmasını hesapla.
3. ★ Bir kod 4 çekirdekte `2,5` kat hızlanıyor. Karp–Flatt ile etkin seri kesri bul. Bu değer neyi ima ediyor?
4. ★ Bir algoritmanın `T1 = 100` ve `T∞ = 10`. En fazla kaç işlemci anlamlı katkı verir? Brent sınırına göre `T4` için bir üst sınır yaz.
5. ★★ 1000 elemanlık bir dizinin ağaçla toplamında kaç toplama yapılır ve kaç seviye vardır? (Mülakat) Seviye sayısını 2'nin kuvvetine yaklaşmadan açıkla.
6. ★★ Blelloch önek toplamında `n = 16` ve `n = 2^20` için toplama sayısını ve süper adım sayısını hesapla. Büyük `n` için paralellik neye yaklaşır?
7. ★★ Dört iş parçacığı, paylaşılan bir sayacı her biri `10^6` kez kilitsiz artırıyor. Sonuç hangi aralıktadır? Neden kesin bir alt sınır kanıtlamak zor? (Mülakat)
8. ★★ Dinamik zamanlamada parça boyutu 1 ve parça boyutu `N/p` seçilirse, iki uç durum hangi maliyetle başarısız olur? (Mülakat)
9. ★★★ Birleştirme sıralamasında eşiği `n / p` seçmek neden tek başına yeterli değildir? Dengesiz veride ne olur? (Mülakat)
10. ★★★ Bir kernel'in aritmetik yoğunluğu `0,5` flop/bayt, bellek bant genişliği `40` GB/s ve tepe hesap `200` GFLOPS. Roofline'a göre performansı ne sınırlar, üst sınır kaçtır, köşe nerededir?
11. ★★ Bir programın sekiz çekirdekte `3,5` kat hızlandığını ölçtün. Karp–Flatt ile `e(8)` hesapla ve bu değerin paralel tasarımına etkisini yaz.
12. ★★ Bir kilitsiz sayaç testi on kez çalıştı ve on kez de doğru sonuç verdi. Bu, programın doğru olduğunu kanıtlar mı? Yarış koşullarının testte görünmemesinin nedenlerini say. (Mülakat)

## Kod Okuma Egzersizi

Bu bölümde `multiprocessing.Pool.map`'in parça (chunk) boyutunu nasıl seçtiğini kullandık: `len(self._pool) * 4` ile bölüp kalanı varsa bire tamamladık. Bu formülü kaynakta doğrulamak, varsayılan davranışın ne olduğunu gerçekten bilmenin yoludur. Aşağıdaki kesit, CPython 3.12.10 (`Lib/multiprocessing/pool.py`, `Pool._map_async` içinde) dosyasından alınmıştır. Yerel kurulumdaki yolu `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\multiprocessing\pool.py`'dir. Satır, sayfa genişliğine sığsın diye iki satıra bölündü; anlam değişmedi.

```python
        if chunksize is None:
            chunksize, extra = divmod(len(iterable),
                                      len(self._pool) * 4)
            if extra:
                chunksize += 1
        if len(iterable) == 0:
            chunksize = 0
```

**Sorular — cevaplamadan geçme:**

1. `chunksize`'ın varsayılan değeri neden `len(self._pool) * 4`'e bölünerek hesaplanıyor? Bu 4 katsayısı, Bölüm 53.8'deki deney tablosunda hangi sonucu açıklar?
2. `extra` sıfırdan farklıysa `chunksize` neden bire artırılıyor? Eğer artırmasaydık hangi işler gönderilmezdi?
3. `len(iterable) == 0` durumunda `chunksize = 0` yazılmasının amacı nedir ve bu olmadan hangi hata oluşabilirdi?
4. Bu kod parça boyutunu iş boyutuna göre seçiyor mu, yoksa sabit bir kural mı uyguluyor? Yapılan ölçümde (`3125` ile `10000` arasındaki fark) bu kuralın ne kadar iyi çalıştığını yorumla.
5. Aynı mantığı `ProcessPoolExecutor.map` için de bulabilir misin? Bulamazsan, `ProcessPoolExecutor`'ın varsayılan `chunksize`'ı için nerede bakmalısın ve neden kaynağı okumak dokümantasyondan daha kesindir?
6. Bu formülün Windows'ta `spawn` ile çalışan süreçler için bir maliyet ekleyip eklemediğini düşün. Havuz kurulum süresini (53.8'deki `kurulum` satırı) bu formüle dahil eder misin?

## Bölüm Özeti

- Eşzamanlılık bir yapı (birden çok işi yönetme), paralellik bir çalıştırma özelliğidir (aynı anda yürütme). Yarış ve kilitlenme eşzamanlılığın, hızlanma sınırı ise paralelliğin sorunudur.
- Flynn'in sınıfları (SISD, SIMD, MIMD) ve GPU'nun SIMT modeli, bir işlemcinin hangi paralellik türünü sunduğunu tarif eder. Bu makinede 8 fiziksel çekirdek ve 16 mantıksal iş parçacığı var.
- Amdahl (sabit iş) ve Gustafson (büyüyen iş) yasaları, seri kesirin hızlanmaya nasıl sınır koyduğunu gösterir. Karp–Flatt ile ölçülen hızlanmadan etkin seri kesri çıkarabilirsin; ölçümde `s = 0,10` için değer yaklaşık 0,12 çıktı.
- İş–açıklık modeli (`T1`, `T∞`, paralellik `T1/T∞`) ve Brent sınırı, bir algoritmanın yapısal paralelliğini tahmin etmeyi sağlar.
- Map, indirgeme, tarama (Blelloch), boru hattı, stencil ve fork-join kalıpları çoğu paralel problemi tanımlar. Blelloch taraması iki kat iş pahasına logaritmik açıklık kazandırır.
- Dengesiz işte statik bölme kayıp verir; dinamik ve guided zamanlama bunu geri kazanır. İş çalma aynı fikrin dağıtık bir uygulamasıdır.
- Bellek bant genişliği çekirdek eklemekle yükselmez; triad ölçümünde yaklaşık 31–32 GB/s'de doydu. Roofline modeli, bir kernel'in bellek ya da hesap tavanına bağlı olduğunu gösterir.
- Kayan nokta toplamasında birleşme sırası sonucu değiştirir; paralel sonucu sıralı referansla tolerans içinde karşılaştır, Kahan ile hatayı azalt.
- Python'da GIL CPU-bağlı işi iş parçacıklarında durdurur; süreç havuzu hızlandırır ama serileştirme ve `chunksize` maliyeti vardır. NumPy'nin BLAS iş parçacıkları ise matris işlerinde gerçek paralellik sağlar.

### Kısım XIII'ün kapanışı: Bölüm 52'den 53'e

Kısım XIII'ü tek bir soruyla özetleyebiliriz: bir sinyal işlemi ya da bir hesap, işi birden çok çekirdeğe bölerek ne kadar hızlanabilir ve bu hızlanmayı neyin sınırladığını nasıl ölçersin? Bölüm 52 sinyal işlemenin temel işlemlerini ele aldı; bu bölümde o işlemlerin paralel çalıştırılmasının neden iş–açıklık modeline, bellek bant genişliğine ve sayısal doğruluğa bağlı olduğunu gösterdik. Bu kısımda her iddianın bir ölçümle doğrulanmasını öğrenmiş olmalısın: Amdahl eğrisini ölçmeden yorumlama, roofline'ı kernel'in yoğunluğunu hesaplamadan çizme, paralel sonucu sıralı referansla karşılaştırmadan doğru kabul etme.

**Sonraki bölümde:** Bölüm 54, ML'e Giriş ve Pipeline ile Kısım XIV'e, Makine Öğrenmesi'ne başlıyor. Bu bölümde paralel işin ölçülmesini ve sayısal doğruluğu öğrendik; Bölüm 54'te aynı disiplini bir öğrenme probleminin çerçevelenmesine, veri bölmeye ve veri sızıntısını önlemeye uygulayacağız.

::: mulakat
1. Eşzamanlılık ile paralellik arasındaki fark nedir? Tek çekirdekli bir makinede hangisi mümkündür?
2. Seri kesri %15 olan bir işte 32 çekirdek hızlanmasının üst sınırı nedir? Bu sınır neden çekirdek sayısını artırmakla aşılamaz?
3. Gustafson yasası, Amdahl yasasının hangi varsayımını değiştirir? Büyüyen bir problem için hangisi daha uygundur?
4. Bir paralel toplamı kaç seviyede ve kaç toplamayla yaparsın? Bu sayılar Brent sınırında nasıl görünür?
5. Dinamik ve statik zamanlama arasında ne zaman statik tercih edilir, ne zaman dinamik? Gerekçeni iş maliyetinin dağılımıyla açıkla.
6. Kayan nokta toplamasında paralel sonucun sıralı sonuçla neden tam eşleşmeyebileceğini bir örnekle açıkla. Hangi önlem sonucu daha kararlı yapar?
7. Bellek-bağlı bir kernel'e çekirdek eklemek neden hızlandırmaz? Roofline modeli bunu nasıl gösterir?
8. Python'da CPU-bağlı bir işi neden iş parçacıklarıyla değil süreçlerle hızlandırırsın? Süreç havuzunda hangi maliyetler vardır?
:::
