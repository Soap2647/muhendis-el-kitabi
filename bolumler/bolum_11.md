%% kisim_no: III
%% kisim_ad: Veri Yapıları
%% bolum_no: 11
%% baslik: Graph

## Giriş: Bağlantıların matematiği

Bölüm 10'da ağacı gördük: düğümler ve kenarlar, ama bir kural vardı. Her düğümün tek bir ebeveyni vardı ve döngü yoktu. Bu kuralı kaldırırsak elimizde **graf (graph)** kalır. Graf, nesneleri ve aralarındaki ilişkileri modelleyen en genel yapıdır. Bir sosyal ağda kişiler düğüm, arkadaşlıklar kenardır. Bir şehirler arası yol ağında kavşaklar düğüm, yollar kenardır. Bir yazılım projesinde modüller düğüm, "şu modül şuna bağlıdır" ilişkisi kenardır.

Savunma sanayiinde graf her yerdedir. Bir İHA'nın rota noktaları, bir sensör ağının bağlantı yapısı, bir haberleşme ağının yönlendirme tabloları birer graftır. Bir savaş yönetimi sisteminde "hangi birimler bu düğümden ulaşılabilir?" ya da "bu bağlantı koparsa ağ ikiye bölünür mü?" gibi sorular doğrudan graf sorularıdır. Mülakatlarda ise graf soruları, özellikle "bu problemi bir grafa çevirebilir misin?" biçiminde, en çok zorlayan sorular arasındadır.

::: not
Bu bölümde graf üzerinde **en kısa yol** algoritmalarını (Dijkstra, Bellman-Ford) ve **minimum yayılan ağaç** (Kruskal, Prim) gibi ağır algoritmaları yapmayacağız. Onlar Bölüm 17'nin konusudur. Burada hedefimiz, grafı doğru temsil etmek, temel gezinmeyi kurmak ve bir problemi grafa çevirme becerisini kazanmaktır.
:::

## 11.1 Graf terminolojisi

Bir **graf** `G = (V, E)` biçiminde yazılır: `V`, düğümlerin (vertex, node) kümesi; `E`, kenarların (edge) kümesidir. Bir kenar iki düğümü birbirine bağlar. Bölüm 10'daki ağaç terminolojisi burada da geçerlidir, ama grafta bazı kavramlar genişler.

Düğümün **derecesi (degree)**, o düğüme bağlı kenar sayısıdır. Şekil 11.1'deki graf üzerinde 3 numaralı düğümün derecesi 3'tür; çünkü 1, 2 ve 4 ile bağlıdır. Yönsüz bir grafta kenarların her iki ucu da derecesine katkı yapar. Bu yüzden tüm derecelerin toplamı, kenar sayısının iki katıdır: `Σ derece(v) = 2|E|`. Buna **el sıkışma lemması (handshaking lemma)** denir: her kenar iki elin sıkışmasına benzer ve iki el de sayılır.

Bir **yol (path)**, kenarlarla birbirine ardışık bağlanmış düğümlerin dizisidir. Yol içinde bir düğüm tekrar edebilir ya da etmeyebilir. Bir **döngü (cycle)** ise başladığı düğüme dönen, en az üç kenarlı kapalı bir yoldur (yönsüz grafta aynı kenarı geri kullanmadan). Şekil 11.1'de `0 - 1 - 3 - 2 - 0` bir döngüdür. Yönsüz bir graf **bağlantılı (connected)** ise her iki düğüm arasında bir yol vardır. Bağlantılı olmayan bir grafın her bağlantılı parçasına **bileşen (component)** denir.

![Şekil 11.1: Graf terminolojisi. Düğüm 3'ün derecesi 3'tür. 0-1-3-2-0 kırmızı renkli bir döngüdür. Düğüm 4, 3 üzerinden grafa bağlıdır; grafın tamamı tek bir bileşendir.](gorseller/b11_terminoloji.png)

Ağaçla grafın ilişkisi tam olarak burada kurulur. **Ağaç**, döngüsüz ve bağlantılı bir yönsüz graftır. `n` düğümlü bir ağaçta tam olarak `n - 1` kenar vardır (Bölüm 10.1). Tersi de doğrudur: bağlantılı bir grafta `n - 1` kenar varsa, bu graf bir ağaçtır. Yani bir graf için şu üç özellikten herhangi ikisi, üçüncüsünü garanti eder: bağlantılılık, döngüsüzlük, `n - 1` kenar. Bu gözlemi Çözümlü Örnek 3'te kullanacağız.

**Yönlü döngüsüz graf (DAG, Directed Acyclic Graph)**, kenarları yönlü ve hiçbir yönlü döngüsü olmayan graftır. Bağımlılık ilişkileri, görev sıraları ve git commit geçmişi tipik DAG'lardır. Bir ağaç, köküne doğru ya da kökünden dışarı doğru yönlendirildiğinde bir DAG'dır; yani her ağaç bir DAG'dır ama her DAG bir ağaç değildir.

Son olarak yoğunluk kavramı: kenar sayısı düğüm sayısına göre az ise graf **seyrek (sparse)**, çok ise **yoğun (dense)** denir. Basit (çoklu kenar ve döngü içermeyen) yönsüz bir grafta en fazla `V(V - 1) / 2` kenar olabilir, çünkü her düğüm diğer `V - 1` düğümün her biriyle en fazla bir kez bağlanabilir. Yönlü grafta bu sayı `V(V - 1)`'dir, çünkü her çift için iki yön ayrı kenar sayılır. Seyrek graflarda `|E|`, `V` ile orantılı kalır; yoğun graflarda ise `|E|` yaklaşık `V²` olur. Bu ayrım, hangi temsilin seçileceğini belirler (11.5).

## 11.2 Yönlü, yönsüz, ağırlıklı graflar

Graf türleri iki bağımsız soruya göre ayrılır. Birincisi: kenarların bir yönü var mı? İkincisi: kenarların bir ağırlığı (maliyet, mesafe, süre) var mı?

**Yönsüz (undirected)** graf kenarları çift yönlüdür: `A - B` kenarı, A'dan B'ye de B'den A'ya da gidilebileceğini söyler. Sosyal ağlardaki arkadaşlık tipik bir örnektir: sen onun arkadaşıysan o da senin arkadaşındır. **Yönlü (directed)** graf kenarları tek yönlüdür: `A → B` kenarı yalnızca A'dan B'ye gidilebileceğini söyler. Tek yön sokaklar, takip ilişkileri (sosyal medyada "takip ediyorum" ama karşılığı olmayan durum) ve bağımlılıklar yönlüdür.

**Ağırlıklı (weighted)** graf kenarlara bir sayı atar. Bu sayı mesafe, süre ya da maliyet olabilir. Ağırlığı olmayan graf, her kenarın ağırlığını 1 kabul eden bir ağırlıklı graftır. Bölüm 8'de BFS'in "en kısa yol" bulmasını gördük; bu garanti yalnızca ağırlıksız grafta geçerlidir. Ağırlıklı grafta en kısa yol için Bölüm 17'deki Dijkstra gerekir.

![Şekil 11.2: Solda yönlü ve ağırlıklı graf: tek yön kenarları oklarla gösterilir. Sağda aynı düğümler yönsüz: her kenar iki yönde de geçerlidir. Kırmızı kenar, A'dan C'ye tek yönlü gidişi vurgular.](gorseller/b11_yonlu_agirlikli.png)

Şekil 11.2'deki yönlü grafta A'dan D'ye iki yolla gidilebilir: `A → B → D` (toplam ağırlık 4 + 5 = 9) ya da `A → C → D` (2 + 8 = 10). Sağdaki yönsüz grafta ise yeni yollar açılır: `D → B → A`, `D → C → A` gibi. Yani yönü kaldırmak, bir graftaki ulaşılabilirlik kümesini değiştirir. Bu yüzden yön bilgisini yanlış modellemek, yanlış cevaba götürür.

Kod tarafında ağırlığı nasıl saklayacağımız temsil seçimine bağlıdır. Bunu 11.3 ve 11.4'te göreceğiz. Burada bir uyarı yapalım: ağırlık olarak 0 kullanılabiliyorsa, "kenar yok" işaretini 0 ile yapamazsın. Bu durumda `-1` ya da çok büyük bir sayı (sonsuz) gibi ayrı bir işaret kullanılmalıdır.

## 11.3 Komşuluk matrisi

