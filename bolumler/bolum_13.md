%% kisim_no: IV
%% kisim_ad: Algoritmalar
%% bolum_no: 13
%% baslik: Sıralama

## Giriş: Sıralama neden her yerde?

Bir veritabanında `ORDER BY` yazdığında, bir sensör kaydını zamana göre dizdiğinde ya da bir hedef listesini önceliğe göre sıraladığında, aslında aynı problemi çözersin: n tane kaydı bir anahtara göre düzenlemek. Sıralama, bilgisayar biliminin en çok çalışılmış ve en çok kullanılan işlemlerinden biridir. Bölüm 14'te göreceğimiz ikili arama (binary search) da sıralı bir diziye ihtiyaç duyar; yani sıralama olmasa çoğu hızlı arama yöntemi de olmaz.

Mülakatta "bir diziyi sırala" sorusu ilk bakışta ısınma gibi görünür. Asıl sınav, neyi neden seçtiğini anlatmaktır. Hangi algoritma kararlıdır, ek bellek ister mi, girdi zaten sıralıysa ne kadar hızlıdır, en kötü durumda ne olur? Bu soruların cevabı, Bölüm 12'de kurduğumuz araçlarla verilir. Bu bölümde her algoritmayı üç soruyla inceleyeceğiz: ne yapar, ne kadar sürer, neye mal olur.

Savunma sanayiinde sıralamanın yeri daha da net. Bir uçuş kontrol döngüsünde sensör paketleri zaman damgasına göre birleştirilir. Bir hedef takip sisteminde, aynı önceliğe sahip iki hedefin sırası değişirse operatör ekranda farklı bir tablo görür. Burada kararlılık süslü bir ayrıntı değil, veri bütünlüğü sorunudur. Bu yüzden kararlılık, bu bölümün ana kavramlarından biri olacak.

Mert'in EV Dashboard projesine dönersek, STM32 kartından gelen sensör kayıtları farklı sensörlerden ve zaman damgasıyla gelir. Bir grafikte her sensörün zaman çizgisini çizmek istiyorsan, önce sensöre, sonra zamana göre sıralamalısın. Bölüm 13.8'de bu çok anahtarlı sıralamayı kararlılıkla nasıl yapacağını göstereceğiz.

::: not
Bu bölümde sıralanan şey yalnızca tamsayı değil, bir **anahtar** ve bir **kimlik** taşıyan kayıttır. Anahtar sıralama ölçütüdür (ör. sıcaklık). Kimlik ise kaydın girişteki konumunu tutar; kararlılığı görünür kılmak için bunu kullanacağız. Algoritmaların karmaşıklığını Bölüm 12'deki adım sayma ve ölçüm araçlarıyla değerlendireceğiz.
:::

## 13.1 Problem, ölçütler ve laboratuvar iskeleti

Sıralama problemi şöyle tanımlanır: `n` kayıttan oluşan bir dizi verildiğinde, anahtarlarına göre artan sırada yeni bir düzen üret. Girdi ve çıktı aynı boyutta olduğundan, bir algoritmayı değerlendirirken en az beş ölçüte bakarız.

- **Karşılaştırma sayısı.** İki anahtarın sırasını sorma sayısı. Karşılaştırma tabanlı algoritmalar için ana maliyet budur.
- **Yazma sayısı.** Bir dizi hücresine kayıt yazma sayısı. Büyük kayıtlarda bu, karşılaştırmadan pahalı olabilir.
- **Zaman.** Gerçek makinede ölçülen süre. Bölüm 12.10'daki protokolle ölçeriz.
- **Yardımcı bellek.** Girdinin dışında ek olarak ne kadar bellek gerektiği. `O(1)` ise sıralama **yerinde (in-place)** yapılır.
- **Kararlılık (stability).** Anahtarları eşit iki kaydın göreli sırası korunuyor mu? Korunuyorsa algoritma **kararlıdır**. Bu, 13.8'de ayrıntılı işlenecek.
- **Uyarlanabilirlik (adaptive).** Girdi zaten kısmen sıralıysa algoritma daha az iş yapıyor mu?

Bu ölçütleri gerçekten ölçebilmek için küçük bir C laboratuvarı yazacağız. Her algoritma aynı kayıt dizisi üzerinde çalışacak ve tüm karşılaştırmalar tek bir fonksiyondan geçecek. Böylece sayaçlar adil olur. Laboratuvarın ilk parçası, kayıt yapısı, sayaçlar ve iki temel fonksiyondur:

Aşağıdaki kod parçası laboratuvarın iskeletidir. `Kayit` yapısı anahtar ve giriş konumunu tutar. `kucuk` fonksiyonu tek karşılaştırma noktasıdır ve sayacı artırır. `takas` iki kaydı değiştirir ve yazma sayacını iki artırır. Rastgele sayı için `rand()` yerine kendi xorshift64 üretecimizi kullandık; böylece aynı tohum (42) her platformda aynı diziyi üretir:

```c
/* siralama.c: Bolum 13 siralama laboratuvari */
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
    int anahtar;   /* siralanacak deger */
    int sira;      /* giristeki konum (kararlilik testi icin) */
} Kayit;

static long long kars, yaz;   /* karsilastirma ve yazma sayaci */
static int izle;              /* 1 ise ara durumlari yazdir */
static unsigned long long durum = 42;

static unsigned rastgele(void) {          /* xorshift64, tohum 42 */
    durum ^= durum << 13;
    durum ^= durum >> 7;
    durum ^= durum << 17;
    return (unsigned)(durum >> 32);
}

static int kucuk(const Kayit *x, const Kayit *y) {
    kars++;
    return x->anahtar < y->anahtar;
}

static void takas(Kayit *x, Kayit *y) {
    Kayit t = *x;
    *x = *y;
    *y = t;
    yaz += 2;
}
```

Laboratuvarın kodu parçalar hâlinde verilecek. Hepsini dosyadaki sırayla birleştirdiğinde tek bir `siralama.c` dosyası elde edersin. Parçaların bölüm ve satır karşılığı aşağıdadır:

| Bölüm | Dosyadaki satırlar | İçerik |
|---|---|---|
| 13.1 | 1–34 | başlık, `Kayit`, sayaçlar, `rastgele`, `kucuk`, `takas` |
| 13.3 | 36–81 | `goster`, `kabarcik`, `secmeli`, `eklemeli` |
| 13.3 | 380–402 | `kur`, `iz_modu` (ara durum kipi) |
| 13.4 | 83–113 | birleştirme sıralaması |
| 13.5 | 115–137, 139–176, 178–201 | pivot seçimi, Hoare, hızlı sıralama, Lomuto |
| 13.6 | 203–223 | yığın sıralaması |
| 13.7 | 225–267 | sayma ve radix |
| 13.10 | 269–335 | doğrulama, girdi üretimi, `algler`, `olc` |
| 13.10 | 337–378, 404–435 | tablo kipi, ölçek kipi, `main` |

## 13.2 Karşılaştırma tabanlı sıralamanın alt sınırı

Her algoritmayı tek tek sınıflandırmadan önce, bir soru sormalıyız: karşılaştırmalarla sıralama en az ne kadar iş yapmak zorundadır? Bu soruyu bir **karar ağacı** ile cevaplayabiliriz.

Diyelim ki üç kayıt `a, b, c` var ve her karşılaştırma bir "evet/hayır" sorusu. Algoritma, sorulara verilen cevaba göre bir sonraki soruyu seçer. Sonunda bir yaprağa ulaşır ve yaprak, girdinin hangi sıralı düzenine denk geldiğini söyler. Şekil 13.1'de bu ağaç `n = 3` için çizilmiştir.

