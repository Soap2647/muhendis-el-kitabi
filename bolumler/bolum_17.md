%% kisim_no: IV
%% kisim_ad: Algoritmalar
%% bolum_no: 17
%% baslik: Graph Algoritmaları

## Giriş: Ağın içinde yol bulmak

Bölüm 11'de grafı nasıl temsil edeceğimizi öğrendik. Komşuluk listesi ile bir grafın kenarlarını saklayabiliyorduk; BFS ve DFS ile düğümleri dolaşabiliyorduk. Ama bu gezinmeler "hangi düğümlere ulaşabilirim?" sorusunu cevaplıyordu, "en ucuz yol hangisi?" sorusunu değil. Bu bölüm o ikinci soruya geçiş yapıyor ve grafın bütün önemli algoritmalarını tek bir yerde topluyor.

Bu algoritmalar mühendisliğin her yerinde çıkar. İnternet yönlendiricileri bir paketin hangi yoldan gideceğini en kısa yol hesabıyla belirler (OSPF Dijkstra kullanır). Bir paket yöneticisi `pip` ya da `apt` bir kütüphaneyi kurmadan önce bağımlılıkları doğru sırada kurmak zorundadır; bu bir topolojik sıralamadır. Bir derleyici modül bağımlılıklarındaki döngüyü fark etmek zorundadır. Bir sensör ağında tek bir düğüm arızalandığında ağın ikiye bölünüp bölünmediği, Bölüm 11'in sonunda sorduğumuz soruydu; cevabı eklem noktaları verir. Mülakatlarda da graf soruları sık gelir ve adayın hangi algoritmayı seçtiğine, neden seçtiğine bakılır.

Savunma sanayiinde ise rota planlama doğrudan bu konudur. Bir İHA'nın kalkış ile hedef arasında engellerden kaçıp en az enerjiyi harcadığı rotayı bulması, ızgara üzerinde bir en kısa yol problemidir. Bölüm 62'deki Viterbi algoritması da bir DP'dir (Bölüm 16) ve durum geçişleri bir DAG üzerinde ilerler; bu bölümde gördüğümüz topolojik sıra fikri, bu tür hesapların neden tek geçişte çalıştığını açıklar.

Bu bölümde iki büyük ailenin arasında bir ayrım göreceğiz. Birincisi **gezinme ve yapı** algoritmaları: DFS, topolojik sıralama, güçlü bağlı bileşenler, eklem noktaları, iki renklendirme. İkincisi **ağırlık ve optimizasyon** algoritmaları: en kısa yollar ve minimum yayılan ağaç. Birincisinde kenarın ağırlığı yoktur, cevap bir yapı ya da bir sıradır. İkincisinde her kenarın bir maliyeti vardır ve cevap o maliyetin en küçüğüdür.

::: not
Bu bölümdeki C programları WSL içinde Ubuntu 24.04 üzerinde gcc 13.3.0 ile `-std=c11 -Wall -Wextra` uyarılarıyla derlendi; bellek ve tanımsız davranış denetimi için `-fsanitize=address,undefined` ile de çalıştırıldı. Python programları Python 3.12.10 ile çalıştırıldı. Rastgele veriler `random.Random(42)` (Python) ya da sabit tohumlu bir xorshift (C) ile üretildi; sayılar sizde de aynı çıkmalıdır. Windows'ta `long` 4 bayttır, bu yüzden C kodunda tam sayıları `int` ve `uint32_t` ile açıkça seçtik. Yığın derinliği konusunda WSL'nin varsayılan yığını 8192 KB'dir (`ulimit -s`).
:::

## 17.1 DFS: derine inmek ve zaman damgaları

**DFS (derinlemesine arama, depth-first search)** bir düğümden başlar, bir komşusuna gider, oradan da yapabildiği kadar derine iner. Geri dönmesi gerektiğinde ise son ziyaret ettiği düğüme döner. Bölüm 11.6'da DFS'i bir gezinme aracı olarak gördük. Burada onu bir **analiz aracı** olarak kullanacağız: her düğüme iki zaman damgası vereceğiz ve bu damgalar bize grafın yapısını anlatacak.

Her düğümün üç durumu olabilir. **Beyaz**: henüz hiç görülmemiş. **Gri**: ziyaret edilmiş ama işi bitmemiş (şu an yığında, yani hâlâ içinde bulunduğumuz bir dalın parçası). **Siyah**: işi tamamen bitmiş. Her düğüm beyaz olarak başlar. Gri olduğunda bir **giriş zamanı** `d[u]` alır; siyah olduğunda bir **çıkış zamanı** `f[u]` alır. Zamanlar ilk ziyaretten itibaren 1, 2, 3, ... diye sayılır. Böylece `d[u] < f[u]` her zaman doğrudur ve iki düğümün zaman aralıkları ya iç içe ya da ayrıktır; kesişip ayrı kalmazlar. Bu, DFS'in ağaç yapısının temel özelliğidir.

Kenarları DFS sırasında dört türe ayırabiliriz. `u -> v` kenarını ele alalım. `v` beyazsa kenar bir **ağaç kenarıdır**: DFS ağacının bir parçasıdır. `v` griyse `v`, `u`'nun atasıdır (hâlâ yığında). Bu kenara **geri kenar** (back edge) denir ve yönlü graftaki bir döngünün işaretidir. `v` siyahsa iki durum vardır: `d[u] < d[v]` ise `v`, `u`'nun bir torunudur ve kenar **ileri kenar**dır. `d[u] > d[v]` ise `v` farklı bir dalda bitmiştir ve kenar **çapraz kenar**dır.

Bu sınıflandırmanın en önemli sonucu şudur: **yönlü bir graf, ancak ve ancak DFS sırasında bir geri kenar bulunduğunda döngü içerir.** Döngü varsa, döngüdeki en son ziyaret edilen düğüm, döngünün ilk düğümüne geri bir kenarla bağlanır ve bu kenar griye düşer. Tersine, döngü yoksa hiçbir kenar griye düşmez. Bu gözlemi 17.3'te topolojik sıralama için kullanacağız.

Aşağıdaki C programı altı düğümlü küçük bir yönlü grafta DFS'i özyinelemeli olarak çalıştırır, her kenarı sınıflandırır ve zaman damgalarını yazdırır. Graf, `komsu[u][i]` dizisiyle saklanır: her düğümün çıkış kenarları eklenme sırasıyla tutulur. Kod iki kısımdan oluşur; önce grafın veri yapısı ve yardımcı fonksiyonlar gelir.

Aşağıdaki kod, DFS'in özyinelemeli sürümünün ve kenar sınıflandırmanın tamamıdır. Programın tümü (`dfs.c`) bu bölümde ve 17.2'de iki parça hâlinde verilmiştir.

```c
/* dfs.c - Yonlu graf uzerinde DFS: ozyinelemeli, yinelemeli (dogru ve
 * naif) ve kenar siniflandirmasi. Rastgele graflarda uc surumu sinar.
 * Derleme: gcc -std=c11 -Wall -Wextra -O2 dfs.c -o dfs
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define MAXN 64
#define MAXD 4           /* bir dugumun en fazla cikis kenari */
#define BEYAZ 0
#define GRI 1
#define SIYAH 2

typedef struct {
    int n;
    int dere[MAXN];           /* dere[u]: u'nun cikis kenari sayisi */
    int komsu[MAXN][MAXD];    /* komsu[u][i]: u'nun i. kenari */
} Graf;

static int renk[MAXN], d[MAXN], f[MAXN], zaman;
static int say[4];
static const char *ad[4] = {"agac", "geri", "ileri", "capraz"};

static void sifirla(void) {
    memset(renk, 0, sizeof renk);
    memset(d, 0, sizeof d);
    memset(f, 0, sizeof f);
    memset(say, 0, sizeof say);
    zaman = 0;
}

/* u -> v kenarini siniflandirir. Kenar, v beyazken cagrilmalidir. */
static void sinifla(int u, int v, int yaz) {
    int t;
    if (renk[v] == BEYAZ)     t = 0;  /* agac: v yeni kesfedildi */
    else if (renk[v] == GRI)  t = 1;  /* geri: v, u'nun atasi */
    else if (d[u] < d[v])     t = 2;  /* ileri: v, u'nun torunu */
    else                      t = 3;  /* capraz: v farkli bir dal */
    say[t]++;
    if (yaz)
        printf("  %d -> %d : %s\n", u, v, ad[t]);
}

```

Ana fonksiyon, sınıflandırma sonucunu ve zaman damgalarını yazdırır. Önce özyinelemeli DFS'in kenar akışını izleyelim; ardından aynı grafın tüm rastgele testlerini 17.2'de göreceğiz.

```c
static void dfs_rec(const Graf *g, int u, int yaz) {
    renk[u] = GRI;
    d[u] = ++zaman;
    for (int i = 0; i < g->dere[u]; i++) {
        int v = g->komsu[u][i];
        sinifla(u, v, yaz);
        if (renk[v] == BEYAZ)
            dfs_rec(g, v, yaz);
    }
    renk[u] = SIYAH;
    f[u] = ++zaman;
}

/* Dogru yinelemeli DFS: yiginda (dugum, siradaki kenar) tutulur. */
```

Özyinelemeli DFS fonksiyonu, yukarıdaki kuralın birebir uygulamasıdır: düğüm griye çekilir, zamanı yazılır, her çıkış kenarı sınıflandırılır, beyaz komşuya inilir, sonunda düğüm siyaha çekilip çıkış zamanı yazılır. Ana fonksiyon bu grafı çalıştırır:

```c
int main(void) {
    Graf g;
    int kenarlar[][2] = {{0,1},{0,3},{0,2},{1,2},{2,0},{3,2},{4,5}};
    g.n = 6;
    memset(g.dere, 0, sizeof g.dere);
    size_t m = sizeof kenarlar / sizeof kenarlar[0];
    for (size_t i = 0; i < m; i++) {
        int u = kenarlar[i][0];
        g.komsu[u][g.dere[u]++] = kenarlar[i][1];
    }

    sifirla();
    printf("Kenar siniflandirmasi (ozyinelemeli DFS):\n");
    tum_kokler(&g, 1);
    printf("Dugum  d  f\n");
    for (int u = 0; u < g.n; u++)
        printf("  %d    %2d %2d\n", u, d[u], f[u]);
    printf("Sayim: agac=%d geri=%d ileri=%d capraz=%d\n",
           say[0], say[1], say[2], say[3]);

    int kesif[MAXN], gor[MAXN], ns[MAXN], k = 0;
    kesif_sirasi(g.n, kesif);
    memset(gor, 0, sizeof gor);
    for (int u = 0; u < g.n; u++)
        k = dfs_naif(&g, u, gor, ns, k);
    printf("Ozyinelemeli ziyaret: ");
    for (int i = 0; i < g.n; i++)
        printf("%d ", kesif[i]);
    printf("\nNaif ziyaret       : ");
    for (int i = 0; i < g.n; i++)
        printf("%d ", ns[i]);
    printf("\n");

    /* Rastgele graflarda uc surumu karsilastir. */
    enum { TUR = 200, N = 40 };
    int dogru = 0, naif_farkli = 0;
    for (int t = 0; t < TUR; t++) {
```

Aşağıdaki çıktı, bu programın derlenip çalıştırılmasından elde edildi. Zaman damgaları ile kenar sınıfları el ile yaptığımız izle aynıdır: `0 -> 2` kenarı ileri kenardır çünkü `2` siyahtır ve `d[0] = 1 < d[2] = 3`.

```term
$ gcc -std=c11 -Wall -Wextra -O2 dfs.c -o dfs
$ ./dfs
Kenar siniflandirmasi (ozyinelemeli DFS):
  0 -> 1 : agac
  1 -> 2 : agac
  2 -> 0 : geri
  0 -> 3 : agac
  3 -> 2 : capraz
  0 -> 2 : ileri
  4 -> 5 : agac
Dugum  d  f
  0     1  8
  1     2  5
  2     3  4
  3     6  7
  4     9 12
  5    10 11
Sayim: agac=4 geri=1 ileri=1 capraz=1
Ozyinelemeli ziyaret: 0 1 2 3 4 5 
Naif ziyaret       : 0 2 3 1 4 5 

Rastgele 200 graf (n=40, tohum 42):
  yinelemeli == ozyinelemeli (d ve f): 200/200
  naif sira ozyinelemeliden farkli   : 200/200
```

Aynı program `-fsanitize=address,undefined` ile de derlendi; bellek ve tanımsız davranış hatası bildirilmedi ve çıkış kodu `0` döndü.

```term
$ gcc -fsanitize=address,undefined -std=c11 -g dfs.c -o dfs_asan
$ ./dfs_asan > /dev/null; echo $?
0
```

Çıktıyı adım adım okuyalım. DFS `0`'dan başlar (`d[0] = 1`). `0`'ın ilk komşusu `1`'dir; `1` beyazdır, ağaç kenarıdır, `d[1] = 2` olur. `1`'in komşusu `2`'dir, yine ağaç kenarı, `d[2] = 3`. `2`'nin tek komşusu `0`'dır ve `0` griye (yığında) olduğu için bu bir **geri kenar**dır: `2 -> 0` bir döngüyü (`0 -> 1 -> 2 -> 0`) işaretler. `2`'nin işi biter, `f[2] = 4`; `1`'in işi biter, `f[1] = 5`. Sonra `0`'ın ikinci komşusu `3`'e iner (`d[3] = 6`). `3`'ün komşusu `2`'dir ve `2` siyahtır; `d[3] = 6 > d[2] = 3` olduğu için bu bir **çapraz kenar**dır. `0`'ın üçüncü komşusu `2`'dir; `2` siyah ve `d[0] = 1 < d[2] = 3` olduğu için bu bir **ileri kenar**dır. Son olarak `4` beyazdır ve `4 -> 5` ağaç kenarı olarak ziyaret edilir. Bu grafta dört farklı tür de vardır.

Şekil 17.1, aynı grafın DFS ağacını ve zaman damgalarını gösterir. Kenar renkleri sınıfları ayırır.

![Şekil 17.1: DFS zaman damgaları (d/f) ve kenar türleri. Ağaç kenarları lacivert, geri kenar bordo, ileri kenar yeşil, çapraz kenar hardal renkte.](gorseller/b17_dfs_zaman.png)

Burada iki noktaya dikkat edin. İlki: DFS her kökten (beyaz düğümden) yeniden başlatılır. Yukarıdaki kod `tum_kokler` ile tüm düğümleri dolaşır; `4` ve `5` ilk kökten ulaşılamadığı için ikinci bir ağaç oluşturur. İkincisi: `d` ve `f` dizileri, tüm sınıflandırmadan sonra grafın tamamı hakkında bilgi taşır. Bu bilgiyi 17.3, 17.4 ve 17.5'te kullanacağız.

Özyinelemeli DFS'in karmaşıklığı `O(V + E)`'dir: her düğüm bir kez griye, bir kez siyaha geçer ve her kenar bir kez incelenir. Ancak özyineleme derinliği grafın en uzun yoluna eşittir. Bölüm 10.5'te gördüğümüz gibi, zincir biçimindeki bir graf yığını aşabilir. Bu yüzden büyük graflarda DFS'in yinelemeli sürümü tercih edilir; onu 17.2'de yazacağız.

## 17.2 Yinelemeli DFS: sırayı birebir korumak

Büyük bir grafta özyinelemeli DFS yığın taşmasına gidebilir. Çözüm, DFS'in kendi yığınını açıkça tutmaktır. Ama burada ince bir tuzak var: yığına düğümleri "komşularını yığına it" diye basit bir şekilde koyarsanız, ortaya çıkan gezinme **doğru bir DFS değildir**. Sırası değişir ve zaman damgaları özyinelemeli sürümle uyuşmaz.

Doğru yöntem, yığında her düğüm için **bir sonraki bakılacak kenarın indeksini** de tutmaktır. Bir düğüm yığının tepesindeyken, indeksi ilerletip bir sonraki komşuya bakar; komşu beyazsa onu yığına iter. Tüm kenarları bittiğinde düğüm yığından çıkar ve siyaha çekilir. Bu, özyinelemenin çağrı yığınını birebir taklit eder. Aşağıdaki fonksiyon bunu yapar.

```c
static void dfs_yin(const Graf *g, int s) {
    int yigin[MAXN], sira[MAXN], ust = 0;
    renk[s] = GRI;
    d[s] = ++zaman;
    sira[s] = 0;
    yigin[ust++] = s;
    while (ust > 0) {
        int u = yigin[ust - 1];
        if (sira[u] < g->dere[u]) {          /* siradaki kenar */
            int v = g->komsu[u][sira[u]++];
            sinifla(u, v, 0);
            if (renk[v] == BEYAZ) {
                renk[v] = GRI;
                d[v] = ++zaman;
                sira[v] = 0;
                yigin[ust++] = v;
            }
        } else {                             /* kenarlar bitti: cik */
            renk[u] = SIYAH;
            f[u] = ++zaman;
            ust--;
        }
    }
```

Dikkat edin: `sira[u]` ve `yigin` birlikte, özyinelemeli sürümdeki "hangi çağrıda hangi `for` döngüsü kaldığı" bilgisini saklar. Bu yüzden fonksiyon aynı kenar sırasını izler ve aynı `d` ve `f` değerlerini üretir.

Naif sürümü de yazıp farkı görelim. Naif sürümde yığına tüm komşular basılır ve düğüm yığından çıkarken ziyaret edilir. Bu, bir ziyaret sırası üretir ama bu sıra özyinelemeli DFS'in sırası değildir.

