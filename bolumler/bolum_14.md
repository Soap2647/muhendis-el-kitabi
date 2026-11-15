%% kisim_no: IV
%% kisim_ad: Algoritmalar
%% bolum_no: 14
%% baslik: Arama

## Giriş: Sıralı veri, bedava bir bilgidir

Bilgisayar her gün bir şey arar: bir dosya adı, bir kullanıcı kaydı, bir önbellek satırı, bir sensör kalibrasyon değeri. En temel soru hep aynıdır: aradığım değer bu koleksiyonda var mı, varsa nerede? Bölüm 7'de diziyi, Bölüm 9'da hash tablosunu, Bölüm 10'da ağaçları arama yapısı olarak gördük. Bu bölümde odağı sıralı diziye çeviriyoruz, çünkü orada bir karşılaştırma bize sadece "eşit mi" bilgisini değil, "hangi yönde" bilgisini de verir.

Sıralı bir dizide `a[mid]` ile `x`'i karşılaştırdığında, `a[mid]`'in solundaki ve sağındaki adayların yarısını elersin. Bölüm 12'de bu fikrin `O(log n)` maliyet verdiğini gördük. Ama fikir kolay, kodu doğru yazmak zor. İkili aramanın yazımı yıllarca hatalı kalmıştır: Bölüm 5'te gördüğümüz `(lo + hi) / 2` taşması, bunun en bilinen örneğidir. Asıl zorluk, algoritmanın kendisinden çok, sınır durumlarında (ilk konum, son konum, değerin hiç olmaması, tekrarlar, boş dizi) yazılan birkaç satırdadır.

Mülakatta "bir dizide ikili arama yap" sorusu ilk bakışta kolaydır. Ama "değerin ilk konumunu bul", "döndürülmüş bir dizide ara", "cevabın kendisi üzerinde ikili arama yap" gibi varyasyonlar, adayın fikri gerçekten anlayıp anlamadığını ortaya çıkarır. Savunma ve gömülü sistemlerde de aramanın süresi önemlidir. Bir sensör tablosunda her örnekleme turunda en yakın kalibrasyon noktasını bulmanız gerekiyorsa, arama adımının sayısı ve en kötü durumu döngü süresini belirler. Mert'in EV Dashboard projesindeki kalibrasyon tablosu tam olarak böyle bir aramadır.

::: not
Bu bölümde çoğu algoritmayı üç açıdan göreceğiz: sezgi, bir **döngü değişmezi** ile doğruluk ve mümkün olduğunda ölçüm. Yazdığımız C programları WSL'de gcc 13.3 ile `-std=c11` olarak derlendi; Python programları Python 3.12 ile çalıştırıldı. Sanitizer'ların raporladığı tek hata, 14.3'te bilerek ürettiğimiz taşmadır. Metindeki ölçüm sayıları bu programların çıktısından alınmıştır.
:::

## 14.1 Doğrusal arama ve nöbetçi hilesi

En basit arama, diziyi baştan sona taramaktır. Sıralı olup olmadığına bakmaz, her elemanı tek tek karşılaştırır. Bulursa konumu, bulamazsa `-1` döndürür. Sırasız veride bu tek seçenektir: hiçbir yapı kurmadan çalışır. Maliyeti Bölüm 12.6'daki gibi en iyi `Θ(1)`, en kötü `Θ(n)`'dir; bulunamayan bir değer her zaman en kötü durumdur.

Doğrusal aramayı ayrıca incelemenin iki nedeni var. Birincisi, `n` küçükken, sırasız veride ya da bir kez aranacak veride çoğu zaman en iyi seçimdir. İkincisi, döngünün içindeki her kontrolü saymayı öğretir; bu sayma alışkanlığı ikili aramada da işe yarayacak.

Aşağıdaki kod, iki sürümü yan yana koyar. `dogrusal` her turda iki karşılaştırma yapar: sınır (`i < n`) ve değer (`a[i] == x`). `nobetci` ise dizinin sonuna `x`'i koyar; böylece döngü sınırı kontrol etmeden mutlaka `x`'te durur ve her turda tek karşılaştırma kalır. Karşılaştırma sayacı, bu farkı ölçmek için eklendi:

```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

/* Klasik doğrusal arama. cmp: karşılaştırma sayacı. */
long dogrusal(const int *a, size_t n, int x, long *cmp) {
    for (size_t i = 0; i < n; i++) {
        *cmp += 2;               /* i < n ve a[i] == x */
        if (a[i] == x)
            return (long)i;
    }
    *cmp += 1;                   /* son, başarısız i < n kontrolü */
    return -1;
}

/* Nöbetçili arama: a[n] hücresi x'i tutar; döngüde sınır
   denetimi yok. */
long nobetci(int *a, size_t n, int x, long *cmp) {
    int eski = a[n];
    size_t i = 0;
    a[n] = x;
    while (a[i] != x) {
        *cmp += 1;               /* doğru olan her tur için */
        i++;
    }
    *cmp += 1;                   /* son, yanlış kontrol */
    a[n] = eski;
    return (i < n) ? (long)i : -1;
}
```

Aynı dosyanın `main` fonksiyonu, iki sürümü aynı diziye uygular ve sayaçları yazdırır:

```c
int main(void) {
    size_t n = 1000;
    int *a = malloc((n + 1) * sizeof *a);
    if (a == NULL)
        return 1;
    for (size_t i = 0; i < n; i++)
        a[i] = 2 * (int)i;
    a[n] = 0;                    /* nöbetçi hücresinin ilk değeri */
    int hedef[] = {1000, 1001, 0};
    for (int k = 0; k < 3; k++) {
        long c1 = 0, c2 = 0;
        long r1 = dogrusal(a, n, hedef[k], &c1);
        long r2 = nobetci(a, n, hedef[k], &c2);
        printf("x=%5d klasik: konum=%4ld cmp=%5ld\n",
               hedef[k], r1, c1);
        printf("        nobetci: konum=%4ld cmp=%5ld\n", r2, c2);
    }
    free(a);
    return 0;
}
```

Bu programı derleyip çalıştırdık. Dizi `a[i] = 2i` ile 1000 elemanlıdır; `1000` 500. konumda, `1001` hiç yoktur, `0` ilk konumdadır:

```term
$ gcc -O2 -Wall -Wextra -std=c11 dogrusal.c -o dogrusal
$ ./dogrusal
x= 1000 klasik: konum= 500 cmp= 1002
        nobetci: konum= 500 cmp=  501
x= 1001 klasik: konum=  -1 cmp= 2001
        nobetci: konum=  -1 cmp= 1001
x=    0 klasik: konum=   0 cmp=    2
        nobetci: konum=   0 cmp=    1
```

Sonuçlar bir şeyi açıkça gösteriyor. Değer ortada olduğunda klasik sürüm 1002, nöbetçili sürüm 501 karşılaştırma yaptı. Değer hiç olmadığında fark ikiye katlanır: 2001 ve 1001. Büyüme sınıfı değişmedi; ikisi de `Θ(n)`. Bu, Bölüm 12.11'de gördüğümüz sabit çarpan farkıdır: nöbetçi hile, kodu daha hızlı yapar ama algoritmanın büyüme sınıfını değiştirmez.

Nöbetçi hilenin bedeli de var. Diziye yazabilmek ve `a[n]` hücresinin var olması gerekir. Sabit (`const`) bir dizi ya da başka bir iş parçacığının aynı anda okuduğu bir dizi için geçici yazma yapmak uygun değildir. Bu yüzden gerçek kodda hile, kontrolü bir kez yapılmış, kendi sahip olduğumuz bellekte kullanılır.

Doğrusal aramanın ikili aramaya üstün olduğu durumlar da vardır. Bunlar, ölçümle doğrulanması gereken sezgilerdir:

- **Küçük `n`.** Dizi birkaç düzine elemanlıysa, ikili aramanın her turdaki ek iş (orta hesabı, iki yönlü dal) doğrusal taramanın basitliğini geçemeyebilir.
- **Sırasız veri ya da tek seferlik arama.** Diziyi sıralamak `O(n log n)` alır (Bölüm 13). Tek bir arama için sıralamak, doğrusal taramadan pahalıdır.
- **Önbellek.** Doğrusal tarama bellekte ardışık ilerler; donanım bunu çok iyi önbelleğe alır (Bölüm 12.11 ve Bölüm 25). Ardışık erişimin avantajı, `n` küçükken ikili aramanın karşılaştırma avantajını dengeleyebilir.
- **Sık değişen veri.** Diziyi her ekleme ya da silmede sıralı tutmak `O(n)` iş getirir; bu durumda sıralı dizi yerine başka bir yapı düşünmek gerekir (14.13).

Bu sezgilerin eşiğini bilmek için ölçüm gerekir. Ek Alıştırmalar'da bu ölçümü yapacaksın.

## 14.2 İkili arama ve döngü değişmezi

İkili aramayı Bölüm 5'te problem çözme adımlarıyla, Bölüm 12'de maliyetiyle gördük. Burada aynı algoritmanın doğruluğunu kanıtlıyoruz. Kanıtın aracı **döngü değişmezidir (loop invariant)**: döngünün her başında doğru kalan bir ifade. Değişmezi bulursan, döngü bittiğinde sonucun doğru olduğunu zorunlu olarak görürsün.

Alt sınır (lower bound) arıyoruz: `a[i] >= x` olan ilk `i`. Dizi artan sıralı olsun ve yarı açık aralık `[lo, hi)` kullanalım. Değişmez şudur:

- **(I)** `a[0 .. lo)` içindeki her eleman `x`'ten küçüktür.
- **(II)** `a[hi .. n)` içindeki her eleman `x`'e eşit ya da büyüktür.

Cevap, `[lo, hi)` aralığının içinde kalır. Döngü `lo == hi` olunca aralık boşalır ve iki şart birlikte `lo`'nun cevap olduğunu söyler.

Şekil 14.1, aynı diziyi üç adımda gösterir. Dizi `[2, 5, 8, 12, 16, 23, 38, 45, 56, 72, 91, 99]`, hedef `x = 56`. Mavi kutular (I) şartını, kırmızı kutular (II) şartını sağlar; beyaz kutular henüz karar verilmemiş belirsiz bölgedir.

![Şekil 14.1: İkili aramada [lo, hi) aralığının daralması. Mavi hücreler x'ten küçük (I), kırmızı hücreler x'e eşit ya da büyük (II), beyaz hücreler belirsiz aralıktır. Her adımda orta değer aralığı yarıya indirir.](gorseller/b14_ikili_aralik.png)

Üç adımda değişmezin nasıl korunduğunu görelim. Başlangıçta `lo = 0`, `hi = n = 12`; iki şart da boş küme üzerinde doğrudur. Her turda `orta = lo + (hi - lo) / 2` seçilir ve iki durum vardır:

- `a[orta] < x` ise `lo = orta + 1` yapılır. Sıralılık nedeniyle `a[0 .. orta]` içindeki her eleman `a[orta]`'dan küçük ya da eşittir, yani `x`'ten küçüktür. (I) korunur.
- `a[orta] >= x` ise `hi = orta` yapılır. Sıralılık nedeniyle `a[orta .. n)` içindeki her eleman `x`'ten büyük ya da eşittir. (II) korunur.

Sonlanma da kolaydır. Her turda aralık kesin küçülür: `lo = orta + 1` durumunda uzunluk `hi - orta - 1 < hi - lo` olur, çünkü `orta >= lo`; `hi = orta` durumunda uzunluk `orta - lo < hi - lo` olur, çünkü `orta < hi`. Tamsayı bir uzunluk sıfıra inmek zorundadır. Döngü bitince `lo == hi` olur ve (I), (II) birlikte `lo`'nun alt sınır olduğunu gösterir.

Bu kanıtın üç pratik sonucu var. Birincisi, `hi = orta` (ve `orta - 1` değil) yazılmasının nedeni, cevabın `orta` olabilmesidir: `orta`'yı dışlarsak (II) bozulur. İkincisi, döngünün `lo < hi` ile kontrol edilmesi, aralığı boş bırakan son durumu doğru ele almasıdır. Üçüncüsü, `orta`'nın her zaman `[lo, hi)` içinde olmasıdır: `lo + (hi - lo) / 2 < hi` çünkü `hi - lo >= 1`.

Kanıttaki `orta` satırı C'de şöyle yazılır. Burada yalnızca değişmezi koruyan kısmı gösteriyoruz; tam program 14.4'te:

```c
/* Alt sınır: a[i] >= x olan ilk i (yoksa n). */
size_t alt_sinir(const int *a, size_t n, int x) {
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        if (a[orta] < x)
            lo = orta + 1;
        else
            hi = orta;
    }
    return lo;
}
```

Bu fonksiyon, Bölüm 5'te gördüğümüz ikili aramanın kanıtlanmış hâlidir. Bölüm 5'teki CPython `bisect_left` de aynı değişmezi kullanır. Yeni olan, değişmezi açıkça yazıp sonuçtan önce doğrulamaktır.

## 14.3 Yarı açık aralık disiplini ve taşma

Yarı açık aralık `[lo, hi)`, `hi` elemanını dahil etmez. Bu tercihin üç avantajı vardır. Uzunluk doğrudan `hi - lo` olur. Boş aralık `lo == hi` ile ifade edilir ve `-1` ya da `+1` düzeltmesi gerekmez. Ardışık aralıklar `[0, k)` ve `[k, n)` biçiminde birbirine tam oturur, yani bir diziyi iki parçaya bölmek kolaydır.

Kapalı aralığı `[lo, hi]` kullanmak da mümkündür, ama her satırda dikkat gerektirir. Aşağıdaki tablo iki konvansiyonun farkını gösterir:

| Konvansiyon | Başlangıç | Döngü | Güncelleme | Boş aralık |
|---|---|---|---|---|
| Yarı açık `[lo, hi)` | `hi = n` | `lo < hi` | `hi = orta` ya da `lo = orta + 1` | `lo == hi` |
| Kapalı `[lo, hi]` | `hi = n - 1` | `lo <= hi` | `hi = orta - 1` ya da `lo = orta + 1` | `lo > hi` |

Kapalı sürümde `hi = orta - 1` yazmak da doğrudur, ama bir koşulla: cevabı `lo` olarak okumak gerekir ve döngü bittiğinde cevabın `hi + 1` olduğunu hatırlamak gerekir. Hatanın sık görülen biçimi, döngü sonunda `hi`'yi cevap sanmaktır. Yarı açık sürümde cevap doğrudan `lo`'dur ve bu ek akıl yürütme yoktur. Bu yüzden alt ve üst sınır aramalarında yarı açık aralığı kullanmak daha az hataya açıktır.

Orta değerin hesabında bir tuzak daha var. `(lo + hi) / 2` yazmak, `lo + hi` toplamı tip sınırını aşarsa işaretli tamsayıda taşmaya yol açar. C'de işaretli tamsayı taşması **tanımsız davranıştır (UB)**: derleyici bunun için bir sonuç garanti etmez, tipik olarak negatif bir değere sarar ama bu bir garanti değildir. Aşağıdaki program taşmayı çalışma anında kasıtlı üretir; `lo` ve `hi` komut satırından okunur ki derleyici sonucu önceden hesaplayıp uyarı vermesin.

```c
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 3)
        return 1;
    int lo = atoi(argv[1]);      /* çalışma anında okunur */
    int hi = atoi(argv[2]);
    int yanlis = (lo + hi) / 2;          /* işaretli taşma: UB */
    int dogru = lo + (hi - lo) / 2;      /* taşmaz */
    printf("INT_MAX=%d\n", INT_MAX);
    printf("yanlis=%d dogru=%d\n", yanlis, dogru);
    return 0;
}
```

Programı `2147483646` ve `2147483647` argümanlarıyla çalıştırdık. `INT_MAX` bu platformda `2147483647`'dir; çünkü C'deki `int` Windows ve WSL'de 32 bittir:

```term
$ gcc -O2 -Wall -Wextra -std=c11 tas.c -o tas
$ ./tas 2147483646 2147483647
INT_MAX=2147483647
yanlis=-1 dogru=2147483646
```

Yanlış formül `-1` üretti: `lo + hi` toplamı `-3`'e sarmıştır, `-3 / 2` ise `-1`'dir. Doğru formül `2147483646` verdi. `-O2` ile derlenen bu programda gördüğümüz `-1` tipik bir sonuçtur, bir garanti değil. `-fsanitize=undefined` ile derlediğimizde UBSan, `signed integer overflow` (işaretli tamsayı taşması) uyarısı verir ve taşmanın yerini gösterir. Bu uyarı, kodunda taşma olup olmadığını bulmanın en hızlı yoludur.

İşaretsiz tür kullanmak bu sorunu çözmez. `size_t` ile `lo + hi` sarar, ama işaretsiz taşma tanımlıdır: sonuç yine de yanlış bir orta değerdir. Doğru yazım `lo + (hi - lo) / 2`'dir. `hi - lo` taşmaz, çünkü `0 <= hi - lo <= n` ve `n` dizinin uzunluğudur; toplam ise her zaman bir dizi konumudur. Bölüm 5'te bu hatanın tarihçesini gördük; burada hatanın nedenini kendimiz ürettik.

::: dikkat
Platform notu: Windows'ta `long` 4 bayttır (LLP64 modeli); Linux'ta 64-bit mimaride 8 bayttır. Bu yüzden 64-bit indeks ya da toplam gerektiğinde `long` yerine `long long` ya da `size_t` kullan. Burada kullandığımız tüm tamsayılar 32-bit `int` ya da `size_t`'dir ve sonuçlar iki platformda da aynıdır.
:::

## 14.4 Alt sınır, üst sınır ve eşit aralık

İkili aramanın en kullanışlı genellemesi iki sınırdır. **Alt sınır (lower bound)**, `x`'ten küçük olmayan ilk konumdur: `a[i] >= x` olan ilk `i`. **Üst sınır (upper bound)**, `x`'ten büyük olan ilk konumdur: `a[i] > x` olan ilk `i`. Bu iki sınır birlikte **eşit aralığı (equal range)** `[alt, ust)` verir. Aralık boşsa `x` dizide yoktur ve `alt`, `x`'in ekleneceği konumdur. Aralığın uzunluğu `ust - alt`, `x`'in kaç kez geçtiğini verir.

Şekil 14.2 aynı diziyi gösterir: `[1, 2, 2, 2, 3, 5, 5, 8]`. Değer 2 üç kez geçer; alt sınır 1, üst sınır 4 ve eşit aralık `[1, 4)`'tür.

![Şekil 14.2: Alt sınır (1), üst sınır (4) ve x = 2 için eşit aralık [1, 4). Sayı, aralığın uzunluğudur: 3.](gorseller/b14_sinir.png)

İki sınırın kodu, 14.2'deki kanıtın küçük bir değişikliğidir. Tek fark koşulda: alt sınır `a[orta] < x` ile, üst sınır `a[orta] <= x` ile yönlendirilir. Aşağıdaki program iki sınırı, eşit aralığı ve sayıyı dört sorgu için hesaplar. Dizi 8 elemanlı; sorgular `2` (üç kez var), `4` (yok, ekleme konumu 5), `9` (yok, sona eklenir), `0` (yok, başa eklenir):

```c
#include <stddef.h>
#include <stdio.h>

typedef struct {
    size_t ilk;
    size_t son;
} aralik;

/* Alt sınır: a[i] >= x olan ilk i (yoksa n). */
size_t alt_sinir(const int *a, size_t n, int x) {
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        if (a[orta] < x)
            lo = orta + 1;
        else
            hi = orta;
    }
    return lo;
}

/* Üst sınır: a[i] > x olan ilk i (yoksa n). */
size_t ust_sinir(const int *a, size_t n, int x) {
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        if (a[orta] <= x)
            lo = orta + 1;
        else
            hi = orta;
    }
    return lo;
}

/* x'in eşit aralığı [ilk, son): x yoksa ilk == son. */
aralik esit_aralik(const int *a, size_t n, int x) {
    aralik r = {alt_sinir(a, n, x), ust_sinir(a, n, x)};
    return r;
}
```

Programın `main` fonksiyonu, sorguları yazdırır:

```c
int main(void) {
    int a[] = {1, 2, 2, 2, 3, 5, 5, 8};
    size_t n = sizeof a / sizeof a[0];
    int sorgu[] = {2, 4, 9, 0};
    printf("%3s %4s %4s %5s\n", "x", "alt", "ust", "sayi");
    for (int k = 0; k < 4; k++) {
        aralik r = esit_aralik(a, n, sorgu[k]);
        printf("%3d %4zu %4zu %5zu\n", sorgu[k], r.ilk, r.son,
               r.son - r.ilk);
    }
    return 0;
}
```

Programın çıktısı şöyle:

```term
$ gcc -O2 -Wall -Wextra -std=c11 alt_ust.c -o alt_ust
$ ./alt_ust
  x  alt  ust  sayi
  2    1    4     3
  4    5    5     0
  9    8    8     0
  0    0    0     0
```

Değer 2 için `alt = 1`, `ust = 4` ve sayı `3`'tür. Değer 4 için `alt = ust = 5`: aralık boş ve 4, 5. konuma eklenirdi (`a[5] = 5`). Değer 9 ve 0 için de aynı mantık geçerli. Eşit aralık, bu nedenle sadece "var mı" sorusunun değil, "kaç tane ve nereye" sorusunun da cevabıdır.