Bir grafı bilgisayara koymanın en doğrudan yolu **komşuluk matrisi (adjacency matrix)** kullanmaktır. `V` düğümlü bir graf için `V × V` boyutunda bir matris tutulur. `m[u][v]`, u'dan v'ye bir kenar varsa 1 (ağırlıklı ise ağırlık), yoksa 0 olur. Yönsüz graflarda matris simetriktir: `m[u][v] == m[v][u]`.

Bu temsilin en büyük avantajı kenar sorgusunun sabit zamanda olmasıdır. "u ile v bağlı mı?" sorusu tek bir dizi erişimi ile cevaplanır. Bunun bedeli bellektir: düğüm sayısı `V` ise matris `V²` hücre tutar, graf çok seyrek olsa bile. 

Aşağıdaki C programı, Şekil 11.3'teki 7 düğümlü grafı matrisle temsil eder. Dikkat edilmesi gereken iki şey var. Birincisi, `kenar_ekle` yönsüz graf için iki hücreyi de yazar. İkincisi, matris `static` olduğu için tüm hücreler otomatik olarak 0 ile başlar; yerel bir dizi olsaydı bu garanti olmazdı.

```c
#include <stddef.h>
#include <stdio.h>

#define N 7

/* Komsuluk matrisi: m[u][v] == 1 ise u ile v bagli. */
static int m[N][N];

void kenar_ekle(int u, int v) {
    m[u][v] = 1;
    m[v][u] = 1;      /* yonsuz: iki yonu de yaz */
}
```

Fonksiyonların ikinci kısmı sorgu ve derece hesabını yapar. Derece, satırdaki 1'lerin toplamıdır; bu yüzden O(V) zaman alır.

```c
int kenar_var_mi(int u, int v) {
    return m[u][v];          /* O(1): dogrudan bak */
}

int derece(int u) {
    int d = 0;
    for (int v = 0; v < N; v++)
        d += m[u][v];        /* satirdaki 1'leri say: O(V) */
    return d;
}
```

Ana program kenarları ekler, her düğümün derecesini yazdırır ve el sıkışma lemmasını kontrol eder:

```c
int main(void) {
    int kenarlar[][2] = {{0,1},{0,2},{1,3},{2,3},{3,4},{5,6}};
    size_t e = sizeof kenarlar / sizeof kenarlar[0];
    for (size_t i = 0; i < e; i++)
        kenar_ekle(kenarlar[i][0], kenarlar[i][1]);
    int toplam = 0;
    for (int u = 0; u < N; u++) {
        printf("derece(%d) = %d\n", u, derece(u));
        toplam += derece(u);
    }
    printf("toplam = %d, 2 * |E| = %zu\n", toplam, 2 * e);
    printf("1-3 var mi? %d, 0-5 var mi? %d\n",
           kenar_var_mi(1, 3), kenar_var_mi(0, 5));
    return 0;
}
```

Derlemeyi ve çalıştırmayı şöyle yaparsın. Bu kod WSL2 içindeki gcc ile sanitizer'lar açık olarak da derlenip çalıştırılmıştır; Windows'ta MinGW ile de aynı çıktıyı almalısın:

```term
$ gcc -std=c11 -Wall -Wextra matris.c -o matris
$ ./matris
derece(0) = 2
derece(1) = 2
derece(2) = 2
derece(3) = 3
derece(4) = 1
derece(5) = 1
derece(6) = 1
toplam = 12, 2 * |E| = 12
1-3 var mi? 1, 0-5 var mi? 0
```

Toplam 12 çıktı ve `2 * |E| = 12` ile eşleşiyor; el sıkışma lemmasının bir sayısal kontrolüdür. Matrisin bellek maliyeti `V²` olduğu için, 1 milyon düğümlü bir graf için `int` matrisi yaklaşık 4 TB tutar. Bu, komşuluk matrisinin büyük seyrek graflar için neden uygun olmadığını gösterir.

![Şekil 11.3: Komşuluk matrisi (solda) ve aynı graf (sağda). Her 1 değeri bir kenarı temsil eder; matris simetriktir ve köşegen sıfırdır.](gorseller/b11_matris.png)

## 11.4 Komşuluk listesi ve kenar listesi

Seyrek graflarda çoğu matris hücresi 0'dır ve bu büyük bir israftır. **Komşuluk listesi (adjacency list)**, her düğüm için yalnızca gerçek komşularını tutar. Bellek kullanımı `O(V + E)`'dir. Şekil 11.4'te her düğümün yanında kendi bağlı listesi görülür.

C'de komşuluk listesi, her düğüm için bir bağlı liste başı (`Kenar *`) dizisidir. Bölüm 7'deki bağlı listeyi ve Bölüm 2'deki işaretçileri burada doğrudan kullanıyoruz. Aşağıdaki bloklar graf yapısını ve kurucu fonksiyonunu tanımlar:

```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct Kenar {
    int hedef;
    struct Kenar *sonraki;
} Kenar;

typedef struct {
    int n;               /* dugum sayisi: 0 .. n-1 */
    Kenar **bas;         /* bas[u]: u'nun komsu listesinin basi */
} Graf;

Graf *graf_yap(int n) {
    Graf *g = malloc(sizeof *g);
    if (g == NULL) return NULL;
    g->n = n;
    g->bas = calloc((size_t)n, sizeof *g->bas);  /* hepsi NULL */
    if (g->bas == NULL) {
        free(g);
        return NULL;
    }
    return g;
}
```

`calloc` bellekteki her baytı sıfırladığı için `bas` dizisinin her elemanı `NULL` ile başlar; `malloc` bunu garanti etmez. Bu, Bölüm 10'daki düğüm kurucusunda `NULL` atamamızın aynı nedenidir.

Kenar eklemesi, yeni düğümü listenin başına koyar. Başa eklemek O(1)'dir, çünkü listenin sonunu aramak gerekmez. Yönsüz kenar için iki yönlü ekleme yapılır:

```c
static int yonlu_ekle(Graf *g, int u, int v) {
    Kenar *k = malloc(sizeof *k);
    if (k == NULL) return 0;
    k->hedef = v;
    k->sonraki = g->bas[u];   /* basa ekle: O(1) */
    g->bas[u] = k;
    return 1;
}

int kenar_ekle(Graf *g, int u, int v) {
    if (!yonlu_ekle(g, u, v)) return 0;
    return yonlu_ekle(g, v, u);   /* yonsuz: ters yon de */
}
```

Bu yazımda bir hata payı var: ilk yön eklendikten sonra ikinci `malloc` başarısız olursa grafta yarım kenar kalır. Üretim kodunda bunu geri alan bir yol gerekir; burada kısalık için bunu not olarak bırakıyoruz.

Graf yapısını temizlemek için her düğümün listesini tek tek serbest bırakırız. Burada da bir sıra önemlidir: sonraki işaretçisini `free` çağrılmadan önce kaydetmeliyiz, yoksa serbest bırakılmış belleğe erişiriz (UB).

```c
void graf_serbest(Graf *g) {
    if (g == NULL) return;
    for (int u = 0; u < g->n; u++) {
        Kenar *k = g->bas[u];
        while (k != NULL) {
            Kenar *sonraki = k->sonraki;  /* once ilerini kaydet */
            free(k);
            k = sonraki;
        }
    }
    free(g->bas);
    free(g);
}

void liste_yaz(const Graf *g) {
    for (int u = 0; u < g->n; u++) {
        printf("%d:", u);
        for (const Kenar *k = g->bas[u]; k != NULL; k = k->sonraki)
            printf(" %d", k->hedef);
        printf("\n");
    }
}
```

Bu programın geri kalanını 11.6'da, DFS ve BFS ile birlikte göreceksin. Derlenebilir bütün program 11.6'daki `main` ile tamamlanır.