```c
}

/* Naif yinelemeli DFS: tum komsular yigina itilir; ziyaret cikista.
 * 'gorulen' kokler arasinda paylasilir; sira 'cikti'ya yazilir. */
static int dfs_naif(const Graf *g, int s, int *gorulen, int *cikti,
                    int k) {
    int yigin[MAXN * MAXD], ust = 0;
    yigin[ust++] = s;
    while (ust > 0) {
        int u = yigin[--ust];
        if (gorulen[u])
            continue;
        gorulen[u] = 1;
        cikti[k++] = u;
        for (int i = 0; i < g->dere[u]; i++)
            yigin[ust++] = g->komsu[u][i];
    }
    return k;
}

/* Kesif zamanina gore dugumleri sirala (ozyinelemeli sira). */
static void kesif_sirasi(int n, int *cikti) {
    int k = 0;
    for (int t = 1; t <= 2 * n; t++)
        for (int u = 0; u < n; u++)
            if (d[u] == t)
                cikti[k++] = u;
}

```

Ana programın son kısmı, üç sürümü rastgele 200 graf üzerinde karşılaştırır. Dikkat: dördüncü ve beşinci satırlardaki `kesif_sirasi` ve naif ziyaret çıktısı, aynı 6 düğümlü örnek üzerinde yapılır.

```c
        Graf r;
        graf_uret(&r, N);

        sifirla();
        tum_kokler(&r, 0);
        int d_rec[MAXN], f_rec[MAXN], rec_sira[MAXN];
        memcpy(d_rec, d, sizeof d);
        memcpy(f_rec, f, sizeof f);
        kesif_sirasi(N, rec_sira);

        sifirla();
        for (int u = 0; u < N; u++)
            if (renk[u] == BEYAZ)
                dfs_yin(&r, u);
        if (memcmp(d_rec, d, sizeof d) == 0 &&
            memcmp(f_rec, f, sizeof f) == 0)
            dogru++;

        int gorulen[MAXN], naif_sira[MAXN], k = 0;
        memset(gorulen, 0, sizeof gorulen);
        for (int u = 0; u < N; u++)
            k = dfs_naif(&r, u, gorulen, naif_sira, k);
        for (int i = 0; i < N; i++)
            if (naif_sira[i] != rec_sira[i]) {
                naif_farkli++;
                break;
            }
    }
    printf("\nRastgele %d graf (n=%d, tohum 42):\n", TUR, N);
    printf("  yinelemeli == ozyinelemeli (d ve f): %d/%d\n",
           dogru, TUR);
    printf("  naif sira ozyinelemeliden farkli   : %d/%d\n",
           naif_farkli, TUR);
    return 0;
}
```

Aşağıdaki çıktı, aynı programın rastgele test bölümünün sonucudur. Ziyaret sıraları 17.1'deki çıktıyla birlikte okunmalıdır.

```term
$ ./dfs | tail -3
Rastgele 200 graf (n=40, tohum 42):
  yinelemeli == ozyinelemeli (d ve f): 200/200
  naif sira ozyinelemeliden farkli   : 200/200
```

Sonuç açıktır. Doğru yinelemeli DFS, 200 rastgele grafın hepsinde özyinelemeli sürümle aynı `d` ve `f` değerlerini üretir. Naif sürüm ise 200 grafın hiçbirinde aynı sırayı vermez. Örnek grafta sıra farkı bir bakışta görülür: özyinelemeli sıra `0 1 2 3 4 5`, naif sıra `0 2 3 1 4 5`. Naif sürüm `0`'ın komşularını `1, 3, 2` sırasıyla yığına koyar, ama en son konan `2` ilk çıkar ve `1`'den önce ziyaret edilir. Özyinelemeli DFS ise `1`'e iner ve `2`'yi `1`'in içinden görür.

Bu fark sadece bir kozmetik sorun değildir. Topolojik sıralama ve güçlü bağlı bileşenler gibi algoritmalar, zaman damgalarının özyinelemeli sıraya göre tutarlı olmasını gerektirir. Yanlış sırayla çalışan bir DFS, yanlış cevap üretir.

Yinelemeli sürümün karmaşıklığı da `O(V + E)`'dir. Yığın, en fazla `V` düğüm tutar; bu, özyinelemeye göre bellekte değil, düz bir dizide yer kaplar ve Windows'un 1 MB'lık ana yığınından etkilenmez (genel bilgi: Windows'ta ana iş parçacığı yığını varsayılan olarak 1 MB'tır).

## 17.3 Topolojik sıralama: Kahn ve DFS

Bir **topolojik sıralama**, yönlü çevrimsiz bir grafın (DAG) düğümlerini, her kenarın kaynağı hedeften önce gelecek şekilde sıralamaktır. Bir `u -> v` kenarı "`u` önce, `v` sonra" anlamına gelir. Bu sıra, bir iş planının doğal bir çözümüdür: "A bitmeden B başlayamaz" kuralları bir DAG oluşturur, topolojik sıra da bu kuralları bozmayan bir çalışma planıdır.

Bölüm 11.9'da derleme bağımlılığının bir DAG olduğunu görmüştük. Bir projede `main.c` `util.o`'ya, o da `util.c`'ye bağlıysa, derleme sırası `util.c`, `util.o`, `main.c` olmak zorundadır. Bu sıra bulunamıyorsa bir döngü vardır ve derleme tanımsızdır. Bölüm 11'de bu soruyu "topolojik sıralama bulur" diye bırakmıştık; şimdi cevabını vereceğiz.

Topolojik sıralamanın iki klasik yöntemi vardır.

**Kahn algoritması** (1962, Arthur Kahn) gelen kenar sayısı (derece) ile çalışır. Derecesi sıfır olan düğümler, önce yapılabilecek işlerdir. Bunları bir kuyruğa koyarız. Kuyruktan bir düğüm çıkarıp sıraya ekleriz ve onun her çıkış kenarı için hedefin derecesini bir azaltırız. Derecesi sıfıra düşen her düğüm kuyruğa girer. Kuyruk boşaldığında, bütün düğümler işlenmişse sıra tamamdır; işlenmemiş düğüm kalmışsa graf bir döngü içerir. Bu, Kahn'ın döngüyü **fark etmesinin** yoludur: döngüdeki düğümlerin derecesi hiç sıfıra düşmez, çünkü her birinin girişinde döngünün bir önceki düğümünden gelen bir kenar vardır ve o düğüm de ancak bu düğüm bittikten sonra işlenebilir.

**DFS yöntemi** ise tersten çalışır. DFS bir düğümü bitirdiğinde (siyaha çektiğinde) o düğümün tüm bağımlıları zaten bitmiştir (çünkü DAG'da onlara giden yollar ondan önce bitti). Yani **çıkış zamanına göre azalan sıra** bir topolojik sıradır. Bitiş sırasını ters çevirmek yeterlidir. Döngü varsa DFS bir geri kenarla bunu fark eder (17.1'deki kural).

Aşağıdaki Python programı iki yöntemi de uygular. Her ikisi de `adj[u]` komşuluk listesini alır. Kahn fonksiyonu döngü olup olmadığını da döndürür.

```python
# topo.py - Topolojik siralama: Kahn (derece+kuyruk) ve DFS.
from collections import deque

INF = float("inf")


def kahn(n, adj):
    """adj[u] = [v, ...]. Donus: (sira, dongu_var).
    Dongu varsa sira tum dugumleri icermez."""
    derece = [0] * n
    for u in range(n):
        for v in adj[u]:
            derece[v] += 1
    kuyruk = deque(u for u in range(n) if derece[u] == 0)
    sira = []
    while kuyruk:
        u = kuyruk.popleft()
        sira.append(u)
        for v in adj[u]:
            derece[v] -= 1
            if derece[v] == 0:
                kuyruk.append(v)
    return sira, len(sira) != n


def dfs_topo(n, adj):
    """Donus: (sira, None) ya da dongu varsa (None, (u, v)), v griyken
    u'dan gorulen geri kenar."""
    renk = [0] * n                     # 0 beyaz, 1 gri, 2 siyah
    bitis = []
    dongu = [None]

    def ziyaret(u):
        renk[u] = 1
        for v in adj[u]:
            if dongu[0] is not None:
                return
            if renk[v] == 1:           # gri: geri kenar, dongu!
                dongu[0] = (u, v)
                return
            if renk[v] == 0:
                ziyaret(v)
        renk[u] = 2
        bitis.append(u)                # cikis: sonuncu biten ilk

    for u in range(n):
        if renk[u] == 0:
            ziyaret(u)
    if dongu[0] is not None:
        return None, dongu[0]
    return bitis[::-1], None


```

DFS yöntemi için fonksiyon, bitişleri bir listeye ekler ve sonunda tersini döndürür. Geri kenar bulunursa, döngünün iki ucunu döndürür.

```python
def dfs_topo(n, adj):
    """Donus: (sira, None) ya da dongu varsa (None, (u, v)), v griyken
    u'dan gorulen geri kenar."""
    renk = [0] * n                     # 0 beyaz, 1 gri, 2 siyah
    bitis = []
    dongu = [None]

    def ziyaret(u):
        renk[u] = 1
        for v in adj[u]:
            if dongu[0] is not None:
                return
            if renk[v] == 1:           # gri: geri kenar, dongu!
                dongu[0] = (u, v)
                return
            if renk[v] == 0:
                ziyaret(v)
        renk[u] = 2
        bitis.append(u)                # cikis: sonuncu biten ilk

    for u in range(n):
        if renk[u] == 0:
            ziyaret(u)
    if dongu[0] is not None:
        return None, dongu[0]
    return bitis[::-1], None

```

Son fonksiyon, DAG'da en kısa yol problemine bir ön hazırlık olarak yazıldı; onu 17.7'de kullanacağız. Ana program, bir ders ön koşul grafı üzerinde iki yöntemi çalıştırır ve bir döngü ekleyince ne olduğunu gösterir.

```python
def dag_en_kisa(n, adj, kaynak):
    """adj[u] = [(v, w)]; yalnizca DAG. Donus: dist listesi."""
    komsu = [[v for v, _ in adj[u]] for u in range(n)]
    sira, dongulu = kahn(n, komsu)
    if dongulu:
        raise ValueError("graf DAG degil")
    dist = [INF] * n
    dist[kaynak] = 0
    for u in sira:                     # topolojik sirada tek gecis
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist


if __name__ == "__main__":
    ad = ["Programlama", "Matematik", "Veri Yapilari", "Algoritmalar",
          "Isletim Sist.", "Ag", "Derleyici", "Bitirme"]
    kenar = [(0, 2), (0, 4), (2, 3), (1, 3), (4, 5), (2, 6), (3, 6),
             (3, 7), (5, 7), (6, 7)]
    adj = [[] for _ in ad]
    for u, v in kenar:
        adj[u].append(v)
    sira, dongulu = kahn(len(ad), adj)
    print("Kahn :", [ad[u] for u in sira], "dongu:", dongulu)
    sira, dongu = dfs_topo(len(ad), adj)
    print("DFS  :", [ad[u] for u in sira], "dongu:", dongu)
    adj[6].append(0)                   # Derleyici -> Programlama
    sira, dongulu = kahn(len(ad), adj)
    print("Dongulu Kahn: sira", sira, "dongu:", dongulu)
    sira, dongu = dfs_topo(len(ad), adj)
    print("Dongulu DFS : sira", sira, "geri kenar:", dongu)
```

Aşağıdaki çıktı, ders grafındaki iki yöntemin sıralarını ve döngü eklenince verdikleri tepkiyi gösterir.

```term
$ python topo.py
Kahn : ['Programlama', 'Matematik', 'Veri Yapilari', 'Isletim Sist.',
    'Algoritmalar', 'Ag', 'Derleyici', 'Bitirme'] dongu: False
DFS  : ['Matematik', 'Programlama', 'Isletim Sist.', 'Ag', 'Veri
    Yapilari', 'Algoritmalar', 'Derleyici', 'Bitirme'] dongu: None
Dongulu Kahn: sira [1] dongu: True
Dongulu DFS : sira None geri kenar: (6, 0)
```

Kahn'ın sırasında `Programlama` ve `Matematik` derecesi sıfır olduğu için ilk kuyruğu oluşturur. `Programlama` çıkınca `Veri Yapilari` ve `Isletim` derecesi sıfıra düşer ve kuyruğa girer. Döngü eklenince (`Derleyici -> Programlama`), `Programlama`'nın derecesi hiç sıfıra düşmez ve yalnızca `Matematik` işlenir; sıra kısa kalır ve `dongu: True` döner. DFS yöntemi aynı durumda, `Derleyici`'den `Programlama`'ya giden kenarın gri bir düğüme gittiğini görür ve geri kenarı `(6, 0)` olarak bildirir. Kenar numaraları düğüm numaralarıdır: `6` `Derleyici`, `0` `Programlama`.

Şekil 17.2 aynı DAG'ı gösterir. Dairelerdeki sayılar Kahn'ın işleme sırasıdır.

![Şekil 17.2: Ders ön koşul grafı. Daire içindeki sayı Kahn'ın işleme sırasıdır; her kenar soldan sağa, bağımlılık yönünde ilerler.](gorseller/b17_topo_sira.png)

İki yöntemin karmaşıklığı da `O(V + E)`'dir: Kahn her düğümü ve kenarı bir kez inceler; DFS de öyle. Birden fazla geçerli sıra olabilir; yukarıdaki iki sıra da geçerlidir ama farklıdır. Bu, topolojik sıralamanın tek bir cevabı olmadığının işaretidir. Kahn yöntemi, kuyruk yerine öncelik kuyruğu (Bölüm 10.8'deki `heapq`) kullanılırsa, her adımda en küçük indeksli düğümü seçen tek bir sıra üretir. Bu, derleme sisteminde kararlılık için faydalıdır.

Gerçek dünyada bu bağlantı açıktır. `make` ve benzeri derleme sistemleri bağımlılık grafını kurar ve bir topolojik sırayla derleme yapar; bir bağımlılık döngüsü bulduğunda hata verir. Paket yöneticileri de kurulacak paketleri aynı mantıkla sıralar. Python'un standart kütüphanesindeki `graphlib` modülü bu işi hazır sunar. Aşağıdaki kısa örnek, aynı mantığı onun üzerinde gösterir. Bu programın kaynağını Kod Okuma bölümünde ayrıntılı olarak inceleyeceğiz.

```python
# graphlib_demo.py - Python'un topolojik siralayicisi ve dongu hatasi.
import graphlib

# Anahtar: dugum, deger: onun on kosullari (once bitmesi gerekenler)
ders = {
    "Bitirme": ["Ag", "Derleyici"],
    "Ag": ["Isletim"],
    "Derleyici": ["Algoritmalar"],
    "Algoritmalar": ["Veri"],
    "Isletim": ["Programlama"],
    "Veri": ["Programlama"],
}
print("Sira:", list(graphlib.TopologicalSorter(ders).static_order()))

donguyle = {"A": ["B"], "B": ["C"], "C": ["A"]}
try:
    list(graphlib.TopologicalSorter(donguyle).static_order())
except graphlib.CycleError as hata:
    print("Hata mesaji:", hata.args[0])
    print("Dongu:", hata.args[1])
```

Çıktıda, döngü için `hata.args[1]` listesi döngüyü verir. Liste, `A`'dan başlayıp `A`'ya dönen bir yoldur; son eleman ilkiyle aynıdır. Hangi düğümle başlayacağı, düğümlerin ekleniş sırasına bağlıdır.

```term
$ python graphlib_demo.py
Sira: ['Programlama', 'Isletim', 'Veri', 'Ag', 'Algoritmalar',
    'Derleyici', 'Bitirme']
Hata mesaji: nodes are in a cycle
Dongu: ['A', 'C', 'B', 'A']
```

## 17.4 İki renklendirme: bipartite kontrolü

Bir grafın düğümlerini iki renkle boyayabiliyorsak ve hiçbir kenar aynı renkteki iki düğümü birleştirmiyorsa, graf **iki parçalıdır** (bipartite). Örneğin bir eşleştirme problemi (işçiler ve işler) doğal olarak iki parçalı bir graftır: kenarlar yalnızca işçi ile iş arasındadır. İki parçalı olup olmadığını bilmek, pek çok algoritmanın (eşleştirme, akış) ön koşuludur.

Bir grafın iki parçalı olması için gerek ve yeterli koşul, **hiçbir tek uzunluklu döngünün olmamasıdır**. Bir döngüde renkler sırayla değişir; döngü çift uzunluklu ise başa dönüldüğünde renk tutarlı kalır, tek uzunluklu ise bir yerde çakışma olur. Bu yüzden 4 düğümlü bir kare iki renklenebilirken, 5 düğümlü bir beşgen iki renklenemez.

Kontrolü BFS ile yaparız (Bölüm 8.5'te kuyruğu ve BFS'i gördük). Bir düğüme ilk rengi veririz, komşularına karşıt rengi veririz ve bu şekilde katman katman ilerleriz. Bir komşu zaten boyanmışsa ve rengi aynıysa, bir çakışma bulmuşuzdur.

```python
# bipartite.py - BFS ile iki renkli (2-renklendirme) kontrolu.
from collections import deque


def iki_renkli(n, adj):
    """adj: yonsuz komsuluk listesi. Donus: (True, renk) ya da
    (False, (u, v)): ayni renkli iki komsu (cakisan kenar)."""
    renk = [-1] * n
    for s in range(n):
        if renk[s] != -1:
            continue
        renk[s] = 0
        kuyruk = deque([s])
        while kuyruk:
            u = kuyruk.popleft()
            for v in adj[u]:
                if renk[v] == -1:
                    renk[v] = 1 - renk[u]    # komsu: karsit renk
                    kuyruk.append(v)
                elif renk[v] == renk[u]:
                    return False, (u, v)     # cakisma: tek dongu
    return True, renk


```

Fonksiyon bağlantısız grafları da destekler: her bağlantılı bileşen için yeni bir başlangıç düğümü seçilir. Ana program bir 4 düğümlü ve bir 5 düğümlü döngüyü dener.

```python
if __name__ == "__main__":
    def graf(n, kenar):
        adj = [[] for _ in range(n)]
        for u, v in kenar:
            adj[u].append(v)
            adj[v].append(u)
        return adj

    dort_dongu = graf(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    bes_dongu = graf(5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)])
    print("C4 :", iki_renkli(4, dort_dongu))
    print("C5 :", iki_renkli(5, bes_dongu))
```