![Şekil 13.1: n = 3 için karşılaştırma karar ağacı. Her iç düğüm bir karşılaştırmadır, her yaprak bir sıralı düzendir. Altı yaprak vardır ve ağacın yüksekliği en az log₂ 6 ≈ 2,58, yani 3'tür.](gorseller/b13_karar_agaci.png)

Genel durum için şu gözlem yeterlidir. `n` elemanın `n!` farklı sıralı düzeni olabilir, ve doğru sıralı düzen her girdi için bir yaprağa karşılık gelmelidir. Yani ağacın en az `n!` yaprağı olmalıdır. İkili bir ağacın yüksekliği `h` ise en fazla `2^h` yaprağı olabilir. Buradan `2^h ≥ n!`, yani `h ≥ log₂(n!)` çıkar. Ağacın yüksekliği, en kötü durumdaki karşılaştırma sayısıdır. Demek ki karşılaştırma tabanlı her sıralama, en kötü durumda en az `⌈log₂(n!)⌉` karşılaştırma yapar.

Bu sayıyı büyüklük olarak anlamak için Stirling yaklaşımını kullanalım: `n! ≈ √(2πn) (n/e)ⁿ`. Logaritmasını alırsak `log₂(n!) = n log₂ n − n log₂ e + O(log n)` elde ederiz. Baş terim `n log₂ n` olduğu için `log₂(n!) = Ω(n log n)` olur. Ortalama durum için de benzer bir kanıt vardır; bu bölümde ortalama için yalnızca bu sonucu kullanacağız.

Aşağıdaki tablo, değerleri hesap makinesiyle kontrol ettiğimiz `log₂(n!)` sayılarını verir. Son sütun `n log₂ n` ile karşılaştırma içindir:

| n | log₂(n!) | en az karşılaştırma | n log₂ n |
|---|---|---|---|
| 3 | 2,58 | 3 | 4,8 |
| 10 | 21,79 | 22 | 33,2 |
| 100 | 524,8 | 525 | 664,4 |
| 1 000 | 8 529,4 | 8 530 | 9 965,8 |
| 1 000 000 | 18 488 884,8 | 18 488 885 | 19 931 568,6 |

Stirling yaklaşımı `n = 10` için `33,219 − 14,427 + 2,986 = 21,78` verir; bu, kesin değer 21,79 ile uyumludur. Tablodan görülen şey, karşılaştırma tabanlı her sıralamanın `n log n` çizgisinin altına inemediğidir. Merge sort ve heap sort bu sınırı zaten yakalar; yani asimptotik olarak "daha iyisi yok" demektir. Bu sınırı aşmak için karşılaştırmanın dışına çıkmak gerekir: anahtarların bit ya da basamak yapısını ya da değer dağılımını kullanmak. Bunu 13.7'de sayma ve radix sıralamasıyla yapacağız.

::: dikkat
Alt sınır, **karşılaştırma tabanlı** sıralamalar içindir. Anahtarın değerine bakan (sayma, radix gibi) algoritmalar bu sınırın kapsamında değildir. "Sıralama en az n log n gerektirir" cümlesini her yere genellemek, mülakatta sık düşülen bir hatadır; sınırın hangi model için geçerli olduğunu her zaman söyle.
:::

## 13.3 Basit O(n²) sıralamalar: kabarcık, seçmeli, eklemeli

Bu üç algoritma, anlaması en kolay olanlardır ve küçük dizilerde gerçekten kullanılırlar. İlk olarak **kabarcık sıralaması (bubble sort)** ele alalım. Fikir basittir: dizinin baştan sona taranmasında bitişik iki eleman yanlış sıradaysa takas edilir. Her geçişte en büyük eleman sona "kabarır". En fazla `n − 1` geçiş gerekir. Bir geçişte hiç takas olmazsa dizi sıralıdır ve erken çıkılabilir. Bu erken çıkış, algoritmayı uyarlanabilir yapar.

Aşağıdaki kod, goster yardımcısı ile kabarcık ve seçmeli sıralamayı içerir. Takas yalnızca `kucuk(a[i+1], a[i])` kesin olarak doğruysa yapılır; eşit anahtarlar yer değiştirmez, bu da kararlılığı korur:

```c
static void goster(const char *ad, const Kayit *a, size_t n) {
    printf("%-10s", ad);
    for (size_t i = 0; i < n; i++)
        printf(" %d", a[i].anahtar);
    printf("\n");
}

static void kabarcik(Kayit *a, size_t n) {
    for (size_t son = n; son > 1; son--) {
        int degisti = 0;
        for (size_t i = 0; i + 1 < son; i++) {
            /* yalniz kesin buyukse takas: kararlilik */
            if (kucuk(&a[i + 1], &a[i])) {
                takas(&a[i], &a[i + 1]);
                degisti = 1;
            }
        }
        if (izle) goster("kabarcik", a, n);
        if (!degisti) break;
    }
}
```

**Seçmeli sıralama (selection sort)** dizinin her adımında kalan parçanın en küçüğünü bulur ve başa takas eder. Her zaman aynı sayıda karşılaştırma yapar; `n(n−1)/2`. Yazma açısından avantajlıdır: en fazla `n − 1` takas. Ancak standart takasla kararsızdır. Örneğin `[2a, 2b, 1]` dizisinde 1 ile `2a` takas edilir ve `2a`, `2b`'nin arkasına düşer. Bu takas ayrıntısını 13.8'de tekrar göreceğiz.

**Eklemeli sıralama (insertion sort)** kartlarını sıralayan birinin yaptığı işe benzer: her yeni kartı, sol tarafındaki sıralı kısmın doğru yerine yerleştirir. Yerleştirme sırasında büyük elemanlar sağa kaydırılır. Kaydırma sayısı, tam olarak **ters çevrim (inversion)** sayısına eşittir: yani `i < j` ama `a[i] > a[j]` olan çift sayısı. Bu sayı sıralı dizide sıfır, ters dizide `n(n−1)/2`dir. Bu yüzden eklemeli sıralama, neredeyse sıralı girdilerde çok hızlıdır. Kod aşağıdadır:

```c
static void secmeli(Kayit *a, size_t n) {
    for (size_t i = 0; i + 1 < n; i++) {
        size_t en = i;
        for (size_t j = i + 1; j < n; j++)
            if (kucuk(&a[j], &a[en])) en = j;
        if (en != i) takas(&a[i], &a[en]);
        if (izle) goster("secmeli", a, n);
    }
}

static void eklemeli(Kayit *a, size_t n) {
    for (size_t i = 1; i < n; i++) {
        Kayit x = a[i];
        size_t j = i;
        while (j > 0 && kucuk(&x, &a[j - 1])) {
            a[j] = a[j - 1];
            yaz++;
            j--;
        }
        a[j] = x;
        yaz++;
        if (izle) goster("eklemeli", a, n);
    }
}
```

Üç algoritmanın da iş akışını görmek için laboratuvara bir **iz kipi** ekledik. `./siralama iz` komutu, küçük bir diziyi her geçişten sonra yazdırır. Bu kip, aşağıdaki kodla birlikte çalışır. Kabarcık için girdi `5 2 4 6 1 3` olarak alınmış, her geçiş bir satır olarak yazılmıştır:

```c
static void kur(Kayit *a, const int *deger, int n) {
    for (int i = 0; i < n; i++) {
        a[i].anahtar = deger[i];
        a[i].sira = i;
    }
}

static int iz_modu(void) {
    Kayit a[6];
    int deger[6] = {5, 2, 4, 6, 1, 3};
    izle = 1;
    printf("kabarcik:\n");
    kur(a, deger, 6);
    kabarcik(a, 6);
    printf("secmeli:\n");
    kur(a, deger, 6);
    secmeli(a, 6);
    printf("eklemeli:\n");
    kur(a, deger, 6);
    eklemeli(a, 6);
    izle = 0;
    return 0;
}
```

```term
$ ./siralama iz
kabarcik:
kabarcik   2 4 5 1 3 6
kabarcik   2 4 1 3 5 6
kabarcik   2 1 3 4 5 6
kabarcik   1 2 3 4 5 6
kabarcik   1 2 3 4 5 6
secmeli:
secmeli    1 2 4 6 5 3
secmeli    1 2 4 6 5 3
secmeli    1 2 3 6 5 4
secmeli    1 2 3 4 5 6
secmeli    1 2 3 4 5 6
eklemeli:
eklemeli   2 5 4 6 1 3
eklemeli   2 4 5 6 1 3
eklemeli   2 4 5 6 1 3
eklemeli   1 2 4 5 6 3
eklemeli   1 2 3 4 5 6
```

Bu izi elle doğrulayalım. Kabarcıkta ilk geçiş `5` ile `2`'yi, sonra `5` ile `4`'ü, sonra `6` ile `1`'i, en sonda `6` ile `3`'ü takas eder. Sonuç `2 4 5 1 3 6`dır; çıktıdaki ilk satır budur. Son geçişte (beşinci satır) takas olmaz ve algoritma erken çıkar. Seçmelide ilk geçiş en küçük elemanı, yani `1`'i, başa getirir. Eklemelide ise `1`, sol tarafındaki dört elemanın tamamını kaydırarak başa gelir. Her üç izde de son satır sıralı diziyi gösterir.

Üç algoritmanın özelliklerini bir tabloda toplayalım. Bu tablo, 13.10'daki ölçümlerle karşılaştırılacaktır:

| Algoritma | En iyi | Ortalama | En kötü | Ek bellek | Kararlı | Yerinde | Uyarlanabilir |
|---|---|---|---|---|---|---|---|
| Kabarcık | Θ(n) | Θ(n²) | Θ(n²) | O(1) | evet | evet | evet (erken çıkış) |
| Seçmeli | Θ(n²) | Θ(n²) | Θ(n²) | O(1) | hayır | evet | hayır |
| Eklemeli | Θ(n) | Θ(n²) | Θ(n²) | O(1) | evet | evet | evet |

Bu tabloda "en iyi" sütunundaki `Θ(n)` ifadeleri, girdinin sıralı olduğu duruma aittir. Seçmelinin en iyi durumu yoktur: her girdi için `n(n−1)/2` karşılaştırma yapar. Bunun nedeni, algoritmanın girdiyi okuyup "bu zaten sıralı mı?" diye sormamasıdır. Bu, seçmelinin bir zayıflığı değil, tasarım tercihidir: takas sayısı en aza iner, ama karşılaştırma sayısı değişmez.

Kabarcık ve eklemeli algoritmalar yerinde ve kararlıdır. Bu nedenle küçük, neredeyse sıralı veri setlerinde (ör. yeni gelen birkaç kaydı mevcut sıralı listeye eklemek) eklemeli sıralama sık tercih edilir. Python'un Timsort algoritması da küçük parçaları eklemeli (ikili eklemeli) yöntemle sıralar; bunu 13.9'da göreceğiz.

## 13.4 Birleştirme sıralaması (merge sort)

Birleştirme sıralaması, "böl ve yönet" yaklaşımının en temiz örneğidir. Diziyi ikiye böl, her yarıyı ayrı ayrı sırala, sonra iki sıralı yarıyı tek bir sıralı dizide birleştir. Asıl iş birleştirme adımındadır. İki sıralı diziyi birleştirmek için her iki dizinin başına birer gösterici koyup küçük olanı çıktıya alırsın. Bu, her elemanı en fazla bir kez ziyaret eder, yani `O(n)` iş yapar.

Maliyet bağıntısı Bölüm 12.9'daki gibidir: `T(n) = 2T(n/2) + n`. Master Teoremi'nin ikinci durumunda `a = 2`, `b = 2`, `c = 1` olduğu için `T(n) = Θ(n log n)` bulunur. Şekil 13.2, `[38, 27, 43, 3, 9, 82, 10]` dizisi üzerinde bölme ve birleştirme seviyelerini gösterir.

![Şekil 13.2: Birleştirme sıralaması, [38, 27, 43, 3, 9, 82, 10]. Gri oklar bölmeyi, bordo oklar sıralı parçaların birleştirmesini gösterir. Her seviye toplam n iş yapar ve dört seviye vardır.](gorseller/b13_birlestirme.png)

Birleştirme, kararlılığı kolayca korur: eşitlik durumunda sol parçadaki elemanı önce alırsak, eşit anahtarlı kayıtların göreli sırası değişmez. Aşağıdaki kod bu kuralı açıkça uygular: sağdaki eleman yalnızca kesin olarak küçükse önce alınır. Geçici dizi `g`, tüm birleştirme boyunca tek bir tahsisle kullanılır:

```c
static void birlestir(Kayit *a, Kayit *g, size_t lo,
                      size_t orta, size_t hi) {
    size_t i = lo, j = orta, k = lo;
    while (i < orta && j < hi) {
        /* sag eleman yalniz kesin kucukse once gelir */
        if (kucuk(&a[j], &a[i]))
            g[k++] = a[j++];
        else
            g[k++] = a[i++];
        yaz++;
    }
    while (i < orta) { g[k++] = a[i++]; yaz++; }
    while (j < hi)   { g[k++] = a[j++]; yaz++; }
    for (k = lo; k < hi; k++) { a[k] = g[k]; yaz++; }
}

static void birlesme_rec(Kayit *a, Kayit *g, size_t lo, size_t hi) {
    if (hi - lo < 2) return;
    size_t orta = lo + (hi - lo) / 2;
    birlesme_rec(a, g, lo, orta);
    birlesme_rec(a, g, orta, hi);
    birlestir(a, g, lo, orta, hi);
}

static void birlestirme(Kayit *a, size_t n) {
    if (n < 2) return;
    Kayit *g = malloc(n * sizeof *g);
    if (!g) { fprintf(stderr, "bellek yok\n"); exit(1); }
    birlesme_rec(a, g, 0, n);
    free(g);
}
```

Birleştirme sıralamasının özellikleri şöyledir. Üç durumda da `Θ(n log n)` karşılaştırma yapar. Ek bellek `O(n)`dir (geçici dizi), dolayısıyla yerinde değildir. Kararlıdır. Klasik biçimi uyarlanabilir değildir; ancak sıralı girdide karşılaştırma sayısı azalır, çünkü sol parça bittiğinde kalan sağ parça toplu olarak kopyalanır. Yazma sayısı ise girdiden bağımsızdır, çünkü her seviyede her eleman iki kez yazılır.

Ölçümde (13.10) `n = 20 000` rastgele girdi için birleştirme, 260 774 karşılaştırma ve yaklaşık 1 ms sürdü. Aynı girdide eklemeli sıralama 99 728 691 karşılaştırma ve yaklaşık 44 ms sürdü. Bu fark, `O(n²)` ile `O(n log n)` arasındaki farkın ilk işaretidir.

Birleştirme sıralamasının iki biçimi vardır. **Üstten aşağı (top-down)** biçim, yukarıdaki özyinelemeli koddur. **Alttan yukarı (bottom-up)** biçimde genişliği 1, 2, 4, ... olan parçaları art arda birleştirirsin; özyineleme yoktur. İkisi de `Θ(n log n)`dir. Bağlı listede birleştirme sıralaması ise `O(1)` ek bellekle yapılabilir; bu, 13.4'ün çözümlü örneklerinde değil, Ek Alıştırmalar'da ele alınacak.

Birleştirme sıralaması, bellekten büyük verileri sıralamak için de temel oluşturur. Veriyi diskte parçalara bölüp her parçayı bellekte sıralarsın; sonra bu sıralı parçaları k-yollu birleştirmeyle tek bir dosyada birleştirirsin. Bu **dış sıralama (external sort)** yöntemidir ve veritabanlarında yaygındır.

## 13.5 Hızlı sıralama (quicksort)

Hızlı sıralamanın fikri, birleştirmenin tersidir. Bir **pivot** seçersin, dizideki elemanları pivottan küçükler solda, büyükler sağda kalacak şekilde **bölümlersin**, ve sonra iki tarafı özyinelemeyle sıralarsın. Birleştirme adımı yoktur; iş bölümleme sırasında yapılır. Bu yüzden yerinde çalışabilir.

Hızlı sıralamanın tüm sorunu, pivot seçiminde ve bölümlemenin dengesinde yatar. İyi bir pivot diziyi kabaca yarıya bölerse algoritma `Θ(n log n)`; kötü bir pivot her seferinde bir elemanı ayırırsa `Θ(n²)` olur.

**Pivot seçimi.** Üç yaygın strateji vardır. İlki, ilk elemanı seçmektir. Bu basit, ama sıralı girdide her seferinde en küçük elemanı pivot yapar; bölüm `1` ve `n − 1` elemanlıdır, toplam `n(n−1)/2` karşılaştırma olur. Bu, Bölüm 12.6'da gördüğümüz naif sürümdür. İkincisi rastgele pivottur; kötü girdi dizisine karşı korur, çünkü girdi değil rastgelelik belirler. Üçüncüsü üçün medyanıdır: ilk, orta ve son elemanın medyanı pivot yapılır. Sıralı girdide bu, neredeyse tam ortayı seçer. Kod, üç stratejiyi de tek bir parametreyle destekler (`strat` = 0, 1, 2):

```c
/* x, y, z indekslerinden degeri ortanca olanin indeksi */
static ptrdiff_t uc_medyan(const Kayit *a, ptrdiff_t x,
                           ptrdiff_t y, ptrdiff_t z) {
    if (kucuk(&a[x], &a[y])) {
        if (kucuk(&a[y], &a[z])) return y;
        if (kucuk(&a[x], &a[z])) return z;
        return x;
    }
    if (kucuk(&a[x], &a[z])) return x;
    if (kucuk(&a[y], &a[z])) return z;
    return y;
}

/* Pivotu a[lo]'ya tasi. strat: 0 ilk, 1 rastgele, 2 ucun medyani */
static void pivot_sec(Kayit *a, ptrdiff_t lo, ptrdiff_t hi,
                      int strat) {
    ptrdiff_t k = lo;
    if (strat == 1)
        k = lo + (ptrdiff_t)(rastgele() % (unsigned)(hi - lo + 1));
    else if (strat == 2)
        k = uc_medyan(a, lo, lo + (hi - lo) / 2, hi);
    takas(&a[lo], &a[k]);
}
```

**Hoare bölümlemesi.** Hoare'un şeması, iki göstericiyi iki uçtan içe doğru hareket ettirir. Soldaki gösterici pivottan küçük olmayan bir eleman, sağdaki gösterici pivottan büyük olmayan bir eleman bulduğunda ikisini takas eder. Pivot `a[lo]`'ya taşındığında bu şema, bölüm noktası `j`'yi `lo ≤ j < hi` aralığında verir. Eşit elemanları takas ettiği için çok tekrarlı verilerde dengeli kalır. Aşağıdaki kod ayrıca özyinelemenin yalnızca küçük parçada yapılmasını sağlar: büyük parça döngüyle işlenir. Böylece yığın derinliği en fazla `log₂ n` seviyeye çıkar, çünkü her özyinelemeli çağrıda parça en fazla yarıya iner:

```c
/* Hoare bolumlemesi: pivot a[lo]; donus j, [lo..j] <= p */
/* ve [j+1..hi] >= p. Pivot a[hi]'ya gelmez, j < hi. */
static ptrdiff_t hoare(Kayit *a, ptrdiff_t lo, ptrdiff_t hi) {
    Kayit p = a[lo];
    ptrdiff_t i = lo - 1, j = hi + 1;
    for (;;) {
        do { i++; } while (kucuk(&a[i], &p));
        do { j--; } while (kucuk(&p, &a[j]));
        if (i >= j) return j;
        takas(&a[i], &a[j]);
    }
}

/* Kucuk parcaya ozyinele, buyuk parcayi dongu ile isle */
static void hizli_rec(Kayit *a, ptrdiff_t lo, ptrdiff_t hi,
                      int strat) {
    while (lo < hi) {
        pivot_sec(a, lo, hi, strat);
        ptrdiff_t p = hoare(a, lo, hi);
        if (p - lo + 1 <= hi - p) {
            hizli_rec(a, lo, p, strat);
            lo = p + 1;
        } else {
            hizli_rec(a, p + 1, hi, strat);
            hi = p;
        }
    }
}

static void hizli_ilk(Kayit *a, size_t n) {
    if (n > 1) hizli_rec(a, 0, (ptrdiff_t)n - 1, 0);
}
static void hizli_medyan(Kayit *a, size_t n) {
    if (n > 1) hizli_rec(a, 0, (ptrdiff_t)n - 1, 2);
}
static void hizli_rastgele(Kayit *a, size_t n) {
    if (n > 1) hizli_rec(a, 0, (ptrdiff_t)n - 1, 1);
}
```

Bu kodda üç sarmalayıcı (`hizli_ilk`, `hizli_medyan`, `hizli_rastgele`) yalnızca pivot stratejisini seçer. Ölçümde bu üç strateji ayrı satırlarda yer alır.

**Lomuto bölümlemesi.** Lomuto şeması daha kısadır: pivot olarak son elemanı alır ve tek bir gösterici `i` ile soldan sağa tarar. `a[j] < pivot` olduğunda `a[i]` ile takas edip `i`'yi artırır. Bitişte pivotu `i` konumuna koyar. Lomuto, sıralama mantığını anlamak için iyi bir modeldir, ama eşit elemanlarda zayıftır. Aşağıdaki kod ve Şekil 13.3, bir örneği adım adım gösterir:

```c
/* Lomuto: pivot son eleman. Esit degerlerde ayrim yapamaz. */
static ptrdiff_t lomuto(Kayit *a, ptrdiff_t lo, ptrdiff_t hi) {
    Kayit p = a[hi];
    ptrdiff_t i = lo;
    for (ptrdiff_t j = lo; j < hi; j++) {
        if (kucuk(&a[j], &p)) {
            takas(&a[i], &a[j]);
            i++;
        }
    }
    takas(&a[i], &a[hi]);
    return i;
}

static void lomuto_rec(Kayit *a, ptrdiff_t lo, ptrdiff_t hi) {
    if (lo >= hi) return;
    ptrdiff_t p = lomuto(a, lo, hi);
    lomuto_rec(a, lo, p - 1);
    lomuto_rec(a, p + 1, hi);
}

static void lomuto_sar(Kayit *a, size_t n) {
    if (n > 1) lomuto_rec(a, 0, (ptrdiff_t)n - 1);
}
```

Şekil 13.3, CLRS kitabındaki klasik örneği, `[2, 8, 7, 1, 3, 5, 6, 4]`'ü, pivot `4` ile Lomuto bölümlemesinden geçirdiğinde ne olduğunu gösterir. Bölümlemeden sonra pivot `4` üçüncü indekse (sıfır tabanlı) yerleşir; solunda küçükler, sağında büyükler vardır. Dizinin sıralı olmadığına dikkat et; bölümleme yalnızca pivotu doğru yere koyar.

![Şekil 13.3: Lomuto bölümlemesi, pivot 4. Üstte bölümleme öncesi, altta sonrası. Yeşil kutular 4'ten küçük, kırmızılar büyük, sarı pivottur. Pivot sonra 3. indekste, solunda küçükler, sağında büyükler yer alır.](gorseller/b13_lomuto.png)

**Eşit elemanlar.** Lomuto'nun asıl zayıflığı, tüm elemanlar eşit olduğunda ortaya çıkar: `a[j] < pivot` hiçbir zaman doğru olmaz, bu yüzden bölüm hep `0` ve `n − 1` elemanlı olur ve toplam `n(n−1)/2` karşılaştırma yapılır. Hoare'un şeması ise eşit elemanlarda da takas yaptığı için iki parçayı dengeli tutar. Eşit elemanları açıkça ayırmak için **üç yollu bölümleme (3-way partition)** kullanılır: `< pivot`, `= pivot`, `> pivot` olmak üzere üç bölgeye ayırırsın. Bu fikir, Çözümlü Örnek 1'deki Hollanda bayrağı probleminin ta kendisidir; orada tek geçişli üç yollu bölümlemeyi göreceksin.

**Karmaşıklık.** Üç durumu bir tabloda toplayalım:

- **En iyi durum** `Θ(n log n)`: her bölüm diziyi yarıya böler. Bunun için pivotun medyan olması gerekir.
- **Ortalama durum** `Θ(n log n)`: rastgele pivotla beklenen karşılaştırma sayısı `2n ln n` ile verilir; bu, yaklaşık `1,39 · n log₂ n` demektir. Bu, literatürdeki klasik sonuçtur; burada türetmiyoruz.
- **En kötü durum** `Θ(n²)`: her bölüm bir elemanı ayırır. İlk eleman seçilir ve girdi sıralıysa bu olur.

Ölçümde `n = 20 000` sıralı girdide ilk eleman pivotu `200 029 998` karşılaştırma yaptı; bu, `n(n−1)/2 = 199 990 000` değerine çok yakındır. Aynı girdide üçün medyanı yalnızca `363 291` karşılaştırma yaptı. Lomuto'nun on farklı değerli girdide yaptığı `20 110 676` karşılaştırma ile Hoare-medyan'ın `395 314`ü arasındaki fark, eşit elemanların ne kadar önemli olduğunu gösterir.

**Özyineleme derinliği.** Hızlı sıralamanın yığın kullanımı, özyineleme derinliğine bağlıdır. Her iki parçayı da özyinelemeyle işlersen, en kötü durumda derinlik `n` olur; Python'da bu, Bölüm 12.8'de gördüğümüz gibi `RecursionError` ile sonuçlanır. Kodumuz ise küçük parçayı özyinelemeyle, büyük parçayı döngüyle işler. Her özyinelemeli çağrıda parça en fazla yarıya indiği için derinlik `O(log n)` kalır. Bu tekniği, C'de yığın taşmasını önlemenin standart yolu olarak kullan.

**Yorum.** Hızlı sıralama, pratikte en çok kullanılan sıralamalardan biridir. Bunun nedeni, asimptotik olarak `n log n` olmasının yanında yerinde çalışması ve önbelleği iyi kullanmasıdır (sıralı bölümleme ardışık bellek erişimi yapar; bunu Bölüm 25'te ayrıntılı göreceğiz). Ama kararlı değildir ve en kötü durumu `n²`dir. Bu ikilemi çözmek için kütüphaneler **introsort** kullanır; bunu 13.9'da anlatacağız.

## 13.6 Yığın sıralaması (heap sort)

Yığın sıralaması, Bölüm 10'daki yığın (heap) yapısını kullanır. Önce diziyi bir **max-heap**'e çevirirsin: her ebeveyn çocuklarından büyük olacak şekilde. Bunu Bölüm 10.7'deki heapify ile `O(n)` sürede yaparsın. Sonra kökü (en büyük eleman) dizinin sonuna takas eder, yığının boyutunu bir azaltır ve yeni kökü aşağı doğru düzeltirsin (sift-down). Bu adım `O(log n)` sürer ve `n − 1` kez tekrarlanır. Heapify'ın `O(n)` olduğunu Bölüm 12'deki Örnek 4'te kanıtladık; burada o sonucu kullanacağız.

Şekil 13.4, heapify'dan sonra `[16, 14, 10, 8, 7, 9, 3, 2, 4, 1]` dizisinin ağaç ve dizi gösterimini verir. Köşe kutuların altındaki köşeli parantez değerler dizi indeksidir.

![Şekil 13.4: Heapify sonrası max-heap (n = 10). Her ebeveyn çocuklarından büyüktür. Dizi gösteriminde ebeveyn i, çocuklar 2i+1 ve 2i+2 indekslerindedir.](gorseller/b13_yigin.png)

Yığın sıralamasının kodu, sift-down ile yığın kurulumunu ve sıralamayı birlikte içerir:

```c
/* Yigin: en buyuk ust, a[0..n-1] icinde */
static void elen(Kayit *a, ptrdiff_t n, ptrdiff_t i) {
    for (;;) {
        ptrdiff_t en = i, sol = 2 * i + 1, sag = 2 * i + 2;
        if (sol < n && kucuk(&a[en], &a[sol])) en = sol;
        if (sag < n && kucuk(&a[en], &a[sag])) en = sag;
        if (en == i) return;
        takas(&a[i], &a[en]);
        i = en;
    }
}

static void yigin_sirala(Kayit *a, size_t n_) {
    ptrdiff_t n = (ptrdiff_t)n_;
    for (ptrdiff_t i = n / 2 - 1; i >= 0; i--)
        elen(a, n, i);
    for (ptrdiff_t son = n - 1; son > 0; son--) {
        takas(&a[0], &a[son]);
        elen(a, son, 0);
    }
}
```

Özellikler: en kötü durumda da `Θ(n log n)` (kurulum `O(n)`, çıkarmalar `n·O(log n)`), ek bellek `O(1)`, yerinde, **kararsız** ve uyarlanabilir değil. Kararsızlık, ebeveyn ile çocuğun takasından kaynaklanır: iki eşit kayıt, yığının farklı katmanlarına düşebilir. Ölçümde yığın, rastgele girdide `510 785` karşılaştırma yaptı; bu değer `n log₂ n`nin yaklaşık 1,8 katıdır. Ölçek grafiğinde (Şekil 13.7) yığın, benzer boyutta birleştirme ve hızlı sıralamadan belirgin biçimde yavaştır; bunun bir nedeni ardışık olmayan bellek erişimleridir, ama bu bölümde bunu ayrıca ölçmedik.

## 13.7 Sayma ve radix: karşılaştırmadan kaçmak

Bölüm 13.2'de `Ω(n log n)` alt sınırını gördük. Sayma (counting) ve radix sıralaması bu sınırın dışındadır. Nedeni basittir: bu algoritmalar anahtarları iki kişinin karşılaştırdığı nesneler olarak değil, **sayı** olarak kullanır. Anahtarın değerine göre bir kutuya doğrudan yazarlar. Karşılaştırma yapmadıkları için sınır onlara uygulanmaz.

**Sayma sıralaması (counting sort)**, anahtarların `0..k−1` aralığında olduğunu bilir. Her anahtarın kaç kez geçtiğini sayar, önek toplamı ile her anahtarın çıktıdaki başlangıç konumunu hesaplar, ve elemanları sondan başa doğru yerleştirir. Sondan başa tarama kararlılığı sağlar: eşit anahtarlı son eleman, çıktıda en sona yerleşir. Kod aşağıdadır. Ölçümde bu algoritma hiçbir karşılaştırma yapmaz; sayıcı değerleri 0'dır.

```c
/* Sayma: anahtarlar 0..k-1 arasinda. Kararlilik icin sondan basla */
static void sayma_sirala(Kayit *a, size_t n, size_t k) {
    size_t *say = calloc(k, sizeof *say);
    Kayit *c = malloc(n * sizeof *c);
    if (!say || !c) { fprintf(stderr, "bellek yok\n"); exit(1); }
    for (size_t i = 0; i < n; i++)
        say[a[i].anahtar]++;
    for (size_t v = 1; v < k; v++)
        say[v] += say[v - 1];
    for (size_t i = n; i-- > 0; ) {
        c[--say[a[i].anahtar]] = a[i];
        yaz++;
    }
    memcpy(a, c, n * sizeof *a);
    yaz += n;
    free(say);
    free(c);
}

static void sayma_sar(Kayit *a, size_t n) {
    sayma_sirala(a, n, 1000000);
}
```

Sayma sıralamasının karmaşıklığı `O(n + k)` zaman ve `O(n + k)` bellektir. Bu, `k` küçük olduğunda çok iyidir; `k` büyükse (ör. 32 bitlik anahtarlar) sayaç dizisinin kendisi sorun olur. Bu yüzden genellikle radix'e geçilir.

**Radix sıralaması (LSD)** anahtarı basamaklarına ayırır ve en düşük basamaktan başlayarak her basamağa göre kararlı bir sayma sıralaması uygular. Kararlılık burada zorunludur: bir basamağa göre yaptığın sıralama, bir önceki basamağın düzenini bozmamalıdır. Aşağıdaki kod, 32 bitlik anahtarları 8 bitlik (256 kovalı) basamaklarla dört geçişte sıralar. Kovalar için her geçişte başlangıç konumlarını önek toplamıyla bulur ve elemanları ileri yönde yerleştirir; bu da kararlılığı sağlar:

```c
/* LSD radix: 8 bitlik kovalar, 4 gecis. Her gecis kararli. */
static void radix_sirala(Kayit *a, size_t n) {
    Kayit *c = malloc(n * sizeof *c);
    if (!c) { fprintf(stderr, "bellek yok\n"); exit(1); }
    for (unsigned sh = 0; sh < 32; sh += 8) {
        size_t say[256] = {0};
        for (size_t i = 0; i < n; i++)
            say[((unsigned)a[i].anahtar >> sh) & 255]++;
        size_t t = 0;
        for (int v = 0; v < 256; v++) {
            size_t s = say[v];
            say[v] = t;
            t += s;
        }
        for (size_t i = 0; i < n; i++)
            c[say[((unsigned)a[i].anahtar >> sh) & 255]++] = a[i];
        memcpy(a, c, n * sizeof *a);
    }
    free(c);
}
```

Şekil 13.5, anlatım için onluk tabanda (basamak `0..9`) `[170, 45, 75, 90, 802, 24, 2, 66]` dizisinin üç geçişini gösterir. Kodun gerçekte 256 tabanını kullandığını unutma; ilke aynıdır.

![Şekil 13.5: LSD radix sıralaması, onluk taban. Birinci geçiş birler, ikinci onlar, üçüncü yüzler basamağına göre kararlı dağıtır. Her geçiş bir öncekinin basamak dışı sırasını korur.](gorseller/b13_radix.png)

Radix sıralaması `d` basamak ve `b` tabanı için `O(d(n + b))` zaman harcar. 32 bitlik `unsigned` anahtar ve 8 bit basamak için `d = 4`, `b = 256`dir. Yani süre, `n` ile doğrusal büyür. Ölçümde `n = 1 048 576` için radix 13,94 ms sürdü ve log-log eğimi 1,00 çıktı; yani sabit sayıda geçiş, `n` ile doğru orantılıdır. Bu, Bölüm 12.3'teki `O(n)` sınıfının somut bir örneğidir.

Ne zaman hangisi? Sayma sıralaması `k` küçük olduğunda, radix ise anahtar bit ya da basamak sayısı sabit olduğunda kullanılır. İkisi de karşılaştırma yapmaz, bu nedenle anahtarın yapısı hakkında bilgi gerektirir. Anahtar bir sayı değilse (ör. metin ya da karmaşık bir nesne), ilk adım bunu sayısal bir anahtara dönüştürmek olur. Bu dönüşüm, sıralamanın bir parçası olarak sayılmalıdır.

## 13.8 Kararlılık ve çok anahtarlı sıralama

Bir sıralamanın **kararlı (stable)** olması, anahtarları eşit olan kayıtların girişteki göreli sırasını koruması demektir. Kavramı somutlaştıralım. Dört kişilik bir listeyi, sınıf numarasına göre sıralamak istediğini düşün. Ali ve Mert aynı sınıftadır (3), Ayşe ve Zeynep aynı sınıftadır (1). Girişte Ali, Ayşe'den önce, Mert ise Zeynep'ten önce gelir. Kararlı bir sıralama, sınıf 1'de Ayşe'nin Zeynep'ten önce, sınıf 3'te Ali'nin Mert'ten önce kalmasını sağlar. Kararsız bir sıralama bu sırayı bozabilir.

Şekil 13.6, aynı girdinin kararlı ve kararsız sonucunu yan yana gösterir. Kararsız sonuç, bu bölümde yazdığımız seçmeli sıralamanın takas adımından doğar: `Ali` ile `Zeynep` yer değiştirdiğinde, `Mert` sonraki takasta `Ali`'nin önüne geçer.

![Şekil 13.6: Kararlılık. Girişteki sırada Ali, Mert'ten önce gelir. Kararlı sonuç bu sırayı korur; kararsız sonuçta Mert, Ali'nin önüne geçmiştir.](gorseller/b13_kararlilik.png)

Python'un `sorted` fonksiyonu kararlıdır ve bu, Bölüm 3'te gördüğümüz `key` parametresiyle birlikte güçlü bir araçtır. Aşağıdaki kod aynı örneği çalıştırır. İkinci satır `reverse=True` ile azalan sırada sıralar; Python belgeleri bu durumda da eşit anahtarların göreli sırasının korunduğunu söyler, çıktı da bunu gösterir:

```python
kayitlar = [("Ali", 3), ("Ayse", 1), ("Mert", 3), ("Zeynep", 1)]
print(sorted(kayitlar, key=lambda k: k[1]))
print(sorted(kayitlar, key=lambda k: k[1], reverse=True))
```

```term
$ python -I kararlilik_py.py
[('Ayse', 1), ('Zeynep', 1), ('Ali', 3), ('Mert', 3)]
[('Ali', 3), ('Mert', 3), ('Ayse', 1), ('Zeynep', 1)]
```

Çıktıda sınıf 1'de Ayşe önce gelir, sınıf 3'te Ali önce gelir. İkinci satırda azalan sırada da Ali ile Mert ve Ayşe ile Zeynep'in girişteki sırası korunmuştur.

Kararlılık, **çok anahtarlı sıralamanın** temelidir. EV Dashboard'daki bir kayıt, sensör kimliği ve zaman damgası taşıyor olsun. Bunları önce zamana, sonra sensör kimliğine göre sıralamak istiyorsun: yani her sensörün kendi içinde zaman sırasında olduğu bir liste. Bunu iki kararlı sıralamayla yaparsın: önce zamana göre sıralarsın, sonra sensör kimliğine göre kararlı bir sıralama uygularsın. İkinci sıralama, eşit kimliklerin zaman sırasını bozmaz. Bu, radix sıralamasının arkasındaki ilkenin aynısıdır: her geçiş kararlı olmalı ve en önemli anahtar en son uygulanmalıdır.

Dikkat etmen gereken bir nokta: C'nin standart `qsort` fonksiyonu kararlılık garantisi vermez. Bölüm 2'de gördüğümüz bu durum, çok anahtarlı sıralamada sessiz bir hataya yol açabilir. Kendi kayıt yapında kararlılığa ihtiyacın varsa, kararlı bir algoritma seç ya da anahtarına girişteki konumunu ekleyerek kararsız algoritmayı kararlı hâle getir. Laboratuvarımızdaki `Kayit` yapısının `sira` alanı tam bunun için vardır.

## 13.9 Gerçek dünyada sıralama: Timsort, introsort, pdqsort

Bu bölümde anlattığımız algoritmaların hiçbiri tek başına gerçek kütüphanelerin tamamını açıklamaz. Dil çalışma zamanları, girdinin özelliğine göre birden fazla yöntemi birleştirir. Üç örneğe bakalım. Her iddiayı kendi kaynağından doğruladık; kaynak yolunu ve sürümünü yanında yazıyoruz.

**Timsort (CPython `list.sort` ve `sorted`).** CPython 3.12.10'un `Objects/listobject.c` dosyası, Timsort'u uygular. Algoritmanın tasarım notu `Objects/listsort.txt` dosyasındadır. Temel fikir şudur: dizi üzerinde soldan sağa geçerken önce **doğal çalıştırmaları (run)** bulur. Bir run, ya kesin azalmayan ya da kesin azalan bir parçadır. Azalan run'lar, kararlılık korunarak ters çevrilir. Çok kısa run'lar, `minrun` uzunluğuna (32 ile 64 arasında) ikili eklemeli sıralamayla genişletilir. Run'lar bulunduktan sonra bir yığında tutulur ve birleştirilir. Birleştirme sırasında bir taraf art arda `MIN_GALLOP = 7` kez kazanırsa algoritma "galloping" moduna geçer ve üstel arama ile büyük blokları toplu kopyalar.

Bu tasarımın sonucu iki özelliktir. Birincisi, algoritma kararlıdır. İkincisi, girdi zaten sıralıysa tek bir run oluşur ve iş `O(n)`'de biter; `listsort.txt` de en iyi durumda `N − 1` karşılaştırma yapıldığını belirtir. En kötü durumda `O(n log n)`dir. Bölüm 12.11'de bahsettiğimiz "küçük parçalarda basit yöntem" fikri burada doğrudan uygulanır.

Ölçümümüzde bu davranış görülebilir (13.10'daki Python çıktısı): `10⁶` rastgele tamsayı yaklaşık 190 ms, aynı tamsayıların sıralı hâli yaklaşık 42 ms sürdü. Bu bir kanıt değildir, ama Timsort'un doğal run'lardan yararlandığını gösteren bir ipucudur.

**Introsort (GCC libstdc++ `std::sort`).** Musser'in 1997'de önerdiği introsort, hızlı sıralamanın kötü durumunu yığın sıralamasıyla sınırlar. GCC 13.3.0'ın `libstdc++-v3/include/bits/stl_algo.h` dosyasında üç parça vardır. Birincisi, bölüm boyutu 16'nın altına inince özyineleme durur (`_S_threshold = 16`). İkincisi, derinlik sınırı `2 · lg(n)` olarak alınır. Üçüncüsü, sınır aşılırsa `__partial_sort` çağrılır; bu da yığın tabanlıdır. Sonunda kalan küçük bölgeler ekleme sıralamasıyla bitirilir. Böylece en kötü durum `O(n log n)` olur. Introsort kararlı değildir.

**pdqsort ve modern türevleri.** Go 1.19'dan itibaren `sort.Sort` ve `sort.Slice` pdqsort (örüntü-bozucu hızlı sıralama) kullanır; `src/sort/sort.go` ve `src/sort/zsortfunc.go` dosyalarında bu görülür. Rust tarafında durum yeniden düzenlenmiştir: Rust 1.81.0 kaynağında kararlı `slice::sort` **driftsort**, kararsız `slice::sort_unstable` **ipnsort** kullanır. Eski Rust sürümlerinde `sort_unstable` pdqsort tabanlıydı; bu bilgiyi bu bölümde kaynaktan doğrulamadık, yalnızca not olarak yazıyoruz.

Aşağıdaki tablo, bu iddiaların her birini kaynağıyla birlikte özetler:

| Dil ve işlev | Kullanılan algoritma | Kararlı | Kaynak (doğrulanan sürüm) |
|---|---|---|---|
| CPython `list.sort`, `sorted` | Timsort | evet | `Objects/listobject.c`, `Objects/listsort.txt` (3.12.10) |
| GCC `std::sort` | introsort | hayır | `libstdc++-v3/include/bits/stl_algo.h` (GCC 13.3.0) |
| Go `sort.Sort`, `sort.Slice` | pdqsort | hayır | `src/sort/sort.go`, `zsortfunc.go` (go1.19) |
| Rust `slice::sort` | driftsort | evet | `library/core/src/slice/sort/stable/mod.rs` (1.81.0) |
| Rust `slice::sort_unstable` | ipnsort | hayır | `library/core/src/slice/sort/unstable/mod.rs` (1.81.0) |
| C standart `qsort` | belirtilmemiş | garanti yok | C standardı; Bölüm 2 |

Bu tablodan çıkan ders şudur: "hangi sıralamayı kullanıyor?" sorusunun cevabı dile ve sürüme bağlıdır. Mülakatta ya da üretimde bu cevabı bir kaynaktan doğrulamadan kesin ifade etme.

## 13.10 Karşılaştırmalı ölçüm ve karar tablosu

Ölçüm protokolü Bölüm 12.10'daki gibidir: sabit tohum, birkaç tekrar ve en iyi süreyi almak, makine bilgisini yazmak ve eğimi hesaplamak. Bu bölümde iki ortam kullandık. C kodu WSL2 (Ubuntu 24.04) içinde `gcc 13.3.0` ile `-O2` seviyesinde derlendi. Python ölçümü Windows'ta CPython 3.12.10 ile yapıldı. Makine, Bölüm 12 ile aynıdır: AMD Ryzen 7 6800H (8 çekirdek, 16 iş parçacığı, en yüksek saat 3201 MHz), 32 GB bellek, Windows 11 Pro. WSL2 bir sanal makinedir; mutlak süreler yerel bir Linux'tan farklı olabilir, ama eğimler ve karşılaştırma sayıları daha taşınabilirdir.

Girdi üretimi, `rastgele` fonksiyonundaki xorshift64 üreteciyle tohum 42'den başlar. Dört girdi türü vardır: rastgele, sıralı, ters ve yalnızca 10 farklı değer içeren. Her algoritma her girdi için üç kez çalıştırılır ve en iyi süre alınır. Bu, algoritmanın kendi maliyetine en yakın ölçüdür.

Ölçümün kodu üç parçadan oluşur. Önce doğrulama ve girdi üretimi:

```c
static int sirali(const Kayit *a, size_t n) {
    for (size_t i = 1; i < n; i++)
        if (a[i - 1].anahtar > a[i].anahtar) return 0;
    return 1;
}

static int kararli(const Kayit *a, size_t n) {
    for (size_t i = 1; i < n; i++)
        if (a[i - 1].anahtar == a[i].anahtar &&
            a[i - 1].sira > a[i].sira) return 0;
    return 1;
}

/* tur: 0 rastgele, 1 sirali, 2 ters, 3 yalniz 10 farkli deger */
static void veri_uret(Kayit *a, size_t n, int tur) {
    for (size_t i = 0; i < n; i++) {
        int k;
        switch (tur) {
        case 0:  k = (int)(rastgele() % 1000000); break;
        case 1:  k = (int)i; break;
        case 2:  k = (int)(n - i); break;
        default: k = (int)(rastgele() % 10); break;
        }
        a[i].anahtar = k;
        a[i].sira = (int)i;
    }
}
```

Sonra algoritma tablosu ve ölçüm sarmalayıcısı. `olc` her tekrardan önce diziyi kopyalar, süreyi ölçer ve çıktının sıralı ve (gerekiyorsa) kararlı olduğunu kontrol eder:

```c
typedef void (*Siralayici)(Kayit *, size_t);

typedef struct {
    const char *ad;
    Siralayici f;
} Alg;

static const Alg algler[] = {
    {"kabarcik", kabarcik},         {"secmeli", secmeli},
    {"eklemeli", eklemeli},         {"birlestirme", birlestirme},
    {"hizli-ilk", hizli_ilk},       {"hizli-medyan", hizli_medyan},
    {"hizli-rast", hizli_rastgele}, {"lomuto", lomuto_sar},
    {"yigin", yigin_sirala},        {"sayma", sayma_sar},
    {"radix", radix_sirala},
};
#define ALG_SAYI (sizeof algler / sizeof algler[0])
static const char *turler[] = {"rastgele", "sirali", "ters",
                               "10 deger"};

/* Olcum: en iyi sure (3 tekrar). Sayac ve kararlilik son tekrardan */
static double olc(Siralayici f, const Kayit *ana, size_t n,
                  long long *k_out, int *kar_out) {
    Kayit *a = malloc(n * sizeof *a);
    double en = 1e30;
    if (!a) { fprintf(stderr, "bellek yok\n"); exit(1); }
    for (int t = 0; t < 3; t++) {
        memcpy(a, ana, n * sizeof *a);
        kars = yaz = 0;
        clock_t t0 = clock();
        f(a, n);
        double s = (double)(clock() - t0) / CLOCKS_PER_SEC;
        if (s < en) en = s;
        if (!sirali(a, n)) printf("HATA: sirali degil\n");
    }
    *k_out = kars;
    *kar_out = kararli(a, n);
    free(a);
    return en;
}
```

Ana tablo kipi, 20 000 elemanlı dört girdi türünde tüm algoritmaları çalıştırır ve üç ayrı tablo yazar: karşılaştırma sayısı, süre ve kararlılık. Kararlılık yalnızca 10 değerli girdi için raporlanır, çünkü bu girdide eşit anahtarlar bol olduğundan sonuç en belirleyici olandır. Bu kip ile ölçek kipini, `main` fonksiyonuyla birlikte aşağıda veriyoruz:

```c
static int tablo_modu(void) {
    size_t n = 20000;
    static Kayit ana[20000];
    long long kt[ALG_SAYI][4];
    double zt[ALG_SAYI][4];
    int kr[ALG_SAYI][4];
    printf("n = %zu\n\n", n);
    for (int tur = 0; tur < 4; tur++) {
        veri_uret(ana, n, tur);
        for (size_t g = 0; g < ALG_SAYI; g++) {
            long long k = 0;
            int r = 0;
            zt[g][tur] = olc(algler[g].f, ana, n, &k, &r);
            kt[g][tur] = k;
            kr[g][tur] = r;
        }
    }
    printf("Karsilastirma sayisi:\n%-13s", "");
    for (int tur = 0; tur < 4; tur++) printf("%12s", turler[tur]);
    printf("\n");
    for (size_t g = 0; g < ALG_SAYI; g++) {
        printf("%-13s", algler[g].ad);
        for (int tur = 0; tur < 4; tur++)
            printf("%12lld", kt[g][tur]);
        printf("\n");
    }
    printf("\nSure (ms):\n%-13s", "");
    for (int tur = 0; tur < 4; tur++) printf("%12s", turler[tur]);
    printf("\n");
    for (size_t g = 0; g < ALG_SAYI; g++) {
        printf("%-13s", algler[g].ad);
        for (int tur = 0; tur < 4; tur++)
            printf("%12.2f", zt[g][tur] * 1000.0);
        printf("\n");
    }
    printf("\nKararli mi (10 deger):\n");
    for (size_t g = 0; g < ALG_SAYI; g++)
        printf("%-13s %s\n", algler[g].ad,
               kr[g][3] ? "evet" : "hayir");
    printf("\ndogrulama tamam\n");
    return 0;
}
```

```c
static int olcek_modu(void) {
    static Kayit ana[1 << 20];
    size_t n;
    int kr;
    long long k;
    printf("O(n^2) grup, rastgele girdi (ms)\n");
    for (n = 2000; n <= 16000; n *= 2) {
        veri_uret(ana, n, 0);
        printf("n=%7zu kabarcik %9.2f secmeli %9.2f eklemeli %8.2f\n",
               n, olc(kabarcik, ana, n, &k, &kr) * 1000,
               olc(secmeli, ana, n, &k, &kr) * 1000,
               olc(eklemeli, ana, n, &k, &kr) * 1000);
    }
    printf("n log n grubu, rastgele girdi (ms)\n");
    for (n = 65536; n <= 1048576; n *= 2) {
        veri_uret(ana, n, 0);
        printf("n=%7zu birlestirme %7.2f hizli %8.2f yigin %8.2f"
               " radix %7.2f\n", n,
               olc(birlestirme, ana, n, &k, &kr) * 1000,
               olc(hizli_medyan, ana, n, &k, &kr) * 1000,
               olc(yigin_sirala, ana, n, &k, &kr) * 1000,
               olc(radix_sirala, ana, n, &k, &kr) * 1000);
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "iz") == 0) return iz_modu();
    if (argc > 1 && strcmp(argv[1], "olcek") == 0)
        return olcek_modu();
    return tablo_modu();
}
```

Tablo kipinin çıktısı şöyledir. Karşılaştırma ve süreler bu makinede alınmıştır; üç bağımsız koşuda sayaç sütunları birebir aynı çıktı. Süreler üç bağımsız koşuda 0,3 ms üzerindeki hücrelerde en fazla yüzde 7 farklılaştı:

```term
$ ./siralama
n = 20000

Karsilastirma sayisi:
                 rastgele      sirali        ters    10 deger
kabarcik        199985535       19999   199990000   198014922
secmeli         199990000   199990000   199990000   199990000
eklemeli         99728691       19999   199990000    90021385
birlestirme        260774      139216      148016      251870
hizli-ilk          490248   200029998   200039998      337138
hizli-medyan       443403      363291      363311      395314
hizli-rast         402846      403381      403199      347242
lomuto             353408   199990000   199990000    20110676
yigin              510785      529074      493307      470817
sayma                   0           0           0           0
radix                   0           0           0           0

Sure (ms):
                 rastgele      sirali        ters    10 deger
kabarcik           229.03        0.01      478.03      208.85
secmeli            302.74      302.28      302.38      302.14
eklemeli            44.32        0.02       88.41       39.25
birlestirme          1.01        0.25        0.27        0.60
hizli-ilk            0.93       47.39       68.15        0.38
hizli-medyan         0.91        0.18        0.18        0.40
hizli-rast           1.04        0.45        0.43        0.44
lomuto               0.75       89.39       99.46        9.16
yigin                0.78        0.63        0.66        0.76
sayma                0.46        0.37        0.38        0.43
radix                0.13        0.11        0.12        0.12

Kararli mi (10 deger):
kabarcik      evet
secmeli       hayir
eklemeli      evet
birlestirme   evet
hizli-ilk     hayir
hizli-medyan  hayir
hizli-rast    hayir
lomuto        hayir
yigin         hayir
sayma         evet
radix         evet

dogrulama tamam
```

Tabloyu okurken birkaç şeye dikkat et. Seçmeli sıralama her girdide tam `n(n−1)/2 = 199 990 000` karşılaştırma yaptı; girdiyi "önceden" tanımamaktadır. Eklemeli sıralama sıralı girdide yalnızca 19 999 karşılaştırma, ters girdide ise tam `n(n−1)/2` yaptı. Lomuto, sıralı ve ters girdide 199 990 000 karşılaştırma yaptı, çünkü son eleman pivotu bu girdilerde hep en uçtaki değerdir. Sayma ve radix hiç karşılaştırma yapmadı. Kararlılık sütunu da beklenen sonucu verdi: 10 değerli girdide seçmeli, hızlı, yığın ve Lomuto "hayır", kabarcık, eklemeli, birleştirme, sayma ve radix ise "evet" çıktı.

Ölçek kipi ise büyüme eğrisini ölçer. Her iki grup da `n` ikiye katlanarak büyüyen boyutlarda ölçülür. Çıktıyı Bölüm 12.10'daki `egim` işleviyle (log-log en küçük kareler) yorumlayabiliriz:

```term
$ ./siralama olcek
O(n^2) grup, rastgele girdi (ms)
n=   2000 kabarcik      1.81 secmeli      3.08 eklemeli     0.46
n=   4000 kabarcik      6.97 secmeli     12.40 eklemeli     1.80
n=   8000 kabarcik     29.17 secmeli     48.95 eklemeli     7.17
n=  16000 kabarcik    129.87 secmeli    196.73 eklemeli    28.68
n log n grubu, rastgele girdi (ms)
n=  65536 birlestirme    3.61 hizli     3.21 yigin     3.04 radix    0.60
n= 131072 birlestirme    7.78 hizli     6.74 yigin     7.42 radix    0.95
n= 262144 birlestirme   16.48 hizli    14.35 yigin    19.10 radix    2.38
n= 524288 birlestirme   34.40 hizli    29.88 yigin    46.82 radix    4.66
n=1048576 birlestirme   73.24 hizli    62.31 yigin   115.25 radix   11.28
```

Eğimler şu şekilde hesaplandı (aynı yöntem, Şekil 13.7'nin kodunda da yer alır):

| Algoritma | Boyut aralığı | Eğim |
|---|---|---|
| kabarcık | 2 000 – 16 000 | 2,07 |
| seçmeli | 2 000 – 16 000 | 2,02 |
| eklemeli | 2 000 – 16 000 | 2,01 |
| birleştirme | 2¹⁶ – 2²⁰ | 1,09 |
| hızlı (üçün medyanı) | 2¹⁶ – 2²⁰ | 1,04 |
| yığın | 2¹⁶ – 2²⁰ | 1,32 |
| radix | 2¹⁶ – 2²⁰ | 1,00 |

Üç O(n²) algoritmanın eğimi 2'ye çok yakındır. Birleştirme ve hızlı sıralama, n log n'nin beklenen hafif üstü olan 1,04–1,09 aralığındadır. Yığın sıralamasının 1,32 eğimi beklenenden büyüktür; bu koşuda nedenini ayırt etmedik. Bellek erişim düzeni (Bölüm 12.11) olası bir aday olsa da bunu kanıtlamadık. Radix'in eğimi 1,00'dır: dört sabit geçiş, `n` ile doğru orantılı çalışır.

![Şekil 13.7: Ölçülen süreler, log-log eksende. Sol: O(n²) grubu, eğimler 2,0 civarı. Sağ: n log n grubu. Radix eğimi 1,00, yığın 1,32 olarak ölçüldü.](gorseller/b13_olcum.png)

Python tarafında aynı girdi türlerini `sorted` ile ölçtük. Ölçüm, Timsort'un sıralı ve ters girdilerde nasıl davrandığını gösterir:

```python
# olc_py.py: sorted() icin girdi turune gore en iyi sure
import random
import time


def en_iyi(fonk, tekrar=3):
    en = float("inf")
    for _ in range(tekrar):
        t0 = time.perf_counter()
        fonk()
        en = min(en, time.perf_counter() - t0)
    return en


n = 10 ** 6
random.seed(42)
rast = [random.randrange(10 ** 6) for _ in range(n)]
sirali = sorted(rast)
ters = sirali[::-1]
tekrar = [random.randrange(10) for _ in range(n)]

print(f"n = {n}")
for ad, veri in [("rastgele", rast), ("sirali", sirali),
                 ("ters", ters), ("10 deger", tekrar)]:
    s = en_iyi(lambda: sorted(veri))
    print(f"{ad:<10} {s * 1000:9.2f} ms")

kayitlar = [("Ali", 3), ("Ayse", 1), ("Mert", 3), ("Zeynep", 1)]
print(sorted(kayitlar, key=lambda k: k[1]))
```

```term
$ python -I olc_py.py
n = 1000000
rastgele      196.67 ms
sirali         43.11 ms
ters          124.70 ms
10 deger       49.21 ms
[('Ayse', 1), ('Zeynep', 1), ('Ali', 3), ('Mert', 3)]
```

Python koşusunu iki kez çalıştırdık. İkinci koşuda sütunlar şöyle çıktı: rastgele 188,82 ms, sıralı 42,33 ms, ters 125,07 ms, 10 değer 48,23 ms. Bu, koşular arasında birkaç yüzde fark olduğunu gösterir. Son satır, kararlılık örneğinin çıktısının bir kopyasıdır ve kodu yukarıdadır.

Son olarak, laboratuvarın bellek ve tanımsız davranış kontrolünü yaptık. C kodunu `-fsanitize=address,undefined` ile derledik; ASan ve UBSan hiçbir uyarı vermedi, çıkış kodu 0 idi. Komut şöyledir (WSL kabuğunda çalıştırıldı):

```term
$ gcc -O2 -g -Wall -Wextra -std=c11 \
>   -fsanitize=address,undefined siralama.c -o siralama_asan
$ ./siralama_asan
```

Bu bölümün sonunda, ölçümün ve analizin bize verdiği **karar tablosunu** görelim. Bu tablo, bir mülakatta ya da gerçek bir projede ilk bakışta hangi sıralamayı seçeceğini söylemek için kullanılabilir. Son sütun hangi bölümde gerekçelendirildiğini söyler:

| Durum | Öneri | Gerekçe |
|---|---|---|
| Küçük parça ya da neredeyse sıralı küçük veri | eklemeli | yerinde, kararlı, uyarlanabilir; ölçümle eşik belirlenmeli (13.3) |
| Kararlılık gerekli, `O(n)` ek bellek kabul edilebilir | birleştirme ya da Timsort | en kötü durum `Θ(n log n)`, kararlı (13.4, 13.9) |
| Kararlılık gereksiz, genel amaç, ortalama hız öncelikli | introsort ya da pdqsort | kütüphane varsayılanları; en kötü durum `n log n` (13.5, 13.9) |
| Ek bellek çok kısıtlı, en kötü durum garanti | yığın | `O(1)` ek bellek, `Θ(n log n)` (13.6) |
| Anahtarlar küçük bir tamsayı aralığında | sayma | karşılaştırmasız, `O(n + k)` (13.7) |
| Sabit genişlikli tamsayı ya da basamaklı anahtar | radix (LSD) | `O(d(n + b))`, kararlı geçişler (13.7) |
| Çok anahtarlı sıralama | son anahtardan başa doğru kararlı geçişler | kararlılık zinciri (13.8) |
| Veri belleğe sığmıyor | dış birleştirme sıralaması | parçaları sırala, k-yollu birleştir (13.4) |

Bu tabloyu ezberlemek yerine, her satırın gerekçesini kendi sözcüklerinle söyleyebiliyor muyuz diye sınamak gerekir. Örneğin "neden radix kararlı geçişler ister?" sorusuna cevap verebilmek, tablonun ötesine geçmenin işaretidir.

## Çözümlü Örnekler

Bu bölümde dört örnek var: ★, ★★, ★★ ve ★★★. Her örnek Bölüm 5'teki altı adımı izler. Adım 6'da elle izlenebilen bir iz tablosu bulunur. Örneklerde kodu yazmadan önce problemi anlamaya ve bir örnekle sınamaya öncelik ver.

### Örnek 1 (★): Hollanda bayrağı, tek geçişte üç renk

**Problem:** Yalnızca `0`, `1` ve `2` içeren bir diziyi, yerinde ve tek bir geçişle sırala. Sıralama sonucu `0`'lar, sonra `1`'ler, sonra `2`'ler olmalı.

**Adım 1 — Anla.** Girdi bir liste, çıktı aynı listenin sıralı hâli. Kısıtlar: tek geçiş, `O(1)` ek bellek. Kenar durumlar: boş liste ve tek renk.

**Adım 2 — Örnekle.** `[2, 0, 2, 1, 0, 1]` dizisi. Dizide iki `0`, iki `1` ve iki `2` vardır. Sonuç `[0, 0, 1, 1, 2, 2]` olmalı. Sayıları ayırmak kolay; zor olan, bunu tek geçişte ve yer değiştirerek yapmaktır.

**Adım 3 — Kaba çöz.** Önce say, sonra yaz: `0`, `1`, `2` sayılarını bulup dizinin başına sırayla yaz. Bu `O(n)` zamanlı ve `O(1)` ek bellekli (üç sayaç) doğru bir çözümdür. Ama iki geçiş yapar: biri saymak, diğeri yazmak. Problem tek geçiş istiyor.

**Adım 4 — Örüntü.** Dizi dört bölgeye ayrılır: solda `0`'lar `[0, lo)`, sonra `1`'ler `[lo, orta)`, sonra henüz incelenmemiş `[orta, hi]`, en sağda `2`'ler `(hi, n)`. Her adımda `a[orta]`'ya bakarsın. `0` ise `lo` ile takas edip ikisini de ilerletirsin. `1` ise yalnızca `orta` ilerler. `2` ise `hi` ile takas edip yalnızca `hi`'yi azaltırsın, çünkü takasla gelen eleman henüz incelenmemiştir.

**Adım 5 — İyileştir.** Sayaçlar yerine üç işaretçi yeter. Her adımda ya bir `0` ya bir `1` ya da bir `2` işlenir ve her `2` tam bir takas yapar. Toplam iş `O(n)`, ek bellek `O(1)`dir. Bu yaklaşımın doğruluğu, bölgelerin her adımda korunan bir değişmezle (invariant) sağlanmasına dayanır. Bunu Adım 6'da iz tablosunda görürsün.

**Adım 6 — Doğrula.** Kod, üç örnek girdiyle birlikte aşağıdadır:

```python
def hollanda_bayragi(a):
    """0, 1, 2 iceren diziyi tek gecisle, yerinde sirala."""
    lo, orta, hi = 0, 0, len(a) - 1
    while orta <= hi:
        if a[orta] == 0:
            a[lo], a[orta] = a[orta], a[lo]
            lo += 1
            orta += 1
        elif a[orta] == 1:
            orta += 1
        else:
            a[orta], a[hi] = a[hi], a[orta]
            hi -= 1
    return a


if __name__ == "__main__":
    print(hollanda_bayragi([2, 0, 2, 1, 0, 1]))
    print(hollanda_bayragi([1, 0]))
    print(hollanda_bayragi([]))
```

```term
$ python -I ornek1.py
[0, 0, 1, 1, 2, 2]
[0, 1]
[]
```

Girdi `[2, 0, 2, 1, 0, 1]` için her adımın izi şöyledir. Son sütun, `(lo, orta, hi)` değerlerini gösterir:

| Adım | İşlem | Dizi | lo | orta | hi |
|---|---|---|---|---|---|
| 0 | başlangıç | `2 0 2 1 0 1` | 0 | 0 | 5 |
| 1 | `a[orta] = 2`: `hi` ile takas, `hi` azalt | `1 0 2 1 0 2` | 0 | 0 | 4 |
| 2 | `a[orta] = 1`: `orta` artır | `1 0 2 1 0 2` | 0 | 1 | 4 |
| 3 | `a[orta] = 0`: `lo` ile takas, ikisini artır | `0 1 2 1 0 2` | 1 | 2 | 4 |
| 4 | `a[orta] = 2`: `hi` ile takas, `hi` azalt | `0 1 0 1 2 2` | 1 | 2 | 3 |
| 5 | `a[orta] = 0`: `lo` ile takas, ikisini artır | `0 0 1 1 2 2` | 2 | 3 | 3 |
| 6 | `a[orta] = 1`: `orta` artır, `orta > hi` olur | `0 0 1 1 2 2` | 2 | 4 | 3 |

Döngü `orta > hi` olduğunda biter. Son dizi `0 0 1 1 2 2`dir; bu, beklenen sonuçtur. Boş liste ve `[1, 0]` girdileri de kodun çıktısında doğru sonucu verir.

**Bunu AI'sız yazabilir misin?** Aynı problemi, sayma yöntemiyle (iki geçiş) ve sonra üç işaretçiyle, boş bir dosyada yaz. Sonra şunu açıkla: `a[orta] = 2` durumunda `orta`'yı neden artırmıyoruz?

### Örnek 2 (★★): Kapalı aralıkları birleştirme

**Problem:** `[s, e]` biçiminde kapalı aralıkların bir listesi verilsin. Birbiriyle kesişen ya da değen aralıkları birleştirip ayrık aralıkların listesini bul. Örneğin `[1, 3]` ile `[2, 6]` birleşip `[1, 6]` olur.

**Adım 1 — Anla.** Girdi aralık listesi, çıktı ayrık ve sıralı aralık listesi. Kenar durumlar: boş liste, tek aralık, değen aralıklar (`[1, 4]` ile `[4, 5]` birleşir), içe geçen aralıklar (`[1, 10]` ile `[2, 3]`).

**Adım 2 — Örnekle.** `[(1, 3), (8, 10), (2, 6), (15, 18), (17, 20)]`. Elle: `1-3` ile `2-6` kesişir, `1-6` olur. `8-10` ayrıdır. `15-18` ile `17-20` kesişir, `15-20` olur. Sonuç `[[1, 6], [8, 10], [15, 20]]`.

**Adım 3 — Kaba çöz.** Her aralığı diğer her aralıkla karşılaştır; kesişen çiftleri birleştir ve bitene kadar tekrarla. Bu `O(n²)` ya da daha kötüdür.

**Adım 4 — Örüntü.** Aralıklar başlangıca göre sıralıysa, bir aralık yalnızca sonuç listesinin **son** aralığıyla kesişebilir. Çünkü sonraki aralıkların başlangıcı, önceki aralıkların başlangıcından büyük ya da eşittir. Yani tek bir geçiş yeter: her aralığı son birleşik aralıkla karşılaştır.

**Adım 5 — İyileştir.** Önce sırala, sonra tek geçiş yap. Sıralama `O(n log n)`, geçiş `O(n)`, toplam `O(n log n)`. Python'un `sorted` fonksiyonu Timsort kullandığı için, aralıklar zaten başlangıca göre kabaca sıralıysa sıralama maliyeti `O(n)`'ye yaklaşır (13.9).

**Adım 6 — Doğrula.** Kod:

```python
def araliklari_birlestir(aralik):
    """Kapali araliklari [s, e] birlestirir. O(n log n)."""
    if not aralik:
        return []
    aralik = sorted(aralik)
    sonuc = [list(aralik[0])]
    for s, e in aralik[1:]:
        if s <= sonuc[-1][1]:
            sonuc[-1][1] = max(sonuc[-1][1], e)
        else:
            sonuc.append([s, e])
    return sonuc


if __name__ == "__main__":
    print(araliklari_birlestir([(1, 3), (8, 10), (2, 6),
                                (15, 18), (17, 20)]))
    print(araliklari_birlestir([(1, 4), (4, 5)]))
```

```term
$ python -I ornek2.py
[[1, 6], [8, 10], [15, 20]]
[[1, 5]]
```

Sıralanmış girdi `(1, 3), (2, 6), (8, 10), (15, 18), (17, 20)` ile iz tablosu:

| Aralık | `sonuc[-1]` önce | Karar | `sonuc` sonra |
|---|---|---|---|
| başlangıç | — | `[1, 3]` ile başla | `[[1, 3]]` |
| `(2, 6)` | `[1, 3]` | `2 ≤ 3`: kesişir, bitişi `max(3, 6) = 6` | `[[1, 6]]` |
| `(8, 10)` | `[1, 6]` | `8 > 6`: ayrı | `[[1, 6], [8, 10]]` |
| `(15, 18)` | `[8, 10]` | `15 > 10`: ayrı | `[[1, 6], [8, 10], [15, 18]]` |
| `(17, 20)` | `[15, 18]` | `17 ≤ 18`: kesişir, bitişi `max(18, 20) = 20` | `[[1, 6], [8, 10], [15, 20]]` |

Son sonuç `[[1, 6], [8, 10], [15, 20]]`dir ve çıktıyla aynıdır. İkinci test, `[1, 4]` ile `[4, 5]`in değmesinin birleştirildiğini gösterir: `4 ≤ 4` olduğu için sonuç `[[1, 5]]`tir.

**Bunu AI'sız yazabilir misin?** Aralıklar birleştirildikten sonra, verilen bir `x` noktasını içeren aralığın olup olmadığını ikili arama ile (Bölüm 14'ün habercisi) sorgulayan bir fonksiyon yaz. Sorgu, sıralı sonuç listesi üzerinde kaç adımda biter?

### Örnek 3 (★★): k-ıncı en küçük eleman (quickselect)

**Problem:** `n` elemanlı bir dizide `k`-ıncı en küçük elemanı bul (0 tabanlı: `k = 0` en küçük, `k = n − 1` en büyük). Tüm diziyi sıralamadan.

**Adım 1 — Anla.** Girdi dizi ve `k`, çıktı bir değer. Kenar durumlar: `k = 0`, `k = n − 1`, tekrarlı değerler.

**Adım 2 — Örnekle.** `[7, 2, 9, 4, 1, 8, 3]` dizisinde `k = 4` (beşinci en küçük). Sıralı hâli `[1, 2, 3, 4, 7, 8, 9]`dur; indeks 4'teki değer `7`dir.

**Adım 3 — Kaba çöz.** Diziyi sırala ve `a[k]`'yi al. Bu `O(n log n)`dir ve doğrudur. Ama yalnızca bir elemana ihtiyacımız var; tüm sıralamanın bedelini ödemek gereksiz.

**Adım 4 — Örüntü.** Hızlı sıralamanın bölümlemesi, pivotu doğru yerine koyar. Pivotun indeksi `i` ise: `k = i` ise cevap pivottur; `k < i` ise cevap solda; `k > i` ise sağda. Yani her adımda yalnızca bir tarafa bakarsın. Tarafın yarıya indiğini varsayarsak toplam iş `n + n/2 + n/4 + ... ≤ 2n` olur.

**Adım 5 — İyileştir.** Kod son elemanı pivot aldığı için sıralı girdide her adım bir elemanı atar ve `O(n²)` olur. Pivotu rastgele seçersen beklenen iş `O(n)`'dir. Bunu tek bir satırla yaparsın: `piv = random.randint(lo, hi)` ve sonra `a[piv]` ile `a[hi]` takas edilir. Aşağıdaki kod, izlenebilirlik için son elemanı pivot alır.

**Adım 6 — Doğrula.** Kod:

```python
def kinci_en_kucuk(a, k):
    """a icinde k. en kucuk (0 tabanli) deger. Beklenen O(n)."""
    a = list(a)
    lo, hi = 0, len(a) - 1
    while True:
        if lo == hi:
            return a[lo]
        p = a[hi]
        i = lo
        for j in range(lo, hi):
            if a[j] < p:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[i], a[hi] = a[hi], a[i]
        if k == i:
            return a[i]
        if k < i:
            hi = i - 1
        else:
            lo = i + 1


if __name__ == "__main__":
    veri = [7, 2, 9, 4, 1, 8, 3]
    for k in range(len(veri)):
        print(k, kinci_en_kucuk(veri, k))
```

```term
$ python -I ornek3.py
0 1
1 2
2 3
3 4
4 7
5 8
6 9
```

`k = 4` için iz. Pivot her turda `a[hi]`dir; sonucu tablo olarak veriyoruz:

| Tur | Aralık `[lo..hi]` | Dizi (tur başı) | Pivot | Pivot indeksi `i` | Karar |
|---|---|---|---|---|---|
| 1 | `0..6` | `7 2 9 4 1 8 3` | 3 | 2 | `k = 4 > 2`: sağa, `lo = 3` |
| 2 | `3..6` | `2 1 3 4 7 8 9` | 9 | 6 | `k = 4 < 6`: sola, `hi = 5` |
| 3 | `3..5` | `2 1 3 4 7 8 9` | 8 | 5 | `k = 4 < 5`: sola, `hi = 4` |
| 4 | `3..4` | `2 1 3 4 7 8 9` | 7 | 4 | `k = i = 4`: cevap `a[4] = 7` |

Dördüncü turda `i = k` olduğu için `7` döndürülür. Kodun çıktısı da `4 7` satırını verir.

**Bunu AI'sız yazabilir misin?** Aynı işlevi, `k`'yı sağ taraftan (`n − 1 − k`) soran bir sürümle yaz. Sonra şunu açıkla: rastgele pivot yerine medyan-of-üç kullanırsan sıralı girdide beklenen iş değişir mi?

### Örnek 4 (★★★): Ters çevrim sayısını birleştirme sıralaması ile bulma

**Problem:** Bir dizide `i < j` ama `a[i] > a[j]` olan çiftlerin sayısını (ters çevrim sayısı) `O(n log n)` zamanda bul. Örneğin `[2, 4, 1, 3, 5]` dizisinde üç ters çevrim vardır: `(2, 1)`, `(4, 1)`, `(4, 3)`.

**Adım 1 — Anla.** Girdi dizi, çıktı tamsayı. Ters çevrim sayısı, eklemeli sıralamanın takas sayısına eşittir (13.3). Kenar durumlar: sıralı dizi (0), tersine sıralı dizi (`n(n−1)/2`), eşit elemanlar (eşit çift ters çevrim sayılmaz).

**Adım 2 — Örnekle.** `[2, 4, 1, 3, 5]` için üç çift elle sayılır, sonuç 3. `[4, 3, 2, 1]` için bütün çiftler (6 çift) ters çevrimdir.

**Adım 3 — Kaba çöz.** Her `i < j` çiftine bak ve `a[i] > a[j]` ise say. Bu `O(n²)`dir. Ters çevrimleri tek tek saymak gereksiz gibi görünür; ama bu bir örüntü arayışına götürür.

**Adım 4 — Örüntü.** Birleştirme sıralamasında iki sıralı parça `sol` ve `sag` birleşirken, `sag[j]` sol parçadan küçük olduğunda `sag[j]` ile `sol[i]`, `sol[i+1]`, ..., `sol[son]` arasındaki her çift ters çevrimdir. Bunların sayısı `len(sol) − i`dir. Bu, birleştirmenin karşılaştırmasıyla aynı anda hesaplanır, ekstra bir tarama gerektirmez.

**Adım 5 — İyileştir.** Birleştirme sıralamasını bu sayımla genişlet. Her birleştirme adımında sayım eklenir; özyinelemenin sonunda üç parçanın (sol, sağ, çapraz) toplamı döner. Toplam `O(n log n)`dir, çünkü birleştirme sıralamasının maliyeti budur.

**Adım 6 — Doğrula.** Kod:

```python
def ters_sayisi(a):
    """Ters cevrim (i < j ve a[i] > a[j]) sayisi, merge sort ile."""
    def ayir(v):
        if len(v) < 2:
            return v, 0
        orta = len(v) // 2
        sol, c1 = ayir(v[:orta])
        sag, c2 = ayir(v[orta:])
        birlesik = []
        i = j = c = 0
        while i < len(sol) and j < len(sag):
            if sol[i] <= sag[j]:
                birlesik.append(sol[i])
                i += 1
            else:
                birlesik.append(sag[j])
                j += 1
                c += len(sol) - i
        birlesik += sol[i:] + sag[j:]
        return birlesik, c1 + c2 + c
    return ayir(list(a))[1]


if __name__ == "__main__":
    print(ters_sayisi([2, 4, 1, 3, 5]))
    print(ters_sayisi([3, 1, 2]))
    print(ters_sayisi([1, 2, 3, 4]))
    print(ters_sayisi([4, 3, 2, 1]))
```

```term
$ python -I ornek4.py
3
2
0
6
```

`[2, 4, 1, 3, 5]` girdisi için birleştirmeler ve her birleştirmenin çapraz sayımı:

| Birleştirme | `sol` | `sag` | Çapraz sayım | Sonuç |
|---|---|---|---|---|
| 1 | `[2]` | `[4]` | 0 | `[2, 4]` |
| 2 | `[3]` | `[5]` | 0 | `[3, 5]` |
| 3 | `[1]` | `[3, 5]` | 0 | `[1, 3, 5]` |
| 4 | `[2, 4]` | `[1, 3, 5]` | 3 | `[1, 2, 3, 4, 5]` |

Dördüncü birleştirmede çapraz sayım şöyle oluşur: `1` sağdan alındığında `sol`da kalan `2` ve `4` iki ters çevrim üretir (+2). Sonra `3` alındığında `sol`da kalan yalnızca `4` vardır (+1). Toplam `0 + 0 + 0 + 3 = 3`tür. Diğer girdiler de doğru sonucu verir: `[3, 1, 2]` için 2, sıralı `[1, 2, 3, 4]` için 0, tersine `[4, 3, 2, 1]` için 6.

**Bunu AI'sız yazabilir misin?** Aynı sayımı, birleştirme yerine eklemeli sıralamaya uygula. Kaç işlem yapar ve bu neden `O(n²)`dir? Sonra iki sürümün takas ve karşılaştırma sayılarını `n = 10 000` rastgele girdi için karşılaştır.

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Sıralama algoritmaları, ancak kendi elinle yazdığında ve kendi ölçümünle doğruladığında öğrenilir. Bir ölçüm beklediğinden farklı çıktığında nedenini bulmak, bu bölümün asıl eğitimidir.
:::

### Proje 1 (★★): Sıralama laboratuvarını genişlet

**Amaç:** Bu bölümdeki `siralama.c` laboratuvarına yeni bir algoritma ekleyip tüm algoritmaları aynı tablo altında karşılaştırmak.

**Yapılacak / Beklenen davranış:**

1. Yeni bir algoritma yaz: ör. Shell sort (aralık dizisi `n/2, n/4, ..., 1`) ya da introsort'un basit biçimi (hızlı sıralama, derinlik sınırı ve yığın yedeği).
2. Algoritmayı `Siralayici` imzasına uydur ve `algler` dizisine ekle. Bütün karşılaştırmalar `kucuk`, bütün takaslar `takas` üzerinden geçsin.
3. Tablo kipine, kararlılık ve karşılaştırma sayısının yanına bir "yazma" sütunu ekle (`yaz` sayacı zaten var).
4. Yeni algoritmanın dört girdi türü için tablo satırlarını üret ve kendi sonuçlarını yorumla.

**Önerilen yaklaşım:** Önce yeni algoritmayı küçük bir diziyle (`iz` benzeri) doğrula. Sonra tabloyu büyüt. Shell sort kararlı değildir; bunu tablo üzerinde kendi gözlemin olarak yaz. Ölçüm için Bölüm 12.10'daki protokolü kullan: sabit tohum, en iyi süre, makine bilgisi.

**Başarı kriterleri:**

- Yeni algoritma, dört girdi türünde ve `n = 20 000` için `dogrulama tamam` çıktısını verir.
- ASan ve UBSan (`-fsanitize=address,undefined`) hiçbir uyarı vermez.
- Karşılaştırma sayısı ve süre tablosu, makine bilgisiyle birlikte yazılmıştır.
- Kararlılık sonucu, bu bölümdeki teoriyle uyumludur ya da farkı açıklanmıştır.

### Proje 2 (★★★): EV Dashboard için çok anahtarlı kararlı sıralama

**Amaç:** EV Dashboard'a gelen sensör kayıtlarını (sensör kimliği, zaman damgası, değer) `10⁶` kayıt için, önce sensör kimliğine, sonra zaman damgasına göre sıralamak. Sonuçta her sensörün kendi zaman dizisi bulunmalıdır.

**Yapılacak / Beklenen davranış:**

1. Kayıtları C'de bir yapı olarak tanımla: `sensor` (16 bit tamsayı), `zaman` (32 bit işaretsiz), `deger` (kayan nokta ya da tamsayı).
2. Girdiyi xorshift ile üret (tohum sabit). Sensör kimliği `0..63` aralığında, zaman damgası rastgele olsun.
3. Çok anahtarlı sıralamayı kararlı iki geçişle yap. Hangi anahtarla başlayacağını ve neden önce en az önemli anahtarı sıralaman gerektiğini açıkla (13.8).
4. Sonucu bağımsız bir kontrol ile doğrula: küçük girdide (ör. 1000 kayıt) `qsort` ile karşılaştırma yap, ancak bunu kararlı bir karşılaştırma fonksiyonu olarak yaz (`sira` alanı gibi bir ikincil anahtar ekleyerek).
5. Bellek ve süre ölç; tepe bellek kullanımını (ör. geçici dizi boyutu) raporla.

**Önerilen yaklaşım:** LSD radix mantığını 16 bitlik sensör kimliği ve 32 bitlik zaman üzerinde uygula. Her geçiş bir sayma sıralaması olabilir. Geçici dizi tek kez ayrılsın; her geçişte dizi değiştirilsin. Bu projede, sıralamanın kendi karmaşıklığı ile veri hazırlama maliyetini ayrı ölç.

**Başarı kriterleri:**

- Çıktı, her sensör için zaman sırasındadır ve sensörler kimlik sırasındadır; bu, küçük girdide bağımsız bir kontrolle doğrulanmıştır.
- Girdi aynı tohumla iki kez üretildiğinde çıktılar birebir aynıdır.
- `10⁶` kayıt için süre ve tepe bellek, makine bilgisiyle birlikte raporlanmıştır.
- ASan ve UBSan ile çalıştırıldığında hata çıkmaz.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün, sonra kendi kodunla doğrula.

1. ★ Dizide tek bir eleman dışında hepsi çift sayılarsa ve bu elemanın yeri belli değilse, eklemeli sıralamanın takas sayısı nedir? Ters çevrim sayısıyla açıkla.
2. ★ Kabarcık sıralamasında erken çıkışı kaldırırsan, en iyi durum ne olur? Hangi girdi bu farkı gösterir?
3. ★★ Eklemeli sıralamanın ikili arama (binary search) ile yer bulan bir sürümü, karşılaştırma sayısını `O(n log n)`ye indirir. Yazma sayısı ne olur ve neden hâlâ `O(n²)`dir? (Mülakat)
4. ★★ `n` elemanlı bir dizi, her elemanı en fazla `k` konum uzakta olacak şekilde sıralanmış olsun. Bu diziyi `O(n log k)` zamanda sıralayan bir yöntem bul. (Mülakat)
5. ★★ Birleştirme sıralamasını bağlı liste üzerinde `O(1)` ek bellekle yapabileceğini, dizi sürümünün ise `O(n)` gerektirdiğini açıkla. Birleştirme adımında neyi değiştirmek gerekir?
6. ★★ Hızlı sıralamada tüm elemanlar eşit olduğunda Lomuto ve Hoare şemalarının karşılaştırma sayılarını yaz. Hangisi `n²` olur, neden? (Mülakat)
7. ★★ Radix sıralamasında tabanı `b = 2` seçersen, `32` bitlik anahtar için kaç geçiş gerekir? Tabanı `b = 65 536` seçersen? Hangisi daha iyi olabilir ve neden?
8. ★★ Bir dizide en fazla bir elemanın yeri yanlış olduğunu biliyorsun. Bu diziyi `O(n)` zamanda sıralayan bir algoritma yaz. (Mülakat)
9. ★★★ Quicksort'ta bölümlemeden sonra daha küçük parçaya özyineleyip büyük parçayı döngüyle işlemenin, yığın derinliğini `O(log n)` tuttuğunu kanıtla. (Mülakat)
10. ★★★ `n` tane ondalıklı sayıyı (`0 ≤ x < 1`) `O(n)` ortalama zamanda sıralayan kova sıralamasının (bucket sort) beklenen zamanını açıkla. En kötü durumu ne zaman alır?
11. ★★★ Yığın sıralamasını, `min-heap` ile yapıp dizinin sonunda azalan sıra elde etmek mümkün mü? Hangi değişiklikler gerekir? (Mülakat)
12. ★★★ İki sıralı `n` elemanlık diziyi, ortak `k` elemanlı çıktı bulmadan birleştirme karmaşıklığını düşün. `k`-yollu birleştirme (k sıralı dizi) için bir yığın kullanarak `O(n log k)` algoritmasını açıkla. (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: CPython 3.12.10'un `Objects/listobject.c` dosyası. Dosyayı `python/cpython` deposunun `v3.12.10` etiketinden indirdik ve tasarım notunu `Objects/listsort.txt` içinde doğruladık. Aşağıdaki kesitler birebir alınmıştır; sadeleştirme yapılmamıştır.

Önce, `count_run` fonksiyonunun kullandığı `IFLT` makrosunun tanımı:

```c
#define IFLT(X, Y) if ((k = ISLT(X, Y)) < 0) goto fail;  \
           if (k)
```

Makro, `ISLT` ile karşılaştırma yapar; sonuç `k` değişkenine yazılır ve bir hata olursa `fail` etiketine atlanır. Yani bu makro, C'de hata kontrollü bir karşılaştırma ifadesidir.

Sonra, dizinin başından itibaren en uzun doğal çalıştırmayı (run) bulan `count_run`. Bu kesitte fonksiyon imzası, aşağıdaki minrun kesitinde ise bir yorum satırı sayfa genişliğine sığması için iki satıra bölünmüştür; içerikleri değişmemiştir:

```c
count_run(MergeState *ms, PyObject **lo, PyObject **hi,
          int *descending)
{
    Py_ssize_t k;
    Py_ssize_t n;

    assert(lo < hi);
    *descending = 0;
    ++lo;
    if (lo == hi)
        return 1;

    n = 2;
    IFLT(*lo, *(lo-1)) {
        *descending = 1;
        for (lo = lo+1; lo < hi; ++lo, ++n) {
            IFLT(*lo, *(lo-1))
                ;
            else
                break;
        }
    }
    else {
        for (lo = lo+1; lo < hi; ++lo, ++n) {
            IFLT(*lo, *(lo-1))
                break;
        }
    }

    return n;
fail:
    return -1;
}
```

Fonksiyon, `lo` ile başlayıp ilk iki elemanı karşılaştırır. Elemanlar azalıyorsa `descending = 1` olur ve `lo[0] > lo[1] > ...` koşulu sürdüğü sürece sayılır. Artıyorsa `lo[0] <= lo[1] <= ...` koşulu sürdüğü sürece sayılır. Yorum, azalan tanımındaki katılığın (`>` ve `≥` değil) kararlılık için gerekli olduğunu söyler: eşit elemanlar aynı azalan dizide olamaz, böylece çalıştırma güvenle ters çevrilebilir.

Son olarak, minrun uzunluğunu hesaplayan `merge_compute_minrun`:

```c
static Py_ssize_t
merge_compute_minrun(Py_ssize_t n)
{
    Py_ssize_t r = 0;           /* becomes 1 if any 1 bits are shifted
                                   off */

    assert(n >= 0);
    while (n >= 64) {
        r |= n & 1;
        n >>= 1;
    }
    return n + r;
}
```

Bu fonksiyon, `n` 64'ten küçük olana kadar sağa kaydırır ve kaydırılan düşük bitlerden herhangi biri birse sonuca `1` ekler. Sonuç, dokümandaki gibi 32 ile 64 arasındadır (n 64'ten küçükse n'nin kendisi).

**Sorular — cevaplamadan geçme:**

1. `count_run` azalan çalıştırmayı `IFLT(*lo, *(lo-1))` ile tanımlıyor. Eşit iki eleman `[3, 3]` olsaydı, çalıştırma hangi yöne girerdi ve dönüş değeri ne olurdu? Kararlılık bu seçimle nasıl etkilenir?
2. Dizi `[1, 2, 2, 1]` olsun. `count_run` kaç döndürür ve `descending` hangi değeri alır? Cevabını kodu adım adım izleyerek doğrula.
3. `merge_compute_minrun(1000)` kaç kez kaydırma yapar ve sonuç ne olur? Sonucun 32 ile 64 arasında olduğunu gösteren hangi özellik vardır?
4. `count_run` ve `merge_compute_minrun` birlikte kullanıldığında, `n = 1000` rastgele girdi için kaç run oluşması beklenir? Bu tahmini `listsort.txt`'teki minrun açıklamasıyla karşılaştır.
5. `sorted()` sıralı bir listede neden `O(n)`'ye yakın çalışır? Bu davranışı sağlayan kod hangi fonksiyonda ve hangi koşulda devreye girer?
6. CPython'un Timsort'u ile bu bölümdeki birleştirme sıralaması, rastgele girdide neden benzer maliyetli olur, ama sıralı girdide neden ayrılır? Cevabında Ölçüm (13.10) ile bu kodun ilişkisini kur.

## Bölüm Özeti

Bu bölümde sıralamayı bir problem olarak değil, bir karşılaştırma ve takas ağı olarak inceledik:

- **Ölçütler:** karşılaştırma, yazma, zaman, yardımcı bellek, kararlılık, yerinde ve uyarlanabilirlik. Laboratuvarda bunların hepsi sayılır.
- **Alt sınır:** karşılaştırma tabanlı sıralama en az `log₂(n!) = Ω(n log n)` karşılaştırma yapar. Karar ağacı bu sonucun kanıtıdır.
- **Basit sıralamalar:** kabarcık, seçmeli ve eklemeli sıralama `O(n²)`dir. Eklemeli ve kabarcık, sıralı girdide `O(n)`'ye iner ve kararlıdır. Seçmeli kararsızdır ve hiçbir girdi için `n²`den kaçamaz.
- **Birleştirme:** `Θ(n log n)` her durumda, `O(n)` ek bellek, kararlı.
- **Hızlı:** ortalama `Θ(n log n)`, en kötü `Θ(n²)`. Pivot seçimi, Hoare ve Lomuto bölümlemesi, eşit elemanlar ve küçük parçaya özyineleme ile yığın derinliğinin `O(log n)` tutulması.
- **Yığın:** `Θ(n log n)` her durumda, `O(1)` ek bellek, kararsız.
- **Karşılaştırmadan kaçış:** sayma ve radix, anahtarın yapısını kullanarak alt sınırı aşar. Radix için kararlı geçişler zorunludur.
- **Kararlılık ve çok anahtarlı sıralama:** son anahtardan başa doğru kararlı geçişler. Python `sorted` kararlıdır; C `qsort` kararlılık garantisi vermez (glibc pratikte kararlı sonuç verebilir, ama buna güvenilmez).
- **Gerçek dünya:** Timsort (kararlı, sıralı girdide `O(n)`), introsort (GCC), pdqsort (Go) ve Rust'ın driftsort/ipnsort'u. Her iddia kaynağıyla doğrulanmalıdır.

**Sonraki bölümde:** Bu bölümde sıraladığımız diziler, bir sonraki bölümde arama için kullanılacak. Bölüm 14'te sıralı bir dizi üzerinde doğrusal aramanın `O(n)`'den ikili aramanın `O(log n)`'ye nasıl indiğini göreceğiz. Bölüm 14, lower ve upper bound aramalarını, rotasyonlu dizilerde aramayı, matris aramasını ve interpolasyon aramasını da kapsayacak. Sıralamanın kendisine yaptığımız yatırımın arama tarafında nasıl geri döndüğünü de Bölüm 14'te göstereceğiz.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Kararlı bir sıralama algoritması kararsız bir sıralama algoritmasından ne zaman daha değerlidir? Çok anahtarlı bir sıralamada bu neden önemlidir?
2. Hızlı sıralamanın en kötü durumunu tetikleyen girdiyi nasıl tanırsın? Pivotu rastgele seçmek bu sorunu neden çözer ama tamamen ortadan kaldırmaz?
3. Yığın sıralamasının ek belleği `O(1)`, ama önbellek davranışı genellikle hızlı sıralamadan kötüdür. Bu ikilemi nasıl açıklarsın?
4. Sayma sıralaması karşılaştırma yapmadığı halde `Ω(n log n)` alt sınırına neden takılmaz? Alt sınırın kapsamını nasıl tanımlarsın?
5. Radix sıralamasında geçişlerin en önemli basamaktan başlayarak yapılması neden yanlış olur? Hangi anahtar kümesi için bu kuralı bozabilirsin?
6. Bir veritabanında milyon satırlık bir tabloyu bellekte sığmayacak kadar büyükken sıralaman gerekiyor. Dış birleştirme sıralamasını nasıl kurarsın, I/O maliyetini nasıl hesaba katarsın?
7. Python'un `sorted` fonksiyonunu kullanarak aynı anda iki anahtara göre (önce yaş, sonra isim) sıralamak istiyorsun. Bunu bir çağrıyla mı, iki çağrıyla mı yaparsın ve neden?
8. Bir mülakat sorusunda "bu diziyi sırala" diyorlar ve dizi yalnızca `0` ile `100` arasında tamsayılar içeriyor. Hangi algoritmayı seçersin ve hangi koşulda bu seçimi değiştirirsin?
:::