Dikkat edilecek bir nokta: C standart kütüphanesinde `lower_bound` yoktur. `bsearch` yalnızca eşleşen bir eleman döndürür ve hangisini döndüreceğini belirtmez (14.14'te göreceğiz). Bu yüzden tekrarlı dizilerde alt ve üst sınırı kendimiz yazmak gerekir.

## 14.5 Off-by-one kataloğu ve sonsuz döngü tuzakları

İkili arama hataları çoğunlukla "bir fazla" ya da "bir eksik" tipindedir. Bu hatalar derlenir, uyarı vermez ve yanlış sonuç üretebilir. Aşağıdaki tablo, sık görülen hataları ve düzeltmelerini toplar:

| Hata | Belirti | Düzeltme |
|---|---|---|
| `hi = n - 1` ile `lo < hi` | Son eleman hiç denenmez | Yarı açık `hi = n` ya da `lo <= hi` |
| `lo = orta` (`orta + 1` yerine) | `lo` ve `hi` komşuyken ilerlemez, sonsuz döngü | `lo = orta + 1` |
| `hi = orta - 1` (yarı açıkta) | Cevap olabilecek `orta` atlanır | Yarı açıkta `hi = orta` |
| `(lo + hi) / 2` | Büyük dizide taşma (UB) | `lo + (hi - lo) / 2` |
| `n = 0` ile `n - 1` | İşaretsiz tipte `n - 1` sarar; sınır dışı erişim | Boş dizi için erken dönüş |
| Bulunamayınca `lo` döndürmek | Bulunmuş gibi davranır | Sonucu `a[lo] == x` ile doğrula |

İlk iki hatayı programla gösterelim. Aşağıdaki iki fonksiyon, yanlış sürümlerdir. İkincisi gerçek bir programda sonsuza kadar döner, bu yüzden tur sayısına bir sınır koyduk ve sınırı aşınca `-2` döndürdük:

```c
#include <stdio.h>

/* Hata 1: hi = n - 1 ve lo < hi. Son aralık hiç denenmez. */
int hatali_son(const int *a, int n, int x) {
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        int orta = (lo + hi) / 2;
        if (a[orta] < x)
            lo = orta + 1;
        else if (a[orta] > x)
            hi = orta - 1;
        else
            return orta;
    }
    return -1;
}

/* Hata 2: lo = orta (orta + 1 yerine). Komşuyken ilerlemez. */
int hatali_dongu(const int *a, int n, int x, int tur_siniri) {
    int lo = 0, hi = n - 1, tur = 0;
    while (lo < hi) {
        if (++tur > tur_siniri)
            return -2;           /* sonsuz döngü, sınırda kestik */
        int orta = (lo + hi) / 2;
        if (a[orta] < x)
            lo = orta;
        else
            hi = orta - 1;
    }
    return lo;
}
```

Bu iki fonksiyonu çağıran `main` şöyle:

```c
int main(void) {
    int a[] = {1, 3, 5};
    int b[] = {1, 3};
    printf("hata 1, x=5: %d (dogru: 2)\n", hatali_son(a, 3, 5));
    int r = hatali_dongu(b, 2, 2, 20);
    if (r == -2)
        printf("hata 2, x=2: 20 turda durduruldu (sonsuz)\n");
    else
        printf("hata 2, x=2: %d\n", r);
    return 0;
}
```

Programın çıktısı:

```term
$ gcc -O2 -Wall -Wextra -std=c11 hatalar.c -o hatalar
$ ./hatalar
hata 1, x=5: -1 (dogru: 2)
hata 2, x=2: 20 turda durduruldu (sonsuz)
```

Birinci hata, `{1, 3, 5}` dizisinde `5`'i bulamadı, çünkü `lo < hi` döngüsü `lo == hi == 2` olduğunda durur ve `a[2]` hiç kontrol edilmez. İkinci hata, `{1, 3}` dizisinde `2` için ilerlemedi: `lo = 0`, `hi = 1` iken `orta = 0` ve `a[0] = 1 < 2` olduğu için `lo = orta = 0` kalır. Aralık hiç daralmaz. Bu yüzden her ikili arama döngüsünde şu iki soruyu sorman gerekir: "her turda aralık gerçekten küçülüyor mu?" ve "`lo` ya da `hi` cevabı dışlayarak mı değişiyor?"

::: ipucu
Bir ikili arama yazdığında bu üç satırı tek tek kontrol et: başlangıç aralığı (`hi` yarı açık mı, kapalı mı?), döngü koşulu (`<` mi, `<=` mi?) ve her dalın güncellemesi (`orta` dahil mi, hariç mi?). Bu üç karar birbirine bağlıdır; birini değiştirirsen diğer ikisini de değiştirmen gerekir.
:::

## 14.6 Monoton yüklem: "ilk true" kalıbı

Şimdiye kadar aranan şey bir değerdi. İkili aramanın asıl gücü ise daha geneldir: aranan şey, **monoton bir yüklemle** tanımlanabiliyorsa, ikili arama çalışır. Yüklem `p(i)` bir sayı dizisi üzerinde tanımlı bir koşuldur ve monoton demek, `p`'nin bir kez `T` olduktan sonra hep `T` kalması demektir. Bu, `F F F ... F T T T ... T` biçimindeki bir dizidir. Amaç, ilk `T`'nin konumunu bulmaktır.

Bu kalıp, alt sınır aramasının genellemesidir. Sıralı bir `a` dizisinde `p(i) = (a[i] >= x)` yazarsan, ilk `T` tam olarak alt sınırdır. Yani 14.2'deki değişmez, herhangi bir monoton yüklem için de geçerlidir. Mülakatta zorluk çoğu zaman sıralı dizi değildir; asıl beceri, problemi bu biçimdeki bir yükleme çevirebilmektir.

Algoritma, 14.2'deki döngünün aynısıdır. `p(orta)` doğruysa ilk `T` ya `orta`'dadır ya da solundadır: `hi = orta`. Yanlışsa ilk `T` sağdadır: `lo = orta + 1`. Hiç `T` yoksa döngü `hi`'de biter; bu nedenle `hi` "bulunamadı" sonucunun da doğru değeridir.

Aşağıdaki kod, bu kalıbı bir yüklemin herhangi bir fonksiyonu olacak şekilde yazar. Kodun ikinci yarısı, rastgele eşikli yüklemlerle doğrusal taramayı karşılaştırır:

```python
import random


def ilk_dogru(lo, hi, p):
    """[lo, hi) üzerinde p monoton (F...F T...T) olsun.
    İlk T'nin indeksini döndürür; hiç T yoksa hi."""
    while lo < hi:
        orta = lo + (hi - lo) // 2
        if p(orta):
            hi = orta
        else:
            lo = orta + 1
    return lo


def dogrusal_ilk(lo, hi, p):
    """Karşılaştırma için doğrusal tarama."""
    for i in range(lo, hi):
        if p(i):
            return i
    return hi

```

Aynı dosyanın ana bloğu, bir yüklemi çalıştırır ve sonucu karşılaştırır:

```python
if __name__ == "__main__":
    random.seed(42)
    p = lambda i: i * i >= 50
    dizi = "".join("T" if p(i) else "F" for i in range(10))
    print("p(0..9):", dizi)
    print("ilk T (i*i >= 50):", ilk_dogru(0, 100, p))
    hatali = 0
    for _ in range(2000):
        n = random.randint(0, 200)
        esik = random.randint(0, n)
        q = lambda i, e=esik: i >= e
        if ilk_dogru(0, n, q) != dogrusal_ilk(0, n, q):
            hatali += 1
    print("2000 rastgele test, hatali:", hatali)
```

Programın çıktısı şöyle:

```term
$ python ilk_true.py
p(0..9): FFFFFFFFTT
ilk T (i*i >= 50): 8
2000 rastgele test, hatali: 0
```

Yüklem `p(i) = i*i >= 50` için ilk `T` 8. konumdadır, çünkü `7*7 = 49 < 50` ve `8*8 = 64 >= 50`. Şekil 14.3 bu dizinin yapısını gösterir.

![Şekil 14.3: Monoton yüklem. p(i) = (i*i >= 50) için F ve T dizisi; tek bir geçiş noktası vardır ve ilk T 8. konumdadır.](gorseller/b14_monoton.png)

Yüklemin monoton olduğunu kanıtlamak sizin sorumluluğunuzdur. Algoritma, dizinin monoton olup olmadığını kontrol etmez. Monoton olmayan bir yüklemde (ör. `i % 2 == 0`) sonuç anlamsızdır; bu tür bir hatayı çalışma anında fark etmek zordur, çünkü algoritma yine bir sayı döndürür. Bu yüzden yüklemi yazarken "bir kez doğru olunca sonrasında hep doğru mu?" sorusunu açıkça cevapla.

## 14.7 Cevap üzerinde ikili arama

Monoton yüklemin en güçlü kullanımı, aranan şeyin bir dizi elemanı olmadığı durumlardır. Bunun yerine bir **karar problemi** sorarsın: "şu değer yeterli mi?". Bu soru, değer büyüdükçe ya hep `T` ya da hep `F` kalan bir yüklem tanımlar. Böylece en küçük yeterli değeri, yani cevabı, ikili aramayla bulabilirsin. Buna **cevap üzerinde ikili arama (binary search on the answer)** denir.

Bu kalıbın iki gereksinimi vardır. Birincisi, yüklem monoton olmalıdır: değer arttıkça karar değişmemeli ya da yalnızca bir kez değişmelidir. İkincisi, cevabın bulunabileceği bir aralık belli olmalıdır. Bu aralığı genellikle iki uçtan bulursun: bir uç, yanıtın alabileceği en küçük değerdir; diğeri, kesin olarak yeterli olan bir değerdir.

Önce tam sayılar için bir örnek alalım: `n`'in tam karekökü, yani en büyük `k` ile `k*k <= n`. Yüklem `p(k) = (k*k > n)` yazılabilir. Bu yüklem `k` arttıkça `F`'den `T`'ye bir kez değişir; ilk `T`'nin bir eksiği, cevaptır. Bu yüklem 14.6'daki `ilk_dogru` ile de çözülebilir. Burada aralığı `[0, n + 1)` olarak aldık ve sonucu bir eksik okuduk: `k*k > n` olan ilk `k`, `floor(sqrt(n)) + 1`'dir.

```python
import math


def tam_karekok(n):
    """floor(sqrt(n)): en büyük k, k*k <= n. Yüklem: k*k > n."""
    lo, hi = 0, n + 1
    while lo < hi:
        orta = lo + (hi - lo) // 2
        if orta * orta <= n:
            lo = orta + 1
        else:
            hi = orta
    return lo - 1
```

Kayan nokta sayılarında aynı fikir, sabit sayıda yarılama olarak uygulanır. Tam sonuç yerine yeterli bir hassasiyete ulaşmak yeterlidir. Burada 60 tur kullandık; her tur aralığı yarıya indirir:

```python
def kok_ikili(c, tur=60):
    """c >= 1 için karekök: sabit sayıda yarılama."""
    lo, hi = 0.0, max(1.0, c)
    for _ in range(tur):
        orta = (lo + hi) / 2
        if orta * orta < c:
            lo = orta
        else:
            hi = orta
    return lo
```

Aşağıdaki ana blok, iki yaklaşımı karşılaştırır. Tam karekök için `math.isqrt` (Python 3.8 ve sonrası) ile 0'dan 9999'a kadar her değeri sınadık; kayan nokta için `math.sqrt(2)` ile fark ölçtük:

```python
if __name__ == "__main__":
    for n in range(10000):
        assert tam_karekok(n) == math.isqrt(n), n
    print("tam_karekok: 0..9999 icin math.isqrt ile ayni")
    print("kok_ikili(2):", repr(kok_ikili(2.0)))
    print("math.sqrt(2):", repr(math.sqrt(2.0)))
    print("fark:", abs(kok_ikili(2.0) - math.sqrt(2.0)))
```

Programın çıktısı:

```term
$ python cevap.py
tam_karekok: 0..9999 icin math.isqrt ile ayni
kok_ikili(2): 1.414213562373095
math.sqrt(2): 1.4142135623730951
fark: 2.220446049250313e-16
```

Tam karekök için sonuç tüm değerlerde `math.isqrt` ile aynı çıktı. Kayan nokta sonucu ise `1.414213562373095` çıktı ve gerçek değerden yalnızca bir son bit (1 ulp, yaklaşık `2,2 * 10^-16`) uzak kaldı. Bu, sabit iterasyonlu ikili aramanın bir özelliğidir: sonuç bir aralık içinde kalır ve son haneler kayan nokta gösteriminin kesinliğine bağlıdır. Karşılaştırmada `==` yerine bir tolerans kullan. Tam sayılar için ise `math.isqrt` doğru araçtır.

Şekil 14.4, bu kalıbın gerçek bir problemi nasıl çözdüğünü gösterir. Ağırlıkları `1, 2, ..., 10` olan 10 paketi, sırayla ve en fazla `D = 5` günde taşımak istiyoruz. Her gün en fazla `C` kiloluk paket taşınabilir. Kapasite `C` arttıkça gereken gün sayısı azalmaz; bu nedenle "`C` ile `D` güne sığar mı?" yüklemi monotondur. Bu problemi Örnek 3'te tam olarak çözeceğiz.

![Şekil 14.4: Kapasiteye göre gerekli gün sayısı (paketler 1..10, sırayla taşıma). Gün sayısı kapasite arttıkça hiç artmaz; D = 5 çizgisini kesen ilk kapasite 15'tir.](gorseller/b14_cevap.png)

Cevap uzayında arama için iki uç belirlemek gerekir. Kapasite en az en ağır paketi taşıyabilmelidir (`max(w)`), en fazla tüm paketlerin toplamı kadar olabilir (`sum(w)`, tek günde biter). Bu iki uç, aralığı kanıtlanabilir biçimde sınırlar. Bu aralığın içinde yüklem `F...F T...T` biçimindedir ve ilk `T` aradığımız cevaptır.

## 14.8 Döndürülmüş sıralı dizi

Artan sıralı bir dizinin bir kısmını başa taşıyarak elde edilen diziye **döndürülmüş sıralı dizi** denir. Örneğin `[4, 5, 6, 7, 0, 1, 2]`, `[0, 1, 2, 4, 5, 6, 7]` dizisinin döndürülmüş hâlidir. Sıralılık bozulmuş görünse de yapı korunur: dizi tek bir "kırılma noktasına" sahiptir ve kırılma noktası minimumdur.

Bu yapıyı ikili arama için kullanmak mümkündür. Orta eleman `a[orta]`, `a[hi]` ile karşılaştırılır. `a[orta] > a[hi]` ise kırılma noktası `orta`'nın sağındadır, yani minimum `(orta, hi]` aralığında yer alır. `a[orta] < a[hi]` ise sağ taraf sıralıdır ve minimum `orta` dahil solda kalır. Böylece minimum her turda yarıya iner; bulduktan sonra aynı dizide sıralı bir ikili arama, minimumdan başlayan bir ofsetle yapılır.

Aşağıdaki program iki şeyi yapar: minimumun konumunu bulur ve bu konumu kullanarak `x`'i arar. Minimum bulma, bir adım sayacı tutar. Fonksiyonun tekrarlı dizilerdeki en kötü durumunu da ölçebilmek için eşitlik dalına (`a[orta] == a[hi]`) özellikle dikkat edin:

```c
#include <stddef.h>
#include <stdio.h>

/* Döndürülmüş sıralı dizinin minimum konumu (n >= 1).
   adim: döngü turu sayacı. Eşitlik dalı (hi--) tekrarlarda
   her turda bir eleman eler; bu en kötü durumu O(n) yapar. */
size_t min_konum(const int *a, size_t n, long *adim) {
    size_t lo = 0, hi = n - 1;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        (*adim)++;
        if (a[orta] > a[hi])
            lo = orta + 1;       /* minimum orta'nın sağında */
        else if (a[orta] < a[hi])
            hi = orta;           /* minimum orta dahil solda */
        else
            hi--;                /* a[orta] == a[hi]: karar yok */
    }
    return lo;
}

/* Farklı elemanlı döndürülmüş dizide x'in konumu, yoksa -1. */
long dondurulmus_ara(const int *a, size_t n, int x) {
    long adim = 0;
    size_t k = min_konum(a, n, &adim);
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        size_t gercek = (orta + k) % n;
        if (a[gercek] < x)
            lo = orta + 1;
        else if (a[gercek] > x)
            hi = orta;
        else
            return (long)gercek;
    }
    return -1;
}
```

Ana blok, farklı elemanlı bir dizi için sonuçları yazdırır; ardından tekrarlı bir dizi ailesinde en kötü durumu ölçer:

```c
int main(void) {
    int a[] = {4, 5, 6, 7, 0, 1, 2};
    size_t n = sizeof a / sizeof a[0];
    long adim = 0;
    size_t k = min_konum(a, n, &adim);
    printf("min konumu=%zu adim=%ld\n", k, adim);
    int sorgu[] = {0, 3, 6, 9};
    for (int i = 0; i < 4; i++)
        printf("x=%d -> %ld\n", sorgu[i],
               dondurulmus_ara(a, n, sorgu[i]));
    printf("tekrarli en kotu durum (min en solda, geri kalan 1):\n");
    for (size_t m = 8; m <= 64; m *= 2) {
        int b[64];
        b[0] = 0;
        for (size_t i = 1; i < m; i++)
            b[i] = 1;
        long t = 0;
        min_konum(b, m, &t);
        printf("  n=%2zu adim=%2ld\n", m, t);
    }
    return 0;
}
```

Programın çıktısı:

```term
$ gcc -O2 -Wall -Wextra -std=c11 dondurulmus.c -o dondurulmus
$ ./dondurulmus
min konumu=4 adim=3
x=0 -> 4
x=3 -> -1
x=6 -> 2
x=9 -> -1
tekrarli en kotu durum (min en solda, geri kalan 1):
  n= 8 adim= 7
  n=16 adim=15
  n=32 adim=31
  n=64 adim=63
```

Farklı elemanlı dizide minimum 4. konumda bulundu ve üç adım sürdü. Aramalar doğru konumları döndürdü: `0` 4. konumda, `6` 2. konumda; `3` ve `9` dizide yok. Tekrarlı dizide ise tablo çarpıcı bir sonuç veriyor. `[0, 1, 1, ..., 1]` dizisinde adım sayısı tam olarak `n - 1`'dir. Bunun nedeni eşitlik dalıdır: `a[orta] == a[hi]` iken minimum hangi tarafta olduğuna karar verilemez, bu yüzden tek bir eleman (`hi`) elenir. Her tur yalnızca bir eleman eler; `n` elemanlı dizide `n - 1` tur gerekir.

::: dikkat
Tekrarlar yalnızca süreyi değil **doğruluğu** da bozar. `{1, 1, 1, 3, 1}` dizisinde döndürme noktası 4. konumdaki `1`'dir (dizi `1, 1, 1, 1, 3` sırasının döndürülmüş hâli). Ama `min_konum` bir minimum bulur, döndürme noktasını değil: bu dizide `0` döndürür. `dondurulmus_ara` da diziyi 0. konumdan başlıyormuş gibi sıralı sanar ve `3`'ü aradığında `-1` döner, oysa `3` 3. konumdadır. Bunu WSL'de gcc 13.3 ile çalıştırarak gördük:
:::

```term
$ ./dondurulmus_test
min_konum=0 ara(3)=-1
```

Düzeltme fikri: eşitlik dalında `hi`'yi atmadan önce `a[hi - 1] > a[hi]` mi diye bak; öyleyse döndürme noktası `hi`'dir ve atılmamalıdır. Bu düzeltmeyi yazmak ve doğrulamak Ek Alıştırmalar'da senin işin.

Şekil 14.5, iki durumu yan yana gösterir. Soldaki panel döndürülmüş diziyi ve minimumu gösterir. Sağdaki panel, farklı elemanlarda en kötü adım sayısının `n = 8` ile `n = 1024` arasında tam olarak `log₂ n` olduğunu (3'ten 10'a), tekrarlı en kötü durumun ise `n - 1` olduğunu gösterir.

![Şekil 14.5: Solda döndürülmüş dizi ve minimum (4. indeks). Sağda, farklı elemanlarda en kötü adım sayısı log₂ n'e eşittir; tekrarlı en kötü durumda ise n - 1 adım.](gorseller/b14_dondurulmus.png)

Bu nedenle sıralı arama için verdiğimiz "O(log n)" garantisi, farklı elemanlar varsayımına dayanır. Tekrarlar olduğunda minimum bulma `O(n)`'e düşebilir. Bu, mülakatta sık sorulan bir tuzaktır ve Ek Alıştırmalar'da yeniden göreceğiz. `dondurulmus_ara` de yalnızca farklı elemanlar için tasarlanmıştır: tekrarlı bir dizide minimumun konumu bir rotasyon noktası olmayabilir.

## 14.9 İki boyutlu matris araması

Bir matris (ya da 2B tablo) üzerinde arama iki farklı varsayımla yapılabilir ve bu varsayımlar algoritmayı değiştirir.

**Durum A: satırlar ve sütunlar ayrı ayrı artan sıralıdır.** Bu durumda sağ üst köşeden başlayan bir yürüyüş, `O(m + n)` adımda sonuca ulaşır. Sağ üst köşe, satırın en büyüğü ve sütunun en küçüğüdür. Eğer bu köşedeki değer `x`'ten büyükse, o sütundaki diğer değerler (aşağıdakiler dahil) daha da büyük olur, sütun elenebilir. Eğer küçükse, o satırdaki diğer değerler (soldakiler) daha küçüktür, satır elenebilir. Her adım bir satır ya da bir sütun eler; bu yüzden en fazla `m + n` adım atılır.

**Durum B: her satır bir öncekinin bittiği yerden devam eder.** Yani bir satırın ilk elemanı, önceki satırın son elemanından büyüktür. Bu durumda matris, düz (tek boyutlu) bir sıralı dizi gibidir ve `m * n` uzunluklu tek bir ikili arama yeter. Satır-major depolamada `k`. eleman `m[k]` ile erişildiği için satır ve sütun hesabı gerekmez; `k` ile satır-sütun karşılığı, sütun sayısı `sut` olmak üzere `k / sut` ve `k % sut` olur.

Şekil 14.6, Durum A'da sağ üst köşeden yürüyüşü gösterir. Dizi 4 x 5'tir ve `x = 20` aranmaktadır; bu değer yoktur.

![Şekil 14.6: Durum A'da sağ üst köşeden yürüyüş (x = 20). Ziyaret sırası 1'den 5'e; her adım bir satır ya da sütunu eler.](gorseller/b14_matris.png)

Aşağıdaki program iki durumu da uygular. Durum A fonksiyonu `matris_ara1`, Durum B fonksiyonu `matris_ara2` adını taşır. Her ikisi de adım sayacı tutar ve sayaç, sonuçla birlikte yazdırılır:

```c
#include <stddef.h>
#include <stdio.h>

/* Satır ve sütunları artan sıralı matris. Sağ üst köşeden yürünür:
   her adımda bir satır ya da sütun elenir: en fazla sat+sut adım. */
int matris_ara1(const int *m, size_t sat, size_t sut, int x,
                long *adim) {
    if (sat == 0 || sut == 0)
        return 0;
    size_t i = 0, j = sut - 1;
    while (i < sat) {
        (*adim)++;
        int v = m[i * sut + j];
        if (v == x)
            return 1;
        if (v > x) {
            if (j == 0)
                break;
            j--;                 /* bu sütun x'ten büyük: sola */
        } else {
            i++;                 /* bu satır x'ten küçük: aşağı */
        }
    }
    return 0;
}

/* Satırlar birbirini izler: matris düz bir dizi gibi aranır. */
int matris_ara2(const int *m, size_t sat, size_t sut, int x,
                long *adim) {
    (void)sut;                   /* satır-major: indeks doğrudan */
    size_t lo = 0, hi = sat * sut;
    while (lo < hi) {
        (*adim)++;
        size_t orta = lo + (hi - lo) / 2;
        if (m[orta] < x)
            lo = orta + 1;
        else if (m[orta] > x)
            hi = orta;
        else
            return 1;
    }
    return 0;
}
```

Ana blok, her iki durumda birer sorgu dizisi çalıştırır:

```c
int main(void) {
    int a[4][5] = {
        {1, 4, 7, 11, 15},
        {2, 5, 8, 12, 19},
        {3, 6, 9, 16, 22},
        {10, 13, 14, 17, 24}};
    int sorgu[] = {5, 20, 1, 24, 0};
    for (int k = 0; k < 5; k++) {
        long adim = 0;
        int s = matris_ara1(&a[0][0], 4, 5, sorgu[k], &adim);
        printf("sirali x=%2d bulundu=%d adim=%ld\n",
               sorgu[k], s, adim);
    }
    int b[3][4] = {
        {1, 3, 5, 7},
        {10, 11, 16, 20},
        {23, 30, 34, 60}};
    int sorgu2[] = {34, 3, 35};
    for (int k = 0; k < 3; k++) {
        long adim = 0;
        int s = matris_ara2(&b[0][0], 3, 4, sorgu2[k], &adim);
        printf("duz    x=%2d bulundu=%d adim=%ld\n",
               sorgu2[k], s, adim);
    }
    return 0;
}
```

Programın çıktısı:

```term
$ gcc -O2 -Wall -Wextra -std=c11 matris.c -o matris
$ ./matris
sirali x= 5 bulundu=1 adim=5
sirali x=20 bulundu=0 adim=5
sirali x= 1 bulundu=1 adim=5
sirali x=24 bulundu=1 adim=4
sirali x= 0 bulundu=0 adim=5
duz    x=34 bulundu=1 adim=4
duz    x= 3 bulundu=1 adim=3
duz    x=35 bulundu=0 adim=4
```

Durum A'da `x = 20` için 5 adım atıldı; en fazla `m + n = 9` adım sınırının içinde. `x = 24`, matrisin sağ alt köşesindedir ve 4 adımda bulundu. Durum B'de `34` 4 adımda, `3` 3 adımda bulundu. Dikkat edin: Durum B'de `m * n = 12` elemanlık dizi için adım sayısı `log₂ 12`'ye yakındır. Matris bir tek boyuta indirgendiğinde, Durum A'nın yürüyüşü yerine ikili aramanın logaritmik garantisi geçerli olur.

Bu iki durumu ayırt etmek önemlidir. Durum B'nin yapısı yoksa (ör. satırlar birbirinden bağımsız sıralıysa), düz dizi olarak aramak yanlış sonuç verir. Durum A ise daha genel bir yapıdır ve düz diziye indirgenemez; bu yüzden yürüyüş gerekir.

## 14.10 Üstel arama ve sınırsız diziler

Bazen dizinin uzunluğunu bilmezsin. Bir ağ akışından okuduğun sıralı bir veri, bir log dosyasında sınırı bilinmeyen bir sıra ya da bir sonsuz dizi bu duruma girer. Ayrıca aranan değer çoğu zaman başa yakın olabilir. Bu durumlarda **üstel arama (exponential search, galloping)** kullanılır.

Fikir basittir. Önce `1, 2, 4, 8, ...` konumlarını sorgulayarak `x`'in bulunduğu bir sınır bul: `oku(sınır) >= x` olana kadar sınırı ikiye katla. Sonra `[sınır/2, sınır]` aralığında 14.2'deki ikili aramayı yap. Aranan konum `p` ise, sınır bulma aşaması `O(log p)` sorgu yapar ve ikili arama da `O(log p)` sorgu yapar. Toplam `O(log p)`'dir. Ayrıca `p` küçükse, sınır çok hızlı bulunur.

Aşağıdaki program, `oku(i) = 3 * i` ile tanımlanan sonsuz bir dizi üzerinde sorgu sayısını sayar. Karşılaştırma için, `n = 2^21` uzunluğu bilinen bir dizide ikili aramanın sorgu sayısını da ölçtük. Birinci kısım üstel aramanın mantığı, ikinci kısım yardımcı fonksiyonlar, üçüncü kısım ana blok:

```python
def ikili_say(n, x, sayac):
    """Bilinen n uzunluklu 3*i dizisinde x'in ilk konumu (ikili)."""
    lo, hi = 0, n
    while lo < hi:
        sayac[0] += 1
        orta = lo + (hi - lo) // 2
        if 3 * orta < x:
            lo = orta + 1
        else:
            hi = orta
    return lo


def ustel_ara(oku, x, sayac):
    """oku(i): sonsuz artan dizinin i. elemanı. x'in ilk konumu."""
    sinir = 1
    while oku(sinir, sayac) < x:
        sinir *= 2
    lo, hi = sinir // 2, sinir
    while lo < hi:
        orta = lo + (hi - lo) // 2
        if oku(orta, sayac) < x:
            lo = orta + 1
        else:
            hi = orta
    return lo


def sonsuz_dizi(i, sayac):
    """0, 3, 6, ... dizisinin i. elemanı; erişimler sayılır."""
    sayac[0] += 1
    return 3 * i
```

Ana blok, konum `p` için hem üstel hem de ikili aramayı çalıştırır ve sorgu sayılarını yazdırır:

```python
if __name__ == "__main__":
    print("konum | ustel adim | ikili adim (n = 2^21)")
    for p in [0, 1, 2, 10, 1000, 10**6]:
        x = 3 * p
        s1, s2 = [0], [0]
        k1 = ustel_ara(sonsuz_dizi, x, s1)
        k2 = ikili_say(2**21, x, s2)
        assert k1 == p == k2
        print("%5d | %10d | %10d" % (p, s1[0], s2[0]))
```

Programın çıktısı:

```term
$ python ustel.py
konum | ustel adim | ikili adim (n = 2^21)
    0 |          2 |         22
    1 |          2 |         22
    2 |          3 |         21
   10 |          8 |         21
 1000 |         20 |         21
1000000 |         40 |         21
```

Sonuçlar iki şeyi gösterir. Küçük `p` için üstel arama belirgin biçimde kazanır: `p = 0` için 2 sorgu, ikili arama ise 22 sorgu. `p = 1000` için 20 sorguya karşılık 21 sorgu. Ama `p = 10^6` için üstel arama 40 sorgu yapar; ikili arama, dizinin uzunluğu bilindiği için 21 sorguda biter. Bu nedenle üstel arama, yalnızca cevabın başa yakın olduğunu tahmin ettiğinde ya da uzunluğu bilmediğinde tercih edilir. İkili aramanın sorgu sayısının 21 ya da 22 çıkması da bir ayrıntıdır: son turda kalan aralığın uzunluğu, cevabın sol ya da sağ tarafta kalmasına göre değişir.

Şekil 14.7, üstel aramanın sorguladığı konumları gösterir. Mavi noktalar sınır bulma aşamasındadır: 1, 2, 4, ..., 1024. Yeşil noktalar ikili arama aşamasındadır ve aranan konum 1000'e yaklaşır.

![Şekil 14.7: Üstel arama, aranan konum 1000 için sorgulanan indeksler. Mavi: 1, 2, 4, ..., 1024 (sınır bulma); yeşil: ikili arama aşaması.](gorseller/b14_ustel.png)

Burada bir ayrıntı daha var. Sınır bulma döngüsü `oku(sınır) >= x` olduğunda durur. Bu durumda `sınır/2` konumu (bir önceki sınır) `x`'ten küçüktür; bu yüzden ikili aramanın alt ucu `sınır/2` seçilebilir. Üst uç `sınır` ise cevabın üst sınırıdır ve yarı açık aralıkta da doğru çalışır (14.3).

## 14.11 İnterpolasyon araması

İkili arama ortadaki elemana bakar. Ama sıralı bir dizi düzgün dağılmışsa, aranan değerin hangi konuma yakın olduğunu tahmin edebilirsin. Telefon rehberinde "Y" harfine bakarken sayfanın sonlarına açmak, bu sezginin günlük hayattaki karşılığıdır. **İnterpolasyon araması**, `x`'in konumunu değerler arasında doğrusal bir tahminle hesaplar:

`pos = lo + (x - a[lo]) * (hi - lo) / (a[hi] - a[lo])`

Bu formül, `a[lo]` ile `a[hi]` arasındaki doğrusal ilişkiyi kullanır. Değerler düzgün dağılmışsa tahmin çoğu zaman hedefe çok yakın olur. Literatürde, tekdüzen dağılımlı `n` elemanlı bir dizide ortalama aramanın `O(log log n)` olduğu gösterilmiştir (Perl, Itai ve Avni, 1978). Bu sonucu kendimiz kanıtlamadık; aşağıda yalnızca ölçtük. Öte yandan en kötü durumda, değerler çok düzensizse tahmin her seferinde bir elemanı eler ve arama `O(n)`'e düşer.

Bu iki durumu ölçmek için iki veri ailesi kullandık. Birincisi, `[0, 10^9)` aralığından rastgele seçilmiş ve sıralanmış tamsayılar (tekdüzen). İkincisi, `a[i] = 2^i` ile üssel büyüyen bir dizi (düzensiz). Tekdüzen veride her `n` için 2000 rastgele var olan değer, üssel veride ise tüm elemanlar sorgulandı ve ortalama sonda sayısı alındı. Sonda sayısı bir sayımdır; aynı tohum ve aynı Python sürümüyle herhangi bir makinede aynı sonucu verir. Süreyi ölçmedik.

Aşağıdaki program, iki aramayı ve veri üretimini tanımlar. Kod iki parçaya bölündü: önce fonksiyonlar, sonra ölçüm ana bloğu.

```python
import random


def ikili(a, x):
    lo, hi, say = 0, len(a) - 1, 0
    while lo <= hi:
        say += 1
        orta = (lo + hi) // 2
        if a[orta] == x:
            return orta, say
        if a[orta] < x:
            lo = orta + 1
        else:
            hi = orta - 1
    return -1, say


def enterpolasyon(a, x):
    lo, hi, say = 0, len(a) - 1, 0
    while lo <= hi and a[lo] <= x <= a[hi]:
        say += 1
        if a[hi] == a[lo]:
            pos = lo
        else:
            pos = lo + (x - a[lo]) * (hi - lo) // (a[hi] - a[lo])
        if a[pos] == x:
            return pos, say
        if a[pos] < x:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1, say


def ort_adim(a, sorgular, f):
    toplam = 0
    for x in sorgular:
        toplam += f(a, x)[1]
    return toplam / len(sorgular)
```

Ölçüm ana bloğu, iki veri ailesinde sonda sayısını ortalar:

```python
if __name__ == "__main__":
    random.seed(42)
    print("tekduzen veri (rastgele tamsayilar)")
    print("   n  ikili  enterp.")
    for n in [1000, 10000, 100000, 1000000]:
        a = sorted(random.sample(range(10**9), n))
        sorgular = [random.choice(a) for _ in range(2000)]
        print("%7d %6.2f %7.2f" % (n, ort_adim(a, sorgular, ikili),
              ort_adim(a, sorgular, enterpolasyon)))
    print("ussel veri (a[i] = 2^i)")
    print("   n  ikili  enterp.")
    for n in [10, 20, 40, 60]:
        a = [2**i for i in range(n)]
        sorgular = a
        print("%7d %6.2f %7.2f" % (n, ort_adim(a, sorgular, ikili),
              ort_adim(a, sorgular, enterpolasyon)))
```

Programın çıktısı:

```term
$ python olcum.py
tekduzen veri (rastgele tamsayilar)
   n  ikili  enterp.
   1000   8.98    2.94
  10000  12.35    3.85
 100000  15.72    3.91
1000000  18.94    4.24
ussel veri (a[i] = 2^i)
   n  ikili  enterp.
     10   2.90    3.70
     20   3.70    7.90
     40   4.58   17.02
     60   5.05   26.52
```

Tekdüzen veride ikili arama, `n` 1000'den 1 milyona çıktığında ortalama sonda sayısını 8,98'den 18,94'e çıkardı; bu, `log₂ n`'nin doğal büyümesidir. İnterpolasyon ise aynı aralıkta 2,94'ten 4,24'e çıktı; büyüme çok yavaş. Üssel veride tablo tersine döner. `n = 60` için interpolasyon 26,52 sorgu yaptı, ikili arama 5,05. Üssel veride `n`'in 60 olması, interpolasyonun doğrusal büyümesini belirgin kılar. Küçük `n = 10`'da ise interpolasyon (3,70) ikili aramadan (2,90) daha fazla sorgu yaptı; yani "interpolasyon her zaman daha iyidir" demek yanlış.

Şekil 14.8, bu ölçümü iki panelde gösterir. Sol panelde tekdüzen veride `n` log ölçekte; sağ panelde üssel veride `n` 10'dan 60'a.

![Şekil 14.8: Ortalama sonda sayısı. Solda tekdüzen veri: interpolasyon (kırmızı) çok daha az sorgu yapar. Sağda üssel veri: interpolasyon doğrusal büyür ve ikili aramayı geçer.](gorseller/b14_olcum.png)

Uygulamada iki uyarı var. Birincisi, C'de `(x - a[lo]) * (hi - lo)` çarpımı 32-bit `int` ile taşabilir; hesabı 64-bit (`long long`) ile yap ve `a[hi] == a[lo]` durumunda sıfıra bölmeyi engelle. Python'da tamsayılar sınırsız olduğu için bu sorun yoktur. İkincisi, tahmin dağılıma bağlıdır; düzensiz veride en kötü durum `O(n)` olabilir. Gerçek bir sistemde bu yüzden adım sayısına bir üst sınır koyup sınır aşıldığında ikili aramaya dönmek güvenli bir tasarımdır. Bu tasarımın doğruluğu, dağılımın ne olduğunu bilmekten gelir; bu bir ölçüm sorusudur.

## 14.12 Ternary search (kısaca)

Bazen aranan şey bir fonksiyonun **tek tepeli (unimodal)** olduğu bir noktadır: önce artar, sonra azalır (ya da tersi). Böyle bir fonksiyonun maksimumunu bulmak için **ternary search** kullanılır. Aralığı üçe böler, iki iç noktayı değerlendirir ve değeri daha kötü olan dış üçte birini atarsın.

Bu yöntemin maliyeti, her adımda iki fonksiyon değerlendirmesi ve aralığın `2/3`'ünü tutmasıdır. Bu, `log_{3/2} n ≈ 1,71 log₂ n` adım ve adım başına iki değerlendirme, yani toplam yaklaşık `3,4 log₂ n` değerlendirme eder. Altın oran (golden section) yöntemi, iç noktalardan birini yeniden kullanarak adım başına yalnızca bir değerlendirme yapar ve toplamı yaklaşık `1,44 log₂ n` yapar. Fonksiyonun türevi (ya da ardışık farkı) hesaplanabiliyorsa, türevin sıfır olduğu noktayı ikili aramayla bulmak genellikle daha iyidir. Düzlükler (aynı değere sahip aralıklar) varsa tek tepe varsayımı bozulur ve yöntem yanlış sonuç verebilir.

## 14.13 Arama yapılarını karşılaştırmak: karar tablosu

Hangi arama yapısını kullanacağın, neyi sorguladığına ve veriyi nasıl değiştirdiğine bağlıdır. Aşağıdaki tablo, bu bölüme kadar gördüğümüz üç yapıyı yan yana koyar:

| Yapı | Arama (ortalama) | Arama (en kötü) | Ekleme ve silme | Sıralı sorgu (aralık, en yakın) | Not |
|---|---|---|---|---|---|
| Sıralı dizi + ikili arama | `O(log n)` | `O(log n)` | `O(n)` | Evet: alt/üst sınır, aralık | Kompakt bellek, ardışık erişim |
| Hash tablosu (Bölüm 9) | `O(1)` | `O(n)` | `O(1)` ortalama | Hayır | Sıra bilgisi yok; tekrarlı anahtarlarda ve kötü hash'te `O(n)` |
| Dengeli BST / AVL (Bölüm 10) | `O(log n)` | `O(log n)` | `O(log n)` | Evet: sıralı gezinme | İşaretçi ek yükü; dengesiz BST'de en kötü `O(n)` |

Bu tabloya göre karar vermek için üç soru sor. Veri sık değişiyor mu? Sıralı sorgu (bir aralıktaki tüm değerler, en yakın değer) gerekiyor mu? Anahtarlar tekrarlı ya da saldırgan girdi olabilir mi? Veri neredeyse hiç değişmiyor ve yalnızca okunuyorsa, sıralı dizi hem en az bellekle hem de önbellek dostu erişimle genellikle en iyi seçimdir. Sık ekleme ve silme gerekiyorsa, `O(n)` ekleme maliyeti sıralı diziyi pahalı yapar; bu durumda dengeli ağaç ya da (sadece eşitlik gerekiyorsa) hash tablosu düşünülür. Hash tablosunun ortalama `O(1)`'i, Bölüm 9 ve Bölüm 12.11'de gördüğümüz hash flooding saldırısı nedeniyle garanti değildir.

Diskteki veritabanı indekslerinin temelinde ise B-ağaçları vardır; bunlar, okuma sayısını azaltmak için dallanma faktörü büyük tutulan ağaçlardır. Bu kitapta B-ağaçlarını derinlemesine işlemiyoruz.

## 14.14 Gerçek dünyada aramalar

Bu bölümdeki fikirler, günlük kullandığın araçların içinde de çalışır. Üç örneğe bakalım ve yalnızca doğrulayabildiklerimizi yazalım.

**`git bisect`.** Bir hatanın hangi commit'te girdiğini bulmak için Git, commit geçmişi üzerinde ikili arama yapar (Bölüm 6'da hata daraltmayı gördük). Yüklem "bu commit kötü mü?"dür ve "bir noktadan sonra hep kötü" varsayımına dayanır. Deneyde 100 commit'lik bir geçmiş kurduk: ilk 60 commit'te test geçiyor, 61. ve sonrasında kalıyor. Git'i test betiğiyle çalıştırdığımızda, bisection satırları ve sonuç şöyle oldu:

```term
$ git bisect run /tmp/bisect_test.sh
Bisecting: 24 revisions left to test after this (roughly 5 steps)
Bisecting: 12 revisions left to test after this (roughly 4 steps)
Bisecting: 5 revisions left to test after this (roughly 3 steps)
Bisecting: 2 revisions left to test after this (roughly 2 steps)
Bisecting: 0 revisions left to test after this (roughly 1 step)
a025cc69cb5303c0613df08aaa7a22847b9c64c1 is the first bad commit
```

Bu koşuda test 7 kez çalıştı; `ceil(log₂ 100) = 7`. Commit hash'leri her koşuda değişir, ama sonuç her zaman doğru commit'tir (c61). Yüklem monoton değilse (ör. bir commit'te test rastgele geçip kalıyorsa, "flaky test") `git bisect` yanlış commit'i gösterebilir. Bu yüzden bisection'dan önce testin kararlı olduğunu doğrula.

**C `bsearch`.** Standart kütüphanedeki `bsearch` (`<stdlib.h>`), sıralı bir dizide anahtarla eşleşen bir öğenin işaretçisini ya da bulunamazsa `NULL`'u döndürür. Karşılaştırma fonksiyonunu sen verirsin. Ancak eşleşen birden çok öğe varsa hangisinin döndüreceği standartta belirtilmez. Doğrulama için WSL'de (Ubuntu 24.04, glibc 2.39) `{1, 2, 2, 2, 3}` dizisinde `2` aradık ve 2. indeks döndü; alt sınır olan 1. indeks değildi. Bu yüzden alt sınır gerektiğinde 14.4'teki kendi fonksiyonunu kullan.

**C++ `std::lower_bound` ve `std::upper_bound`.** Bunlar `<algorithm>` içinde, sıralı aralıklar üzerinde alt ve üst sınırı döndürür. `{1, 2, 2, 2, 3}` dizisinde `2` için `lower_bound` 1, `upper_bound` 4 döndürdü (g++ 13.3, `-std=c++17`). Yani 14.4'teki iki fonksiyonun C++ karşılığıdır.

**Java `Arrays.binarySearch`.** JDK 17 ile doğruladık. Anahtar bulunursa eşleşen bir indeks döner (ilk olduğu garanti değildir; `{1, 2, 2, 2, 3}` için `2` döndü). Bulunamazsa dönüş değeri `-(ekleme noktası) - 1`'dir: `{1, 3, 5, 7}` için `4` aranınca `-3` döndü (ekleme noktası 2), `0` için `-1`, `8` için `-5`. Bu kuralı çözerken eksi bir eksik yazmak sık görülen bir hatadır.

**Python `bisect`.** `bisect_left` ve `bisect_right`, Bölüm 5 ve Bölüm 12'de gördüğümüz modüldür. Burada yalnızca atıf yapıyoruz; Kod Okuma'da kaynağına bir kez daha bakacağız.

En önemli ders şudur: kütüphanedeki hazır bir arama fonksiyonu kullanırken, döndürdüğü değerin ne anlama geldiğini (ilk mi, herhangi biri mi, bulunamazsa ne döner?) belgeden doğrula. Bu sözleşme ayrıntıları, en çok hata üreten yerlerdir.

## Çözümlü Örnekler

Bu bölümdeki dört örnek ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz. Doğrulama adımında mutlaka elle iz sürme tablosu olacak; tablodaki değerler, örnekte verilen kodun gerçek çalışmasından alınmıştır.

### Örnek 1 (★): Sıralı dizide ilk ve son konum

**Problem:** Artan sıralı bir `a` dizisi ve bir `x` değeri verildiğinde, `x`'in ilk ve son konumunu bul. `x` dizide yoksa `(-1, -1)` döndür. Örneğin `[5, 7, 7, 8, 8, 10]` dizisinde `8` için cevap `(3, 4)`'tür.

**Adım 1 — Anla.** Girdi sıralı bir dizi ve bir değerdir; çıktı iki konumdur. Kenar durumları: `x` hiç yok, dizi boş, dizinin tamamı `x` ile dolu.

**Adım 2 — Örnekle.** `[5, 7, 7, 8, 8, 10]` dizisi için `8` 3. ve 4. konumlarda geçer. `6` ise dizide yoktur, çünkü `7`'den sonra gelen `8` vardır ve `6` hiç görünmez.

**Adım 3 — Kaba çöz.** Diziyi baştan sona tara; ilk eşleşmede ilk konumu al, son eşleşmeyi ayrıca tut. Bu doğrudur ama sıralılığı hiç kullanmaz; `O(n)` iş yapar.

**Adım 4 — Örüntü.** Sıralılık, ilk ve son konumun bir alt ve üst sınırla ifade edilebileceğini söyler. 14.4'te gördük: `alt = a[i] >= x` olan ilk `i` ve `ust = a[i] > x` olan ilk `i`. Eşleşme varsa ilk konum `alt`, son konum `ust - 1`'dir. Aralık boşsa (`alt == ust`), `x` yoktur.

**Adım 5 — İyileştir.** Bu iki sınırı iki ikili aramayla bulabiliriz. Toplam maliyet `O(log n)`'dir. Boş aralık kontrolünü unutmamak gerekir, çünkü `ust - 1` değeri o durumda geçersizdir.

```c
#include <stddef.h>
#include <stdio.h>

/* Alt sınır: a[i] >= x olan ilk i (yoksa n). */
size_t alt_sinir(const int *a, size_t n, int x) {
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        if (a[orta] < x)
            lo = orta + 1;
        else
            hi = orta;
    }
    return lo;
}

/* Üst sınır: a[i] > x olan ilk i (yoksa n). */
size_t ust_sinir(const int *a, size_t n, int x) {
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        if (a[orta] <= x)
            lo = orta + 1;
        else
            hi = orta;
    }
    return lo;
}

/* x'in ilk ve son konumu. Bulunamazsa (-1, -1). */
void ilk_son(const int *a, size_t n, int x, long *ilk, long *son) {
    size_t l = alt_sinir(a, n, x);
    size_t u = ust_sinir(a, n, x);
    if (l == u) {
        *ilk = -1;
        *son = -1;
    } else {
        *ilk = (long)l;
        *son = (long)u - 1;
    }
}
```

Ana fonksiyon, dört sorguyu çalıştırır:

```c
int main(void) {
    int a[] = {5, 7, 7, 8, 8, 10};
    size_t n = sizeof a / sizeof a[0];
    int sorgu[] = {8, 7, 6, 11};
    for (int k = 0; k < 4; k++) {
        long ilk, son;
        ilk_son(a, n, sorgu[k], &ilk, &son);
        printf("x=%2d ilk=%2ld son=%2ld\n", sorgu[k], ilk, son);
    }
    return 0;
}
```

**Adım 6 — Doğrula.** `x = 8` için iki sınır fonksiyonunun her turunu, sırasıyla tabloya yazdık:

| Adım | Fonksiyon | lo | hi | orta | a[orta] | Karar |
|---|---|---|---|---|---|---|
| 1 | `alt_sinir` | 0 | 6 | 3 | 8 | `8 < 8` yanlış, `hi = 3` |
| 2 | `alt_sinir` | 0 | 3 | 1 | 7 | `7 < 8` doğru, `lo = 2` |
| 3 | `alt_sinir` | 2 | 3 | 2 | 7 | `7 < 8` doğru, `lo = 3` |
| 4 | `ust_sinir` | 0 | 6 | 3 | 8 | `8 <= 8` doğru, `lo = 4` |
| 5 | `ust_sinir` | 4 | 6 | 5 | 10 | `10 <= 8` yanlış, `hi = 5` |
| 6 | `ust_sinir` | 4 | 5 | 4 | 8 | `8 <= 8` doğru, `lo = 5` |

Sonuç: `alt = 3`, `ust = 5`, dolayısıyla `ilk = 3`, `son = ust - 1 = 4`. Program `x = 8` için `ilk= 3 son= 4` çıktı. `x = 6` için alt ve üst sınır 1'de buluştu (`alt = ust = 1`), yani aralık boştur ve program `-1 -1` döndürdü.

**Bunu AI'sız yazabilir misin?** Bu örnekte `x`'ten küçük en büyük değerin konumunu (önceki eleman) bulmak istiyoruz. Bu konumu, `alt` sınırıyla nasıl ifade edersin? Ve `alt == 0` olduğunda neden özel bir durum vardır?

### Örnek 2 (★★): Döndürülmüş dizi kaç kez döndürüldü?

**Problem:** Artan sıralı, farklı elemanlı bir dizi sağa doğru bir miktar döndürülmüş. Örneğin `[9, 12, 15, 18, 22, 3, 5, 7]` dizisi, sıralı `[3, 5, 7, 9, 12, 15, 18, 22]` dizisinin sağa doğru 5 konum döndürülmüş hâlidir. Döndürme miktarını, yani dizinin sıralı başlangıcının kaçıncı konumda olduğunu bul. Bu dizi için cevap `5`'tir ve bu, minimum elemanın (`3`) konumudur.

**Adım 1 — Anla.** Girdi farklı elemanlı, döndürülmüş sıralı bir dizidir; çıktı, minimumun konumudur. Dizi sıralı ise cevap `0`'dır.

**Adım 2 — Örnekle.** `[9, 12, 15, 18, 22, 3, 5, 7]` dizisinde minimum `3`'tür ve 5. konumdadır. Dizi sıralı olsaydı minimum 0. konumda olurdu.

**Adım 3 — Kaba çöz.** Her elemanı tara, minimumu bul: `O(n)`. Doğru, ama dizi döndürülmüş sıralı olduğu için bunu daha az işle yapabiliriz.

**Adım 4 — Örüntü.** 14.8'de gördük: orta eleman `a[orta]`, sağdaki `a[hi]` ile karşılaştırılırsa, `a[orta] > a[hi]` ise minimum orta'nın sağındadır; değilse minimum orta dahil soldadır.

**Adım 5 — İyileştir.** Bu karşılaştırmayı bir ikili arama döngüsünde kullan. Her turda aralığın yarısı elenir: `O(log n)`.

```c
#include <stddef.h>
#include <stdio.h>

/* Farklı elemanlı, döndürülmüş sıralı dizi. Kaç kez döndürüldüğünü,
   yani minimumun konumunu döndürür. n >= 1 olmalı. */
size_t dondurme_sayisi(const int *a, size_t n) {
    size_t lo = 0, hi = n - 1;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        if (a[orta] > a[hi])
            lo = orta + 1;
        else
            hi = orta;
    }
    return lo;
}
```

Ana fonksiyon, iki diziyi çalıştırır:

```c
int main(void) {
    int a[] = {9, 12, 15, 18, 22, 3, 5, 7};
    size_t n = sizeof a / sizeof a[0];
    printf("dondurme sayisi: %zu\n", dondurme_sayisi(a, n));
    int b[] = {1, 2, 3, 4, 5};
    printf("dondurme sayisi: %zu\n", dondurme_sayisi(b, 5));
    return 0;
}
```

**Adım 6 — Doğrula.** Her turu tabloya yazdık (`lo`, `hi` başlangıçta `0` ve `7`):

| Tur | lo | hi | orta | a[orta] | a[hi] | Karar |
|---|---|---|---|---|---|---|
| 1 | 0 | 7 | 3 | 18 | 7 | `18 > 7` doğru, `lo = 4` |
| 2 | 4 | 7 | 5 | 3 | 7 | `3 > 7` yanlış, `hi = 5` |
| 3 | 4 | 5 | 4 | 22 | 3 | `22 > 3` doğru, `lo = 5` |

Döngü `lo = 5` ile biter; cevap `5`'tir ve program `5` yazdırdı. İkinci dizi `[1, 2, 3, 4, 5]` sıralıdır ve program `0` yazdırdı.

**Bunu AI'sız yazabilir misin?** Dizi tekrarlı olsaydı, `a[orta] == a[hi]` durumunda ne yapardın? Bu eşitlik, en kötü durum süresini nasıl değiştirir ve 14.8'deki tekrarlı dizi ailesiyle nasıl bağlantılıdır?

### Örnek 3 (★★): Cevap üzerinde ikili arama: kargo kapasitesi

**Problem:** `w = [1, 2, ..., 10]` ağırlıklarındaki 10 paketi sırayla, en fazla `D = 5` günde taşımak istiyoruz. Her gün taşınan paketlerin toplamı kapasite `C`'yi aşamaz. En küçük `C`'yi bul. Cevap `15`'tir: `C = 15` ile paketler `[1,2,3,4,5]`, `[6,7]`, `[8]`, `[9]`, `[10]` şeklinde beş güne sığar.

**Adım 1 — Anla.** Girdi ağırlıklar ve gün sayısı `D`'dir. Çıktı, `D` güne sığan en küçük kapasitedir. Kenar durumu: en ağır paket tek başına taşınamıyorsa kapasite o paketten küçük olamaz.

**Adım 2 — Örnekle.** `C = 14` ile gün sayısı 6, `C = 15` ile 5 olur. Yani `D = 5` için en küçük kapasite 15'tir. `C = 10` ise 7 gün sürer.

**Adım 3 — Kaba çöz.** `C`'yi 10'dan 55'e kadar tek tek dene ve ilk `D` güne sığanı seç. Her deneme `O(n)` iş yapar; toplam `46 · n` işlem.

**Adım 4 — Örüntü.** Yüklem `p(C) = (gün_sayısı(C) <= D)` yazılabilir. Kapasite arttıkça gün sayısı artmaz, bu yüzden `p` monoton: `F F ... F T T ... T`. İlk `T` aradığımız cevaptır. Bu, 14.7'deki cevap üzerinde ikili aramadır.

**Adım 5 — İyileştir.** Aralık `[max(w), sum(w)] = [10, 55]` olarak alınır: alt uç en ağır paket, üst uç tüm paketlerin toplamı (tek günde biter). Bu aralıkta yaklaşık `log₂ 46 ≈ 6` yüklem değerlendirmesi yeter.

```python
def gun_sayisi(agirliklar, kapasite):
    """Paketleri sırayla, kapasiteyi aşmadan günlere doldur."""
    gun, yuk = 1, 0
    for w in agirliklar:
        if yuk + w > kapasite:
            gun += 1
            yuk = 0
        yuk += w
    return gun


def min_kapasite(agirliklar, d, iz=False):
    lo = max(agirliklar)         # en ağır paket tek başına sığmalı
    hi = sum(agirliklar)         # hepsi tek günde: her zaman yeterli
    while lo < hi:
        orta = lo + (hi - lo) // 2
        g = gun_sayisi(agirliklar, orta)
        if iz:
            print(lo, hi, orta, g, "uygun" if g <= d else "yetmez")
        if g <= d:
            hi = orta
        else:
            lo = orta + 1
    return lo


if __name__ == "__main__":
    w = list(range(1, 11))
    print("min kapasite:", min_kapasite(w, 5))
    # kontrol: kapasite 14 ve 15 ile gun sayilari
    print("14 -> %d gun, 15 -> %d gun" % (gun_sayisi(w, 14),
          gun_sayisi(w, 15)))
```

**Adım 6 — Doğrula.** Aralığın her adımını, `min_kapasite(w, 5, iz=True)` çağrısıyla yazdırdık (ana blokta yazdırılmaz; kendin de çağırabilirsin). Tablo `lo`, `hi`, `orta`, gün sayısı ve kararı içerir:

| lo | hi | orta | gün (orta) | Karar |
|---|---|---|---|---|
| 10 | 55 | 32 | 2 | uygun, `hi = 32` |
| 10 | 32 | 21 | 3 | uygun, `hi = 21` |
| 10 | 21 | 15 | 5 | uygun, `hi = 15` |
| 10 | 15 | 12 | 6 | yetmez, `lo = 13` |
| 13 | 15 | 14 | 6 | yetmez, `lo = 15` |

Sonuç `lo = 15`'tir. Doğrulamak için `C = 14` ve `C = 15` değerlerinde gün sayısını ayrıca hesapladık: `6` ve `5`. Program `min kapasite: 15` yazdırdı.

**Bunu AI'sız yazabilir misin?** `D = 3` için en küçük kapasiteyi kâğıtta bul. Önce aralığı yaz, sonra en az iki adım yap ve her adımda gün sayısını elle hesapla.

### Örnek 4 (★★★): İki sıralı dizinin medyanı

**Problem:** İki artan sıralı dizi `a` ve `b` verildiğinde, birleşimlerinin medyanını bul. Toplam eleman sayısı tekse ortadaki eleman, çiftse ortadaki iki elemanın ortalaması. Çözüm, birleşik diziyi oluşturmadan `O(log min(m, n))` olmalıdır.

**Adım 1 — Anla.** Girdi iki sıralı dizidir; çıktı bir sayıdır. Kenar durumları: biri boş, iki dizinin uzunluğu çok farklı, tüm değerler eşit.

**Adım 2 — Örnekle.** `a = [1, 3, 8]` ve `b = [2, 4, 6, 9]` için birleşim `[1, 2, 3, 4, 6, 8, 9]` ve medyan `4`'tür.

**Adım 3 — Kaba çöz.** İki diziyi birleştir, sırala, ortadaki elemanı al. Birleştirme `O(m + n)` iş ve ek bellek gerektirir. İki işaretçiyle birleştirme de `O(m + n)`'dir ve ek bellek kullanır.

**Adım 4 — Örüntü.** Asıl soru, birleşik sıralı dizinin "sol yarısını" bulmaktır. Her iki diziden de bir kesim yaparsak, sol kümeye `i` eleman `a`'dan, `j = yarım - i` eleman `b`'den girer. Doğru kesim, iki koşulu sağlar: `a[i-1] <= b[j]` ve `b[j-1] <= a[i]`. Bu koşulu sağlayan `i`'yi arayabiliriz; `i` arttıkça `a`'nın sol kümesi büyür, dolayısıyla koşul monoton biçimde değişir. Arama `i` üzerinde yapılır ve `i` en fazla `m` (daha kısa dizinin uzunluğu) değerini alabilir.

**Adım 5 — İyileştir.** Aramayı kısa dizi üzerinde yap: `a` her zaman daha kısa olsun (gerekirse `a` ile `b` yer değiştirir). Böylece arama aralığı `[0, m]` olur ve maliyet `O(log m)`, yani `O(log min(m, n))`'dir.

```python
import random


def medyan(a, b):
    """İki sıralı dizinin birleşiminin medyanı, O(log min(m, n))."""
    if len(a) > len(b):
        a, b = b, a
    m, n = len(a), len(b)
    toplam = m + n
    yarim = (toplam + 1) // 2        # sol kümedeki eleman sayısı
    lo, hi = 0, m
    while lo <= hi:
        i = (lo + hi) // 2           # a'dan sol kümeye alınan
        j = yarim - i                # b'den sol kümeye alınan
        a_sol = a[i - 1] if i > 0 else float("-inf")
        a_sag = a[i] if i < m else float("inf")
        b_sol = b[j - 1] if j > 0 else float("-inf")
        b_sag = b[j] if j < n else float("inf")
        if a_sol <= b_sag and b_sol <= a_sag:
            if toplam % 2 == 1:
                return float(max(a_sol, b_sol))
            return (max(a_sol, b_sol) + min(a_sag, b_sag)) / 2
        if a_sol > b_sag:
            hi = i - 1
        else:
            lo = i + 1
    raise ValueError("girdi siralı degil")
```

Ana blok, örneği ve 3000 rastgele testi çalıştırır:

```python
if __name__ == "__main__":
    random.seed(42)
    print("ornek:", medyan([1, 3, 8], [2, 4, 6, 9]))
    hatali = 0
    for _ in range(3000):
        a = sorted(random.randint(-50, 50)
                   for _ in range(random.randint(0, 12)))
        b = sorted(random.randint(-50, 50)
                   for _ in range(random.randint(0, 12)))
        c = sorted(a + b)
        if not c:
            continue
        k = len(c)
        if k % 2:
            beklenen = c[k // 2]
        else:
            beklenen = (c[k // 2 - 1] + c[k // 2]) / 2
        if medyan(a, b) != beklenen:
            hatali += 1
    print("3000 rastgele test, hatali:", hatali)
```

**Adım 6 — Doğrula.** `a = [1, 3, 8]` ve `b = [2, 4, 6, 9]` için (`m = 3`, `n = 4`, `yarım = 4`) iki turu tabloya yazdık:

| lo | hi | i | j | a_sol | a_sağ | b_sol | b_sağ | Karar |
|---|---|---|---|---|---|---|---|---|
| 0 | 3 | 1 | 3 | 1 | 3 | 6 | 9 | `b_sol <= a_sağ` yanlış (6 > 3), `a_sol > b_sağ` yanlış, `lo = 2` |
| 2 | 3 | 2 | 2 | 3 | 8 | 4 | 6 | `3 <= 6` ve `4 <= 8`, bölme tamam |

İkinci turda `toplam = 7` tektir, medyan `max(a_sol, b_sol) = max(3, 4) = 4`'tür. Program `ornek: 4.0` yazdırdı ve 3000 rastgele test (sabit tohum 42) hatasız geçti. Rastgele testlerde beklenen medyan, iki diziyi birleştirip sıralayan kaba çözümle hesaplandı; algoritmanın sonucu bu referansla karşılaştırıldı.

**Bunu AI'sız yazabilir misin?** Toplam eleman sayısı çift olduğunda medyanın iki ortanın ortalaması olduğunu kodda hangi satır uygular? Bu satırda `max` ve `min` neden bu rolleri üstlenir?

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Arama algoritmalarının asıl eğitimi, sınır durumlarında kendi kodunun yanlış davrandığını fark edip düzeltmektir. Bu hatayı bir yapay zekânın değil, kendi testlerinin bulması gerekir.
:::

### Proje 1 (★★): Log dosyasında zaman aralığı sorgusu

**Amaç:** Zaman damgalı bir log dosyasında, verilen `[t1, t2)` zaman aralığına düşen ilk ve son satırların bayt ofsetlerini bulan bir komut satırı aracı yazmak. Dosya belleğe tamamen alınmadan çalışmalıdır.

**Yapılacak / Beklenen davranış:**

1. Log satırları zaman damgasına göre artan sıralı olsun (ör. `2026-10-18T10:00:01 ...`). Test için bir dosya üret; tohum `42` olsun.
2. Dosyayı bayt ofseti üzerinde ara. Bir ofsete `seek` ile git, ileri giderek bir satır başına gel, satırın damgasını oku ve karşılaştır.
3. `[t1, t2)` aralığının ilk satırını ve son satırını bul; aralık boşsa bunu açıkça bildir.
4. Dosya boyutu `n` bayt olduğunda, arama adımlarının sayısının yaklaşık `log₂ n` olduğunu ölç.

**Önerilen yaklaşım:** Bayt ofsetleri üzerinde yarı açık aralık `[lo, hi)` kullan; `hi` dosyanın boyutudur. Ortadaki ofsetten bir satır başına gelmek için bir sonraki satır sonuna kadar ilerle, bu satırın damgasıyla karar ver. İlk satır kesik olabilir; bu yüzden aramayı satır başı ofsetleri üzerinde yapmaya çalış. Döngünün her turda aralığı küçülttüğünü değişmezle (14.2) kontrol et.

**Başarı kriterleri:**

- 1 GB'lık üretilmiş bir dosyada, 10 000 rastgele aralık sorgusu, doğrusal taramanın sonuçlarıyla birebir eşleşir.
- Her sorgu, dosyayı baştan okumaz; ölçülen okuma sayısı `log₂ n` mertebesindedir.
- Boş aralık, dosyanın başından önce ve sonundan sonra biten sorgularda doğru sonuç verir ve sonsuz döngüye girmez.

### Proje 2 (★★★): Sensör kalibrasyon tablosunda en yakın değer

**Amaç:** Bir sensörün ham ADC değerini (örnek olarak 12-bit, `0..4095`) fiziksel bir değere (ör. sıcaklık, °C) çeviren bir kalibrasyon tablosu yazmak. Tablo, artan sıralı ham değerler ve bunlara karşılık gelen fiziksel değerlerden oluşur.

**Yapılacak / Beklenen davranış:**

1. Tabloyu 64 noktalı, artan sıralı bir dizi olarak tanımla. Tablo `const` ile saklanmalı; çalışma anında değişmemeli.
2. Her ham değer için, tablodaki alt ve üst kalibrasyon noktasını (14.4'teki alt sınır ile) bul ve aradaki doğrusal enterpolasyonla fiziksel değeri hesapla.
3. Tablo dışında kalan ham değerlerde (ör. tablonun ilk noktasından küçük) sonucu geçersiz olarak bildir; sessizce sınır değeri döndürme.
4. Her örnekleme turu için adım sayısını ve kullanılan belleği ölç; en kötü durumun sabit bir üst sınırı olmalı.

**Önerilen yaklaşım:** Enterpolasyonun paydasının sıfır olmadığından emin ol; iki kalibrasyon noktası aynı ham değere sahipse ne olacağını önceden karar ver. Doğrusal enterpolasyonda çarpım 32-bit ile taşabilir; hesabı 64-bit ile yap (14.11). Test için tüm ham değerleri (`0..4095`) doğrusal bir referans taramasıyla karşılaştır. Hedef mikrodenetleyici olmak zorunda değildir; önce bilgisayarda doğrula, sonra STM32 derlemesine geç.

**Başarı kriterleri:**

- `0..4095` arasındaki tüm ham değerlerde sonuç, referans taramasıyla birebir aynıdır.
- Her sorgu için adım sayısı, `⌈log₂ 64⌉ + 1` değerini aşmaz.
- Tablo dışı girdilerde geçersiz bayrağı döner ve tablo hiç değiştirilmez.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün; en son gerekirse kodla doğrula. Mülakat sorularının bir kısmı ayrıca işaretlidir.

1. ★ Sıralı bir dizide `x`'in kaç kez geçtiğini, iki sınırın farkını kullanarak ikili aramayla bul. (Mülakat)
2. ★ Sıralı, farklı tamsayılardan oluşan bir dizide `a[i] == i` olan ilk elemanı bul. Dizi uzunluğu `n` ise bu koşulu ikili aramayla nasıl ararsın? (Mülakat)
3. ★ Sıralı bir dizide `x`'e en yakın değeri bul. Cevap, alt sınır ve onun solundaki elemanlar arasında olmalı; iki adayı karşılaştırmayı unutma. (Mülakat)
4. ★★ Önce artan, sonra azalan bir dizide (dağ dizisi) tepe elemanı, yani en büyük değeri `O(log n)` ile bul. (Mülakat)
5. ★★ Her değer iki kez geçen, yalnızca bir değerin tek geçtiği sıralı bir dizide o tek değeri `O(log n)` ile bul. Eşleşmelerin konumunun çift-tek örüntüsünü kullan. (Mülakat)
6. ★★ Sıralı bir dizide toplamı `k` olan iki elemanın var olup olmadığını, ikili aramayla `O(n log n)` ve iki işaretçiyle `O(n)` yöntemlerini karşılaştırarak yaz. (Mülakat)
7. ★★ Tekrarlı bir döndürülmüş dizide minimum bulma algoritmasının en kötü durumunu bir örnekle göster; adım sayısını her `n` için say ve `n - 1`'e eşit olduğunu doğrula.
8. ★★ Satır ve sütunları artan sıralı bir matriste `x`'in kaç kez geçtiğini `O(m + n)` adımda say. Sağ üst köşeden yürüyüşün her adımı neden bir satır ya da sütunu eler?
9. ★★★ İki sıralı dizinin `k`. en küçük elemanını `O(log(min(m, n)))` ile bul. (Mülakat)
10. ★★ `x³ = 10` denkleminin kökünü, 60 turluk bir kayan nokta ikili aramasıyla bul. Sonucu, Python'un `10 ** (1/3)` ifadesiyle karşılaştır ve farkın ne kadar olduğunu ölç.
11. ★★★ Interpolasyon aramasının en kötü durumunu gösteren bir dizi kur ve 14.11'deki sonda sayacını kullanarak `n`'e göre büyümesini bir tabloda göster.
12. ★★★ Kayan nokta ikili aramasında `1e-9` hassasiyet için kaç tur gerektiğini hesapla; hesabı arama aralığının başlangıç uzunluğuna bağlayarak kanıtla. (Mülakat)
13. ★★★ 14.8'deki `min_konum`'u, tekrarlı dizilerde de **döndürme noktasını** bulacak şekilde düzelt (`{1, 1, 1, 3, 1}` için `4` dönmeli). Ardından `dondurulmus_ara`'yı, uzunluğu 1–8 olan ve elemanları `{0, 1, 2}`'den gelen tüm döndürülmüş sıralı dizilerde, doğrusal aramayla karşılaştırarak kapsamlı test et. (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir kaynağı okuyacaksın: Go standart kütüphanesinin `sort` paketindeki `Search` fonksiyonu. Dosya, Go'nun `go1.22.0` etiketinden alındı (`https://raw.githubusercontent.com/golang/go/go1.22.0/src/sort/search.go`), dosyanın 58–73. satırları aşağıda. Belge yorumunun (doc comment) tamamı çıkarıldı. Fonksiyon gövdesi ve gövde içindeki yorumlar birebir kaynaktan alındı; yalnızca bir yorum satırı, sayfa genişliği için iki satıra bölündü (içerik değişmedi).

```go
func Search(n int, f func(int) bool) int {
	// Define f(-1) == false and f(n) == true.
	// Invariant: f(i-1) == false, f(j) == true.
	i, j := 0, n
	for i < j {
		h := int(uint(i+j) >> 1) // avoid overflow when computing h
		// i ≤ h < j
		if !f(h) {
			i = h + 1 // preserves f(i-1) == false
		} else {
			j = h // preserves f(j) == true
		}
	}
	// i == j, f(i-1) == false, and f(j) (= f(i)) == true
	// =>  answer is i.
	return i
```

Fonksiyonun kendi yorumu, aradığı şeyi şöyle tanımlar: `f` yanlış olan bir önek ve doğru olan bir sonektan oluşuyorsa, `Search` doğru olan ilk konumu döndürür; hiç doğru yoksa `n` döndürür. Bu, 14.6'daki `ilk_dogru` ile aynı kalıptır.

**Sorular — cevaplamadan geçme:**

1. Yorumdaki `f(-1) == false` ve `f(n) == true` varsayımları ile `Invariant: f(i-1) == false, f(j) == true` ifadesi, 14.2'deki (I) ve (II) şartlarıyla nasıl eşleşir? Döngü bittiğinde `i == j` neden cevaptır?
2. `h := int(uint(i+j) >> 1)` neden `(i+j)/2` yerine yazılmıştır? Go dil belirtimi işaretli tamsayı taşmasını nasıl tanımlar, ve `uint` dönüşümü neden doğru orta değeri verir? Bu, 14.3'teki C taşmasıyla nasıl karşılaştırılır?
3. `Search` bulamadığında neden `-1` değil `n` döndürür? `Search(len(a), func(i int) bool { return a[i] >= x })` kalıbında, dönen değer ile `a[i] == x` denetimini birlikte nasıl yorumlarsın?
4. `Search` ile bu dosyada bulunan `SearchInts` (sıralı `int` dilimi için sarmalayıcı) arasındaki ilişki nedir? Hangisini hangi durumda seçerdin?
5. Döngü en fazla kaç kez `f` çağırır? `n = 1000` için tahmin et, sonra `⌈log₂(n + 1)⌉` ile karşılaştır. Farkın nedeni, aralığın her turda ne kadar küçüldüğüdür; bunu açıkla.
6. (Mülakat) Bu kodu `float64` bir dilim için alt sınır olarak kullanmak istiyorsun. `NaN` değerleri dilimde varsa sonuç ne olur? Sıralılık varsayımının hangi kısmı bozulur?

## Bölüm Özeti

Bu bölümde sıralı veride aramayı, doğruluğunu kanıtlayarak ve sınırlarını bilerek öğrendik:

- **Doğrusal arama** `Θ(n)`'dir; nöbetçi hilesi karşılaştırma sayısını yarıya indirir ama büyüme sınıfını değiştirmez. Küçük `n`, sırasız veri ve önbellek gibi durumlarda doğrusal tarama kazanabilir; bu bir ölçüm sorusudur.
- **Döngü değişmezi** (alt sınır için: `a[0..lo)` küçük, `a[hi..n)` büyük ya da eşit) ikili aramanın doğruluğunu kanıtlar.
- **Yarı açık aralık** `[lo, hi)` uzunluğu, boş aralığı ve düzeltmeleri basit tutar. Orta değeri `lo + (hi - lo) / 2` ile hesapla; `(lo + hi) / 2` tipik olarak sarar ama C'de UB'dir.
- **Alt sınır, üst sınır ve eşit aralık** `x`'in ilk konumunu, sonrasını ve sayısını verir. `bsearch` ve `lower_bound`'un sözleşmesini belgeden doğrula.
- **Monoton yüklem** `F...F T...T` üzerinde ilk `T`'yi bulmak, ikili aramanın genelleştirilmiş biçimidir; cevap üzerinde ikili arama, karar problemlerini bu kalıpla çözer.
- **Döndürülmüş dizi** `O(log n)` ile aranır; tekrarlar varken minimum bulma `O(n)`'e düşebilir.
- **Matris araması** iki durumdadır: satır-sütun sıralıysa sağ üst köşeden `O(m + n)` yürüyüş; satırlar birbirini izliyorsa düz dizi olarak `O(log(mn))`.
- **Üstel arama** sınırsız ya da uzunluğu bilinmeyen dizilerde `O(log p)`'dir; **interpolasyon** tekdüzen veride çok az sorgu yapar ama düzensiz veride `O(n)`'e düşer.
- Arama yapısını seçerken sıralı dizi, hash tablosu ve dengeli ağaç arasındaki farkı (sıra bilgisi, en kötü durum, ekleme maliyeti) karar tablosuna göre tart.

**Sonraki bölümde:** Bu bölümde aramanın bir çözüm uzayında ilerlediğini gördük: monoton yüklem, cevap üzerinde arama, döndürülmüş dizinin iki yarısı. Bölüm 15'te özyinelemeyi ve geri izlemeyi (recursion & backtracking) göreceğiz. Orada da çözümü, olası çözümlerin bir ağacını sistematik olarak dolaşarak arayacağız; her dalda bir kararı geri alabilmek, bu bölümdeki değişmez düşüncesinin bir uzantısı olacak.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Sıralı bir dizide `lo <= hi` ile `lo < hi` döngüleri arasındaki fark nedir? Hangi değişmez bozulur, hangi durumda sonsuz döngü ya da kaçırılan eleman oluşur?
2. `(lo + hi) / 2` ile `lo + (hi - lo) / 2` her zaman aynı sonucu verir mi? Hangi tip ve hangi girdi için biri taşar?
3. Döndürülmüş sıralı bir dizide tekrarlar varken neden `O(log n)` garantisi kaybolur? Bir örnek kur ve adım sayısını göster.
4. Cevap üzerinde ikili arama için hangi iki koşul gerekir? Kargo kapasitesi problemi bu koşulları neden sağlar?
5. Interpolasyon araması neden her zaman ikili aramadan hızlı değildir? Hangi veri dağılımında kötü sonuç verir?
6. Hash tablosu ortalama `O(1)` arama yapıyorsa, neden her zaman tercih edilmez? Sıralı sorgu ve en kötü durum bu kararı nasıl değiştirir?
7. Bir matriste satırlar ve sütunlar ayrı ayrı sıralıysa, neden düz bir ikili arama tek başına yetmez? Sağ üst köşeden yürüyüş neden her adımda bir satır ya da sütunu eler?
8. Bir kayan nokta ikili aramasında sabit 60 tur yerine "fark küçülünce dur" kuralı kullanmak neden tehlikeli olabilir? Hangi durumda döngü hiç bitmeyebilir?
:::