Aşağıdaki çıktı ve Şekil 17.3 bu iki durumu gösterir.

```term
$ python bipartite.py
C4 : (True, [0, 1, 0, 1])
C5 : (False, (2, 3))
```

Dört düğümlü döngü `[0, 1, 0, 1]` renklendirmesini alır: karşılıklı köşeler aynı renktedir. Beş düğümlü döngüde BFS, `0`'dan başlayıp `1` ve `4`'e `1` rengini, sonra `2`'ye ve `3`'e `0` ve `1`'i verir. `2` ve `3` arasındaki kenarda renkler `0` ile `1` olmalıyken, `2` ve `3` ikisi de bu noktada `0`'dır ya da çakışma oluşur; program `(2, 3)` kenarını çakışan kenar olarak bildirir. Bu, tek uzunluklu döngünün işaretidir.

![Şekil 17.3: Solda çift uzunluklu C4 iki renklenebilir. Sağda tek uzunluklu C5'te kesikli kırmızı kenar (2,3) çakışmayı gösterir.](gorseller/b17_iki_renk.png)

Karmaşıklık `O(V + E)`'dir. İki renklendirme, Bölüm 16'daki dinamik programlamadan farklı olarak bir sayı değil, bir evet/hayır cevabı üretir. Bunu bilmek önemlidir: bipartite kontrolü, bir optimizasyon problemini çözmez; yalnızca bir yapıyı doğrular.

## 17.5 Güçlü bağlı bileşenler, köprüler ve eklem noktaları

Bölüm 11.7'de yönsüz bir grafın bağlantılı bileşenlerini saymıştık. Yönlü graflarda ise "bağlantılı" kavramı iki ayrı şeye dönüşür. **Güçlü bağlı bileşen (SCC)**, içindeki her düğümden her düğüme yönlü bir yol olan maksimal düğüm kümesidir. Örneğin bir web sayfası grafında birbirine karşılıklı linkle bağlı sayfalar aynı SCC'de olur. Bir kenar tek yönlüyse iki düğüm farklı SCC'lerdedir.

SCC'leri bulmanın en zarif yolu **Tarjan algoritması**dır (1972). Tarjan tek bir DFS geçişiyle çalışır ve her düğüm için bir **low-link** değeri tutar. Bu değer, düğümün alt ağacından erişebildiği en küçük ziyaret indeksidir. Bir düğümün low değeri kendi indeksine eşitse, o düğüm bir SCC'nin kökündür ve yığında onun üstünde kalan düğümler bu bileşeni oluşturur.

Aynı low-link fikri **köprüleri** ve **eklem noktalarını** da bulur. Yönsüz bir grafta **köprü**, silindiğinde grafın bağlantısını koparan kenardır. **Eklem noktası** (kesme noktası) ise silindiğinde bileşen sayısını artıran düğümdür. Bölüm 11'in sonunda, bir sensör ağında tek bir gateway arızasının ağı bölüp bölmediğini sormuştuk. Cevap bir eklem noktasıdır: o düğümü çıkarınca ağ parçalanıyorsa, o düğüm tek nokta arızasıdır.

Aşağıdaki program iki işi de yapar. `tarjan_scc` yönlü grafta bileşenleri bulur. `kopru_eklem` yönsüz grafta köprüleri ve eklem noktalarını bulur. İkisi de özyinelemeli DFS kullanır; küçük graflar için bu güvenlidir (Python'un varsayılan özyineleme sınırı 1000'dir, aşağıdaki program bunu yazdırır).

```python
# tarjan.py - Tarjan: guclu bagli bilesen (yonlu), kopru/eklem.
import sys


def tarjan_scc(n, adj):
    """Yonlu graf. Donus: bilesen listesi (her biri sirali)."""
    index = [-1] * n            # ziyaret sirasi
    low = [0] * n               # alt agactan erisilen en kucuk index
    yigin, ycinde = [], [False] * n
    bilesenler = []
    sayac = 0

    def ziyaret(u):
        nonlocal sayac
        index[u] = low[u] = sayac
        sayac += 1
        yigin.append(u)
        ycinde[u] = True
        for v in adj[u]:
            if index[v] == -1:              # agac kenari
                ziyaret(v)
                low[u] = min(low[u], low[v])
            elif ycinde[v]:                 # yiginda: ayni bilesen
                low[u] = min(low[u], index[v])
        if low[u] == index[u]:              # u bir bilesenin koku
            bilesen = []
            while True:
                w = yigin.pop()
                ycinde[w] = False
                bilesen.append(w)
                if w == u:
                    break
            bilesenler.append(sorted(bilesen))

    for u in range(n):
        if index[u] == -1:
            ziyaret(u)
    return bilesenler


```

Yönsüz kısım için low-link kuralı hafif değişir: ebeveyne giden kenar atlanır, çünkü bir düğümden ebeveynine dönen kenar köprü kontrolünü bozardı. Çocuk düğümün `low` değeri, çocuğun düğümden daha yukarı çıkamadığını gösteriyorsa (`low[v] > disc[u]`) kenar bir köprüdür. Eklem noktası kuralı ise `low[v] >= disc[u]`'dur; kök için ayrı bir kural vardır: iki veya daha fazla çocuğu varsa kök bir eklem noktasıdır.

```python
def kopru_eklem(n, adj):
    """Yonsuz, basit graf. Donus: (kopruler, eklemler)."""
    disc = [-1] * n            # kesif zamani
    low = [0] * n
    kopruler, eklem = [], set()
    zaman = 0

    def dfs(u, ata):
        nonlocal zaman
        disc[u] = low[u] = zaman
        zaman += 1
        cocuk = 0
        for v in adj[u]:
            if v == ata:                    # ebeveyne kenari atla
                continue
            if disc[v] == -1:
                cocuk += 1
                dfs(v, u)
                low[u] = min(low[u], low[v])
                if low[v] > disc[u]:        # u'yu asmaz
                    kopruler.append((min(u, v), max(u, v)))
                if ata != -1 and low[v] >= disc[u]:
                    eklem.add(u)
            else:
                low[u] = min(low[u], disc[v])
        if ata == -1 and cocuk > 1:         # kok, 2+ cocuk
            eklem.add(u)

    for u in range(n):
        if disc[u] == -1:
            dfs(u, -1)
    return sorted(kopruler), sorted(eklem)


```

Ana program bir 8 düğümlü yönlü graf ve bir sensör ağı üzerinde çalışır. Sensör ağında `0` gateway'dir; `1` ve `2` yapraklardır; `3`, `4`, `5` bir üçgen oluşturur ve `3` üzerinden gateway'e bağlıdır.

```python
if __name__ == "__main__":
    print(sys.getrecursionlimit(), "yigin siniri")
    # Yonlu: {0,1,2}, {3,4,5}, {6,7} uc bilesen
    kenar = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5),
             (5, 3), (5, 6), (6, 7), (7, 6)]
    adj = [[] for _ in range(8)]
    for u, v in kenar:
        adj[u].append(v)
    print("SCC:", tarjan_scc(8, adj))
    # Sensor agi: 0 = gateway; s1, s2 yaprak; s3-s4-s5 ucgeni
    kenar = [(0, 1), (0, 2), (0, 3), (3, 4), (4, 5), (5, 3)]
    adj = [[] for _ in range(6)]
    for u, v in kenar:
        adj[u].append(v)
        adj[v].append(u)
    kop, ekl = kopru_eklem(6, adj)
    print("Kopruler :", kop)
    print("Eklemler :", ekl)
```

```term
$ python tarjan.py
1000 yigin siniri
SCC: [[6, 7], [3, 4, 5], [0, 1, 2]]
Kopruler : [(0, 1), (0, 2), (0, 3)]
Eklemler : [0, 3]
```

Çıktıdaki SCC listesi `[6, 7]`, `[3, 4, 5]`, `[0, 1, 2]` sırasıyla gelir. Bu sıra ters topolojik sıradır: Tarjan bir bileşeni bitirdiğinde, ondan erişilen tüm bileşenler zaten bitmiştir. Bu bir özelliktir ve bazı algoritmalar (ör. iki geçişli SCC'nin ikinci geçişi) bu sırayı kullanır. Sensör ağında köprüler `(0, 1)`, `(0, 2)`, `(0, 3)`'tür: bu üç kenarın her biri koparsa bir parça ayrılır. Eklemler `0` ve `3`'tür. `0`'ı çıkarırsanız `1`, `2` ve `3-4-5` birbirinden ayrılır. `3`'ü çıkarırsanız `4-5` ikilisi gateway'den kopar. Şekil 17.4 bu iki durumu gösterir.

![Şekil 17.4: (a) Yönlü graftaki üç SCC ayrı renkte. (b) Sensör ağında kalın kırmızı kenarlar köprü, kesikli halkalar eklem noktasıdır.](gorseller/b17_scc_kopru.png)

Bölüm 11'deki gateway sorusunun pratik cevabı şudur: düğümü tek tek silip bileşen saymak da işe yarar (bu `O(V(V+E))` tutar), ama Tarjan tek bir DFS ile aynı bilgiyi `O(V + E)` sürede verir. Bu ikisinin sonuçlarının aynı olduğunu 17.11'de rastgele graflar üzerinde ölçeceğiz.

## 17.6 En kısa yollar I: BFS, 0-1 BFS ve Dijkstra

En kısa yol problemi şöyle sorulur: bir `s` kaynağından her `t` hedefine giden, toplam kenar ağırlığı en küçük yol nedir? Ağırlıklar mesafe, süre ya da maliyet olabilir. Kenar ağırlıkları negatif değilse Dijkstra algoritması bu soruyu en verimli şekilde çözer. Önce daha basit iki durumu görelim.

**Ağırlıksız graf.** Her kenarın ağırlığı 1 ise, BFS (Bölüm 8.5) doğru cevabı verir: BFS, kaynağa `k` kenar uzaklıktaki düğümleri `k`. katmanda ziyaret eder. Bölüm 8.5'te bu garantiyi zaten kullandık.

**Yalnızca 0 ve 1 ağırlıklı graf.** Bu durumda deque (Bölüm 8.6) kullanarak 0-1 BFS yapabiliriz. Maliyeti 0 olan kenarın hedefi, kuyruğun başına eklenir; maliyeti 1 olan kenarın hedefi sonuna eklenir. Kuyruk, her an mesafelerin sıralı olduğu bir yapıda kalır ve her düğüm `O(V + E)` sürede işlenir.

**Genel ağırlıklı graf: Dijkstra.** Dijkstra'nın fikri şudur: kaynağa en yakın düğümü bul, onu "kesin" olarak işaretle, sonra bu düğüm üzerinden komşularının mesafesini güncelle. Her adımda henüz kesinleşmemiş düğümler arasında en küçük tahmini olan seçilir. Bu seçimi bir öncelik kuyruğu ile yaparız.

Dijkstra'nın doğruluğu şu gözleme dayanır: **negatif kenar yoksa, en kısa yolda hiçbir düğümün mesafesi, ona giden yolun başka bir düğümden geçmesiyle azalmaz.** Bu yüzden en küçük tahminli düğüm kesinleşebilir. Negatif kenar varsa bu gözlem bozulur; 17.7'de bunu bir karşı örnekle göreceğiz.

Kuyruk olarak Python'un `heapq` modülünü kullanacağız (Bölüm 10.8). Bu modül bir min-heap'tir: `heappop` her zaman en küçük elemanı çıkarır. Bir düğümün mesafesi değiştiğinde heap'te yeniden anahtarlamak yerine, yeni bir kayıt ekleriz. Aynı düğümün eski ve geçersiz kayıtları heap'te kalır. Bu yönteme **tembel silme** (lazy deletion) denir. Bir kaydı çıkarırken düğüm zaten kesinleşmişse, bu kaydı atlarız. Böylece karmaşık bir "azaltma anahtarı" işlemine gerek kalmaz.

Aşağıdaki program BFS, 0-1 BFS ve Dijkstra'yı yazar. Dijkstra'nın yol geri kurma yeteneği de vardır: her düğüm için mesafeyi iyileştiren son düğümü (ebeveyni) tutarız. Hedeften ebeveynlere giderek yolu geriye doğru kurarız.

```python
# dijkstra.py - BFS (agirliksiz), 0-1 BFS ve Dijkstra (ikili heap).
import heapq
from collections import deque

INF = float("inf")


def bfs_mesafe(n, adj, kaynak):
    """Agirliksiz graf: kenar sayisi cinsinden mesafeler."""
    dist = [INF] * n
    if n == 0:
        return dist
    dist[kaynak] = 0
    kuyruk = deque([kaynak])
    while kuyruk:
        u = kuyruk.popleft()
        for v, _ in adj[u]:
            if dist[v] == INF:
                dist[v] = dist[u] + 1
                kuyruk.append(v)
    return dist


def zero_one_bfs(n, adj, kaynak):
    """Agirliklar yalnizca 0 ya da 1 ise, deque ile O(V + E)."""
    dist = [INF] * n
    if n == 0:
        return dist
    dist[kaynak] = 0
    dq = deque([kaynak])
    while dq:
        u = dq.popleft()
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                if w == 0:
                    dq.appendleft(v)   # 0 maliyet: basa
                else:
                    dq.append(v)       # 1 maliyet: sona
    return dist


```

Dijkstra fonksiyonu, `ebeveyn` dizisiyle yolu geri kurmamızı sağlar. Bu dizi yalnızca mesafe iyileştiğinde güncellenir; dolayısıyla son hâli her düğüm için bir en kısa yol ağacını tanımlar.

```python
def dijkstra(n, adj, kaynak):
    """adj[u] = [(v, w), ...], w >= 0. Donus: (dist, ebeveyn)."""
    dist = [INF] * n
    ebeveyn = [-1] * n
    if n == 0:
        return dist, ebeveyn
    bitti = [False] * n
    dist[kaynak] = 0
    yigin = [(0, kaynak)]
    while yigin:
        d, u = heapq.heappop(yigin)
        if bitti[u]:
            continue                   # tembel silme: eski kayit
        bitti[u] = True
        for v, w in adj[u]:
            yeni = d + w
            if yeni < dist[v]:
                dist[v] = yeni
                ebeveyn[v] = u
                heapq.heappush(yigin, (yeni, v))
    return dist, ebeveyn


```

Yol geri kurma fonksiyonu ebeveyn dizisinde `-1`'e (kaynağın ebeveyni) ulaşana kadar geriye gider ve listeyi tersine çevirir. Dikkat: hedef erişilemezse de bir liste döner (yalnızca hedefin kendisi). Bu yüzden çağıran kod önce mesafeye bakmalıdır.

```python
def yol_kur(ebeveyn, hedef):
    """Ebeveyn dizisinden kaynak->hedef yolunu geri kurar.
    Hedef erisilemezse de bir liste doner; caller dist'e bakmali."""
    yol = []
    u = hedef
    while u != -1:
        yol.append(u)
        u = ebeveyn[u]
    return yol[::-1]


if __name__ == "__main__":
    kenarlar = [(0, 1, 7), (0, 2, 9), (0, 5, 14), (1, 2, 10),
                (1, 3, 15), (2, 3, 11), (2, 5, 2), (3, 4, 6),
                (5, 4, 9)]
    n = 6
    adj = [[] for _ in range(n)]
    for u, v, w in kenarlar:
        adj[u].append((v, w))
    dist, ebeveyn = dijkstra(n, adj, 0)
    for t in range(n):
        print(f"{t}: mesafe={dist[t]:>2}  yol={yol_kur(ebeveyn, t)}")
    print("BFS (kenar sayisi):", bfs_mesafe(n, adj, 0))
```

Ana program altı düğümlü küçük bir ağda Dijkstra'yı çalıştırır. Bu, Wikipedia'daki klasik örneğin 0 tabanlı hâlidir. Sonuçları elle de kontrol edebiliriz.

```term
$ python dijkstra.py
0: mesafe= 0  yol=[0]
1: mesafe= 7  yol=[0, 1]
2: mesafe= 9  yol=[0, 2]
3: mesafe=20  yol=[0, 2, 3]
4: mesafe=20  yol=[0, 2, 5, 4]
5: mesafe=11  yol=[0, 2, 5]
BFS (kenar sayisi): [0, 1, 1, 2, 2, 1]
```

Düğüm `4`'ün mesafesi `20`'dir. Yol `0-2-5-4`'tür: `9 + 2 + 9 = 20`. Düğüm `3`'ün mesafesi de `20`'dir ve yolu `0-2-3`'tür (`9 + 11`). İki hedef de aynı toplamı verdiği için bu, eşitlik durumudur; program bulduğu ilk yolu tutar ve ikisi de doğrudur. Son satır ise ağırlıkları yok sayan BFS'in kenar sayısını verir: `4`'e `0-5-4` ile iki kenarda ulaşılır, oysa ağırlıklı en kısa yol üç kenarlıdır. Bu, ağırlıklı ve ağırlıksız en kısa yolların farklı olabileceğinin somut örneğidir.

Dijkstra'nın karmaşıklığı bir ikili heap ile `O((V + E) log V)`'dir: her kenar en fazla bir heap kaydı üretir ve her kayıt `O(log V)` sürede eklenir ya da çıkarılır. Yoğun graflarda (E ≈ V²) bir dizi üzerinde düz bir arama daha iyi olabilir; seyrek graflarda heap kazandırır. Dijkstra'nın OSPF gibi iç ağ yönlendirme protokollerinde kullanılmasının nedeni budur: yönlendirme ağları çoğunlukla seyrektir.

## 17.7 Negatif kenarlar ve Bellman-Ford; DAG'da en kısa yol

Dijkstra'nın doğruluğu negatif olmayan kenarlara dayanıyordu. Peki bir kenar negatif olursa ne olur? Bir karşı örnekle başlayalım. Dört düğümlü bir grafta `A -> B` (1), `A -> C` (5), `C -> B` (-10) ve `B -> D` (1) kenarları olsun. `A`'dan `D`'ye giden en kısa yol `A -> C -> B -> D`'dir ve toplamı `5 - 10 + 1 = -4`'tür. Dijkstra'yı bu grafta çalıştırırsak ne olur?

Dijkstra `A`'yı işler ve `B = 1`, `C = 5` yazar. Sonra en küçük olan `B`'yi (1) kesinleştirir ve `D = 2` yazar. `C` işlenince `C -> B` kenarı `B`'yi `-5`'e çeker, ama `B` zaten kesinleşmiştir; `B`'nin çıkış kenarları yeniden gevşetilmez ve `D` `2` olarak kalır. Oysa doğru değer `-4`'tür.

Bu karşı örnek, Dijkstra'nın yanlış çalıştığını gösterir. Aşağıdaki program aynı grafta Dijkstra ve Bellman-Ford'u karşılaştırır. Önce Bellman-Ford fonksiyonunu görelim.

```python
# bellman.py - Bellman-Ford: negatif kenar ve negatif dongu tespiti.
# Ayni grafta Dijkstra'nin negatif kenarda neden yanlis sonuc
# verdigini de gosterir.
from dijkstra import INF, dijkstra, yol_kur


def bellman_ford(n, kenarlar, kaynak):
    """kenarlar: [(u, v, w)]. Donus: (dist, ebeveyn); kaynaktan
    erisilebilir bir negatif dongu varsa None."""
    dist = [INF] * n
    ebeveyn = [-1] * n
    if n == 0:
        return dist, ebeveyn
    dist[kaynak] = 0
    for _ in range(n - 1):             # V - 1 tur
        degisti = False
        for u, v, w in kenarlar:
            if dist[u] + w < dist[v]:  # INF + w = INF: atlanir
                dist[v] = dist[u] + w
                ebeveyn[v] = u
                degisti = True
        if not degisti:
            break                      # erken durma
    for u, v, w in kenarlar:           # V. tur: hala gevsetiliyor mu?
        if dist[u] + w < dist[v]:
            return None                # negatif dongu erisilebilir
    return dist, ebeveyn

```

**Bellman-Ford** (1958) kenarları tüm graf üzerinde tekrar tekrar gevşetir. Her tur, tüm kenarları bir kez dolaşır. Kısa yolların düğüm sayısı (`V`) için bir gözlem yeter: kaynaktan bir hedefe giden basit bir yolun en fazla `V - 1` kenarı vardır. Bir tur sonunda, en fazla `k` kenarlı tüm yollar doğru hesaplanmış olur (tur sayısına göre tümevarım). Bu yüzden `V - 1` tur yeterlidir. Erken durma (`degisti` bayrağı) bir optimizasyondur; tur bir değişiklik yapmazsa daha fazla tur da yapmaz.

Negatif döngü tespiti buradan çıkar. Eğer `V - 1` turdan sonra hâlâ gevşetilebilen bir kenar varsa, yolların uzunluğu sınırsız azalabilir: bir negatif döngü kaynaktan erişilebilir demektir. Bu yüzden `V`. tur, negatif döngü için bir sınavdır.

Dijkstra ve Bellman-Ford'un aynı grafta farkını gösteren program, bellman.py'nin ana bölümüdür.

```python
if __name__ == "__main__":
    # A=0, B=1, C=2, D=3: A->B 1, A->C 5, C->B -10, B->D 1
    kenarlar = [(0, 1, 1), (0, 2, 5), (2, 1, -10), (1, 3, 1)]
    n = 4
    adj = [[] for _ in range(n)]
    for u, v, w in kenarlar:
        adj[u].append((v, w))
    d1, _ = dijkstra(n, adj, 0)
    print("Dijkstra :", d1)
    d2, e2 = bellman_ford(n, kenarlar, 0)
    print("Bellman  :", d2)
    print("Yol D    :", yol_kur(e2, 3))
    # B->C (1) ekleyince C->B->C dongusu: -10 + 1 = -9 < 0
    donguly = kenarlar + [(1, 2, 1)]
    print("Negatif dongu:", bellman_ford(n, donguly, 0))
```

```term
$ python bellman.py
Dijkstra : [0, -5, 5, 2]
Bellman  : [0, -5, 5, -4]
Yol D    : [0, 2, 1, 3]
Negatif dongu: None
```

Çıktı, karşı örneği doğrular. Dijkstra `D` için `2` verir; Bellman-Ford `-4` verir ve yolu `[0, 2, 1, 3]`'tür, yani `A -> C -> B -> D`. Dijkstra'nın `B` için `-5` yazdığına dikkat edin: `B` mesafesi düzeltilmiştir, ama `B`'nin çıkış kenarı `B -> D` gevşetilmemiştir. Bu, Dijkstra'nın "bir kez işlenmiş düğümü yeniden açmama" kuralının bedelidir. Son satır, `B -> C` (1) eklenince `C -> B -> C` döngüsünün toplamının `-9` olduğunu ve Bellman-Ford'un `None` döndürerek bunu bildirdiğini gösterir.

Şekil 17.5 Dijkstra'nın adımlarını, Şekil 17.6 bu negatif kenar karşı örneğini gösterir.

Dijkstra'nın adımlarını daha iyi görmek için, 17.6'daki 6 düğümlü graf üzerinde Şekil 17.5'in dört panelini izleyelim. Birinci panelde yalnız `0` işlenmiştir ve komşularının tahminleri `1`, `2`, `5` için `7`, `9`, `14`'tür. İkinci panelde `0`, `1`, `2` işlenmiştir; `2 -> 5` kenarı `5`'i `11`'e düşürmüş, `1 -> 3` ve `2 -> 3` kenarları `3`'ü `20`'ye çekmiştir. Üçüncü panelde `5` de işlenmiştir ve `4`'ün tahmini `20`'ye iner. Dördüncü panel son durumu gösterir: `3` ve `4` de kesinleşmiştir; nihai mesafeler `0, 7, 9, 20, 20, 11`'dir (düğüm sırasıyla).

![Şekil 17.5: Dijkstra'nın üç ara adımı ve son durumu. Yeşil düğümler kesinleşmiş, sarı düğümler yalnızca tahmindir; kenar etiketleri ağırlıktır.](gorseller/b17_dijkstra_adim.png)

![Şekil 17.6: Negatif kenar karşı örneği. Solda Dijkstra D=2 bulur (yanlış), sağda Bellman-Ford D=-4 bulur (doğru).](gorseller/b17_negatif_kenar.png)

Bellman-Ford'un tur tur nasıl çalıştığını görmek için kenarları farklı bir sırayla dizelim: `(1,3), (0,1), (0,2), (2,1)`. Bu sıra, ilk turda `D`'ye giden yolun henüz hazır olmadığını gösterir ve bilginin turlar boyunca yayıldığını açıkça ortaya koyar. Şekil 17.7 her turdan sonraki mesafe vektörünü verir.

![Şekil 17.7: Bellman-Ford turları. Her turda değişen hücreler sarıdır. D'nin değeri ancak ikinci turda -4 olur.](gorseller/b17_bellman_tur.png)

Bellman-Ford'un karmaşıklığı `O(V · E)`'dir. Dijkstra'dan çok daha yavaştır, ama negatif kenarı kaldırabilir. Bu yüzden RIP gibi mesafe-vektör yönlendirme protokolleri, her yönlendiricinin komşularından aldığı mesafe tablosuyla Bellman-Ford mantığını çalıştırır (genel bilgi: RIP'in sayma sonsuzluğu sorunu bu mantığın bir sonucudur).

**DAG'da en kısa yol.** Yönlü çevrimsiz bir grafta, Bellman-Ford'a gerek yoktur. Topolojik sıra bize her düğümü, ona giden tüm kenarlar işlendikten sonra işleme fırsatı verir. Bu yüzden her düğümü topolojik sırada bir kez işleyip çıkış kenarlarını gevşetmek yeterlidir; karmaşıklık `O(V + E)`'dir ve negatif kenar serbesttir. 17.3'te yazdığımız `dag_en_kisa` fonksiyonu bunu yapar. Test dosyasında (17.11) onu Bellman-Ford ile karşılaştıracağız.

## 17.8 Tüm çiftler: Floyd-Warshall

Bazen tek bir kaynağa değil, her çifte en kısa yolu bilmek isteriz: bir yol haritasında her şehirden her şehire mesafe tablosu gibi. Bunu her düğüm için Dijkstra çalıştırarak da yapabiliriz (`O(V (V+E) log V)`). Ama **Floyd-Warshall** algoritması, dinamik programlama (Bölüm 16) ile tüm çiftleri `O(V³)` sürede hesaplar ve negatif kenarları da kaldırır (negatif döngü yoksa).

Floyd-Warshall'ın durumu şöyledir: `dist[i][j]`, `i`'den `j`'ye, yalnızca `0, 1, ..., k-1` düğümlerini ara durak olarak kullanan en kısa yolun uzunluğudur. Geçiş ise tek bir yeni düğüm `k` ekler: `i`'den `j`'ye, `k` üzerinden geçen yol `dist[i][k] + dist[k][j]` ile karşılaştırılır. Bu, Bölüm 16.2'deki altı soru protokolünün birebir uygulamasıdır. Durum, `k` ile sınırlı yoldur; geçiş, `k`'yı ekleyen formüldür; taban, `dist[i][j] = w[i][j]`'dir; sıra, `k`'nın en dış döngüde artmasıdır.

Burada kritik nokta **döngü sırasıdır**. `k` en dış döngü olmalıdır, çünkü `dist[i][k]` ve `dist[k][j]` değerlerinin `k`-öncesi durumda doğru olması gerekir. Bunun nasıl bozulduğunu göstermek için 0 -> 1 (1), 1 -> 3 (1), 3 -> 2 (1) kenarları olan dört düğümlü bir grafa bakalım. `0`'dan `2`'ye giden tek yol `0 -> 1 -> 3 -> 2`'dir ve uzunluğu `3`'tür. Doğru sırada (`k` en dışta) bu bulunur. Yanlış sırada ise (`i`, `j`, `k` diye iç içe), `0`'ın `j = 2` hücresi hesaplanırken `dist[0][3]` henüz hesaplanmamıştır ve sonuç `inf` kalır. Aşağıdaki program iki sırayı da çalıştırır.

```python
# floyd.py - Floyd-Warshall: tum ciftler icin en kisa yollar (DP).
INF = float("inf")


def floyd(n, w):
    """w[i][j]: kenar agirligi (yoksa INF), w[i][i] = 0.
    Donus: (dist, sonraki); sonraki[i][j], i'den j'ye giden yolun ilk
    adimidir (yol yoksa -1)."""
    dist = [row[:] for row in w]
    sonraki = [[j if w[i][j] < INF else -1 for j in range(n)]
               for i in range(n)]
    for k in range(n):                 # ara dugum k: en dis dongu
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    sonraki[i][j] = sonraki[i][k]
    return dist, sonraki


def yol(sonraki, i, j):
    """sonraki tablosundan i -> j yolunu cikarir."""
    if sonraki[i][j] == -1:
        return []
    p = [i]
    while i != j:
        i = sonraki[i][j]
        p.append(i)
    return p


```

Floyd fonksiyonu ayrıca `sonraki` matrisini tutar; yol geri kurma bu matrisle yapılır. Yanlış sıralı sürüm, karşı örnek için ayrı tutulmuştur.

```python
def floyd_yanlis(n, w):
    """YANLIS siralama: k dongusu en icte. Karsi ornek icin."""
    dist = [row[:] for row in w]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return dist


if __name__ == "__main__":
    # Kenarlar: 0->1, 1->3, 3->2 (hepsi 1). Yol: 0 -> 1 -> 3 -> 2
    n = 4
    w = [[INF] * n for _ in range(n)]
    for i in range(n):
        w[i][i] = 0
    w[0][1] = 1
    w[1][3] = 1
    w[3][2] = 1
    dist, sonraki = floyd(n, w)
    print("Dogru dist:")
    for satir in dist:
        print("  ", satir)
    print("0 -> 2 yolu:", yol(sonraki, 0, 2))
    print("Yanlis siralama dist:")
    for satir in floyd_yanlis(n, w):
        print("  ", satir)
```

```term
$ python floyd.py
Dogru dist:
   [0, 1, 3, 2]
   [inf, 0, 2, 1]
   [inf, inf, 0, inf]
   [inf, inf, 1, 0]
0 -> 2 yolu: [0, 1, 3, 2]
Yanlis siralama dist:
   [0, 1, inf, 2]
   [inf, 0, 2, 1]
   [inf, inf, 0, inf]
   [inf, inf, 1, 0]
```

Doğru sürümde `0 -> 2` mesafesi `3`'tür ve yol `[0, 1, 3, 2]`'dir. Yanlış sürümde aynı hücre `inf`'tir. Şekil 17.8, doğru sürümde her `k` adımından sonra matrisin nasıl değiştiğini gösterir.

![Şekil 17.8: Floyd-Warshall matrisleri. k = 1 adımında (0,3) hücresi 2 olur; k = 3 adımında (0,2) hücresi 3 olur ve yol tamamlanır.](gorseller/b17_floyd_matris.png)

Floyd-Warshall'ın karmaşıklığı `O(V³)`, bellek `O(V²)`'dir. Yoğun graflarda ve küçük `V` için (birkaç yüz düğüm) çok uygundur. Negatif döngü kontrolü de kolaydır: bir `i` için `dist[i][i] < 0` ise `i` bir negatif döngünün üzerindedir.

## 17.9 A*: sezgisel ile daraltma

Dijkstra, hedefe giden yolu bulmak için kaynağın etrafındaki tüm daireleri (mesafesi hedefe ulaşana kadar olan düğümleri) genişletir. Ama bir İHA rota planlayıcısı için büyük bir kısmı gereksiz olabilir: hedef sağ alttaysa sol üsttekileri işlemek boşa gider. **A\*** bu bilgiyi kullanır. Her düğüm için iki değer tutar: `g(u)`, kaynaktan `u`'ya bilinen en kısa mesafe; `h(u)`, `u`'dan hedefe bir **sezgisel** tahmin. Kuyruk `f(u) = g(u) + h(u)` ile sıralanır.

Sezgisel kabul edilebilir (admissible) olmalıdır: hiçbir zaman gerçek kalan mesafeyi aşmamalıdır. Bu durumda A*, hedef ilk kez kuyruktan çıktığında bulunan yolun optimal olduğunu garanti eder. Izgara üzerinde dört yönlü hareket ve her hücreye girme maliyeti en az `1` ise, Manhattan mesafesi (`|r - r_hedef| + |c - c_hedef|`) kabul edilebilir bir sezgiseldir: her adım en az 1 maliyetlidir ve Manhattan mesafesi her adımda en fazla 1 azalır. Bu sezgisel, bir düğümden komşusuna geçerken tutarlıdır (consistent) da; bu, kapalı küme ile yazılan kodun doğruluğu için yeterlidir.

Dijkstra, `h = 0` durumundaki A*'dır. Aşağıdaki program aynı rastgele ızgarada iki yöntemi çalıştırır ve genişletilen düğüm sayısını sayar. Izgara 20 × 20'dir, hücrelerin yaklaşık yüzde 20'si engeldir, her hücre 1 ile 5 arasında bir maliyete sahiptir. Tohum `42`'dir.

```python
# astar.py - Izgarada A* ve Dijkstra karsilastirmasi.
# izgara[r][c] = 0: engel; >= 1: o hucreye girmenin maliyeti.
import heapq
import random

INF = float("inf")


def a_star(izgara, bas, hedef, sezgisel=True):
    """Donus: (maliyet, genisletilen_dugum_sayisi). sezgisel=False ise
    h = 0 alinir ve algoritma Dijkstra'ya donusur."""
    R, C = len(izgara), len(izgara[0])

    def h(r, c):
        if not sezgisel:
            return 0
        return abs(r - hedef[0]) + abs(c - hedef[1])   # Manhattan

    g = {bas: 0}
    kapali = set()
    yigin = [(h(*bas), 0, bas)]               # (f = g + h, g, dugum)
    genis = 0
    while yigin:
        _, gu, (r, c) = heapq.heappop(yigin)
        if (r, c) in kapali:
            continue
        kapali.add((r, c))
        genis += 1
        if (r, c) == hedef:
            return gu, genis
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and izgara[nr][nc] > 0:
                yeni = gu + izgara[nr][nc]
                if yeni < g.get((nr, nc), INF):
                    g[(nr, nc)] = yeni
                    f = yeni + h(nr, nc)
                    heapq.heappush(yigin, (f, yeni, (nr, nc)))
    return INF, genis


```

Yukarıdaki fonksiyon `kapali` kümesini kullanır: bir düğüm bir kez genişletildiğinde (kapatıldığında) tekrar genişletilmez. Eski kayıtlar tembel silme ile atlanır, tıpkı Dijkstra'da olduğu gibi. Izgara üretici ve ana program aşağıdadır.

```python
def rastgele_izgara(n, rng, p_engel=0.2):
    izgara = [[0 if rng.random() < p_engel else rng.randint(1, 5)
               for _ in range(n)] for _ in range(n)]
    izgara[0][0] = izgara[n - 1][n - 1] = 1    # bas ve hedef bos
    return izgara


if __name__ == "__main__":
    rng = random.Random(42)
    hedef = (19, 19)
    izgara = rastgele_izgara(20, rng)
    # ulasilabilir bir izgara bulana kadar yeniden uret
    while a_star(izgara, (0, 0), hedef)[0] == INF:
        izgara = rastgele_izgara(20, rng)
    m1, g1 = a_star(izgara, (0, 0), hedef, sezgisel=True)
    m2, g2 = a_star(izgara, (0, 0), hedef, sezgisel=False)
    print("A*      : maliyet", m1, " genisletilen", g1)
    print("Dijkstra: maliyet", m2, " genisletilen", g2)
```

```term
$ python astar.py
A*      : maliyet 98  genisletilen 286
Dijkstra: maliyet 98  genisletilen 322
```

Her iki yöntem aynı maliyeti (98) bulur; fark genişletilen düğüm sayısındadır: A* 286, Dijkstra 322 düğüm genişletir. Bu, bu ızgarada yaklaşık yüzde 11'lik bir azalmadır. Bu oran, ızgaranın yapısına ve sezgiselin ne kadar sıkı olduğuna bağlıdır; her ızgarada aynı kazancı beklemek yanlış olur. Şekil 17.9 iki arama alanını yan yana gösterir.

![Şekil 17.9: Aynı izgarada A* (solda) ve Dijkstra (sağda) genişletilen düğümler. Kırmızı hat bulunan yolu gösterir.](gorseller/b17_astar_izgara.png)

A*'ın karmaşıklığı, sezgisele bağlı olarak en kötü durumda Dijkstra ile aynıdır (`O((V+E) log V)`). Kazanç, sezgiselin tahmininin gerçeğe ne kadar yakın olduğuna bağlıdır. Ödev olarak bir İHA rota planlayıcısında bu farkı ölçmek, 'Kendin Yap' bölümündeki ilk projenin çekirdeğidir.

## 17.10 Minimum yayılan ağaç: Union-Find, Kruskal, Prim

Bir **yayılan ağaç** (spanning tree), grafın tüm düğümlerini içeren, döngüsüz ve bağlantılı bir alt graftır. `n` düğümlü bir yayılan ağaç her zaman `n - 1` kenar içerir (Bölüm 11.1'deki gözlem). Ağırlıklı bir grafta **minimum yayılan ağaç (MST)**, toplam kenar ağırlığı en küçük olan yayılan ağaçtır. Bir şehirler arasında fiber kablo döşemek ya da bir sensör ağında haberleşme bağlarını en ucuza kurmak bu problemdir.

Bu bölümde iki klasik algoritma göreceğiz: Kruskal ve Prim. İkisinin de doğruluğu aynı fikre dayanır: **kesme özelliği** (cut property). Bir grafı iki parçaya bölen herhangi bir kesmeyi düşünün. Bu kesmenin iki tarafını birleştiren en ucuz kenar, bir MST'nin parçası olabilir. Bu özelliğin tam kanıtı, genel bir açgözlü çerçeve içinde yapılır ve Bölüm 18'in konusudur; burada sezgisel olarak kullanacağız. Kruskal ve Prim, her adımda bu kuralla güvenle bir kenar ekler.

**Union-Find (ayrık kümeler).** Kruskal, iki düğümün aynı bileşende olup olmadığını hızlıca sorgulamak zorundadır. Bunun için Union-Find veri yapısını kullanırız. Her bileşen bir ağaç olarak tutulur; her düğümün bir `ata` (ebeveyn) değeri vardır ve kökün ebeveyni kendisidir. `bul(x)` fonksiyonu `x`'in kökünü bulur; `birlestir(a, b)` iki kümenin köklerini birbirine bağlar.

İki optimizasyon vardır. **Rank (derece) ile birleştirme**: daha küçük ağacı daha büyüğün altına bağlarız, böylece ağaç derinliği logaritmik kalır. **Yol sıkıştırma**: `bul` çağrısı sırasında yolda gördüğümüz tüm düğümleri doğrudan köke bağlarız; sonraki sorgular çok daha kısa sürer. Bu iki yöntemin birlikte kullanılması, `m` işlem için toplam süreyi amortize `O(m · α(n))` yapar; burada `α`, ters Ackermann fonksiyonudur ve pratikte 4'ü geçmeyen sabit bir sayıdır. (Ters Ackermann'ın tanımını bu bölümde vermiyoruz; adını ve rolünü bilmek yeterlidir.)

Aşağıdaki program Union-Find'ı ve iki MST algoritmasını içerir. Union-Find sınıfı, rank ve yol sıkıştırmayı birlikte kullanır.

```python
# mst.py - Union-Find (yol sikistirma + rank), Kruskal ve Prim.
import heapq


class UnionFind:
    def __init__(self, n):
        self.ata = list(range(n))
        self.rank = [0] * n

    def bul(self, x):
        kok = x
        while self.ata[kok] != kok:           # 1. gecis: koku bul
            kok = self.ata[kok]
        while self.ata[x] != kok:             # 2. gecis: sikistir
            sonraki = self.ata[x]
            self.ata[x] = kok
            x = sonraki
        return kok

    def birlestir(self, a, b):
        ra, rb = self.bul(a), self.bul(b)
        if ra == rb:
            return False                      # ayni kume: dongu olur
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra                   # kucugu buyuge bagla
        self.ata[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


```

Kruskal algoritması kenarları ağırlığa göre küçükten büyüğe sıralar ve her kenarı, uçları farklı bileşendeyse ekler. Uçlar aynı bileşendeyse o kenar bir döngü yaratırdı, o yüzden atlanır. Bu, kesme özelliğinin uygulamasıdır: sıralı olduğu için, bir kenarın eklenmesi seçildiğinde o kenar mevcut ormanın iki parçasını bağlayan en ucuz kenardır.

```python
def kruskal(n, kenarlar):
    """kenarlar: [(agirlik, u, v)], yonsuz.
    Donus: (toplam, secilen)."""
    uf = UnionFind(n)
    toplam, secilen = 0, []
    for w, u, v in sorted(kenarlar):          # en ucuzdan basla
        if uf.birlestir(u, v):
            toplam += w
            secilen.append((u, v, w))
    return toplam, secilen


```

Prim algoritması ise bir düğümden başlayıp ağacı büyütür. Her adımda ağaca bağlı düğümlerden dışarıya çıkan en ucuz kenarı bir heap'ten alır. Bu da kesme özelliğinin doğrudan uygulamasıdır: kesme, ağacın içi ile dışıdır.

```python
def prim(n, adj):
    """adj[u] = [(v, w)], yonsuz: her kenar iki yone de yazilir.
    Baglantisiz grafta yalnizca 0'in bileseni kapsanir."""
    if n == 0:
        return 0, []
    bitti = [False] * n
    toplam, secilen = 0, []
    yigin = [(0, 0, -1)]              # (agirlik, dugum, ebeveyn)
    while yigin:
        w, u, p = heapq.heappop(yigin)
        if bitti[u]:
            continue
        bitti[u] = True
        if p != -1:
            toplam += w
            secilen.append((p, u, w))
        for v, wv in adj[u]:
            if not bitti[v]:
                heapq.heappush(yigin, (wv, v, u))
    return toplam, secilen


```

Ana program altı düğümlü bir graf üzerinde iki algoritmayı çalıştırır. Prim için kenarlar iki yöne de yazılmalıdır, çünkü komşuluk listesi yönsüzdür.

```python
if __name__ == "__main__":
    kenarlar = [(4, 0, 1), (3, 0, 2), (1, 1, 2), (2, 1, 3),
                (4, 2, 3), (5, 2, 4), (8, 3, 4), (9, 3, 5),
                (3, 4, 5)]
    n = 6
    adj = [[] for _ in range(n)]
    for w, u, v in kenarlar:
        adj[u].append((v, w))
        adj[v].append((u, w))
    print("Kruskal:", kruskal(n, kenarlar))
    print("Prim   :", prim(n, adj))
```

```term
$ python mst.py
Kruskal: (14, [(1, 2, 1), (1, 3, 2), (0, 2, 3), (4, 5, 3), (2, 4, 5)])
Prim   : (14, [(0, 2, 3), (2, 1, 1), (1, 3, 2), (2, 4, 5), (4, 5, 3)])
```

İki algoritma aynı toplam ağırlığı (14) verir, ama kenarları farklı sırayla seçer. Şekil 17.10 Kruskal ile Prim'in seçtiği kenarların sırasını gösterir. Her iki durumda da seçilen kenar kümesi aynıdır; bu her grafta doğru olmayabilir (eşit ağırlıklı kenarlar varsa birden fazla MST olabilir).

![Şekil 17.10: Aynı grafta Kruskal (solda) ve Prim (sağda). Kırmızı kenarlar MST'dir; #k, seçilme sırasını gösterir.](gorseller/b17_mst_cift.png)

Union-Find ile Kruskal'ın toplam karmaşıklığı kenar sıralamasıyla belirlenir: `O(E log E)`. Prim, ikili heap ile `O(E log V)`'dir. Seyrek graflarda ikisi de pratiktir; yoğun graflarda Prim'in bir dizi üzerinde yazılan `O(V²)` sürümü tercih edilebilir.

Union-Find'ın bellek ve zaman gereksinimi, bağlantısallık sorguları için de kullanılır: bir kümeyi tek bir kökle temsil ettiğimizden, iki düğümün aynı kümede olup olmadığı iki `bul` çağrısıyla yanıtlanır.

Şekil 17.11, yol sıkıştırmanın etkisini gösterir: zincir biçimindeki bir ağaçta bir `bul` çağrısı, yolu doğrudan köke bağlar.

![Şekil 17.11: Union-Find ağacı. Solda 0'dan kök 5'e uzanan zincir; sağda find(0) sonrası tüm düğümler doğrudan köke bağlı.](gorseller/b17_uf_sikistirma.png)

## 17.11 Çapraz testler: algoritmalar birbirini nasıl sınar

Bir algoritmanın doğru olduğunu tek bir örnekle kanıtlayamayız. Ama birbirinden bağımsız iki algoritmanın aynı sonuçları verdiğini rastgele binlerce grafta görürsek, güven artar. Bu bölümdeki her algoritma, ya başka bir algoritmayla ya da kaba kuvvet tanımıyla karşılaştırılır. Tüm rastgele veriler `random.Random(42)` ile üretilir; böylece sonuçları aynen tekrarlayabilirsiniz.

Testlerin amacı üç şeyi ayırt etmektir. Birincisi, iki algoritma aynı sonucu veriyor mu (Dijkstra ile Bellman-Ford). İkincisi, bir sonuç doğru bir tanıma uyuyor mu (Tarjan'ın bileşenleri ile karşılıklı erişilebilirlik). Üçüncüsü, sınır durumlarında ne oluyor (boş graf, tek düğüm, ulaşılamayan düğüm, eşit ağırlıklar). Testin tamamı aşağıdadır; bir parçası elle okunabilmesi için fonksiyonlar gruplara ayrılmıştır.

```python
# cross_test.py - Algoritmalari birbirine ve bagimsiz
# referanslara karsi
# sinar. Tum rastgele veriler random.Random(42) ile uretilir.
import graphlib
import itertools
import random

from bellman import bellman_ford
from bipartite import iki_renkli
from dijkstra import INF, bfs_mesafe, dijkstra, zero_one_bfs
from floyd import floyd
from mst import UnionFind, kruskal, prim
from tarjan import kopru_eklem, tarjan_scc
from topo import dag_en_kisa, dfs_topo, kahn


def yonlu_kenarlar(rng, n, p, lo, hi):
    """(u, v, w) listesi; her yonlu cift en fazla bir kez."""
    return [(u, v, rng.randint(lo, hi)) for u in range(n)
            for v in range(n) if u != v and rng.random() < p]


def komsu(n, kenarlar):
    adj = [[] for _ in range(n)]
    for u, v, w in kenarlar:
        adj[u].append((v, w))
    return adj


def matris(n, kenarlar):
    w = [[INF] * n for _ in range(n)]
    for i in range(n):
        w[i][i] = 0
    for u, v, c in kenarlar:
        w[u][v] = min(w[u][v], c)
    return w


```

Yukarıdaki yardımcılar, rastgele yönlü ağırlıklı graf üretir (`yonlu_kenarlar`), komşuluk listesi ve Floyd için ağırlık matrisi kurar. Test 1 ve 2 en önemli karşılaştırmalardır: negatif olmayan kenarlarda Dijkstra, Bellman-Ford ve Floyd aynı mesafeleri vermelidir; negatif kenarlarda ise Bellman-Ford'un `None` döndürmesi, kaynaktan negatif döngüye erişim olmasıyla birebir eşleşmelidir.

```python
def test_1_negatifsiz():
    """Dijkstra = Bellman-Ford = Floyd (negatif kenar yok)."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(1, 12)
        k = yonlu_kenarlar(rng, n, 0.3, 0, 9)
        s = rng.randrange(n)
        d1, _ = dijkstra(n, komsu(n, k), s)
        d2, _ = bellman_ford(n, k, s)
        fd = floyd(n, matris(n, k))[0]
        ok += d1 == d2 == fd[s]
    print(f"Test 1 Dijkstra = BF = Floyd: {ok}/{top}")


def test_2_negatif():
    """Negatif kenar: BF None <=> kaynaktan negatif dongu erisilir."""
    rng, ok, top, dongulu = random.Random(42), 0, 200, 0
    for _ in range(top):
        n = rng.randint(2, 8)
        k = yonlu_kenarlar(rng, n, 0.35, -2, 9)
        s = rng.randrange(n)
        fd = floyd(n, matris(n, k))[0]
        beklenen = any(fd[s][v] < INF and fd[v][v] < 0
                       for v in range(n))
        sonuc = bellman_ford(n, k, s)
        dongulu += beklenen
        if sonuc is None:
            ok += beklenen
        else:
            ok += (not beklenen) and sonuc[0] == fd[s]
    print(f"Test 2 BF negatif dongu: {ok}/{top} (dongulu {dongulu})")


```

Test 3, BFS ve 0-1 BFS'i Dijkstra ile karşılaştırır. Test 4 Kruskal ile Prim'in toplam ağırlıklarını karşılaştırır ve bağlantı ile `n - 1` kenar koşullarını da denetler. Rastgele bağlı graf üreteci, önce rastgele bir ağaç kurar, sonra ek kenarlar ekler; bu sayede her graf bağlı olur.

```python
def test_3_bfs():
    """BFS = Dijkstra (w=1); 0-1 BFS = Dijkstra (w in {0,1})."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(1, 15)
        k1 = yonlu_kenarlar(rng, n, 0.2, 1, 1)
        k2 = yonlu_kenarlar(rng, n, 0.2, 0, 1)
        s = rng.randrange(n)
        a = (bfs_mesafe(n, komsu(n, k1), s)
             == dijkstra(n, komsu(n, k1), s)[0])
        b = (zero_one_bfs(n, komsu(n, k2), s)
             == dijkstra(n, komsu(n, k2), s)[0])
        ok += a and b
    print(f"Test 3 BFS ve 0-1 BFS: {ok}/{top}")


def rastgele_bagli(rng, n):
    """Once rastgele bir agac, sonra ek kenarlar: her zaman bagli."""
    k = [(rng.randrange(v), v, rng.randint(1, 5))
         for v in range(1, n)]
    for _ in range(n):
        u, v = rng.sample(range(n), 2)
        k.append((u, v, rng.randint(1, 5)))
    return k                               # (u, v, w)


def test_4_mst():
    """Kruskal = Prim (toplam agirlik); n-1 kenar; dugumler bagli."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(2, 15)
        k = rastgele_bagli(rng, n)
        adj = [[] for _ in range(n)]
        for u, v, w in k:
            adj[u].append((v, w))
            adj[v].append((u, w))
        t1, s1 = kruskal(n, [(w, u, v) for u, v, w in k])
        t2, s2 = prim(n, adj)
        uf = UnionFind(n)
        for u, v, _ in s1:
            uf.birlestir(u, v)
        bagli = len({uf.bul(x) for x in range(n)}) == 1
        ok += (t1 == t2 and len(s1) == n - 1
               and len(s2) == n - 1 and bagli)
    print(f"Test 4 Kruskal = Prim: {ok}/{top}")


```

Test 5, sınır durumlarını yazdırır. Bu bir karşılaştırma değil, gözlemdir; sonuçlar çıktıda görülecek ve beklenen değerlerle elle karşılaştırılacaktır.

```python
def test_5_sinir():
    """Sinir durumlari: bos graf, tek dugum, ulasilamayan dugum,
    esit agirlik."""
    print("Test 5 sinir durumlari:")
    print("  kruskal(0, [])       =", kruskal(0, []))
    print("  prim(0, [])          =", prim(0, []))
    print("  dijkstra(1,[[]],0)   =", dijkstra(1, [[]], 0)[0])
    print("  floyd(1, [[0]])      =", floyd(1, [[0]])[0])
    print("  tarjan_scc(1,[[]])   =", tarjan_scc(1, [[]]))
    print("  kahn(0, [])          =", kahn(0, []))
    print("  ulasilamayan dugum   =",
          dijkstra(3, [[(1, 4)], [], []], 0)[0])
    print("  esit agirlik Kruskal =",
          kruskal(3, [(1, 0, 1), (1, 1, 2), (1, 0, 2)]))


```

Test 6, Tarjan'ın SCC'lerini, transitif kapanışla hesaplanan karşılıklı erişilebilirlik kümeleriyle karşılaştırır. Test 7 ise köprü ve eklem noktalarını, düğüm ya da kenar çıkarıp bileşen sayısına bakan kaba kuvvet tanımıyla karşılaştırır.

```python
def test_6_scc():
    """Tarjan SCC = karsilikli erisilebilirlik (transitif kapanis)."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(1, 10)
        k = yonlu_kenarlar(rng, n, 0.25, 1, 1)
        adj = [[] for _ in range(n)]
        for u, v, _ in k:
            adj[u].append(v)
        w = matris(n, k)
        r = [[i == j or w[i][j] < INF for j in range(n)]
             for i in range(n)]
        for m in range(n):
            for i in range(n):
                for j in range(n):
                    r[i][j] = r[i][j] or (r[i][m] and r[m][j])
        beklenen = {frozenset(v for v in range(n)
                              if r[u][v] and r[v][u])
                    for u in range(n)}
        bulunan = {frozenset(c) for c in tarjan_scc(n, adj)}
        ok += beklenen == bulunan
    print(f"Test 6 Tarjan SCC: {ok}/{top}")


def bilesen_sayisi(n, kenar):
    adj = [[] for _ in range(n)]
    for u, v in kenar:
        adj[u].append(v)
        adj[v].append(u)
    gorulen, sayi = [False] * n, 0
    for s in range(n):
        if not gorulen[s]:
            sayi += 1
            yig = [s]
            gorulen[s] = True
            while yig:
                x = yig.pop()
                for y in adj[x]:
                    if not gorulen[y]:
                        gorulen[y] = True
                        yig.append(y)
    return sayi


def test_7_kopru_eklem():
    """Kopru: silince bilesen artar. Eklem: dugum silince
    bilesen artar."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(2, 9)
        adaylar = [(rng.randrange(n), rng.randrange(n))
                   for _ in range(rng.randint(1, 2 * n))]
        kenar = sorted({tuple(sorted(e)) for e in adaylar
                        if e[0] != e[1]})
        adj = [[] for _ in range(n)]
        for u, v in kenar:
            adj[u].append(v)
            adj[v].append(u)
        kop, ekl = kopru_eklem(n, adj)
        b0 = bilesen_sayisi(n, kenar)
        beklenen_kop = sorted(e for e in kenar
                              if bilesen_sayisi(
                                  n, [f for f in kenar if f != e])
                              > b0)
        beklenen_ekl = sorted(u for u in range(n)
                              if bilesen_sayisi(
                                  n, [e for e in kenar if u not in e])
                              - 1 > b0)
        ok += kop == beklenen_kop and ekl == beklenen_ekl
    print(f"Test 7 kopru ve eklem: {ok}/{top}")


```

Test 8 topolojik sıralamayı kontrol eder: Kahn ile DFS'in çıktıları geçerli bir sıra olmalı ve döngü tespiti Python'un `graphlib` modülüyle aynı sonucu vermelidir. Test 9 DAG'de en kısa yolu Bellman-Ford ile, iki renklendirmeyi ise tüm `2^n` renklendirmeyi deneyen kaba kuvvetle karşılaştırır.

```python
def test_8_topo():
    """Kahn ve DFS: gecerli siralar; dongu tespiti graphlib ile
    ayni."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(1, 10)
        dag = rng.random() < 0.5
        k = [(u, v) for u in range(n) for v in range(n)
             if u != v and rng.random() < 0.3 and (not dag or u < v)]
        adj = [[] for _ in range(n)]
        for u, v in k:
            adj[u].append(v)
        sira_k, dk = kahn(n, adj)
        sira_d, dd = dfs_topo(n, adj)
        ts = graphlib.TopologicalSorter(
            {v: [u for u, w in k if w == v] for v in range(n)})
        try:
            ts.prepare()
            gd = False
        except graphlib.CycleError:
            gd = True
        gecerli = True
        if not dk and not dd:
            for sira in (sira_k, sira_d):
                poz = {u: i for i, u in enumerate(sira)}
                gecerli = gecerli and all(poz[u] < poz[v]
                                          for u, v in k)
        ok += (dk == gd == (dd is not None)) and gecerli
    print(f"Test 8 topolojik siralama: {ok}/{top}")


def test_9_dag_ve_iki_renk():
    """DAG'da en kisa yol = BF (negatif kenar serbest); 2-renk
    brute force ile karsilastirilir."""
    rng, ok, top, ok2 = random.Random(42), 0, 200, 0
    for _ in range(top):
        n = rng.randint(1, 10)
        k = [(u, v, rng.randint(-3, 9)) for u in range(n)
             for v in range(u + 1, n)
             if rng.random() < 0.35]
        s = rng.randrange(n)
        ok += (dag_en_kisa(n, komsu(n, k), s)
               == bellman_ford(n, k, s)[0])
    for _ in range(top):
        n = rng.randint(1, 9)
        k = [(u, v) for u in range(n) for v in range(u + 1, n)
             if rng.random() < 0.3]
        adj = [[] for _ in range(n)]
        for u, v in k:
            adj[u].append(v)
            adj[v].append(u)
        beklenen = any(all(c[u] != c[v] for u, v in k)
                       for c in itertools.product((0, 1), repeat=n))
        ok2 += iki_renkli(n, adj)[0] == beklenen
    print(f"Test 9 DAG en kisa yol: {ok}/{top}; "
          f"iki renkli: {ok2}/{top}")


```

Ana program testleri sırayla çalıştırır.

```python
if __name__ == "__main__":
    test_1_negatifsiz()
    test_2_negatif()
    test_3_bfs()
    test_4_mst()
    test_5_sinir()
    test_6_scc()
    test_7_kopru_eklem()
    test_8_topo()
    test_9_dag_ve_iki_renk()
```

```term
$ python cross_test.py
Test 1 Dijkstra = BF = Floyd: 200/200
Test 2 BF negatif dongu: 200/200 (dongulu 25)
Test 3 BFS ve 0-1 BFS: 200/200
Test 4 Kruskal = Prim: 200/200
Test 5 sinir durumlari:
  kruskal(0, [])       = (0, [])
  prim(0, [])          = (0, [])
  dijkstra(1,[[]],0)   = [0]
  floyd(1, [[0]])      = [[0]]
  tarjan_scc(1,[[]])   = [[0]]
  kahn(0, [])          = ([], False)
  ulasilamayan dugum   = [0, 4, inf]
  esit agirlik Kruskal = (2, [(0, 1, 1), (0, 2, 1)])
Test 6 Tarjan SCC: 200/200
Test 7 kopru ve eklem: 200/200
Test 8 topolojik siralama: 200/200
Test 9 DAG en kisa yol: 200/200; iki renkli: 200/200
```

Çıktıda her test için `başarılı/toplam` sayısı verilir. Test 1, 3, 4, 6, 7, 8 ve 9 `200/200` döner; Test 2 de tüm 200 grafta beklenen sonucu verir ve bu grafların 25 tanesi negatif döngü içerir. Sınır durumları Test 5'in çıktısında görülür: boş graf için Kruskal `(0, [])`, tek düğümlü graf için Dijkstra `[0]` döner; ulaşılamayan düğümün mesafesi `inf`'tir. Eşit ağırlıklı kenarlarda Kruskal, sıralamanın kararlı kırılımı nedeniyle `(0, 1)` ve `(0, 2)` kenarlarını seçer; iki kenar da ağırlık 1'dir ve toplam 2'dir.

Bir testin gerçekten bir hata yakalayıp yakalamadığını da görmek gerekir. Doğru Floyd yerine yanlış sıralı sürümü Test 1'e koyduğumuzda, sonuç 200 yerine 148 başarılı olur. Yani test, yanlış sıralı Floyd'u yakalar. Ayrıca bu rastgele graflarda köprü ve eklem noktası içeren graf sayısı yüksektir (200 grafın 173'ünde köprü, 117'sinde eklem vardır); test bu nedenle yalnızca boş sonuçları değil, anlamlı sonuçları da sınar.

Bu test, bir kanıtın yerini tutmaz. Ama Bölüm 16'da da söylediğimiz gibi, bir algoritma küçük örneklerde doğrulanana kadar güvenilir değildir; rastgele karşılaştırma bu doğrulamanın en ucuz yoludur.

## 17.12 Karar tablosu ve gerçek dünya

Hangi problemde hangi algoritmayı kullanacağınızı seçmek, bu bölümün en pratik becerisidir. Aşağıdaki tablo, sorunuzun şekline göre bir ilk seçim verir. Tablodaki karar, kenar ağırlıklarının negatif olup olmadığına, graf yönlü ve çevrimsiz mi, tek kaynak mı tüm çiftler mi olduğuna ve graf yoğun mu seyrek mi olduğuna bakar.

| Problem | Graf özelliği | Algoritma | Karmaşıklık |
|---|---|---|---|
| Ağırlıksız en kısa yol | Tüm kenarlar 1 | BFS | `O(V + E)` |
| 0/1 ağırlıklı en kısa yol | Ağırlık 0 ya da 1 | 0-1 BFS | `O(V + E)` |
| Tek kaynak, negatif yok | Ağırlık ≥ 0 | Dijkstra (heap) | `O((V+E) log V)` |
| Tek kaynak, negatif var | Negatif kenar olabilir | Bellman-Ford | `O(V · E)` |
| DAG'da en kısa yol | Yönlü, döngüsüz | Topolojik sıra + gevşetme | `O(V + E)` |
| Tüm çiftler | Küçük `V` | Floyd-Warshall | `O(V³)` |
| Izgarada hedef odaklı yol | Sezgisel mümkün | A* | `O((V+E) log V)`, en kötü |
| Minimum yayılan ağaç, seyrek | Yönsüz, ağırlıklı | Kruskal + Union-Find | `O(E log E)` |
| Minimum yayılan ağaç, yoğun | Yönsüz, ağırlıklı | Prim (dizi ya da heap) | `O(V²)` / `O(E log V)` |
| Bağımlılık sırası | Yönlü, döngü olabilir | Kahn ya da DFS | `O(V + E)` |
| Döngü ya da iki parçalılık | Yönlü ya da yönsüz | DFS ya da BFS renklendirme | `O(V + E)` |
| SCC, köprü, eklem | Yönlü / yönsüz | Tarjan (low-link) | `O(V + E)` |

Gerçek dünyada bu algoritmalar her yerdedir. **OSPF** iç ağ yönlendirme protokolü, her yönlendiricinin ağın topolojisini bildiği bir durumda Dijkstra çalıştırarak en kısa yolları hesaplar. **RIP** ise her yönlendiricinin yalnızca komşularından mesafe bilgisi aldığı bir mesafe-vektör protokolüdür ve Bellman-Ford mantığını dağıtık olarak uygular. **Paket yöneticileri** bağımlılık grafını topolojik sırayla çözer ve döngü gördüğünde hata verir. **Harita uygulamaları** büyük yol ağlarında doğrudan Dijkstra yerine A* ve kontraksiyon hiyerarşileri (genel bilgi: bu tekniklerin ayrıntısı bu kitabın kapsamı dışındadır) gibi hızlandırmalar kullanır. Savunma tarafında aynı soru, bir İHA'nın rota segmentlerinde engel ve maliyet haritası üzerinde en kısa yolu aramasıdır; bu tam olarak 17.9'daki A* ve 17.6'daki Dijkstra'nın kullanım alanıdır.

Bu karar tablosunun en önemli dersi şudur: yanlış bir algoritma seçmenin bedeli çoğu zaman yanlış cevaptır, yavaşlık değil. Negatif kenarda Dijkstra kullanmak yanlış mesafe verir ve bunu bir hata mesajı olmadan yapar. Bu yüzden önce graf özelliğini sorun, sonra algoritmayı seçin.

Modelleme hatası da algoritma hatasından pahalıdır (Bölüm 11.8'deki ilke). Bir kenara yanlış yön vermek ya da bir maliyeti yanlış birimde yazmak, en iyi algoritmayı bile yanlış cevaba götürür. Bu yüzden bir problemi grafa dönüştürdüğünüzde, önce düğüm ve kenar tanımını yazın, sonra algoritmayı seçin.


## Çözümlü Örnekler

Bu bölümdeki dört örnek ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz; Adım 6'da programın gerçek çıktısından çıkardığımız bir iz tablosu olacak. Çözüm kodunu okumadan önce her örneğin ilk üç adımını kendi kâğıdınızda deneyin.

### Örnek 1 (★): Ders ön koşulları ve geçerli dönem planı

**Problem:** Bir bölümde sekiz ders var. Bazı derslerin ön koşulları vardır: `Veri Yapilari` için `Programlama` gerekir, `Bitirme` için `Ag`, `Derleyici` ve `Algoritmalar` gerekir. Tüm dersleri alabileceğimiz bir sıra bulun. Eğer ön koşullar bir döngü oluşturuyorsa, bunu bildirin.

**Adım 1 — Anla.** Girdi, ders adlarının listesi ile `(önce, sonra)` çiftlerinin listesidir. Çıktı iki durumdan biridir: tüm dersleri içeren geçerli bir sıra, ya da döngüde kalan derslerin listesi. Kenar durumlar: hiç ön koşul yoksa sıra ders listesinin kendisidir; döngü varsa geçerli sıra yoktur.

**Adım 2 — Örnekle.** Sekiz derslik grafı Şekil 17.2'de gördünüz. Ön koşul sayısı on tanedir. Döngüsüz hâlde bir geçerli sıra `Programlama, Matematik, Veri Yapilari, Isletim, Algoritmalar, Ag, Derleyici, Bitirme`'dir. Ters bir kenar eklenirse (`Derleyici -> Programlama`) bu sıra artık geçerli değildir.

**Adım 3 — Kaba çöz.** Sekiz dersin tüm sıralamalarını (permütasyonlarını) dene; her birinde, her ön koşul kenarının önce gelen dersi daha önce yerleştirip yerleştirmediğine bak. Bu doğru, ama `8! = 40320` sıralama ve her biri on kenar kontrolü demek. Yirmi ders için `20!` yaklaşık `2,4 · 10^18` sıralamadır; bu kaba kuvvetle yapılamaz.

**Adım 4 — Örüntü.** Ön koşulu olmayan bir ders hemen alınabilir. Alınan bir dersin bağımlıları, o dersin ön koşulu bir eksildiği için bir adım yaklaşır. Bu, Kahn'ın derece ve kuyruk fikridir: derecesi sıfır olan düğümler kuyruğa girer, işlendikçe bağımlılarının derecesi azalır. Derecesi sıfıra düşen düğüm kuyruğa eklenir.

**Adım 5 — İyileştir.** Her kenar yalnızca kaynağı işlendiğinde bir kez azaltılır; her düğüm bir kez kuyruğa girer. Toplam iş `O(n + m)`'dir (`n` ders, `m` ön koşul). Döngü tespiti de bedavadır: kuyruk boşaldığında hâlâ derecesi sıfırdan büyük bir ders kaldıysa, bu dersler bir döngünün içinde ya da ardında beklemektedir. Program bu kalanları döndürür.

**Adım 6 — Doğrula.** Aşağıdaki iz, programın çıktısındaki kuyruk durumlarıyla birebir aynıdır. Ön koşul kenarlarına bakarak her derecenin doğru azaldığını elle kontrol edebilirsiniz.

```python
# ornek1_ders.py - Ders on kosullari: gecerli sira, dongu (Kahn).
from collections import deque


def ders_sirasi(dersler, onkosul):
    """onkosul: [(once, sonra)]. Donus: (sira, kalan). Dongu varsa
    sira kisadir ve kalan, siraya giremeyen dersleri listeler."""
    idx = {ad: i for i, ad in enumerate(dersler)}
    n = len(dersler)
    adj = [[] for _ in range(n)]
    derece = [0] * n
    for a, b in onkosul:
        adj[idx[a]].append(idx[b])
        derece[idx[b]] += 1
    kuyruk = deque(i for i in range(n) if derece[i] == 0)
    sira = []
    print("  baslangic kuyruk:", [dersler[i] for i in kuyruk])
    while kuyruk:
        u = kuyruk.popleft()
        sira.append(dersler[u])
        for v in adj[u]:
            derece[v] -= 1
            if derece[v] == 0:
                kuyruk.append(v)
        print(f"  {dersler[u]:<14} alindi; kuyruk:",
              [dersler[i] for i in kuyruk])
    kalan = [dersler[i] for i in range(n) if derece[i] > 0]
    return (sira if not kalan else None), kalan


```

Ana program iki sorgu yapar: önce temiz grafı, sonra ters kenar eklenmiş grafı çözer.

```python
if __name__ == "__main__":
    dersler = ["Programlama", "Matematik", "Veri Yapilari",
               "Algoritmalar",
               "Isletim", "Ag", "Derleyici", "Bitirme"]
    onkosul = [("Programlama", "Veri Yapilari"),
               ("Programlama", "Isletim"),
               ("Veri Yapilari", "Algoritmalar"),
               ("Matematik", "Algoritmalar"),
               ("Isletim", "Ag"), ("Veri Yapilari", "Derleyici"),
               ("Algoritmalar", "Derleyici"),
               ("Algoritmalar", "Bitirme"),
               ("Ag", "Bitirme"), ("Derleyici", "Bitirme")]
    sira, kalan = ders_sirasi(dersler, onkosul)
    print("Sira:", sira, "kalan:", kalan)
    print("--- ters kenar eklenirse ---")
    onkosul.append(("Derleyici", "Programlama"))
    sira, kalan = ders_sirasi(dersler, onkosul)
    print("Sira:", sira, "kalan:", kalan)
```

```term
$ python ornek1_ders.py
  baslangic kuyruk: ['Programlama', 'Matematik']
  Programlama    alindi; kuyruk: ['Matematik', 'Veri Yapilari', 'Isletim']
  Matematik      alindi; kuyruk: ['Veri Yapilari', 'Isletim']
  Veri Yapilari  alindi; kuyruk: ['Isletim', 'Algoritmalar']
  Isletim        alindi; kuyruk: ['Algoritmalar', 'Ag']
  Algoritmalar   alindi; kuyruk: ['Ag', 'Derleyici']
  Ag             alindi; kuyruk: ['Derleyici']
  Derleyici      alindi; kuyruk: ['Bitirme']
  Bitirme        alindi; kuyruk: []
Sira: ['Programlama', 'Matematik', 'Veri Yapilari', 'Isletim',
    'Algoritmalar', 'Ag', 'Derleyici', 'Bitirme'] kalan: []
--- ters kenar eklenirse ---
  baslangic kuyruk: ['Matematik']
  Matematik      alindi; kuyruk: []
Sira: None kalan: ['Programlama', 'Veri Yapilari', 'Algoritmalar',
    'Isletim', 'Ag', 'Derleyici', 'Bitirme']
```

Aşağıdaki tablo çıktıdaki kuyruk değişimlerini özetler. Derece sütunu, ilgili dersin işlenmesiyle derecesi sıfıra inen bağımlıları gösterir.

| Adım | İşlenen ders | Derecesi sıfıra düşen | Kuyruk (baştan sona) |
|---|---|---|---|
| 0 | — | `Programlama`, `Matematik` | `Programlama`, `Matematik` |
| 1 | `Programlama` | `Veri Yapilari`, `Isletim` | `Matematik`, `Veri Yapilari`, `Isletim` |
| 2 | `Matematik` | — (`Algoritmalar` 2 → 1) | `Veri Yapilari`, `Isletim` |
| 3 | `Veri Yapilari` | `Algoritmalar` (`Derleyici` 2 → 1) | `Isletim`, `Algoritmalar` |
| 4 | `Isletim` | `Ag` | `Algoritmalar`, `Ag` |
| 5 | `Algoritmalar` | `Derleyici` (`Bitirme` 3 → 2) | `Ag`, `Derleyici` |
| 6 | `Ag` | — (`Bitirme` 2 → 1) | `Derleyici` |
| 7 | `Derleyici` | — (`Bitirme` 1 → 0) | `Bitirme` |
| 8 | `Bitirme` | — | boş |

Ters kenar eklendiğinde `Programlama`'nın derecesi `1`'de kalır, çünkü `Derleyici`'den gelen kenarı hiçbir zaman sıfıra düşürecek bir işlem yoktur. Kuyrukta yalnızca `Matematik` başlar, o işlenince kuyruk boşalır ve yedi ders kalır: `Programlama`, `Veri Yapilari`, `Algoritmalar`, `Isletim`, `Ag`, `Derleyici`, `Bitirme`. Bu kalan kümeyi bir döngü olarak yorumlarsınız; döngünün bir kısmı `Programlama -> Veri Yapilari -> Algoritmalar -> Derleyici -> Programlama` biçimindedir.

**Bunu AI'sız yazabilir misin?** Ön koşul listesi ve bir "döngüde kalanlar" raporu veren bir fonksiyonu, hiç ara bakmadan, on dakikada yazabilir misin? Sonra kendi grafını, bir döngüsü olan bir grafla test et.

### Örnek 2 (★★): Ağda en düşük gecikmeli yol

**Problem:** Altı yönlendiricinin (`R0`–`R5`) arasında gecikme süreleri (ms) bilinen bağlantılar var. `R0`'dan `R5`'e giden, toplam gecikmesi en küçük yolu ve bu gecikmeyi bulun. Bağlantılar iki yönlüdür.

**Adım 1 — Anla.** Girdi dokuz kenar, her biri bir gecikme değeri taşır. Çıktı bir sayı (toplam gecikme) ve bir yol. Gecikmeler negatif değildir; bu nedenle Dijkstra uygundur. Yol bulunamazsa gecikme sonsuzdur.

**Adım 2 — Örnekle.** `R0 -> R2 -> R1 -> R3 -> R4 -> R5` yolu `1 + 2 + 5 + 3 + 1 = 12` ms eder. Doğrudan `R0 -> R1 -> R3 -> R5` yolu `4 + 5 + 6 = 15` ms'dir ve daha kötüdür.

**Adım 3 — Kaba çöz.** `R0`'dan `R5`'e giden tüm basit yolları sıralayıp en kısa olanı seç. Altı düğümlü bir grafta bu, birkaç yüz yolun incelenmesi demektir; ama düğüm sayısı arttıkça üstel büyür.

**Adım 4 — Örüntü.** Her adımda henüz kesinleşmemiş düğümler arasında en küçük tahmini olanı seçersek, bu düğüm kesinleşebilir (negatif kenar yoktur). Bunu bir öncelik kuyruğu ile yaparız: bu Dijkstra'dır (17.6). Ayrıca her düğüm için bir ebeveyn tutarsak yolu geriye doğru kurabiliriz.

**Adım 5 — İyileştir.** Kuyruk `heapq` ile tutulur, eski kayıtlar tembel silme ile atlanır. Toplam karmaşıklık `O((V + E) log V)`'dir. Yol geri kurma `O(V)`'dir.

**Adım 6 — Doğrula.** Programın her pop'tan sonra yazdırdığı `dist` dizisi aşağıdaki tabloda. Son satır, `R5`'in mesafesinin 12 olduğunu ve yolun el ile bulduğumuzla aynı olduğunu gösterir.

```python
# ornek2_gecikme.py - Yonlendiriciler arasi en dusuk gecikmeli yol.
import heapq

INF = float("inf")
AD = ["R0", "R1", "R2", "R3", "R4", "R5"]


def en_kisa(n, kenar, kaynak, hedef):
    """Dijkstra + ebeveyn dizisi. Her adimin izini yazar."""
    adj = [[] for _ in range(n)]
    for u, v, w in kenar:              # yonsuz: iki yone de
        adj[u].append((v, w))
        adj[v].append((u, w))
    dist = [INF] * n
    ebeveyn = [-1] * n
    bitti = [False] * n
    dist[kaynak] = 0
    yigin = [(0, kaynak)]
    while yigin:
        d, u = heapq.heappop(yigin)
        if bitti[u]:
            continue
        bitti[u] = True
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                ebeveyn[v] = u
                heapq.heappush(yigin, (dist[v], v))
        print(f"  {AD[u]} islendi (d={d}); dist =",
              [x if x < INF else "inf" for x in dist])
    yol = []
    u = hedef
    while u != -1:
        yol.append(AD[u])
        u = ebeveyn[u]
    return dist[hedef], yol[::-1]
```

Ana program, kenar listesini ve kaynak-hedef çiftini verir.

```python


if __name__ == "__main__":
    kenar = [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 5), (2, 3, 8),
             (3, 4, 3), (2, 4, 12), (4, 5, 1), (3, 5, 6)]
    gecikme, yol = en_kisa(6, kenar, 0, 5)
    print("R0 -> R5 gecikme:", gecikme, "ms; yol:", " - ".join(yol))
```

```term
$ python ornek2_gecikme.py
  R0 islendi (d=0); dist = [0, 4, 1, 'inf', 'inf', 'inf']
  R2 islendi (d=1); dist = [0, 3, 1, 9, 13, 'inf']
  R1 islendi (d=3); dist = [0, 3, 1, 8, 13, 'inf']
  R3 islendi (d=8); dist = [0, 3, 1, 8, 11, 14]
  R4 islendi (d=11); dist = [0, 3, 1, 8, 11, 12]
  R5 islendi (d=12); dist = [0, 3, 1, 8, 11, 12]
R0 -> R5 gecikme: 12 ms; yol: R0 - R2 - R1 - R3 - R4 - R5
```

| Adım | İşlenen (d) | `R0` | `R1` | `R2` | `R3` | `R4` | `R5` |
|---|---|---|---|---|---|---|---|
| 1 | `R0` (0) | 0 | 4 | 1 | ∞ | ∞ | ∞ |
| 2 | `R2` (1) | 0 | 3 | 1 | 9 | 13 | ∞ |
| 3 | `R1` (3) | 0 | 3 | 1 | 8 | 13 | ∞ |
| 4 | `R3` (8) | 0 | 3 | 1 | 8 | 11 | 14 |
| 5 | `R4` (11) | 0 | 3 | 1 | 8 | 11 | 12 |
| 6 | `R5` (12) | 0 | 3 | 1 | 8 | 11 | 12 |

İkinci adımda `R1`'in mesafesi `4`'ten `3`'e düşer, çünkü `R2` üzerinden gelmek daha ucuzdur: `1 + 2 = 3`. Bu değişim ebeveyn dizisini de günceller (`R1`'in ebeveyni `R0`'dan `R2`'ye geçer). Son satırda `R5`'in ebeveyni `R4`'tür, `R4`'ün ebeveyni `R3`, `R3`'ün ebeveyni `R1`, `R1`'in ebeveyni `R2`, `R2`'nin ebeveyni `R0`'dır. Geri okuyunca `R0 - R2 - R1 - R3 - R4 - R5` elde edilir.

**Bunu AI'sız yazabilir misin?** Bir Dijkstra fonksiyonunu ve yol geri kurmayı sıfırdan, bu tablo gibi her adımın dizisini yazdırarak yazabilir misin? Eşit gecikmeli iki yol olduğunda sonuç ne olur, neden?

### Örnek 3 (★★): Şehirleri en ucuz şekilde bağlamak

**Problem:** Altı şehir (`A`–`F`) arasında yalnızca dokuz olası fiber bağlantı var; her birinin maliyeti bilinmektedir. Tüm şehirleri birbirine bağlayan ve toplam maliyeti en küçük olan bağlantı kümesini bulun.

**Adım 1 — Anla.** Girdi dokuz kenar ve altı düğümdür. Çıktı, seçilen kenarların kümesi ve toplam maliyettir. Graf bağlıdır (her şehir en az bir yoldan ulaşılabilir); aksi hâlde yayılan ağaç olmazdı. Döngü oluşturan bir kenar seçmenin gereği yoktur.

**Adım 2 — Örnekle.** `A-C` (5), `D-E` (5), `E-F` (6), `A-B` (7), `C-D` (7) seçilirse altı şehir bağlanır ve toplam `30`'dur. `B-C` (8) gibi bir kenar eklemek döngü oluşturur; bu yüzden atılır.

**Adım 3 — Kaba çöz.** Dokuz kenardan altı-1 = beşini seçen tüm kümeleri dene (`C(9,5) = 126` küme) ve bağlı olanların en ucuzunu al. Küçük örnekte çalışır; ama büyük graflarda kombinasyon sayısı patlar.

**Adım 4 — Örüntü.** Kesme özelliği sezgisel olarak şunu söyler: bir kesmenin iki tarafını birleştiren en ucuz kenar, bir MST'nin parçası olabilir. Kenarları ağırlığa göre sıralayıp, uçları farklı bileşendeyse en ucuzdan başlayarak ekleyebiliriz. Bu Kruskal'dır (17.10).

**Adım 5 — İyileştir.** Bileşen sorgusunu Union-Find ile yaparız. Sıralama `O(E log E)`, birleşim işlemleri amortize neredeyse sabittir. Döngü oluşturan kenarlar `birlestir` çağrısında `False` döndüğü için kolayca atlanır.

**Adım 6 — Doğrula.** Aşağıdaki tablo, programın kenarları sırayla işlemesini ve her adımda kökleri ve kararı gösterir.

```python
# ornek3_sehir.py - Sehirleri en ucuz baglama (Kruskal + Union-Find).
from mst import UnionFind

SEHIR = ["A", "B", "C", "D", "E", "F"]
KENAR = [(7, 0, 1), (5, 0, 2), (8, 1, 2), (9, 1, 3), (7, 2, 3),
         (5, 3, 4), (15, 2, 5), (6, 4, 5), (8, 3, 5)]


def kruskal_izli(n, kenar):
    uf = UnionFind(n)
    toplam, secilen = 0, []
    for w, u, v in sorted(kenar):
        ku, kv = uf.bul(u), uf.bul(v)
        durum = "KABUL" if ku != kv else "RED  "
        print(f"  {SEHIR[u]}-{SEHIR[v]} ({w:>2})  "
              f"kok {SEHIR[ku]}/{SEHIR[kv]}"
              f"  {durum}")
        if ku != kv:
            uf.birlestir(u, v)
            toplam += w
            secilen.append((SEHIR[u], SEHIR[v], w))
    return toplam, secilen


if __name__ == "__main__":
    toplam, secilen = kruskal_izli(len(SEHIR), KENAR)
    print("Toplam maliyet:", toplam)
    print("Secilen kenarlar:", secilen)
```

```term
$ python ornek3_sehir.py
  A-C ( 5)  kok A/C  KABUL
  D-E ( 5)  kok D/E  KABUL
  E-F ( 6)  kok D/F  KABUL
  A-B ( 7)  kok A/B  KABUL
  C-D ( 7)  kok A/D  KABUL
  B-C ( 8)  kok A/A  RED  
  D-F ( 8)  kok A/A  RED  
  B-D ( 9)  kok A/A  RED  
  C-F (15)  kok A/A  RED  
Toplam maliyet: 30
Secilen kenarlar: [('A', 'C', 5), ('D', 'E', 5), ('E', 'F', 6), ('A', 'B',
    7), ('C', 'D', 7)]
```

| Sıra | Kenar | Ağırlık | Kökler (uç1 / uç2) | Karar | Toplam |
|---|---|---|---|---|---|
| 1 | `A-C` | 5 | `A` / `C` | kabul | 5 |
| 2 | `D-E` | 5 | `D` / `E` | kabul | 10 |
| 3 | `E-F` | 6 | `D` / `F` | kabul | 16 |
| 4 | `A-B` | 7 | `A` / `B` | kabul | 23 |
| 5 | `C-D` | 7 | `A` / `D` | kabul | 30 |
| 6 | `B-C` | 8 | `A` / `A` | red (döngü) | 30 |
| 7 | `D-F` | 8 | `A` / `A` | red (döngü) | 30 |
| 8 | `B-D` | 9 | `A` / `A` | red (döngü) | 30 |
| 9 | `C-F` | 15 | `A` / `A` | red (döngü) | 30 |

Beş kenar kabul edildi (`n - 1 = 5`), toplam `30`. Altıncı satırdan itibaren her kenarın iki ucu zaten aynı kökteydi; yani her biri bir döngü yaratırdı. Dikkat: beş kabul edilen kenarın dördünde `A` ya da `D` köküdür; `D-E` ve `E-F` önce `D` kümesini oluşturur, `C-D` sonra iki kümeyi birleştirir.

**Bunu AI'sız yazabilir misin?** Union-Find sınıfını ve Kruskal'ı, bir kenar listesinden toplam maliyeti ve seçilen kenarları döndürecek şekilde yazabilir misin? Eşit ağırlıkta iki kenar olduğunda hangisinin seçileceğini hangi sıralama kuralı belirler?

### Örnek 4 (★★★): Döviz arbitrajı: log dönüşümü ve negatif döngü

**Problem:** Üç para birimi (USD, EUR, GBP) arasında doğrudan döviz kurları var (örnek sayılar, gerçek piyasa kuru değildir). Bir para birimini diğerine çevirip başka birine çevirerek ve sonunda başlangıç para birimine dönerek kâr elde edilebilir mi? Varsa bu döngüyü bulun.

**Adım 1 — Anla.** Girdi kur tablosu. Çıktı, kârlı bir döngü varsa onun para birimlerinin sırası ve kur çarpımı. Kârlı döngü, kurların çarpımının `1`'den büyük olduğu bir döngüdür.

**Adım 2 — Örnekle.** `USD -> EUR` (0,90), `EUR -> GBP` (0,90), `GBP -> USD` (1,50) kurlarıyla `1 USD` önce `0,90 EUR`, sonra `0,81 GBP`, sonra `1,215 USD` eder. Çarpım `1,215 > 1`: kârlı bir döngü var. Kurların birinde `1,10` kullanırsak çarpım `0,891 < 1` olur ve döngü kârlı değildir.

**Adım 3 — Kaba çöz.** Tüm döngüleri (basit yolları) dene ve her birinin kur çarpımını hesapla. Üç para birimi için az sayıda döngü vardır; ama `n` para birimi için basit döngü sayısı üstel büyür.

**Adım 4 — Örüntü.** Çarpımı toplama çevirmek için logaritma alırız. `w = -ln(kur)` tanımlarsak, bir döngünün kur çarpımı `1`'den büyüktür ancak ve ancak `ln` toplamı pozitifse; yani `-ln` toplamı negatifse. Böylece "kârlı döngü"yü "negatif döngü"ye çeviririz. Bu, Bellman-Ford'un (17.7) tam olarak tespit ettiği şeydir.

**Adım 5 — İyileştir.** Tüm düğümler `0`'dan başlıyormuş gibi (sanal bir kaynak gibi) tüm mesafeler sıfır alınır; böylece her düğüm tek bir kaynağa bağlanmış gibi davranır. `n - 1` tur sonrası hâlâ gevşeyen bir kenar varsa, o kenarın hedefinden `n` adım geri giderek döngünün içine düşeriz ve döngüyü ebeveyn zincirinden çıkarırız. Toplam iş `O(n · m)`'dir.

**Adım 6 — Doğrula.** Aşağıdaki iz, programın tur tur yazdırdığı mesafe vektörüdür. Turların değerleri, `-ln` kenar ağırlıklarından elle yeniden hesaplanabilir.

```python
# ornek4_arbitraj.py - Doviz arbitraji: log donusumu + negatif dongu.
# Kur degerleri ornektir; gercek piyasa kuru degildir.
import math

PB = ["USD", "EUR", "GBP"]
EPS = 1e-12


def negatif_dongu(n, kenar, tur_izi=True):
    """kenar: [(u, v, w)]. Tum dugumler 0'dan baslar
    (sanal kaynak gibi).
    Negatif dongu varsa dugumlerini dondurur, yoksa None."""
    dist = [0.0] * n
    ebeveyn = [-1] * n
    for t in range(1, n):                       # n-1 tur
        for u, v, w in kenar:
            if dist[u] + w < dist[v] - EPS:
                dist[v] = dist[u] + w
                ebeveyn[v] = u
        if tur_izi:
            print(f"  tur {t}:", [round(x, 4) for x in dist])
    for u, v, w in kenar:               # n. tur: gevserse dongu var
        if dist[u] + w < dist[v] - EPS:
            x = v
            for _ in range(n):          # n adim geri: dongunun icinde
                x = ebeveyn[x]
            dongu, y = [x], ebeveyn[x]
            while y != x:
                dongu.append(y)
                y = ebeveyn[y]
            dongu.append(x)
            return dongu[::-1]
    return None


```

Ana program iki senaryoyu, arbitrajlı ve arbitrajsız kur tablolarını, sırayla çözer.

```python
def senaryo(ad, kurlar):
    print(f"== {ad} ==")
    kenar = [(u, v, -math.log(r)) for u, v, r in kurlar]
    for (u, v, _), (_, _, r) in zip(kenar, kurlar):
        print(f"  {PB[u]}->{PB[v]} kur {r}  "
              f"-ln(kur) = {-math.log(r):.4f}")
    dongu = negatif_dongu(len(PB), kenar)
    if dongu is None:
        print("  Negatif dongu yok: arbitraj yok.")
        return
    carpim = 1.0
    for a, b in zip(dongu, dongu[1:]):
        carpim *= next(r for u, v, r in kurlar if (u, v) == (a, b))
    print("  Dongu:", " -> ".join(PB[u] for u in dongu))
    print(f"  Dongu boyunca kur carpimi = {carpim:.4f}")


if __name__ == "__main__":
    senaryo("Arbitrajli", [(0, 1, 0.90), (1, 2, 0.90), (2, 0, 1.50)])
    senaryo("Arbitrajsiz", [(0, 1, 0.90), (1, 2, 0.90), (2, 0, 1.10)])
```

```term
$ python ornek4_arbitraj.py
== Arbitrajli ==
  USD->EUR kur 0.9  -ln(kur) = 0.1054
  EUR->GBP kur 0.9  -ln(kur) = 0.1054
  GBP->USD kur 1.5  -ln(kur) = -0.4055
  tur 1: [-0.4055, 0.0, 0.0]
  tur 2: [-0.6002, -0.3001, -0.1947]
  Dongu: EUR -> GBP -> USD -> EUR
  Dongu boyunca kur carpimi = 1.2150
== Arbitrajsiz ==
  USD->EUR kur 0.9  -ln(kur) = 0.1054
  EUR->GBP kur 0.9  -ln(kur) = 0.1054
  GBP->USD kur 1.1  -ln(kur) = -0.0953
  tur 1: [-0.0953, 0.0, 0.0]
  tur 2: [-0.0953, 0.0, 0.0]
  Negatif dongu yok: arbitraj yok.
```

| Tur | USD | EUR | GBP |
|---|---|---|---|
| Başlangıç | 0 | 0 | 0 |
| 1 | -0,4055 | 0,0000 | 0,0000 |
| 2 | -0,6002 | -0,3001 | -0,1947 |
| 3 (kontrol) | gevşeme var → negatif döngü | | |

Birinci turda yalnızca `GBP -> USD` kenarı bir değişiklik yaratır (`-0,4055`). İkinci turda bu değişiklik zincirleme yayılır: `USD -> EUR`, `EUR -> GBP` ve `GBP -> USD` kenarları sırayla, her biri öncekinin sonucunu kullanarak mesafeleri düşürür. Üçüncü tur sınavında `GBP -> USD` kenarı hâlâ gevşetilebilir ve bu bir negatif döngü demektir. Program döngüyü `EUR -> GBP -> USD -> EUR` olarak bulur; bu döngünün kur çarpımı `0,9 · 0,9 · 1,5 = 1,215`'tir ve çıktı bunu doğrular.

**Bunu AI'sız yazabilir misin?** Kur tablosunu alıp kârlı bir döngüyü bulan ve kâr oranını yazdıran bir fonksiyon yazabilir misin? Döngüyü ebeveyn zincirinden çıkarmak neden `n` adım geri gitmeyi gerektirir; bunu bir cümleyle açıklayabilir misin?


## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Graf algoritmalarının asıl eğitimi, grafı kendi elinle kurmak, zaman damgalarını kendi kâğıdında izlemek ve kendi hatanı bulmaktır. Bir aracın yazdığı kod doğru görünse bile, döngü ve bağlantısızlık gibi sınır durumlarını sen test etmedikçe bilmiyorsun.
:::

### Proje 1 (★★): İHA rota planlayıcı

**Amaç:** Bir İHA'nın kalkış ile hedef arasında, engelli ve maliyetli bölgelerden kaçarak en az enerjiyi harcadığı rotayı bulan bir planlayıcı yazmak. Haritayı bir ızgara olarak modelle: engeller geçilemez, boş hücreler `1` ile `5` arasında bir enerji maliyetine sahiptir (rüzgâr, arazi). Aynı haritada Dijkstra ile A* karşılaştırılacaktır.

**Yapılacak / Beklenen davranış:**

1. Haritayı bir metin dosyasından oku: `#` engel, rakamlar maliyet, `S` başlangıç, `H` hedef.
2. Dört yönlü hareketle Dijkstra çalıştır ve en düşük enerjili rotayı, rota üzerindeki hücreleri işaretleyerek yazdır.
3. Aynı haritada A* çalıştır; sezgisel olarak Manhattan mesafesini kullan. İki yöntemin bulduğu enerjinin aynı olduğunu doğrula.
4. Her iki yöntemin genişlettiği düğüm sayısını say ve karşılaştır.
5. Hedefe hiç ulaşılamayan bir harita verildiğinde programın bunu açıkça bildirmesini sağla.

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Bölüm 17.6'daki Dijkstra iskeletini ve 17.9'daki A* iskeletini kendi elinle yeniden yaz. Engel hücrelerini komşuluk üretiminde atla. Sezgiselin kabul edilebilir olması için her adımın maliyetinin en az `1` olduğunu kendine hatırlat. Haritanın kaydını tuttuğun yerde `g` ve `f` değerlerini bir tabloda yazdırarak ilk üç adımı elle kontrol et.

**Başarı kriterleri:**

- 300 rastgele harita (tohum `42`, 20 × 20) üzerinde A* ve Dijkstra'nın bulduğu enerji her haritada eşittir.
- Engelli bir haritada ulaşılamayan hedef için program çıkış kodu `1` ile biter ve bir mesaj yazar.
- Genişletilen düğüm sayısının ortalaması raporlanmış; A*'ın genişlettiği düğüm sayısı Dijkstra'dan küçük ya da eşit çıkmaktadır. Bu ölçümü kendi ölçümünle yap; 17.9'daki yüzde 11'lik sayıyı ezberleme.

### Proje 2 (★★★): Paket bağımlılık çözücü

**Amaç:** Bir paket yöneticisinin temel işini yapan bir çözücü yazmak. Girdi, her paketin bağımlılıklarını listeleyen bir dosyadır. Çıktı, paketlerin kurulabileceği bir sıra ya da bir döngü raporudur. Çözücü, döngü bulduğunda hangi paketlerin birbirine bağlı olduğunu da göstermelidir.

**Yapılacak / Beklenen davranış:**

1. Girdiyi `paket: bağımlılık1, bağımlılık2` biçiminde oku. Bir pakette hiç bağımlılık yoksa satır yalnızca paket adını içerir.
2. Bilinmeyen bir bağımlılık adı varsa (listede tanımlanmamış paket) açık bir hata ver.
3. Kurulum sırasını Kahn yöntemiyle üret. Eşit öncelikli paketler arasında alfabetik sırayı koru; bu sonucu kararlı kılar.
4. Döngü varsa, döngüdeki paketleri DFS ile (geri kenarı kullanarak) bul ve yazdır.
5. Kendi çıktını `graphlib.TopologicalSorter` ile karşılaştır: döngü olup olmadığı ve geçerli sıranın bağımlılıkları bozmadığı her iki yöntemde aynı çıkmalı.

**Önerilen yaklaşım (ipucu):** Kahn'ın derece dizisini ve kuyruğunu 17.3'teki gibi kur; kuyruğu bir `heapq` ile değiştirirsen alfabetik sırayı kolayca elde edersin. Döngü raporu için 17.3'teki DFS yöntemindeki geri kenar bilgisini ve 17.5'teki yığın fikrini kullan. Bağımlılıkların yönünü (bir paket hangi paketi gerektirir, hangi paket bunu gerektirir) çizerek kontrol et; bu yön hatası en sık yapılan hatadır.

**Başarı kriterleri:**

- 200 rastgele bağımlılık grafında (tohum `42`), döngü var/yok kararı `graphlib` ile tamamen aynıdır.
- Döngüsüz her grafta üretilen sıra, her bağımlılık kuralını sağlar (her bağımlılık paketten önce gelir); bu, kendi testinle kontrol edilmiştir.
- Döngü raporunda gösterilen paketler gerçekten bir döngü oluşturur: her ardışık çift bir bağımlılık kenarıdır ve liste başladığı yerde biter.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün; son çare olarak kodla doğrula. Mülakat sorularının bir kısmı ayrıca işaretlidir.

1. ★ Bir DFS'te her düğüm için giriş ve çıkış zamanları tutuluyor. `d[u] < d[v] < f[v] < f[u]` ilişkisi neyi ifade eder? Bu ilişkinin hangi kenar türüne karşılık geldiğini açıkla. (Mülakat)
2. ★ Bir yönsüz grafta DFS yapıp hangi kenarların geri kenar olduğunu nasıl anlarsın? Yönsüz grafta çapraz kenar neden yoktur? Kısa bir gerekçe yaz.
3. ★ Kahn algoritmasında kuyruğu bir yığınla değiştirirsen topolojik sıra hâlâ geçerli olur mu? Bir DAG ile yanıtını doğrula.
4. ★★ Bir yönlü grafın SCC'lerini kendi tanımlarınla, iki kez DFS yaparak (önce bitiş sırası, sonra ters grafta) bulmayı dene. İki yöntemin de aynı SCC'leri verdiğini küçük bir grafta doğrula. (Mülakat)
5. ★★ Dijkstra'da kuyruktan çıkan eski kayıtları atlamak yerine, bir düğümün mesafesi düştüğünde heap'te yerini değiştirmeye çalışsaydın, hangi işlem gerekirdi ve maliyeti ne olurdu? (Mülakat)
6. ★★ 0-1 BFS'te deque'ye neden her zaman "başa" ve "sona" ekleme yapılır? Kuyruktaki mesafelerin en fazla bir fark taşıdığını gösteren bir değişmez (invariant) yaz.
7. ★★ Negatif kenarı olan bir grafta, Dijkstra'nın bir düğümü birden fazla kez işlemesine izin verilirse ne olur? Bu değişikliğin doğruluğunu ve sonsuz döngü riskini kısaca tartış.
8. ★★ Bir `n` düğümlü grafta en uzun basit yolun uzunluğunu bulmak için Bellman-Ford benzeri bir yöntem neden işe yaramaz? Negatif kenar yerine tüm ağırlıkları `-1` yaparsan ne olur? (Mülakat)
9. ★★ Floyd-Warshall'da `dist[i][i]` değerlerinin negatif olup olmadığını kontrol etmek, bir negatif döngünün varlığını nasıl gösterir? Bu kontrolün hangi düğümleri işaretlediğini küçük bir örnekle göster.
10. ★★★ Kruskal'da Union-Find'a yalnızca yol sıkıştırma (rank olmadan) uygularsan amortize karmaşıklık ne olur? Bunu bir zincir oluşturan kenar sırasıyla gözlemle. (Mülakat)
11. ★★★ Bir MST'nin tek olması için gerek ve yeterli koşul nedir? Eşit ağırlıklı kenarların birden fazla MST oluşturduğunu bir örnekle göster ve bu durumu nasıl tespit edeceğini açıkla.
12. ★★★ Bir ızgarada A* için sezgiselin kabul edilebilir ama tutarlı olmadığı bir durum kurabilir misin? Böyle bir durumda kapalı küme ile yazılan kod neden yanlış cevap verebilir? (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: CPython 3.12.10'un standart kütüphanesindeki `Lib/graphlib.py` dosyası. Kaynak `v3.12.10` etiketinden alındı (`https://raw.githubusercontent.com/python/cpython/v3.12.10/Lib/graphlib.py`). Aşağıdaki kesit `TopologicalSorter._find_cycle` yönteminin tamamıdır; dosyadaki satır numaraları 198-233'tür. Yorumlar dahil birebir kopyalanmıştır. Tek değişiklik, 218. satırın (`itstack.append(iter(n2i[node].successors).__next__)`) 70 karakteri aşmaması için iki satıra bölünmesidir; hiçbir token değiştirilmedi.

Bu yöntem döngü bulmak için bir DFS kullanır. ama özyineleme yerine açık bir yığın (`stack`) ve her düğüm için bir yineleyici (`itstack`) tutar. Bu, 17.2'de yaptığımız şeyin Python'daki karşılığıdır. `node2stacki` sözlüğü ise bir düğümün yığında hangi konumda olduğunu tutar; geri kenarı bulmanın anahtarı budur.

```python
    def _find_cycle(self):
        n2i = self._node2info
        stack = []
        itstack = []
        seen = set()
        node2stacki = {}

        for node in n2i:
            if node in seen:
                continue

            while True:
                if node in seen:
                    # If we have seen already the node and is in the
                    # current stack we have found a cycle.
                    if node in node2stacki:
                        return stack[node2stacki[node] :] + [node]
                    # else go on to get next successor
                else:
                    seen.add(node)
                    itstack.append(
                        iter(n2i[node].successors).__next__)
                    node2stacki[node] = len(stack)
                    stack.append(node)

                # Backtrack to the topmost stack entry with
                # at least another successor.
                while stack:
                    try:
                        node = itstack[-1]()
                        break
                    except StopIteration:
                        del node2stacki[stack.pop()]
                        itstack.pop()
                else:
                    break
        return None
```

**Sorular — cevaplamadan geçme:**

1. `node2stacki` sözlüğü neden gereklidir? `seen` kümesi ile `node2stacki` sözlüğü arasındaki fark nedir? Hangisi "gri" durumunu, hangisi "siyah" durumunu temsil eder?
2. `itstack.append(iter(n2i[node].successors).__next__)` satırı neden bir yineleyicinin `__next__` metodunu saklar? Bu yapı, 17.2'deki `sira[u]` dizisinin hangi işi gördüğünü açıklar mı?
3. Yöntem bir döngü bulduğunda `stack[node2stacki[node]:] + [node]` döndürür. Bu ifade döngüyü neden doğru sırada ve başı sonuyla aynı şekilde verir? Küçük bir örnekle göster.
4. `while stack:` döngüsünün `else: break` kısmı ne zaman çalışır? Bu kısım, yönteme hangi durumda "döngü yok" sonucunu verdirir?
5. Bu yöntem yalnızca bir döngü bulur, tüm döngüleri bulmaz. Bu tasarım seçimi, `CycleError` mesajının "nodes are in a cycle" olarak tek bir döngü verdiğiyle nasıl ilişkilidir?
6. (Mülakat) Bu yöntemin en kötü durum karmaşıklığı nedir? Düğüm ve kenar sayısı cinsinden yaz ve bu karmaşıklığın Kahn'ın `O(V + E)`'siyle aynı olup olmadığını tartış.

## Bölüm Özeti

Bu bölümde graf algoritmalarını iki aileye ayırarak öğrendik: yapı ve sıra algoritmaları, ağırlık ve optimizasyon algoritmaları.

- **DFS**, düğümlere giriş ve çıkış zamanı verir; kenarlar ağaç, geri, ileri ve çapraz olarak sınıflanır. Yönlü bir grafta döngü, bir geri kenarla ortaya çıkar.
- **Yinelemeli DFS** için yığında yalnızca düğüm değil, her düğümün sıradaki kenar indeksi de tutulmalıdır; aksi hâlde özyinelemeli sırayı vermez.
- **Topolojik sıralama** iki yöntemle yapılır: Kahn (derece ve kuyruk; döngüde kalan düğümleri fark eder) ve DFS (bitiş sırasının tersi; geri kenarla döngü bildirir). Derleme ve paket kurulumu bu yapıya dayanır.
- **İki renklendirme** BFS ile yapılır; grafın iki parçalı olması için tek uzunluklu döngü olmaması gerekir.
- **Tarjan** tek bir DFS ile güçlü bağlı bileşenleri, köprüleri ve eklem noktalarını bulur. Eklem noktası, Bölüm 11'deki gateway sorusunun cevabıdır.
- **Dijkstra**, negatif olmayan kenarlarda en kısa yolu bir öncelik kuyruğu ile bulur; yol, ebeveyn dizisiyle geri kurulur. Negatif kenarda yanlış sonuç verir.
- **Bellman-Ford** `V - 1` tur ile negatif kenarı kaldırır ve `V`. turda negatif döngüyü bildirir. **DAG'da en kısa yol** topolojik sırayla `O(V + E)`'dir.
- **Floyd-Warshall** tüm çiftleri DP ile `O(V³)` sürede bulur; `k` döngüsü en dışta olmalıdır.
- **A\***, kabul edilebilir bir sezgiselle Dijkstra'nın genişlettiği düğüm sayısını azaltır; sezgisel sıfır alınırsa Dijkstra'ya dönüşür.
- **Kruskal** (Union-Find ile) ve **Prim** (heap ile), kesme özelliğine dayanarak minimum yayılan ağacı bulur. Union-Find, rank ve yol sıkıştırma ile neredeyse sabit amortize süre verir.

**Sonraki bölümde:** Bu bölümde her adımda "en ucuz görünen" kenarı seçen Kruskal ve Prim'i kullandık ve doğruluğunu sezgisel bir kesme argümanıyla açıkladık. Bölüm 18'de (Greedy) bu açgözlü seçimin neden doğru olduğunu genel bir çerçevede kanıtlayacağız, ardından Huffman kodlamasıyla açgözlü stratejinin nerede başarısız olduğunu ve nerede mükemmel çalıştığını göreceğiz.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. DFS'te bir geri kenar bulmak neden yönlü graftaki bir döngünün kanıtıdır? Yönsüz graf için aynı iddia neden geçerli değildir?
2. Kahn'ın algoritması bir döngüyü nasıl fark eder? Döngüdeki düğümlerin derecesi neden sıfıra inmez?
3. Dijkstra'yı negatif kenarlı bir grafta çalıştırırsan hangi varsayım bozulur? Yanlış sonucu veren küçük bir örnek ver.
4. Bellman-Ford'un `V - 1` tur yeterli olmasının nedeni nedir? `V`. turda bir değişiklik olursa ne anlama gelir?
5. Floyd-Warshall'da üç döngünün sırasını değiştirirsen algoritma neden yanlış sonuç verir? Bunu bir örnekle gösterebilir misin?
6. Bir graftaki eklem noktasını bulmak, bir sensör ağının güvenilirliği hakkında ne söyler? Bu soruyu yanıtlamak için hangi graf kavramını ve hangi algoritmayı kullanırsın?
7. Kruskal ile Prim aynı MST'yi bulur mu? Eşit ağırlıklı kenarlar varsa sonuç neden değişebilir?
8. Union-Find'da yol sıkıştırma ve rank birlikte kullanıldığında karmaşıklık neden neredeyse sabittir? Her birinin tek başına yetmediği bir durum tarif edebilir misin?
:::