Komşuluk listesinin bir yan etkisi vardır: düğümün komşuları ters eklenme sırasında görünür. Bu yüzden 0 numaralı düğümün listesi `2 1` sırasındadır; 1 önce eklenmiş ama başa eklendiği için sonra gelir. Bu bir hata değildir, ama gezinme sıranı etkiler (11.6'da bunun sonucunu göreceksin).

![Şekil 11.4: Komşuluk listesi. Her düğüm kendi bağlı listesini taşır; liste başa ekleme sırasıyla dizilmiştir.](gorseller/b11_liste.png)

Python'da aynı fikir bir sözlük (dict) ile doğal olarak ifade edilir. Aşağıdaki program, komşuları küme (set) olarak tutan bir liste yapısını kurar; set sayesinde "kenar var mı?" sorusu ortalama O(1) olur.

```python
graf = {
    0: {1, 2},
    1: {0, 3},
    2: {0, 3},
    3: {1, 2, 4},
    4: {3},
}
print(graf[3])           # {1, 2, 4}
print(len(graf[3]))      # 3: derece
print(4 in graf[3])      # True: kenar var mi?
print(sorted(graf[0]))   # [1, 2]
```

Terminal çıktısı:

```term
$ python graf_sozluk.py
{1, 2, 4}
3
True
[1, 2]
```

Python sürümü, C'deki bağlı liste kadar bellek verimli değildir (her küme ve her sözlük girdisi ek yük getirir), ama üretkenliği çok yüksektir. Üretim işlerinde Python'da sık sık bu sözlük yapısı kullanılır; performans kritikse C ya da NumPy tabanlı temsiller tercih edilir.

**Kenar listesi (edge list)**, grafı yalnızca `(u, v)` çiftlerinin bir listesi olarak tutar. Bellek `O(E)`'dir, dosyaya yazmak ve okumak kolaydır. Ama belirli bir düğümün komşularını bulmak için tüm listeyi taramak gerekir. Bu temsil, grafı diske kaydetmek ya da bir algoritmaya girdi olarak vermek için uygundur.

**CSR (Compressed Sparse Row)** büyük seyrek graflar için kullanılan sıkıştırılmış bir biçimdir. Üç dizi tutulur: düğüm `u`'nun komşuları `hedefler` dizisinin `satir_basi[u]` ile `satir_basi[u+1]` arasındadır. Bu, komşuları bitişik bellek bloklarında tutar ve önbellek dostudur. SciPy kütüphanesindeki `csr` matrisleri tam olarak bu düzendir. Burada yalnızca fikrini bilmen yeterli.

## 11.5 Temsil maliyetleri: karşılaştırma

Hangi temsilin seçileceğini ezberlemek yerine maliyetleri karşılaştırmak daha kalıcıdır. `V` düğüm, `E` kenar olsun. Aşağıdaki tablo yönsüz, basit bir graf için yaklaşık maliyetleri verir:

| İşlem | Komşuluk matrisi | Komşuluk listesi | Kenar listesi |
|---|---|---|---|
| Bellek | V² | V + E | E |
| u-v kenarı var mı? | O(1) | O(derece(u)) | O(E) |
| u'nun komşularını gez | O(V) | O(derece(u)) | O(E) |
| Kenar ekle | O(1) | O(1) | O(1) |
| Kenar sil | O(1) | O(derece(u)) | O(E) |
| Tüm kenarları gez | O(V²) | O(V + E) | O(E) |

Tablodan çıkan sonuç açıktır. Seyrek graflarda (`E ≈ V`) komşuluk listesi bellekte ve gezinmede matristen kat kat üstündür. Yoğun graflarda (`E ≈ V²`) matrisin sabit zamanlı kenar sorgusu avantaj sağlar ve bellek farkı küçülür. Bir mühendislik kararının bu iki yönü tartması gerekir.

Ağırlıklı graflarda matris hücresi ağırlığı tutar, listede ise her `Kenar` düğümüne bir `agirlik` alanı eklenir. Matriste "kenar yok" ile "ağırlığı 0 olan kenar" ayrımını yapmak için 11.2'deki uyarıyı hatırla.

Yönlü graflarda komşuluk listesi yalnızca çıkan kenarları tutar. Gelen kenarları da görmek istiyorsan (örneğin bir düğümün kimlere bağımlı olduğunu bulmak için) ters bir liste daha tutmak gerekir. Matriste ise yön zaten satır ve sütunla belirlenir: satır çıkış, sütun giriştir.

## 11.6 Graf üzerinde gezinme: DFS ve BFS

Bölüm 8'de BFS'i kuyrukla, Bölüm 10'da ağaç gezinmelerini özyinelemeyle gördük. Graf üzerinde tek ek sorun döngülerdir: bir düğüme birden fazla yoldan gelinebilir ve ziyaret etmediğimiz bir düğüme dönebiliriz. Çözüm **ziyaret edilmiş (visited) dizisi** tutmaktır. Her düğüm en fazla bir kez işlenir; bu, döngüde sonsuz döngüye girmemeyi garanti eder.

**DFS (derinlemesine arama)**, bir düğümden başlayıp bir komşusuna gider, oradan da derine iner; geri dönüş gerektiğinde bir önceki düğüme döner. Özyineleme kullanmak doğaldır, çünkü çağrı yığını zaten bir geri dönüş yığınıdır. **BFS (genişlemesine arama)**, başlangıca bir kenar uzaklıktaki tüm düğümleri, sonra iki kenar uzaklıktakileri ziyaret eder. Kuyruk kullanılır ve BFS, ağırlıksız graflarda en kısa yolu verir.

Aşağıdaki program, 11.4'teki `Graf` yapısını ve yazdırma fonksiyonunu kullanır. DFS ve BFS, düğüm 0'dan başlar. Her iki gezinmede de bir düğümü ziyaret işaretlemeden önce kuyruğa ya da yığına koymamız gerekmez; BFS'te kuyruğa girerken işaretlemek, aynı düğümün kuyruğa iki kez girmesini engeller.

```c
void dfs(const Graf *g, int u, int *ziyaret) {
    ziyaret[u] = 1;
    printf("%d ", u);
    for (const Kenar *k = g->bas[u]; k != NULL; k = k->sonraki)
        if (!ziyaret[k->hedef])
            dfs(g, k->hedef, ziyaret);
}
```

BFS ise kuyruğu bir dizi üzerinde iki indeksle (`bas` ve `son`) gerçekler. Bölüm 8'deki kuyruk fikri aynıdır; burada düz bir dizi yeterlidir, çünkü her düğüm en fazla bir kez kuyruğa girer ve kuyruk dizisi `n` elemandan büyük olmaz.

```c
void bfs(const Graf *g, int s) {
    int *ziyaret = calloc((size_t)g->n, sizeof *ziyaret);
    int *kuyruk = malloc((size_t)g->n * sizeof *kuyruk);
    if (ziyaret == NULL || kuyruk == NULL) {
        free(ziyaret);
        free(kuyruk);
        return;
    }
    size_t bas = 0, son = 0;
    kuyruk[son++] = s;
    ziyaret[s] = 1;
    while (bas < son) {
        int u = kuyruk[bas++];
        printf("%d ", u);
        for (const Kenar *k = g->bas[u]; k != NULL; k = k->sonraki) {
            if (!ziyaret[k->hedef]) {
                ziyaret[k->hedef] = 1;   /* isaretle */
                kuyruk[son++] = k->hedef;
            }
        }
    }
    free(ziyaret);
    free(kuyruk);
}
```

Bu iki fonksiyonu 11.4'teki `Graf` ve `kenar_ekle` ile birleştirip şu ana programı elde ederiz. Program, 7 düğümlü grafı kurar, listeyi yazar ve iki gezinmeyi çalıştırır:

```c
int main(void) {
    Graf *g = graf_yap(7);
    if (g == NULL) return 1;
    int kenarlar[][2] = {{0,1},{0,2},{1,3},{2,3},{3,4},{5,6}};
    for (size_t i = 0; i < 6; i++)
        kenar_ekle(g, kenarlar[i][0], kenarlar[i][1]);
    liste_yaz(g);
    int *z = calloc((size_t)g->n, sizeof *z);
    if (z == NULL) {
        graf_serbest(g);
        return 1;
    }
    printf("DFS: ");
    dfs(g, 0, z);
    printf("\nBFS: ");
    bfs(g, 0);
    printf("\n");
    free(z);
    graf_serbest(g);
    return 0;
}
```

Program, 11.4'teki `graf_yap`, `yonlu_ekle`, `kenar_ekle`, `graf_serbest` ve `liste_yaz` fonksiyonlarıyla birlikte derlenir. Aşağıdaki terminal çıktısı, bu dosyanın tamamıyla elde edilmiştir:

```term
$ gcc -std=c11 -Wall -Wextra graf.c -o graf
$ ./graf
0: 2 1
1: 3 0
2: 3 0
3: 4 2 1
4: 3
5: 6
6: 5
DFS: 0 2 3 4 1 
BFS: 0 2 1 3 4 
```

Çıktıyı elle doğrulayalım. Listede 0'ın komşuları `2, 1` sırasındadır. DFS, önce 2'ye iner; 2'nin listesi `3, 0`'dır, 3'e iner; 3'ün listesi `4, 2, 1`'dir, 4'e iner ve geri döner; sonra 1'e gider. Böylece DFS sırası `0 2 3 4 1`'dir. BFS ise 0'ın komşularını (2 ve 1) kuyruğa koyar, sonra 2'nin komşusu 3'ü ekler; kuyruk 1, 3 sırasıyla çıkar ve 3'ün komşusu 4 en sonda gelir. Sıra `0 2 1 3 4`'tür.

![Şekil 11.5: Aynı graf üzerinde DFS (solda) ve BFS (sağda) gezinmeleri. Kırmızı kenarlar gezinmenin ağacını gösterir; #k ziyaret sırasını belirtir.](gorseller/b11_gezinme.png)

Şekil 11.5, bu iki gezinmenin ağaçlarını gösterir. DFS ağacı derine uzanan bir yapıdır; BFS ağacı ise daha yayvandır. İkisi de 4 kenar kullanır: bir gezinme ağacı, ulaştığı `k` düğümü her zaman `k - 1` kenarla bağlar ve burada ulaşılan düğüm sayısı 5'tir. Grafın 7 düğümü var, ama 5 ve 6 numaralı düğümler başka bir bileşende olduğu için 0'dan başlayan gezinme onlara ulaşamaz; bunu 11.7'de ele alıyoruz.

Gezinmenin maliyeti, komşuluk listesi ile `O(V + E)`'dir: her düğüm bir kez ziyaret edilir ve her kenar en fazla iki kez (iki yönden) incelenir. Komşuluk matrisi ile aynı gezinme `O(V²)`'ye çıkar, çünkü her düğüm için tüm satır taranır.

DFS'in özyinelemeli sürümü derin graflarda yığın taşmasına yol açabilir. Bölüm 10.5'te aynı sorunu bir ağaçta gördük: 10⁶ düğümlü bir zincir Windows'un varsayılan 1 MB yığınını aşar. Büyük graflarda DFS için açık bir yığınla yinelemeli sürüm tercih edilir; bu, Bölüm 8'deki yığını kullanmanın başka bir uygulamasıdır.

## 11.7 Bağlantılı bileşenler

Bir graftaki **bağlantılı bileşen** sayısı, birbirinden ulaşılamayan parçaların sayısıdır. Bunu bulmak için her düğümden bir gezinme başlatırız; gezinme ziyaret etmediğimiz bir düğüme ulaşmışsa yeni bir bileşen bulmuş oluruz. Her gezinmede bir bileşenin tüm düğümleri işaretlenir, bu yüzden toplam iş `O(V + E)`'dir.

Şekil 11.6 bunu G1 grafında gösterir: düğümler 0-4 bir bileşen, 5-6 diğer bileşendir.

![Şekil 11.6: G1 iki bağlantılı bileşene ayrılır. Düğümler 0-4 tek bir bileşen; 5 ve 6 ayrı bir bileşen oluşturur.](gorseller/b11_bilesen.png)

Bileşen sayımını bir mühendislik sorusu olarak düşünelim. Bir sensör ağında her sensör bir düğüm, aralarındaki haberleşme bağı bir kenardır. Ağ tek bileşense her sensör merkeze ulaşabilir. Birden fazla bileşen varsa, ağ bölünmüştür ve bazı sensörlerin verisi merkeze ulaşmaz. Bu tür bir soruyu bileşen sayımı ile hızlıca yanıtlarsın. Bu konu, 11.8'deki sensör ağı örneğinde tekrar karşımıza çıkacak.

## 11.8 Ne zaman graf düşünürüm?

Graf, en genel modelleme aracıdır; bu yüzden her şeyi grafa çevirmek cazip gelir. Ama her problem grafa dönüşmez ya da grafa dönüşmek anlamlı değildir. İyi bir sezgi için şu soruları sor:

1. **Nesneler arasında ilişki var mı?** Problem "kim kime bağlı", "neye bağımlı", "nereye ulaşılır" diye soruyorsa büyük ihtimalle graftır.
2. **Adımlar ve durumlar var mı?** Bir bulmacada her konfigürasyon bir durum, her hamle bir geçiştir. Bu bir **durum uzayı (state space)** grafıdır; en kısa çözüm, bir BFS ile bulunabilir (Çözümlü Örnek 4 buna bir örnek).
3. **Sıra kısıtı var mı?** "A, B'den önce yapılmalı" gibi kısıtlar yönlü kenarlar ve DAG üretir.
4. **Yol, mesafe, maliyet soruluyor mu?** Kenarlara ağırlık eklenir; en kısa yol problemleri için Bölüm 17'ye geçilir.
5. **Yalnızca bir listede arama mı var?** O zaman graf gerekmez. Bir dizide değer aramak için Bölüm 14'teki arama yeterlidir; grafa çevirmek gereksiz karmaşıklık getirir.

Bu sorular cevaplandığında, asıl iş modellemeye geçer: düğüm ne, kenar ne, yönlü mü, ağırlıklı mı? Modelleme hatası, algoritma hatasından daha pahalıdır. Yanlış tanımlanmış bir kenar, en iyi algoritmayı bile yanlış cevaba götürür.

## 11.9 Modelleme örnekleri

Aşağıdaki tablo, sık karşılaşılan problemlerin graf karşılığını özetler. Her satırda düğüm, kenar ve yön/ağırlık kararlarını görebilirsin:

| Problem | Düğüm | Kenar | Yönlü? | Ağırlıklı? |
|---|---|---|---|---|
| Sosyal ağ (arkadaşlık) | Kişi | Arkadaşlık | Hayır | Hayır |
| Takip ilişkisi | Kullanıcı | Takip | Evet | Hayır |
| Şehirler arası yol ağı | Kavşak/şehir | Yol | Tek yön sokakta evet | Mesafe ya da süre |
| Derleme bağımlılığı | Modül/dosya | "şuna bağlı" | Evet | Hayır |
| Bulmaca çözümü | Konfigürasyon | Tek hamle | Genelde evet | Hayır |
| Sensör/haberleşme ağı | Cihaz | Bağlantı | Genelde hayır | Gecikme ya da bant |
| İHA rota noktaları | Rota noktası | Uçuşa uygun segment | Genelde hayır | Mesafe, enerji |

İlk örnekte kişi düğümleri ve arkadaşlık kenarları yönsüzdür; "A, B'nin arkadaşı ise B de A'nın arkadaşıdır" kuralı bunu sağlar. Takip ilişkisi ise yönlüdür, çünkü A'nın B'yi takip etmesi B'nin A'yı takip ettiği anlamına gelmez.

Derleme bağımlılığı çok öğreticidir. Şekil 11.7 (a) panelinde bir uygulama iki nesne dosyasına, bunlar da kaynak ve başlık dosyalarına bağlıdır. Okun yönü "bağlı olduğu şeye" doğrudur ve bu yönlü bir DAG oluşturur. Bir döngü olursa (A, B'ye; B de A'ya bağlıysa) derleme sırası tanımsız olur. Derleme sırasını bulmak, Bölüm 17'de göreceğin topolojik sıralamanın işidir.

Bulmacalar (b paneli) durum uzayı mantığını gösterir. Her durum bir düğümdür, her hamle bir yönlü kenardır. Bu küçük örnekte üç durum ve üç geçiş vardır; ama gerçek bulmacalarda durum sayısı hızla büyür. Bu grafı gezmek için BFS kullanmak, en az hamle sayısını verir.

Gateway arızası (c paneli) bağlantılılık sorusunun pratik bir örneğidir. Merkezi düğüm G çalışmazsa, s1 ve s2 tek başına kalır, s3, s4, s5 ise birbirine bağlı olarak ayrı bir bileşen oluşturur. Bu analizi bileşen sayımı ile yapabilirsin; grafı, arızayı simüle ederek değiştirip yeniden saymak yeterlidir.

![Şekil 11.7: Üç graf modeli. (a) Derleme bağımlılığı, yönlü bir DAG'dır. (b) Durum uzayında her hamle bir yönlü kenardır. (c) Merkezi bir gateway'in düşmesi ağı üç parçaya böler.](gorseller/b11_modelleme.png)

Şimdi bu modellemeyi bir problem üzerinde pratik yapalım: bir bilgisayar ağında iki cihazın birbirine kaç atlamada (hop) ulaşacağını bulmak. Bu, ağırlıksız bir graf üzerinde BFS'in en doğal kullanımıdır. Atlama sayısı, kenar sayısıdır; BFS ilk ulaştığı an en kısa atlama sayısını verir.

## 11.10 Gerçek dünyada graf

**Linux ve Make.** Bir `Makefile`, hedef dosyalar ile bağımlılıkları tanımlar: `app: main.o util.o` gibi. Bu tanımlar bir yönlü graf oluşturur ve `make` aracı, bir hedefi üretmek için gereken dosyaları bu graf üzerinde bulur. Bir bağımlılık döngüsü oluşursa GNU `make` döngüyü fark eder, ama durmaz: `Circular b <- a dependency dropped.` uyarısını yazar, döngüyü kapatan kenarı yok sayar ve çıkış kodu 0 ile devam eder (GNU Make 4.3'te denendi). Yani döngü tespiti yapılır, ama sonuç bir hata değil sessiz bir varsayımdır; derleme yanlış sırayla tamamlanıp "başarılı" görünebilir. Uyarıları okumak bu yüzden önemlidir.

**Git commit geçmişi.** Her commit, bir ya da daha fazla ebeveyn commit'e işaret eder. Bir birleştirme (merge) commit'i iki ebeveyne sahiptir. Bu yapı bir DAG'dır, çünkü bir commit kendi atasının atası olamaz. Şekil 11.8'de bunu küçük bir örnekle görebilirsin. Gerçek bir depoda kendi geçmişini `git log --graph --oneline` komutuyla çizdirebilirsin.

![Şekil 11.8: Küçük bir git geçmişi. Oklar çocuk commit'ten ebeveyne gösterir. M commit'i iki ebeveynlidir: main dalındaki C ve feature dalındaki D.](gorseller/b11_git_dag.png)

**İnternet yönlendirme.** Yönlendiriciler (router) düğümdür, aralarındaki fiziksel ya da mantıksal bağlantılar kenardır. OSPF gibi iç ağ yönlendirme protokolleri, kenarlara maliyet atar ve her yönlendiricinin en kısa yolu hesaplamasını sağlar. Bu hesap, Bölüm 17'deki Dijkstra algoritmasıyla yapılır. BGP ise farklı ağlar (otonom sistemler) arasında bir yönlü politika grafı üzerinde çalışır.

Bu üç örnek, grafın yazılımın her katmanında nasıl bulunduğunu gösterir: derleme sistemi, sürüm kontrolü ve ağ altyapısı. Hepsinin ortak noktası, ilişkilerin açıkça bir yapıda tutulması ve gezinme ile sorgulanabilmesidir.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz; doğrulama adımında elle iz tablosu kullanacağız.

### Örnek 1 (★): Komşuluk listesinden derece

**Problem:** Kenarları `(u, v)` çiftlerinden oluşan yönsüz bir graf verilsin. Her düğümün derecesini ve tüm derecelerin toplamını bul. Toplam, kenar sayısının iki katına eşit olmalı.

**Adım 1 — Anla.** Girdi düğüm sayısı `n` ve kenar listesi, çıktı her düğüm için derece. Yönsüz olduğu için her kenar iki düğümün de derecesini artırır. Kenar durumları: düğümün hiç kenarı yoksa derecesi 0'dır; aynı kenar iki kez verilirse ne olacağını sormak gerekir (bu örnekte tekrar yok).

**Adım 2 — Örnekle.** `n = 4` ve kenarlar `(0, 1), (1, 2)` olsun. Düğüm 0'ın derecesi 1 (yalnızca 1 ile bağlı), düğüm 1'in derecesi 2 (0 ve 2 ile bağlı), düğüm 2'nin derecesi 1, düğüm 3'ün derecesi 0. Toplam 4 = 2 × 2 kenar: el sıkışma lemması tutuyor.

**Adım 3 — Kaba çöz.** Her düğüm için kenar listesini baştan sona tara ve düğümü içeren kenarları say. Bu, `V × E` işlem demektir: O(V·E).

**Adım 4 — Örüntü.** Her kenar `(u, v)` için yalnızca iki sayacı artırmak yeter: `derece[u]` ve `derece[v]`. Tek bir tarama, tüm dereceleri verir. Bu, kenar listesini bir kez gezip sayaç tutmanın örüntüsüdür.

**Adım 5 — İyileştir.** Tek geçiş, O(E) zaman ve O(V) bellek. Bu, bir kenarı okumadan dereceyi bilemeyeceğin için en iyi olanıdır. Kodda tek bir döngü ve iki sayaç artışı yeterlidir.

Aşağıdaki program bu örüntüyü G1 grafı üzerinde uygular:

```python
n = 7
kenarlar = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (5, 6)]
komsu = {u: set() for u in range(n)}
for u, v in kenarlar:
    komsu[u].add(v)
    komsu[v].add(u)
for u in range(n):
    print(u, len(komsu[u]), sorted(komsu[u]))
print("toplam derece:", sum(len(s) for s in komsu.values()))
print("2|E| =", 2 * len(kenarlar))
```

**Adım 6 — Doğrula.** Kodu Şekil 11.1 ve 11.3'teki G1 grafında izleyelim. Her kenarın iki ucuna sayaç eklenir:

| kenar | derece öncesi | derece sonrası |
|---|---|---|
| (0, 1) | 0:0, 1:0 | 0:1, 1:1 |
| (0, 2) | 0:1, 2:0 | 0:2, 2:1 |
| (1, 3) | 1:1, 3:0 | 1:2, 3:1 |
| (2, 3) | 2:1, 3:1 | 2:2, 3:2 |
| (3, 4) | 3:2, 4:0 | 3:3, 4:1 |
| (5, 6) | 5:0, 6:0 | 5:1, 6:1 |

Son derece dizisi `2, 2, 2, 3, 1, 1, 1`'dir ve toplamı 12'dir; `2|E| = 2 × 6 = 12` ile eşleşir. Programın çıktısı da bunu doğrular:

```term
$ python derece.py
0 2 [1, 2]
1 2 [0, 3]
2 2 [0, 3]
3 3 [1, 2, 4]
4 1 [3]
5 1 [6]
6 1 [5]
toplam derece: 12
2|E| = 12
```

**Bunu AI'sız yazabilir misin?** Kenar listesi yerine bir komşuluk matrisi verilseydi derece hesabı nasıl değişirdi? Her iki yaklaşımın bellek ve zaman maliyetini karşılaştır.

### Örnek 2 (★★): Bağlantılı bileşen sayısı

**Problem:** Bir yönsüz grafın kaç bağlantılı bileşeni olduğunu bul. Her bileşenin başlangıç düğümünü de yazdır.

**Adım 1 — Anla.** Girdi düğüm sayısı ve kenarlar, çıktı bileşen sayısı. Kenar durumları: hiç kenarı olmayan düğüm kendi başına bir bileşendir; graf tek düğümlü olabilir.

**Adım 2 — Örnekle.** G1 grafında 0-4 ve 5-6 olmak üzere iki bileşen vardır. Düğüm 0'dan başlayan bir gezinme 0, 1, 2, 3, 4'ü ziyaret eder; sonra ziyaret edilmemiş ilk düğüm 5 bulunur ve yeni bir bileşen başlar.

**Adım 3 — Kaba çöz.** Her düğüm çifti için aralarında yol olup olmadığını (ayrı ayrı gezinerek) kontrol etmek. Bu O(V²) gezinme gerektirir ve gereksizdir.

**Adım 4 — Örüntü.** Her bileşen bir kez gezilir. Ziyaret edilmemiş bir düğüm bulduğumuzda yeni bir gezinme başlatır, bileşen sayacını artırırız. Bu, her düğümü en fazla bir kez ziyaret eden tek bir ana döngüdür.

**Adım 5 — İyileştir.** Her düğüm ve kenar en fazla bir kez işlenir: O(V + E) zaman, DFS'in özyineleme yığını için O(V) bellek. Bu, bileşen sayımı için bilinen en iyi yaklaşımdır.

Aşağıdaki program bu fikri, Şekil 11.3'teki matrisle uygular; yalnızca DFS ve sayımı içerir:

```c
#include <stddef.h>
#include <stdio.h>

#define N 7

static int m[N][N];       /* komsuluk matrisi (yonsuz) */
static int ziyaret[N];

static void kenar(int u, int v) {
    m[u][v] = 1;
    m[v][u] = 1;
}

static void dfs(int u) {
    ziyaret[u] = 1;
    for (int v = 0; v < N; v++)
        if (m[u][v] && !ziyaret[v])
            dfs(v);
}

int main(void) {
    kenar(0, 1); kenar(0, 2); kenar(1, 3);
    kenar(2, 3); kenar(3, 4); kenar(5, 6);
    int bilesen = 0;
    for (int u = 0; u < N; u++) {
        if (!ziyaret[u]) {
            dfs(u);
            bilesen++;
            printf("bilesen %d, baslangic: %d\n", bilesen, u);
        }
    }
    printf("toplam bilesen: %d\n", bilesen);
    return 0;
}
```

**Adım 6 — Doğrula.** Adım adım izleyelim. Döngü u = 0'da ziyaret edilmemiş düğüm bulur, `dfs(0)` çağrılır ve 0-4 işaretlenir. u = 1..4 zaten ziyaret edilmiştir. u = 5'te ziyaret edilmemiş düğüm bulunur; `dfs(5)` 5 ve 6'yı işaretler. u = 6 zaten işaretlidir.

| u | ziyaret[u] | işlem | bileşen sayısı |
|---|---|---|---|
| 0 | 0 | dfs(0): 0,1,3,2,4 işaretlenir | 1 |
| 1-4 | 1 | atla | 1 |
| 5 | 0 | dfs(5): 5,6 işaretlenir | 2 |
| 6 | 1 | atla | 2 |

Çıktı tablodaki sonucu verir: iki bileşen, başlangıçları 0 ve 5. Derleme WSL2 içinde `-fsanitize=address,undefined` ile de temizdir:

```term
$ gcc -std=c11 -Wall -Wextra bilesen.c -o bilesen
$ ./bilesen
bilesen 1, baslangic: 0
bilesen 2, baslangic: 5
toplam bilesen: 2
```

**Bunu AI'sız yazabilir misin?** Aynı sayımı, özyineleme yerine açık bir yığınla yaz. Yığının en fazla kaç eleman tutabileceğini ve bunun neden V ile sınırlı olduğunu açıkla.

### Örnek 3 (★★): Bir graf ağaç mı?

**Problem:** `n` düğümlü ve verilen kenar listeli yönsüz bir grafın ağaç olup olmadığını söyle. Ağaç, bağlantılı ve döngüsüz olan graftır; Bölüm 11.1'deki üç özellikten (bağlantılılık, döngüsüzlük, `n - 1` kenar) ikisi üçüncüyü garanti eder.

**Adım 1 — Anla.** Girdi `n` ve kenar listesi, çıktı `True` ya da `False`. Kenar durumları: `n = 1` ve kenarsız graf bir ağaçtır (tek düğüm). Kenar sayısı `n - 1` olmayan bir graf ağaç değildir.

**Adım 2 — Örnekle.** Beş düğümlü, kenarları `(0,1), (1,2), (1,3), (1,4)` olan bir graf: bağlantılı ve 4 = 5 - 1 kenar. Ağaç olmalı. Buna karşılık `(0,1), (1,2), (0,2), (3,4)` kenarları 4 kenar içerir (n - 1 = 4) ama 3 ve 4 düğümleri 0-2 bileşeninden kopuktur; ağaç değildir.

**Adım 3 — Kaba çöz.** Her düğümden bir gezinme yapıp bağlantılılığı kontrol et, ayrıca döngü olup olmadığına bak. Bu, birden çok gezinme gerektirir.

**Adım 4 — Örüntü.** Bölüm 11.1'deki özellik: bağlantılılık ve `n - 1` kenar birlikte ağacı belirler. Yani tek bir gezinme (0'dan başlayarak) bağlantılılığı kontrol eder, kenar sayısı ise bir karşılaştırmadır. Döngü kontrolüne gerek kalmaz.

**Adım 5 — İyileştir.** Tek BFS ve bir sayı karşılaştırması: O(V + E) zaman, O(V) bellek. Kenar sayısı önce kontrol edilirse BFS bile atlanabilir, ama bağlantılılık için yine de gezinme gerekir.

Aşağıdaki program, bağlantılılık için BFS'i ve ağaç kararını bu iki koşulla verir:

```python
from collections import deque

def bagli_mi(n, kenarlar):
    komsu = [[] for _ in range(n)]
    for u, v in kenarlar:
        komsu[u].append(v)
        komsu[v].append(u)
    gorulen = {0}
    kuyruk = deque([0])
    while kuyruk:
        u = kuyruk.popleft()
        for v in komsu[u]:
            if v not in gorulen:
                gorulen.add(v)
                kuyruk.append(v)
    return len(gorulen) == n

def agac_mi(n, kenarlar):
    return bagli_mi(n, kenarlar) and len(kenarlar) == n - 1

print(agac_mi(5, [(0, 1), (1, 2), (1, 3), (1, 4)]))
print(agac_mi(4, [(0, 1), (1, 2), (2, 0), (2, 3)]))
print(agac_mi(5, [(0, 1), (1, 2), (0, 2), (3, 4)]))
```

**Adım 6 — Doğrula.** Üç test durumu için iz tablosu:

| durum | bağlı mı? | kenar sayısı | n - 1 | sonuç |
|---|---|---|---|---|
| 5 düğüm, yıldız | evet | 4 | 4 | True |
| 4 düğüm, döngü 0-1-2 | evet | 4 | 3 | False (fazla kenar, döngü var) |
| 5 düğüm, üçgen + 3-4 | hayır (3,4 kopuk) | 4 | 4 | False (n-1 kenar ama bağlı değil) |

Üçüncü durum önemlidir: kenar sayısı tek başına yetmez; bağlantılılık da gerekir. Program çıktısı tabloyla birebir eşleşir:

```term
$ python agac.py
True
False
False
```

**Bunu AI'sız yazabilir misin?** Bağlantılılık kontrolünü, BFS yerine DFS ile yaz. İki gezinme arasında performans ya da bellek farkı var mı, açıkla.

### Örnek 4 (★★★): Kelime merdiveni

**Problem:** Bir kelime sözlüğü verilsin. Başlangıç kelimesinden hedef kelimeye, her adımda yalnızca bir harfi değiştirerek ve her ara kelimeyi sözlükte tutarak, en az kaç adımda ulaşılabileceğini bul. Ulaşılamıyorsa `None` döndür.

**Adım 1 — Anla.** Girdi iki kelime ve bir küme, çıktı en kısa kelime dizisi ya da `None`. Kenar durumları: başlangıç ve hedef aynıysa tek adım; hedef sözlükte yoksa hiçbir zaman ulaşılamaz; başlangıç kelimesinin komşusu yoksa hemen `None`.

**Adım 2 — Örnekle.** `kar`'dan `tas`'a: `kar → kas → tas` iki adımdır (r→s, sonra k→t). Başka iki adımlık yol yoktur: `kar`ın komşuları `bar, kas, kat`; `tas`ın komşuları `kas, bas, tat`. Ortak komşu yalnızca `kas`'tır. Bu da ilginçtir: en kısa yol tekdir.

**Adım 3 — Kaba çöz.** Sözlükteki her kelime çiftini karşılaştırıp kenar listesini kur, sonra bu graf üzerinde BFS yap. Kenar kurulumu, `V` kelime ve kelime uzunluğu `L` için O(V² · L) işlem tutar.

**Adım 4 — Örüntü.** Kenar listesini hiç kurmadan, komşuları üretebiliriz: her konumda 26 harften birini dene, sözlükte olanları komşu al. Bu, grafı **örtük (implicit)** olarak tanımlamaktır. Her düğümde O(L · 26) aday üretilir. Bu, Bölüm 11.8'in durum uzayı fikridir.

**Adım 5 — İyileştir.** Örtük komşu üretimi, `V²` karşılaştırmasını ortadan kaldırır. BFS, kuyruğa girerken işaretleme ve geri izleme tablosu (`onceki`) sayesinde yolu da verir. Toplam maliyet O(V · L · 26 · L): her aday bir kelime kopyası olduğu için `L` çarpanı kalır. Sözlük büyükse bu, kenar listesi kurmaktan belirgin biçimde ucuzdur.

Aşağıdaki program, komşuları üreten `komsular` ve yolu geri izleyen BFS'i tek dosyada verir:

```python
from collections import deque
import string

def komsular(kelime, kume):
    for i in range(len(kelime)):
        for c in string.ascii_lowercase:
            aday = kelime[:i] + c + kelime[i + 1:]
            if aday != kelime and aday in kume:
                yield aday

def merdiven(bas, hedef, kume):
    onceki = {bas: None}
    kuyruk = deque([bas])
    while kuyruk:
        u = kuyruk.popleft()
        if u == hedef:
            yol = []
            while u is not None:
                yol.append(u)
                u = onceki[u]
            return yol[::-1]
        for v in komsular(u, kume):
            if v not in onceki:
                onceki[v] = u
                kuyruk.append(v)
    return None

kume = {"kar", "bar", "bas", "tas", "kas", "kat", "tat", "mat"}
yol = merdiven("kar", "tas", kume)
print(" -> ".join(yol), "(%d adim)" % (len(yol) - 1))
print(merdiven("kar", "yok", kume))
```

**Adım 6 — Doğrula.** Kuyruğun her adımdaki durumunu izleyelim. Komşular konum ve harf sırasıyla (önce sol konum, sonra a'dan z'ye) üretilir:

| adım | kuyruk (önden) | çıkan | yeni eklenen ve geri izleme |
|---|---|---|---|
| 1 | [kar] | kar | bar, kas, kat ← kar |
| 2 | [bar, kas, kat] | bar | bas ← bar |
| 3 | [kas, kat, bas] | kas | tas ← kas |
| 4 | [kat, bas, tas] | kat | mat, tat ← kat |
| 5 | [bas, tas, mat, tat] | bas | yeni yok |
| 6 | [tas, mat, tat] | tas | HEDEF; geri izle: tas ← kas ← kar |

Geri izleme `tas, kas, kar` verir; ters çevrildiğinde yol `kar, kas, tas`'tır. Şekil 11.9 bu grafın tamamını ve vurgulu yolu gösterir. Program çıktısı da bunu doğrular:

```term
$ python merdiven.py
kar -> kas -> tas (2 adim)
None
```

![Şekil 11.9: Kelime merdiveni grafı. Düğümler kelimeler; iki kelime tek harf farkıyla bağlıysa kenar vardır. Kırmızı yol, kar'dan tas'a iki adımlık tek en kısa yoldur.](gorseller/b11_kelime.png)

**Bunu AI'sız yazabilir misin?** Kenar kurulumunu yapmadan, BFS'i bir kez daha yaz; ama bu kez hedefe ulaşmayı değil, başlangıçtan en uzak kelimeyi bulmayı hedefle. Hangi durumda yolun geri izlenmesine gerek kalmaz?

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Graf kodunu elinle yaz; ilk testte bağlantı hatası ya da bellek sızıntısı görürsen, neden olduğunu kendin bul. Sanitizer çıktısını okumadan "çalışıyor" deme.
:::

### Proje 1 (★★): Sensör ağı arıza analizi

**Amaç:** Bir sensör ağını graf olarak modelleyip, bir düğüm (gateway) arızalandığında ağın kaç parçaya ayrıldığını ve hangi sensörlerin merkeze ulaşamadığını bulan bir araç yazmak. Bu, EV Dashboard projesindeki STM32 sensör düğümlerinin haberleşme ağına doğrudan uyarlanabilir.

**Yapılacak / Beklenen davranış:**

1. Düğümleri ve kenarları bir dosyadan (`dugum sayisi` ve her satırda bir `u v` çifti) okuyan bir fonksiyon yaz.
2. Komşuluk listesini kur; bellek kullanımını O(V + E) tut.
3. Verilen bir düğüm kaldırıldığında (silindiğinde), kalan grafın bileşen sayısını ve her bileşenin düğüm listesini yazdır.
4. Gateway düğümü olarak bir id kabul et; gateway'e ulaşamayan düğümleri "izole" diye işaretle.

**Önerilen yaklaşım:** Düğümü "silmek" için onu ziyaret edilmiş (işaretli) kabul et ve gezinmeyi o düğümü atlayarak başlat. Böylece graf kopyalamadan analiz yapabilirsin. Bileşen sayımı için Örnek 2'deki döngü yapısını kullan; her bileşende toplanan düğümleri bir liste olarak tut.

**Başarı kriterleri:**

- Üç bileşenli elle çizdiğin bir örnekte programın bileşen sayısı ve düğüm listeleri elle hesapladığınla birebir eşleşir.
- Gateway kaldırıldığında beklediğin ayrışma çıktıda görülür.
- WSL2 içinde `-fsanitize=address,undefined` ile hiçbir bellek hatası ya da sızıntı raporu yoktur.

### Proje 2 (★★★): Türkçe kelime merdiveni ve hız ölçümü

**Amaç:** Örnek 4'teki kelime merdiveni çözücüyü gerçek bir kelime listesi (ör. 50 000 kelimelik bir sözlük) üzerinde çalıştırıp iki farklı komşu üretim yöntemini karşılaştırmak. Ölçüm, grafın yapısını anlamanın en somut yoludur.

**Yapılacak / Beklenen davranış:**

1. Sözlüğü dosyadan oku; her kelimeyi bir kümeye koy. Yalnızca bir uzunluktaki kelimelerle çalış (ör. 4 harfli).
2. **Yöntem A:** Örnek 4'teki gibi her konumda 26 harfi dene.
3. **Yöntem B:** Her kelimeyi "bir konumu joker yapılmış" kalıplara (`_ar`, `k_r` gibi) böl; kalıp → kelime listesi bir sözlükte tut. Komşuları bu sözlükten al.
4. Her iki yöntemle 100 rastgele çift için en kısa yolu bul; ortalama süreyi ve bulunan yol uzunluklarının aynı olduğunu doğrula.

**Önerilen yaklaşım:** Yöntem B'de önişleme (kalıp sözlüğü kurma) bir kez yapılır; sonra her sorgu yalnızca ilgili kalıpların listelerini gezer. Ölçümü `time.perf_counter()` ile yap. Rastgele seçim için `random.seed(42)` kullan ki sonuçlar tekrarlanabilir olsun. Hangi yöntemin daha hızlı olduğunu tahmin etmeden önce, iki yöntemin karmaşıklık ifadelerini yaz.

**Başarı kriterleri:**

- İki yöntem, 100 çiftin her birinde aynı uzunlukta yol bulur.
- Ölçüm tablosu, her yöntemin ortalama süresini ve önişleme süresini ayrı gösterir.
- Yöntem B'nin neden daha hızlı (ya da yavaş) olduğu, kalıp sayısı ve komşu sayısı ile açıklanır.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kendin düşün, sonra kodla.

1. ★ Yönsüz bir grafta derecesi tek olan düğümlerin sayısının çift olduğunu el sıkışma lemmasıyla açıkla.
2. ★ Komşuluk matrisi verilen bir yönsüz grafın kenar sayısını, matrisin üst üçgeninde kaç tane 1 olduğunu sayarak bul.
3. ★★ Yönlü bir grafta her düğümün çıkış ve giriş derecesini (out-degree, in-degree) komşuluk listesinden hesapla. (Mülakat)
4. ★★ Bir yönlü grafta bir düğümden ulaşılabilen tüm düğümleri DFS ile bul. Bu, Örnek 2'deki bileşen sayımından nasıl farklıdır? (Mülakat)
5. ★★ Bir ızgara (grid) üzerinde engelli hücrelerden geçmeden iki hücre arasındaki en kısa adım sayısını BFS ile bul. Her hücreyi bir düğüm kabul et. (Mülakat)
6. ★★ Bir graf iki renkle boyanabilir mi (bipartite)? BFS ile renklendirmeyi dene ve çakışma olursa bunun ne anlama geldiğini açıkla. (Mülakat)
7. ★★ Bir graf verildiğinde her düğümün komşularını ters sırada yazdıran bir fonksiyon yaz. Komşuluk listesi ile matris arasında hangisi bunu daha kolay yapar?
8. ★★ Bir kenar listesinden komşuluk listesi oluşturan fonksiyonun bellek kullanımını, düğüm sayısı ve kenar sayısı cinsinden yaz. (Mülakat)
9. ★★★ Bir yönlü grafta, her düğümün bir sonraki düğümü tek bir çıkış kenarıyla belirleniyorsa (fonksiyonel graf), bir düğümden başlayıp döngüye girdiğini nasıl tespit edersin? (Mülakat)
10. ★★★ `n` düğümlü bir yönsüz grafta, kenar sayısı `n - 1`'den fazlaysa grafın mutlaka bir döngü içerdiğini kanıtla. (Mülakat)
11. ★★★ Bir grafın bağlantılı olup olmadığını matrisi ve listeyi kullanarak karşılaştır. Büyük seyrek bir graf için hangisini seçersin ve neden? (Mülakat)
12. ★ Bir sosyal ağda "üç derecelik arkadaş" sayısını (iki adım içinde ulaşılabilen kişi sayısı) tanımla ve bunun BFS ile nasıl hesaplanacağını, derinliği nasıl sınırlayacağını açıkla.

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kütüphanenin graf sınıfını okuyacaksın: **NetworkX 3.4.2**, `networkx/classes/graph.py` dosyası. Kaynak, PyPI'dan `networkx==3.4.2` wheel dosyası indirilerek alınmıştır; dosya içinde Graph sınıfının komşuluk yapısı, bir dict-of-dict'tir. Aşağıdaki kesitler kaynaktan alınmış, yalnızca docstring'ler ve yorumlar çıkarılmış, kalan satırların ilk halleri korunmuştur. Bir satır çıkarıldıysa bunu ayrıca belirtiyoruz.

Önce sınıfın tanımında kullanılan veri yapısı fabrikaları (kaynak satırları 316-320):

```python
node_dict_factory = dict
node_attr_dict_factory = dict
adjlist_outer_dict_factory = dict
adjlist_inner_dict_factory = dict
edge_attr_dict_factory = dict
```

Bu dört satır, Graph'ın hangi veri yapısını kullandığını söyler. Dış sözlük (`_adj`) her düğümü bir iç sözlüğe eşler; iç sözlük komşuları anahtar, kenar verisini değer olarak tutar. Yani her komşuluk bir "dict of dict"tir.

Kurucu fonksiyonda (satır 373-374) iki sözlük oluşturulur:

```python
self._node = self.node_dict_factory()  # empty node attribute dict
self._adj = self.adjlist_outer_dict_factory()  # empty adjacency dict
```

`add_edge` gövdesi (satır 956-972), iki düğümü ekler ve kenarı iki yönde yazar. Bu kesit tek başına çalışmaz; `self` ve sınıf bağlamı kaynak dosyaya aittir. Docstring ve `nx._clear_cache` çağrısı bu kesitte çıkarılmıştır; None kontrolleri ve ekleme mantığı korunmuştur:

```python
u, v = u_of_edge, v_of_edge
# add nodes
if u not in self._node:
    if u is None:
        raise ValueError("None cannot be a node")
    self._adj[u] = self.adjlist_inner_dict_factory()
    self._node[u] = self.node_attr_dict_factory()
if v not in self._node:
    if v is None:
        raise ValueError("None cannot be a node")
    self._adj[v] = self.adjlist_inner_dict_factory()
    self._node[v] = self.node_attr_dict_factory()
# add the edge
datadict = self._adj[u].get(v, self.edge_attr_dict_factory())
datadict.update(attr)
self._adj[u][v] = datadict
self._adj[v][u] = datadict
```

**Sorular — cevaplamadan geçme:**

1. `self._adj[u][v] = datadict` ve `self._adj[v][u] = datadict` satırları aynı `datadict` nesnesini iki yere yazar. Bu, kenar verisini güncellediğinde (ör. `G[u][v]["weight"] = 5`) yönsüz grafta ne olur? Bir yönlü grafta (DiGraph) bu iki satır neden farklı olurdu?
2. `datadict = self._adj[u].get(v, self.edge_attr_dict_factory())` satırında varsayılan değer her çağrıda oluşturuluyor. Kenar zaten varsa bu yeni sözlük hiç kullanılmaz mı? Bu, performans açısından ne anlama gelir?
3. Kurucu iki sözlük oluşturuyor: `_node` ve `_adj`. Düğüm bilgisi neden ayrı bir sözlükte tutuluyor, komşuluk içinde tutulmuyor? Bu ayrım bir düğüme özellik eklerken bize ne kazandırır?
4. `add_edge` düğümleri eklerken `if u not in self._node` kontrolünü yapar. Bu kontrol olmasaydı ne olurdu? Yeniden eklenen bir düğüm mevcut komşularını siler miydi?
5. Burada kullanılan veri yapısı, Bölüm 11.4'teki komşuluk listesi ile karşılaştırıldığında hangi açılardan farklıdır? İç sözlüğün "anahtar ile erişim" avantajı, 11.5 tablosunda hangi satırı etkiler?
6. Bu kütüphane, sınıf değişkenleri olarak `dict` fabrikalarını dışarıdan değiştirilebilir bırakıyor. Bu tasarım kararı, alt sınıfların (ör. sıralı bir sözlük kullanan graf) davranışını nasıl değiştirmesine izin verir? Neden düz bir `dict` yerine bu soyutlama?

## Bölüm Özeti

Bu bölümde Bölüm 10'daki ağacın kurallarını gevşetip grafa geçtik:

- **Graf**, düğümler ve kenarlardan oluşur. Düğüm derecesi, yol, döngü, bağlantılılık ve bileşen temel terimlerdir. Ağaç, döngüsüz bağlantılı yönsüz graftır ve `n - 1` kenarı vardır.
- **Yönlü ve ağırlıklı** graflar ayrı iki soruya dayanır: kenarın yönü var mı, ağırlığı var mı. Yön bilgisi ulaşılabilirliği değiştirir.
- **Komşuluk matrisi** kenar sorgusunu O(1) yapar ama `V²` bellek tutar; yoğun graflarda uygundur.
- **Komşuluk listesi** `O(V + E)` bellek tutar ve seyrek graflarda standarttır. C'de bağlı liste, Python'da sözlük+küme ile gerçeklenir.
- **DFS ve BFS** graf üzerinde ziyaret işaretiyle çalışır; her ikisi de `O(V + E)`'dir. BFS ağırlıksız grafta en kısa yolu verir.
- **Bağlantılı bileşen** sayımı, her gezinmede bir bileşeni işaretleyerek O(V + E)'de yapılır.
- **Modelleme**, düğüm, kenar, yön ve ağırlık kararlarını doğru vermektir. Durum uzayı, bağımlılık, ağ ve harita problemleri graf olarak düşünülür.
- **Gerçek sistemlerde** Make bağımlılıkları, git commit DAG'ı ve yönlendirme ağları graf yapısıdır.

**Sonraki bölümde:** Graf üzerinde gezinmeyi öğrendik, ama bir algoritmanın ne kadar hızlı olduğunu nasıl ölçeriz? Bölüm 12'de **algoritma analizi**ne giriyoruz: Big-O, Big-Omega ve Big-Theta notasyonları, en iyi, en kötü ve ortalama durumlar, amortize analiz ve Master Teoremi. Bu bölüm Kısım IV'ün kapısıdır; burada yaptığımız O(V + E) hesabının arkasındaki mantığı bütünüyle kuracağız.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Bir yönsüz grafta tüm derecelerin toplamı neden kenar sayısının iki katıdır? Bu gözlem, derecesi tek olan düğüm sayısı hakkında ne söyler?
2. Komşuluk matrisi ile komşuluk listesi arasında hangi durumda biri diğerinden belirgin biçimde daha iyidir? Yoğun ve seyrek graf örneği ver.
3. DFS ve BFS, aynı grafta farklı sırada düğümleri ziyaret eder. Hangisi en kısa yolu verir ve neden? Bu garanti, kenar ağırlıkları eklendiğinde neden bozulur?
4. Bir yönlü grafta ziyaret işareti olmadan DFS yapılırsa ne olur? Döngü içeren bir grafta bu işareti hangi veri yapısında tutarsın?
5. Bir ağaçla bir bağlantılı graf arasındaki fark nedir? Bir graf bağlantılı ve `n - 1` kenarlıysa neden mutlaka ağaçtır?
6. Bir problemi grafa çevirirken düğümü ve kenarı nasıl seçersin? Aynı problem için iki farklı modelleme yapabileceğin bir örnek ver ve hangisinin daha verimli olduğunu açıkla.
7. Bir kelime merdiveninde komşuları tüm sözlükte aramak yerine konum konum üretmek neden daha iyidir? Bu, grafın hangi özelliğini kullanır?
8. Bir sensör ağında tek bir düğümün arızasının ağı bölüp bölmediğini nasıl hızlıca anlarsın? Bu soruyu hangi graf kavramı yanıtlar ve bunu hesaplamak için hangi işlem gerekir?
:::
