%% kisim_no: III
%% kisim_ad: Veri Yapıları
%% bolum_no: 10
%% baslik: Tree

## Giriş: Hiyerarşinin gücü

Bölüm 7'de bağlı listeyi, Bölüm 8'de yığın ve kuyruğu gördük. Bu yapıların hepsi doğrusaldır: her elemanın bir öncekisi ve bir sonrakisi vardır. Dosya sistemi ise doğrusal değildir. Klasörlerin içinde klasörler, onların içinde dosyalar vardır. Bir HTML sayfasının DOM'u, bir derleyicinin söz dizimi ağacı, bir veritabanı indeksi, bir karar motorunun kuralları, hepsi dallanan yapılardır. Bu dallanan yapıların genel adı **ağaç (tree)**tir.

Bölüm 9'da hash tablosunun büyük bir eksiğini gördük: elemanları hiçbir sırayla tutmuyordu. "En küçük anahtar nedir?" ya da "5 ile 9 arasındaki anahtarlar hangileridir?" sorularını hash tablosu O(1)'de cevaplayamaz. Bu bölümde o eksiği dolduran ağaçları öğreneceğiz: ikili arama ağacı (BST) elemanları sıralı tutar, AVL onu dengede tutar, heap ise en küçük (ya da en büyük) elemanı hızla verir, trie ise anahtarları karakter karakter saklar.

Savunma sanayiinde ve gömülü sistemlerde ağaçlar her yerdedir. Bir görev planlayıcısı, zamanlayıcı kuyruğundaki en acil işi bulmak için bir heap kullanır. Bir sensör füzyon katmanı, olayları zaman sırasına göre bir ağaçta tutabilir. Mülakatlarda ise ağaç soruları neredeyse her zaman karşınıza çıkar: "bir ağacın yüksekliği", "iki düğümün ortak atası", "ağaç dengeli mi?" gibi sorular, özyinelemeyi ne kadar iyi kurduğunuzu ölçer.

::: not
Bu bölümde iki tür ağaç göreceğiz: sıralı arama ağaçları (BST, AVL) ve yığın (heap). Heap'in bir ağaç olduğunu ilk bakışta fark etmek zor olabilir; sebebini 10.7'de dizi gösterimiyle göreceksin.
:::

## 10.1 Ağaç terminolojisi

Bir **ağaç**, düğümler (node) ve düğümleri birbirine bağlayan kenarlardan (edge) oluşan, **döngüsüz** ve **bağlantılı** bir yapıdır. Bir düğümün bağlı olduğu alt düğümlere **çocuk (child)**, üstteki düğüme **ebeveyn (parent)** denir. Aynı ebeveyni paylaşan düğümler **kardeştir**. En üstte, ebeveyni olmayan tek düğüm **kök (root)**tur.

Ağacın iki temel sayısı vardır. Düğüm sayısı `n` ise, ağaçta **tam olarak `n - 1` kenar** vardır. Bu, ağacın tanımından çıkan bir sonuçtur: her düğüm (kök hariç) tek bir ebeveynden bağlanır. Bu kuralı bozan her yapı ya döngü içerir ya da kopuktur.

Düğümleri üç sınıfa ayırırız:

- **Kök:** ebeveyni olmayan tek düğüm.
- **Yaprak (leaf):** hiç çocuğu olmayan düğüm.
- **İç düğüm:** en az bir çocuğu olan, kök olmayan düğüm.

Ağaçta konum ve boyut ölçmek için dört kavram gerekir:

- **Derinlik (depth):** bir düğümün köke olan uzaklığı, yani köke giden yoldaki kenar sayısı. Kökün derinliği 0'dır.
- **Yükseklik (height):** bir düğümden en uzak yaprağa giden yoldaki kenar sayısı. Ağacın yüksekliği, kökün yüksekliğidir. Yaprağın yüksekliği 0'dır.
- **Seviye (level):** aynı derinlikteki düğümlerin oluşturduğu katman. Seviye sayısı, yükseklik artı bir'dir.
- **Boyut:** ağaçtaki toplam düğüm sayısı `n`.

Bu kavramları Şekil 10.1'deki ağaç üzerinde izleyelim. Kök `A`'dır. `E`'nin derinliği 2'dir, çünkü `A → B → E` yolunda iki kenar vardır. `D`'nin yüksekliği 1'dir, çünkü en uzun alt yolu `D → G`'dir. Ağacın yüksekliği 3'tür, çünkü `A → B → D → G` yolu üç kenar içerir.

![Şekil 10.1: Ağaç terminolojisi. Kök A, iç düğümler B, C, D, yapraklar E, F, G. Derinlik köke olan kenar sayısıdır; yükseklik ise en uzun alt yoldaki kenar sayısıdır.](gorseller/b10_terminoloji.png)

Yükseklik kavramı önemlidir, çünkü ağaçtaki çoğu işlemin maliyeti yüksekliğe bağlıdır. `n` düğümlü bir ağacın yüksekliği en az `⌊log2 n⌋`, en fazla `n - 1` olabilir. Alt sınır, düğümleri mümkün olduğunca doldurduğumuz ağaçtan gelir; üst sınır ise her düğümün tek çocuğu olduğu, yani bağlı listeye benzeyen durumdan. Bu iki uç arasındaki fark, bütün bu bölümün ana konusudur.

Ağaçlarda sık kullanılan iki özel sınıf da vardır. **Tam ikili ağaç (full binary tree):** her düğümün 0 ya da 2 çocuğu vardır. **Tam dolu ağaç (perfect binary tree):** tüm yapraklar aynı derinlikte ve her iç düğümün tam iki çocuğu vardır. Bu iki tanımı 10.7'de heap ve 10.6'da AVL analizinde kullanacağız.

## 10.2 İkili ağaç ve bellekteki gösterimi

Her düğümün en fazla iki çocuğu varsa, ağaca **ikili ağaç (binary tree)** denir. İkili ağaçlar, bilgisayar biliminde en çok çalışılan ağaç türüdür, çünkü gerçeklemesi basittir ve iki çocuk üzerinden yapılan özyineleme doğaldır.

Bellekte bir ikili ağaç düğümü, bir değer ve iki işaretçiden oluşur. Bölüm 2'de öğrendiğimiz `struct` ve işaretçi kavramları burada doğrudan kullanılır:

```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct Dugum {
    int deger;
    struct Dugum *sol;
    struct Dugum *sag;
} Dugum;

Dugum *dugum_yap(int deger) {
    Dugum *d = malloc(sizeof *d);
    if (d == NULL) return NULL;
    d->deger = deger;
    d->sol = d->sag = NULL;
    return d;
}
```

Yukarıdaki kodda iki noktaya dikkat et. Birincisi, yeni düğümün iki çocuk işaretçisini de `NULL` yapmak zorundayız. `malloc` belleği sıfırlamaz; başlatılmamış bir işaretçi, Bölüm 2'de gördüğümüz gibi tanımsız davranıştır (UB) ve çöp değerle dolaşmaya başlarsın. İkincisi, `malloc`'un başarısız olma ihtimalini kontrol ettik. Her düğüm ayrı bir `malloc` çağrısıdır; bu, Bölüm 7'de bağlı listenin gösterdiği gibi, belleğin dağınık olması ve önbellek (cache) davranışının kötü olması demektir.

Dizi ile ağaç gösterimi de vardır. Eğer ağaç tam (her seviye dolu) ise, düğümleri bir dizide seviye seviye saklayabiliriz ve çocuk indekslerini hesaplayabiliriz. Bu, 10.7'de heap'in temelidir. Genel ikili ağaçlar için ise işaretçi gösterimi daha esnektir.

## 10.3 Dört gezinme: inorder, preorder, postorder, level-order

Ağacı "gezmek" (traverse), her düğümü tam olarak bir kez ziyaret etmek demektir. Bir ikili ağaçta üç derinlemesine gezinme ve bir genişlemesine gezinme vardır. Bu dördünün farkı yalnızca **kök ziyaretinin nerede yapıldığıdır**:

- **Inorder (sol, kök, sağ):** kökü, sol alt ağaçtan sonra ziyaret eder.
- **Preorder (kök, sol, sağ):** kökü önce ziyaret eder.
- **Postorder (sol, sağ, kök):** kökü en son ziyaret eder.
- **Level-order (seviye seviye):** kökten başlayıp her seviyeyi soldan sağa tarar.

Üç derinlemesine gezinme, özyinelemenin doğrudan uygulamasıdır. Ağaç boşsa (`NULL`) hiçbir şey yapmadan dönülür; değilse üç adım sırayla uygulanır. Aşağıdaki kod, Şekil 10.2'deki ağacın üç sırasını yazdırır:

```c
void inorder(const Dugum *d) {
    if (d == NULL) return;
    inorder(d->sol);
    printf("%d ", d->deger);
    inorder(d->sag);
}

void preorder(const Dugum *d) {
    if (d == NULL) return;
    printf("%d ", d->deger);
    preorder(d->sol);
    preorder(d->sag);
}

void postorder(const Dugum *d) {
    if (d == NULL) return;
    postorder(d->sol);
    postorder(d->sag);
    printf("%d ", d->deger);
}
```

Üç fonksiyonun gövdesi neredeyse aynıdır. Fark yalnızca `printf` satırının konumudur. Bu, gezinme düzenini değiştirmek için hangi satırı nereye koyacağını bilmenin yeterli olduğunu gösterir.

Özyineleme, arka planda çağrı yığınını (call stack) kullanır. Bu yığında her çağrının dönüş adresi ve yerel değişkenleri saklanır. Burada bir platform ayrıntısı önemlidir: x86-64'te `call` komutu dönüş adresini doğrudan yığına iter. ARM tabanlı mikrodenetleyicilerde (ör. STM32, Cortex-M) ise `BL` komutu dönüş adresini LR yazmacına koyar; fonksiyon kendi içinde başka bir fonksiyon çağıracaksa LR'yi yığına kendisi iter. Her iki durumda da derin bir ağaç, yığını derin bir şekilde büyütür. Bu nedenle 10.5'te göreceğimiz dengesiz ağaçlarda özyineleme yığın taşması (stack overflow) ile çökebilir.

Yineleme (iteration) ile inorder gezinmesi, Bölüm 8'deki yığını açıkça kullanarak yazılabilir. Yığın, özyinelemenin yaptığı işi elle yapar: sola inerken düğümleri yığına atar, dönerken yığından alır:

```c
void inorder_yinelemeli(Dugum *kok, size_t kapasite) {
    Dugum **yigin = malloc(kapasite * sizeof *yigin);
    if (yigin == NULL) return;
    size_t ust = 0;
    Dugum *d = kok;
    while (d != NULL || ust > 0) {
        while (d != NULL) {
            yigin[ust++] = d;
            d = d->sol;
        }
        d = yigin[--ust];
        printf("%d ", d->deger);
        d = d->sag;
    }
    free(yigin);
}
```

Bu kodda `kapasite` parametresi kritiktir. Yığın, ağacın yüksekliği artı bir kadar eleman tutabilir; kapasite bunun altında kalırsa yazma yazma (buffer overflow) olur ve bu tanımsız davranıştır. Dengesiz bir ağaçta yükseklik `n - 1`'e kadar çıkar, yani çağıranın bunu bilerek kapasiteyi seçmesi gerekir.

Level-order gezinmesi ise derinlemesine değil genişlemesine ilerler. Bölüm 8'deki kuyruk (queue) burada doğal bir seçimdir: kökü kuyruğa koy; kuyruktan bir düğüm alıp değerini yazdır, çocuklarını sona ekle. Kuyruk FIFO olduğu için düğümler seviye seviye çıkar:

```c
void level_order(Dugum *kok, size_t n) {
    if (kok == NULL) return;
    Dugum **kuyruk = malloc(n * sizeof *kuyruk);
    if (kuyruk == NULL) return;
    size_t bas = 0, son = 0;
    kuyruk[son++] = kok;
    while (bas < son) {
        Dugum *d = kuyruk[bas++];
        printf("%d ", d->deger);
        if (d->sol != NULL) kuyruk[son++] = d->sol;
        if (d->sag != NULL) kuyruk[son++] = d->sag;
    }
    free(kuyruk);
}
```

Bu kuyruk bir dizi üzerinde iki indeksle (`bas` ve `son`) gerçeklenmiştir. Her düğüm en fazla bir kez kuyruğa girdiği için `n` elemanlık bir dizi yeterlidir. Ağacın bütün düğümleri için maliyet O(n)'dir.

Aşağıdaki program, bu dört gezinmeyi Şekil 10.2'deki ağaç üzerinde çalıştırır. Ağacı `kur` yardımcısıyla kurar; `kur`'un ve `serbest`'in (postorder ile belleği serbest bırakan) kodu aşağıda:

```c
Dugum *kur(int v, Dugum *sol, Dugum *sag) {
    Dugum *d = dugum_yap(v);
    if (d != NULL) {
        d->sol = sol;
        d->sag = sag;
    }
    return d;
}

void serbest(Dugum *d) {
    if (d == NULL) return;
    serbest(d->sol);
    serbest(d->sag);
    free(d);
}

int main(void) {
    Dugum *kok = kur(8,
        kur(3, kur(1, NULL, NULL),
               kur(6, kur(4, NULL, NULL), kur(7, NULL, NULL))),
        kur(10, NULL, kur(14, kur(13, NULL, NULL), NULL)));
    printf("inorder  : "); inorder(kok); printf("\n");
    printf("preorder : "); preorder(kok); printf("\n");
    printf("postorder: "); postorder(kok); printf("\n");
    printf("yinelemeli inorder: ");
    inorder_yinelemeli(kok, 16); printf("\n");
    printf("level    : "); level_order(kok, 9); printf("\n");
    serbest(kok);
    return 0;
}
```

`serbest`'i postorder yapısıyla yazdık: önce çocukların belleğini bırakıyoruz, sonra kendimizi. Bu sıra zorunludur. Önce `free(d)` çağırıp sonra `d->sol`'a erişirsen, serbest bırakılmış belleğe erişmiş olursun; bu tanımsız davranıştır (UB) ve tipik olarak yanlış değer okumana ya da çökmene yol açar, ama her zaman böyle olacağı garanti değildir.

Derleme ve çalıştırma aşağıdaki gibidir. Windows'ta MinGW ile `gcc ... -o gezinme.exe` yazıp `.\gezinme.exe` ile çalıştırabilirsin. Bellek hatalarını yakalamak için `-fsanitize=address,undefined` ve valgrind gibi Linux araçları gerekir; bunları WSL2 içindeki gcc ile kullan:

```term
$ gcc -std=c11 -Wall -Wextra -pedantic gezinme.c -o gezinme
$ ./gezinme
inorder  : 1 3 4 6 7 8 10 13 14
preorder : 8 3 1 6 4 7 10 14 13
postorder: 1 4 7 6 3 13 14 10 8
yinelemeli inorder: 1 3 4 6 7 8 10 13 14
level    : 8 3 10 1 6 14 4 7 13
```

Çıktıdaki inorder dizisinin küçükten büyüğe sıralı olduğuna dikkat et. Bu bir tesadüf değil; sıralı arama ağaçlarının temel özelliğidir ve bir sonraki bölümün konusudur.

![Şekil 10.2: Aynı ağaç üzerinde dört gezinme. Inorder ağacı soldan sağa sıralar; preorder kökten başlar; postorder kökü en sona bırakır; level-order seviye seviye tarar.](gorseller/b10_gezinme.png)

## 10.4 İkili arama ağacı (BST): arama ve ekleme

İkili arama ağacı (Binary Search Tree, BST), ikili ağacın üzerine tek bir kural koyar: **her düğüm için, sol alt ağaçtaki tüm değerler düğümden küçük, sağ alt ağaçtaki tüm değerler düğümden büyüktür.** Bu kural, inorder gezinmesinin neden sıralı çıktı verdiğini açıklar; ayrıca aramayı, Bölüm 5'teki ikili aramanın ağaç hâline getirir.

Bir değeri aramak için kökten başlarız. Aranan değer kökten küçükse sola, büyükse sağa gideriz; eşitse bulduk demektir. Her adımda bir alt ağaç elenir. Şekil 10.3, 7 değerinin aranmasını gösterir:

![Şekil 10.3: BST'de arama. Aranan 7 için 8'den sola, 3'ten sağa, 6'dan sağa gidilir ve 7 bulunur. Her düğümde yalnızca tek bir karşılaştırma yapılır; sağ dal zaten alt ağaçların sınırlarını belirler.](gorseller/b10_bst_arama.png)

Bu yolun uzunluğu ağacın yüksekliği kadardır. Dolayısıyla BST'de arama, ağacın yüksekliği `h` olmak üzere **O(h)** zaman alır. Yükseklik, ağacın şekline bağlıdır: dengeli bir ağaçta `h ≈ log2 n` olur ve arama O(log n) olur; dengesiz bir ağaçta ise `h ≈ n` olur ve arama O(n) olur. Bunu 10.5'te göreceğiz. Rastgele sırada eklenen elemanlarla oluşan BST'lerin ortalama yüksekliği O(log n)'dir; ama bu, girdinin rastgele olduğu varsayımına dayanır.

Aramayı C'de iki satırla yazabiliriz; döngü kullanmak özyinelemeden daha güvenlidir:

```c
Dugum *bst_ara(Dugum *k, int v) {
    while (k != NULL && k->deger != v)
        k = (v < k->deger) ? k->sol : k->sag;
    return k;
}
```

Ekleme de aramayla aynı yolu izler. Yol boş bir işaretçiye ulaştığında, yeni düğüm tam orada yaprak olarak oluşturulur. Bunu özyinelemeli yazmak zariftir: fonksiyon, kendi alt ağacının yeni kökünü döndürür ve ebeveyn bu değeri kendi işaretçisine yazar:

```c
Dugum *bst_ekle(Dugum *k, int v) {
    if (k == NULL) return dugum_yap(v);
    if (v < k->deger)
        k->sol = bst_ekle(k->sol, v);
    else if (v > k->deger)
        k->sag = bst_ekle(k->sag, v);
    return k;
}
```

Bu kodda `v == k->deger` durumunda hiçbir şey yapılmaz; yani BST yinelenen anahtarları tutmaz. Yinelenen değer istiyorsan ya sayaç tutarsın ya da eşitlik durumunda sağa (veya sola) gitmeye karar verirsin. Her iki tercihin de sonucu ağacın şeklini değiştirir; bu yüzden kararı kod yorumuna yazmak gerekir.

Bölüm 9'daki hash tablosuyla karşılaştırırsak BST'nin bedelini ve kazancını görürüz. Hash tablosu ortalama O(1) arar ama sıra tutmaz. BST arama, ekleme ve silmeyi O(h) ile yapar, fakat aynı zamanda sıralıdır: en küçük elemanı, en büyük elemanı ve bir aralıktaki tüm elemanları inorder ile verebilir. Bölüm 9.8'de "sıra gerekiyorsa hash yanlış seçimdir" demiştik; BST bu boşluğu doldurur.

## 10.5 BST'den silme ve dengesizliğin bedeli

Silme, BST'nin en çok hata yapılan işlemidir, çünkü üç farklı durumu vardır. Silinecek düğüm `k` olsun:

1. **Yaprak:** `k`'nın çocuğu yok. Ebeveynindeki işaretçiyi `NULL` yap ve `k`'yı serbest bırak.
2. **Tek çocuk:** `k`'nın yalnızca bir çocuğu var. `k`'yı çocuğuyla değiştir (çocuk, `k`'nın yerine geçer).
3. **İki çocuk:** `k`'nın iki çocuğu var. `k`'nın yerine **inorder halefi** koy: sağ alt ağacındaki en küçük düğüm. Sonra o halefi, sağ alt ağacından sil. Halefin sol çocuğu olmadığı için bu ikinci silme, ya yaprak ya da tek çocuklu durumdur ve tekrar özyinelemeye girmez.

Neden halef? Çünkü inorder halefi, `k`'nın hemen sağındaki değerdir. Onu `k`'nın yerine koyduğumuzda, BST kuralı korunur: sol alt ağaç hâlâ daha küçük, sağ alt ağaç hâlâ daha büyüktür. İnorder halefin yerine inorder selefi (sol alt ağacındaki en büyük düğüm) de kullanabilirsin; simetrik olarak doğrudur.

![Şekil 10.4: BST'den silmenin üç durumu. (a) Yaprak 3 doğrudan kesilir. (b) Tek çocuklu 3, çocuğu 1 ile yer değiştirir. (c) İki çocuklu 3, inorder halefi 4 ile yer değiştirir; sonra 4'ün eski yeri silinir.](gorseller/b10_bst_silme.png)

Üç durumu tek bir özyinelemeli fonksiyonda toplayabiliriz. Halefi bulan yardımcı fonksiyon önce yazılmalıdır:

```c
Dugum *en_kucuk(Dugum *k) {
    while (k->sol != NULL) k = k->sol;
    return k;
}

Dugum *bst_sil(Dugum *k, int v) {
    if (k == NULL) return NULL;
    if (v < k->deger) {
        k->sol = bst_sil(k->sol, v);
    } else if (v > k->deger) {
        k->sag = bst_sil(k->sag, v);
    } else {
        if (k->sol == NULL) {
            Dugum *s = k->sag;
            free(k);
            return s;
        }
        if (k->sag == NULL) {
            Dugum *s = k->sol;
            free(k);
            return s;
        }
        Dugum *h = en_kucuk(k->sag);
        k->deger = h->deger;
        k->sag = bst_sil(k->sag, h->deger);
    }
    return k;
}
```

Silme fonksiyonunda dikkat edilmesi gereken iki nokta var. İlki, `free(k)` çağrısından sonra `k`'ye erişilmediği için tanımsız davranış oluşmuyor; yalnızca `s` (kalan çocuk) döndürülüyor. İkincisi, iki çocuklu durumda değeri kopyalayıp halefi `bst_sil` ile siliyoruz. Bu özyineleme, halefin ya yaprak ya da tek çocuklu olması sayesinde ikinci kez iki çocuklu durumla karşılaşmaz.

Kodu test etmek için ağacı eklemelerle kurup inorder yazdırabiliriz. Aşağıdaki program, 4, 14 ve 8 silindikten sonra ağacın sıralılığını korunduğunu gösterir:

```c
int main(void) {
    Dugum *kok = NULL;
    int girdi[] = {8, 3, 10, 1, 6, 14, 4, 7, 13};
    for (size_t i = 0; i < 9; i++)
        kok = bst_ekle(kok, girdi[i]);
    printf("ilk      : "); inorder(kok); printf("\n");
    printf("7 var mi : %s\n", bst_ara(kok, 7) ? "evet" : "hayir");
    printf("5 var mi : %s\n", bst_ara(kok, 5) ? "evet" : "hayir");
    kok = bst_sil(kok, 4);
    printf("4 silindi: "); inorder(kok); printf("\n");
    kok = bst_sil(kok, 14);
    printf("14 silindi: "); inorder(kok); printf("\n");
    kok = bst_sil(kok, 8);
    printf("8 silindi: "); inorder(kok); printf("\n");
    serbest(kok);
    return 0;
}
```

Bu programda `inorder` ve `serbest` 10.3'te tanımlanmıştır. Programın çıktısı:

```term
$ ./bst
ilk      : 1 3 4 6 7 8 10 13 14
7 var mi : evet
5 var mi : hayir
4 silindi: 1 3 6 7 8 10 13 14
14 silindi: 1 3 6 7 8 10 13
8 silindi: 1 3 6 7 10 13
```

Şimdi asıl tehlikeye gelelim. BST'nin performansı eklenme sırasına bağlıdır. Sıralı bir girdiyi, yani `1, 2, 3, 4, 5`'i sırayla eklersek, her yeni eleman bir öncekinin sağına düşer. Ağaç bağlı listeye dönüşür ve yüksekliği `n - 1` olur. Aramanın maliyeti O(n)'e çöker. Şekil 10.5'in solunda bu durum görülür; sağda ise aynı beş elemanın farklı bir sırayla eklenmesiyle oluşan dengeli ağaç vardır.

![Şekil 10.5: Dengesiz BST. Solda sıralı ekleme bir zincir (yükseklik 4) üretir; sağda aynı elemanlar ortadan başlayarak eklenince yükseklik 2 olur. Ağacın yüksekliği, aramanın maliyetini belirler.](gorseller/b10_dengesiz.png)

Bu bir teorik kaygı değildir. Veritabanına her gün artan kimlik numarasıyla kayıt eklediğini düşün: her yeni kayıt, bir öncekinden büyüktür ve ağacın sağına düşer. Bir saldırgan da, Bölüm 9.8'deki hash flooding saldırısının benzerini yapabilir: sıralı girdi göndererek BST'yi bağlı listeye çevirir. Bu nedenle üretim kodunda BST yerine dengeli ağaçlar (AVL, kırmızı-siyah) kullanılır. Bunu bir sonraki bölümde AVL ile göreceğiz.

Dengesiz bir ağacın bir başka sonucu da yığın taşmasıdır. Ağacı özyinelemeli gezinirsen, 10^6 düğümlük bir zincir için 10^6 çağrı derinliği oluşur; Windows'ta varsayılan yığın boyutu (1 MB) bu kadar derinliği taşıyamaz ve program çöker. Bu yüzden derin ağaçlarda inorder yerine yinelemeli sürümü tercih etmek gerekebilir.

## 10.6 AVL ağaçları: denge ve rotasyon

AVL ağaçları, adını buluşturucuları Adelson-Velsky ve Landis'ten alır (1962). Fikir basittir: her düğümde **denge faktörünü (balance factor)** tut ve bu değer `-1`, `0` ya da `1` dışına çıkarsa ağacı **rotasyon** ile düzelt.

Denge faktörü şöyle tanımlanır:

`bf(d) = yükseklik(sol alt ağaç) - yükseklik(sağ alt ağaç)`

Bir AVL ağacında her düğüm için `bf` değeri `-1`, `0` veya `1` olmalıdır. Bir ekleme sonrası bir düğümde `bf` değeri `2` ya da `-2` olursa, o düğüm dengesiz demektir ve düzeltilmelidir. Dengesizliğin dört türü vardır ve adları, eklenen elemanın hangi yöne doğru uzandığını anlatır:

- **LL:** Sol çocuğun sol alt ağacına ekleme. Tek **sağa** rotasyon ile düzelir.
- **RR:** Sağ çocuğun sağ alt ağacına ekleme. Tek **sola** rotasyon ile düzelir.
- **LR:** Sol çocuğun sağ alt ağacına ekleme. Önce sol çocukta **sola** rotasyon, sonra düğümde **sağa** rotasyon gerekir.
- **RL:** Sağ çocuğun sol alt ağacına ekleme. Önce sağ çocukta **sağa** rotasyon, sonra düğümde **sola** rotasyon gerekir.

Rotasyon, bir ebeveyn ile çocuğu arasında bağlantıları yeniden düzenleyen, inorder sırasını değiştirmeyen bir işlemdir. Tek sağa rotasyonu şöyle düşün: `z` dengesiz düğüm, `y` onun sol çocuğu. `y`'yi yukarı çıkarıp `z`'yi onun sağına koyarız; `y`'nin eski sağ çocuğu ise `z`'nin soluna geçer. Bu iş yalnızca üç işaretçinin değiştirilmesidir, yani O(1)'dir.

![Şekil 10.6: AVL tek rotasyonlar. LL durumunda 30 dengesizdir; sağa döndürme ile 20 kök olur. RR durumu aynı mantığın aynasıdır; sola döndürme ile 20 kök olur. Her iki durumda inorder çıktısı (10 20 30) değişmez.](gorseller/b10_avl_tek.png)

Çift rotasyon durumlarında (LR ve RL), tek rotasyon yetmez. Şekil 10.7'de LR için önce 10'da sola döndürme yapılır; bu, ağacı LL durumuna çevirir. Ardından 30'da sağa döndürme ile denge sağlanır. RL durumu aynı işlemin aynasıdır.

![Şekil 10.7: AVL çift rotasyonlar. LR durumunda önce 10'da sola döndürme (ara adım) yapılır, ardından 30'da sağa döndürme ile 20 kök olur. RL durumu aynı mantığın aynasıdır.](gorseller/b10_avl_cift.png)

Aşağıdaki kod, rotasyonları ve eklemeyi C'de gösterir. Yükseklik her düğümde saklanır; `guncelle` bu değeri çocuklarından yeniden hesaplar:

```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct AVL {
    int deger;
    int yukseklik;
    struct AVL *sol;
    struct AVL *sag;
} AVL;

static int yuk(const AVL *d) { return d ? d->yukseklik : 0; }

static int maks(int a, int b) { return a > b ? a : b; }

static void guncelle(AVL *d) {
    d->yukseklik = 1 + maks(yuk(d->sol), yuk(d->sag));
}

static int denge(const AVL *d) {
    return yuk(d->sol) - yuk(d->sag);
}
```

Dikkat: 10.1'de yüksekliği kenar sayısı olarak tanımlamıştık; AVL kodunda ise yüksekliği düğüm sayısı olarak saklıyoruz. Yani yaprağın `yukseklik` alanı 1'dir ve boş alt ağacın yüksekliği `yuk(NULL)` ile 0 döner. Bu seçim `guncelle` içindeki `1 + maks(...)` formülünü sadeleştirir. Denge faktörü, iki tanımda da aynı sonucu verir, çünkü iki alt ağacın yükseklikleri aynı kaymayla değişir.

Rotasyonlar ve dengeleme aşağıda. Rotasyon fonksiyonları yalnızca üç işaretçiyi değiştirir ve iki yüksekliği günceller:

```c
static AVL *sag_dondur(AVL *z) {
    AVL *y = z->sol;
    z->sol = y->sag;
    y->sag = z;
    guncelle(z);
    guncelle(y);
    return y;
}

static AVL *sol_dondur(AVL *z) {
    AVL *y = z->sag;
    z->sag = y->sol;
    y->sol = z;
    guncelle(z);
    guncelle(y);
    return y;
}

AVL *avl_dengele(AVL *d) {
    guncelle(d);
    int b = denge(d);
    if (b > 1) {
        if (denge(d->sol) < 0)
            d->sol = sol_dondur(d->sol);
        return sag_dondur(d);
    }
    if (b < -1) {
        if (denge(d->sag) > 0)
            d->sag = sag_dondur(d->sag);
        return sol_dondur(d);
    }
    return d;
}
```

`avl_dengele` dört durumu şöyle ayırır: `b > 1` sol ağır demektir. Sol çocuğun bf'si negatifse (sağ ağır), bu LR'dir ve önce sol çocukta sola döndürme yapılır; ardından her durumda sağa döndürme gelir. `b < -1` için simetrik mantık geçerlidir. Eklemeyi ise BST eklemesi gibi yazıp her geri dönüşte dengelemeyi çağırırız:

```c
AVL *avl_ekle(AVL *d, int v) {
    if (d == NULL) {
        AVL *y = malloc(sizeof *y);
        if (y == NULL) return NULL;
        y->deger = v;
        y->yukseklik = 1;
        y->sol = y->sag = NULL;
        return y;
    }
    if (v < d->deger)
        d->sol = avl_ekle(d->sol, v);
    else if (v > d->deger)
        d->sag = avl_ekle(d->sag, v);
    else
        return d;
    return avl_dengele(d);
}
```

Bu kodda `malloc` başarısızlığı durumunda `NULL` dönmek, üst çağrının bunu bir alt ağaç olarak kabul etmesine yol açabilir; kısalık için bu durumu tam ele almadık. Gerçek bir kütüphanede, bellek yetersizliğini ayrıca bildirmek gerekir.

Neden O(log n)? Bir AVL ağacının yüksekliği `h` iken, en az kaç düğüm olabileceğini sayalım. Yükseklik `h` olan en küçük AVL ağacının iki alt ağacı vardır: biri yükseklik `h - 1`, diğeri `h - 2` (çünkü denge en fazla 1 farklı olabilir). Yani `N(h) = N(h-1) + N(h-2) + 1`. Bu, Fibonacci benzeri bir büyüme oranı verir; sonuçta `h ≈ 1,44 · log2 n` çıkar. Dolayısıyla `n` düğümlü bir AVL ağacının yüksekliği O(log n)'dir ve arama, ekleme ve silme O(log n)'de kalır. Eklemede bir rotasyon en fazla bir kez yukarı doğru uygulanır ve her rotasyon O(1)'dir; yani eklemenin ek maliyeti sabittir.

Burada bir not: `1,44` katsayısı, en kötü durumdur. Bir AVL ağacı pratikte genelde daha dengelidir, ama garanti budur. BST'de ise garanti yoktur; yalnızca ortalama davranış iyidir.

## 10.7 Heap: dizide tam ikili ağaç

Heap (yığın), iki kuralı birlikte sağlayan bir ağaçtır:

1. **Şekil kuralı:** Ağaç tamdır; yani her seviye soldan sağa doldurulmuş, yalnızca son seviye kısmen dolu olabilir.
2. **Sıra kuralı (min-heap için):** Her düğüm, çocuklarından küçük ya da eşittir. Böylece en küçük eleman her zaman köktedir.

Max-heap'te sıra kuralı tersine çevrilir: en büyük eleman köktedir. Bu bölümde min-heap'e odaklanıyoruz; max-heap aynı fikirle, karşılaştırmayı ters yaparak elde edilir.

Heap'in güzel tarafı, bir dizide saklanabilmesidir. Düğümleri seviye seviye, soldan sağa numaralandırırsak, `i`. düğümün çocukları ve ebeveyni basit formüllerle bulunur:

- Sol çocuk: `2i + 1`
- Sağ çocuk: `2i + 2`
- Ebeveyn: `(i - 1) / 2` (tamsayı bölmesi)

Bu gösterimde işaretçi yoktur; her şey indeks aritmetiğiyle yapılır. Bu, bellek kullanımını düşürür ve önbellek dostu bir yapı sağlar (Bölüm 7'deki dizi avantajı). Şekil 10.8 aynı heap'in iki yüzünü gösterir:

![Şekil 10.8: Min-heap ağaç ve dizi olarak. Her ebeveyn çocuklarından küçük ya da eşittir. Dizide i. elemanın çocukları 2i+1 ve 2i+2 indekslerindedir.](gorseller/b10_heap.png)

Heap'te iki temel işlem vardır: **sift-up** (yukarı yüzdürme) ve **sift-down** (aşağı batırma). Ekleme, elemanı sona koyup sift-up ile yukarı taşır. En küçük elemanı çıkarma (pop), köke son elemanı koyup sift-down ile aşağı indirir.

Sift-up kodu, eklenen elemanın ebeveyninden küçük olduğu sürece onu yukarı taşır:

```c
typedef struct {
    int *dizi;
    size_t n, kap;
} Yigin;

static void takas(int *a, int *b) {
    int t = *a;
    *a = *b;
    *b = t;
}

void sift_up(Yigin *y, size_t i) {
    while (i > 0) {
        size_t ebeveyn = (i - 1) / 2;
        if (y->dizi[ebeveyn] <= y->dizi[i]) break;
        takas(&y->dizi[ebeveyn], &y->dizi[i]);
        i = ebeveyn;
    }
}
```

Sift-down, bir düğümü iki çocuğundan küçük olan kadar aşağı iter. Hangi çocuğun seçileceği önemlidir: küçük olanı seçmeliyiz; yoksa heap kuralı bozulur.

```c
void sift_down(Yigin *y, size_t i) {
    for (;;) {
        size_t sol = 2 * i + 1, sag = 2 * i + 2, en = i;
        if (sol < y->n && y->dizi[sol] < y->dizi[en]) en = sol;
        if (sag < y->n && y->dizi[sag] < y->dizi[en]) en = sag;
        if (en == i) break;
        takas(&y->dizi[i], &y->dizi[en]);
        i = en;
    }
}
```

Şekil 10.9, en küçük elemanı çıkardıktan sonra oluşan durumu ve sift-down adımlarını gösterir. Başlangıçta 2 çıkarılmış, son eleman 9 köke konmuştur.

![Şekil 10.9: Sift-down adımları. 9 köke gelince küçük çocuk 3 ile takas edilir; 9 bir alt seviyeye iner ve 5 ile takas edilerek yaprağa ulaşır. Heap kuralı yeniden sağlanır.](gorseller/b10_heap_sift.png)

Bu iki işlemle heap'in ana API'sini yazabiliriz. Ekleme, boşluğa sona yazıp sift-up çağırır; en küçüğü çıkarma, kökü döndürüp son elemanı köke koyar ve sift-down çağırır:

```c
int yigin_ekle(Yigin *y, int v) {
    if (y->n == y->kap) return 0;
    y->dizi[y->n] = v;
    sift_up(y, y->n);
    y->n++;
    return 1;
}

int yigin_al_min(Yigin *y) {
    int min = y->dizi[0];
    y->dizi[0] = y->dizi[--y->n];
    sift_down(y, 0);
    return min;
}
```

Bu kodda `yigin_al_min` çağrılmadan önce `n > 0` olduğu varsayılır. Boş heap'ten çıkarma, dizi dışına okuma olur ve tanımsız davranıştır. Üretim kodunda bunu kontrol et.

Peki bir diziyi baştan heap yapmanın maliyeti nedir? Naif yol, her elemanı tek tek eklemektir: her ekleme O(log n), toplam O(n log n). Ama **heapify** denilen daha akıllı bir yol vardır: dizinin son iç düğümünden başlayıp köke doğru her düğüm için sift-down çağır.

```c
void heapify(Yigin *y) {
    for (size_t i = y->n / 2; i > 0; i--)
        sift_down(y, i - 1);
}
```

Heapify'ın maliyetinin O(n) olduğunu iki gözlemle görebiliriz. Yükseklik `h` olan düğümlerin sayısı yaklaşık `n / 2^(h+1)`'dir; çünkü yapraklar (h = 0) ağacın yarısını oluşturur. Her düğümün sift-down maliyeti en fazla `h`'dir. Toplam iş `Σ (n / 2^(h+1)) · h` olur ve bu toplam `n`'in sabit katıdır. Yani heapify O(n)'dir; O(n log n) değildir. Bu fark küçük görünür ama büyük dizilerde ciddi bir kazançtır.

Heap'in en önemli uygulaması öncelik kuyruğudur. Bunu bir sonraki alt bölümde ele alıyoruz.

## 10.8 Öncelik kuyruğu ve Python heapq

**Öncelik kuyruğu (priority queue)**, her elemanın bir önceliği olduğu ve her zaman en yüksek öncelikli elemanın çıkarıldığı bir veri yapısıdır. Kuyruk FIFO değildir; sıra önceliğe göre belirlenir. Dijkstra'nın en kısa yol algoritmasında (Bölüm 17), Huffman kodlamasında (Bölüm 18) ve bir işletim sisteminin zamanlayıcısında bu yapı kullanılır. İşletim sistemlerinde bir görev planlayıcısı, hazır süreçler arasından en yüksek öncelikli olanı seçmek zorundadır; bu, tam olarak bir min-heap işidir.

Öncelik kuyruğunu heap ile gerçeklemek, her işlemi O(log n)'de yapmak demektir: ekleme sift-up, çıkarma sift-down. En yüksek öncelikli elemanın bakılması (peek) ise O(1)'dir.

Python'un standart kütüphanesi `heapq` modülü, bir Python listesi üzerinde bu işlemleri sağlar. Liste, heap kuralını kendiliğinden korur; `heapq` yalnızca fonksiyonları sağlar:

```python
import heapq

h = [5, 1, 4]
heapq.heapify(h)          # O(n): listeyi yerinde heap yapar
heapq.heappush(h, 2)      # O(log n): sift-up
print(heapq.heappop(h))   # O(log n): en küçük; çıktı 1
```

Bu kodun çıktısı `1`'dir. `heapq` yalnızca **min-heap** sağlar; max-heap için sayıları negatife çevirmek yaygın bir yöntemdir (`heappush(h, -x)` ve çıkarılan değeri `-` ile geri çevirmek). Öncelik kuyruğunda eleman olarak tuple kullanılıyorsa, eşit öncelikli elemanlar için ikinci bir alan eklemeyi unutma. Aksi halde Python, tuple'ın ikinci elemanlarını karşılaştırmaya çalışır ve karşılaştırılamayan nesnelerde `TypeError` alırsın. Kendi zamanlayıcını yazarken bu ikinci alana artan bir sayaç koymak, eşit öncelikli işlerin FIFO sırasını da korur.

Python 3.12'de `heapq`'nun genel API'si yalnızca min-heap içindir; kaynakta `_heapify_max` gibi alt çizgiyle başlayan max-heap yardımcıları vardır, ama bunlar özeldir ve sürümler arasında değişebilir. Nitekim Python 3.14 bu yardımcıları `heapify_max`, `heappush_max`, `heappop_max` adlarıyla kamuya açtı. Kodunun hangi sürümde çalışacağını bilmiyorsan negatif sayı yöntemi her sürümde güvenlidir. Kaynağı Kod Okuma egzersizinde inceleyeceğiz.

## 10.9 Trie: karakterle ağaç

Son veri yapımız **trie** (sözcük ağacı, "try" diye okunur), anahtarları karakter karakter saklayan bir ağaçtır. Kökten bir yaprağa giden her yol bir kelimeyi oluşturur. Ortak öneki olan kelimeler ağacın aynı dalını paylaşır: `ev`, `eve`, `evde` kelimeleri `e → v` yolunu paylaşır.

Trie'ın gücü, **önek (prefix)** sorgularında ortaya çıkar. "ev ile başlayan kelimeleri bul" sorusunu hash tablosu O(1)'de cevaplayamaz; her anahtara tek tek bakmak gerekir. Trie'da ise `ev` yolunu takip edip o düğümün altındaki dalı gezersin. Bu, otomatik tamamlama (autocomplete) ve yazım denetiminin temelidir.

![Şekil 10.10: Trie. Kelimeler el, ela, ev, eve, evde. Yeşil düğümler bir kelimenin sonunu işaretler; "ev" için yalnızca v dalının altı gezilir.](gorseller/b10_trie.png)

Her düğüm bir karakter (ya da karakter ile bir "kelime sonu" bayrağı) taşır ve çocukları bir sözlükte tutulur. Aşağıdaki Python sınıfı trie'ın temel işlemlerini gösterir:

```python
class Trie:
    def __init__(self):
        self.kok = {"c": {}, "son": False}

    def ekle(self, kelime):
        d = self.kok
        for ch in kelime:
            d = d["c"].setdefault(ch, {"c": {}, "son": False})
        d["son"] = True

    def _yol(self, s):
        d = self.kok
        for ch in s:
            d = d["c"].get(ch)
            if d is None:
                return None
        return d

    def ara(self, kelime):
        d = self._yol(kelime)
        return d is not None and d["son"]

    def on_ek(self, onek):
        d = self._yol(onek)
        if d is None:
            return []
        sonuc = []
        self._topla(d, onek, sonuc)
        return sorted(sonuc)

    def _topla(self, d, onek, sonuc):
        if d["son"]:
            sonuc.append(onek)
        for ch, c in d["c"].items():
            self._topla(c, onek + ch, sonuc)
```

Ekleme ve arama, kelimenin uzunluğu `L` kadar adım atar: O(L). Bu, sözlükteki toplam kelime sayısından bağımsızdır; bir milyon kelime olsa da `ev` araması iki adımdır. Önek sorgusu ise önek yolunu bulduktan sonra o alt ağacın tamamını gezer; maliyeti, sonuç sayısına orantılıdır.

Trie'ın bedeli bellektedir. Her düğüm bir sözlük ve bir bayrak taşır; ortak öneki olmayan uzun kelimeler çok sayıda düğüm üretir. Gerçek sistemlerde bu yüzden sıkıştırılmış trie (radix tree) ya da bellek dostu gerçeklemeler kullanılır. Bu bölümde amacımız ilkeyi görmektir.

Bölüm 9'daki bağlantıya dönersek: hash tablosu anahtarları eşit parçalara dağıtır ve önek bilgisini atar. Trie ise önek bilgisini yapının kendisinde taşır. Bu iki yapı farklı soruları ucuz cevaplar; hangisinin ne zaman gerektiğini seçmek mühendisliğin işidir.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz; doğrulama adımında elle iz tablosu kullanacağız.

### Örnek 1 (★): Ağacın seviye sayısı

**Problem:** Bir ikili ağacın seviye sayısını (kökten en uzun yaprağa kadar olan düğüm sayısı) bul. Boş ağacın seviye sayısı 0'dır. Örneğin kökü 5, sol çocuğu 3 (sol çocuğu 1), sağ çocuğu 8 olan ağacın seviye sayısı 3'tür.

**Adım 1 — Anla.** Girdi bir ağaç köküdür, çıktı bir tamsayıdır. Kenar durumlar: boş ağaç (`NULL`) ve tek düğümlü ağaç. Seviye sayısı, yüksekliğin 1 fazlasıdır; yani yükseklik kenar sayısı, seviye sayısı düğüm sayısıdır.

**Adım 2 — Örnekle.** Yukarıdaki örnek: 5'in sol alt ağacı (3, 1) iki seviye, sağ alt ağacı (8) bir seviye verir. Bu iki sonucun en büyüğüne bir ekleyince 5'in seviye sayısı bulunur: `max(2, 1) + 1 = 3`.

**Adım 3 — Kaba çöz.** Her düğüm için iki alt ağacın seviye sayısını hesaplayıp büyüğüne bir eklemek. Bu, tüm düğümleri bir kez ziyaret eder: O(n) zaman, yığın derinliği için O(h) bellek.

**Adım 4 — Örüntü.** Bu bir postorder hesaplamasıdır: bir düğümün cevabı, çocuklarının cevabına bağlıdır. Bu örüntü, ağaç sorularının çoğunda ortaktır (yükseklik, boyut, yaprak sayısı).

**Adım 5 — İyileştir.** Ek bir iyileştirmeye ihtiyaç yok; O(n) zaman zaten en iyisidir, çünkü her düğümü görmeden cevabı bilemezsin. Kodda yalnızca boş ağacı taban durum olarak ele almak yeterli.

```python
class Dugum:
    def __init__(self, deger, sol=None, sag=None):
        self.deger = deger
        self.sol = sol
        self.sag = sag

def seviye_sayisi(d):
    if d is None:
        return 0
    return 1 + max(seviye_sayisi(d.sol), seviye_sayisi(d.sag))
```

**Adım 6 — Doğrula.** Ağaç `5(3(1, -), 8)`. Düğümleri postorder sırasıyla hesaplayalım:

| düğüm | sol sonuç | sağ sonuç | döndürülen |
|---|---|---|---|
| 1 | 0 | 0 | 1 |
| 3 | 1 | 0 | 2 |
| 8 | 0 | 0 | 1 |
| 5 | 2 | 1 | 3 |

Kökün döndürdüğü değer 3'tür; beklenen cevap budur. Boş ağaç için `seviye_sayisi(None)` 0 döner, bu da taban durumla uyumludur.

**Bunu AI'sız yazabilir misin?** Aynı fonksiyonu, özyineleme kullanmadan, bir kuyrukla (Bölüm 8) seviye seviye ilerleyerek yaz. Hangi durumda iki yöntemin de aynı cevabı verdiğini açıkla.

### Örnek 2 (★★): BST doğrulama

**Problem:** Bir ikili ağacın gerçekten bir BST olup olmadığını kontrol et. Basit bir hata, yalnızca her düğümün çocuğuna bakıp "çocuk küçük mü?" diye sormaktır; bu yeterli değildir.

**Adım 1 — Anla.** Girdi bir ağaç köküdür, çıktı `True` ya da `False`. BST kuralı, her düğüm için sol alt ağacın **tamamının** düğümden küçük ve sağ alt ağacın **tamamının** büyük olmasını ister. Yerel bir kontrol bunu yakalayamaz.

**Adım 2 — Örnekle.** Kökü 8 olan bir ağaçta 8'in sol çocuğu 3, 3'ün sağ çocuğu 10 olsun. 3'ün 10'dan küçük olduğuna bakıp 3'ü kabul edersen yanılırsın, çünkü 10 kökün (8) sol alt ağacında bulunuyor ve 8'den büyük. Kural tüm alt ağaç için geçerli olmalıdır.

**Adım 3 — Kaba çöz.** Her düğüm için sol alt ağacın maksimumunu ve sağ alt ağacın minimumunu hesaplayıp kontrol etmek. Bu, her düğüm için alt ağacın tamamını gezmek demektir: O(n²) gibi görünür.

**Adım 4 — Örüntü.** Her düğüm, atalarından gelen bir **aralık (lo, hi)** içinde olmalıdır. Kök için aralık `(-∞, +∞)`'dir. Sola inerken üst sınır düğümün değeri olur, sağa inerken alt sınır olur. Bu, tek bir gezinmede kontrolü yapmamızı sağlar.

**Adım 5 — İyileştir.** Aralık yaklaşımıyla her düğümü tam bir kez ziyaret ederiz: O(n) zaman ve O(h) bellek.

```python
def bst_mi(d, lo=float("-inf"), hi=float("inf")):
    if d is None:
        return True
    if not (lo < d.deger < hi):
        return False
    return bst_mi(d.sol, lo, d.deger) and bst_mi(d.sag, d.deger, hi)
```

**Adım 6 — Doğrula.** Ağaç `8(3(-, 10), 10)`: kökün sağ çocuğu 10 (geçerli), ama 3'ün sağ çocuğu 10 (geçersiz). Kontrolü izleyelim:

| düğüm | lo | hi | sonuç |
|---|---|---|---|
| 8 | -∞ | +∞ | geçer |
| 3 | -∞ | 8 | geçer |
| 10 (3'ün sağı) | 3 | 8 | 10 < 8 yanlış: False |

Üçüncü satırda `10 < 8` yanlış olduğu için kontrol `False` döner ve `and` zinciri orada durur. Doğru cevap `False`'tur.

**Bunu AI'sız yazabilir misin?** `bst_mi`'yi hiç özyinelemeden, inorder gezinmesinin çıktısının sıralı olup olmadığını kontrol ederek yaz. Hangi yaklaşım daha az bellek kullanır ve neden?

### Örnek 3 (★★): Bir dizide k'ıncı en büyük eleman

**Problem:** `dizi` içindeki elemanlar arasından `k`'ıncı en büyük olanı bul. Örneğin `[3, 2, 1, 5, 6, 4]` ve `k = 2` için cevap 5'tir.

**Adım 1 — Anla.** Girdi bir tamsayı dizisi ve `k`, çıktı bir tamsayı. Kenar durumlar: `k` dizi boyutundan büyük olamaz; tekrarlı elemanlar olabilir.

**Adım 2 — Örnekle.** Diziyi büyükten küçüğe sıralarsak `[6, 5, 4, 3, 2, 1]`; ikinci eleman 5'tir. Ama sıralama O(n log n) yapar ve tüm diziyi gereksiz yere sıralar.

**Adım 3 — Kaba çöz.** Diziyi sıralamak: O(n log n). Daha kötüsü, her seferinde en büyüğü bulup `k` kez tekrarlamak: O(nk).

**Adım 4 — Örüntü.** Yalnızca **en büyük k elemanı** tutmamız yeter. Bu, boyutu `k` olan bir min-heap ile yapılabilir: heap'in kökü, tuttuğumuz `k` elemanın en küçüğüdür. Yeni bir eleman kökten büyükse, kökü atıp yeni elemanı ekleriz.

**Adım 5 — İyileştir.** Heap boyutu `k` ile sınırlı olduğu için her ekleme/değiştirme O(log k)'dir. Toplam O(n log k) zaman ve O(k) bellek.

```python
import heapq

def kinci_en_buyuk(dizi, k):
    yigin = []
    for x in dizi:
        if len(yigin) < k:
            heapq.heappush(yigin, x)
        elif x > yigin[0]:
            heapq.heapreplace(yigin, x)
    return yigin[0]
```

**Adım 6 — Doğrula.** `dizi = [3, 2, 1, 5, 6, 4]`, `k = 2`. Heap'in durumunu izleyelim:

| x | işlem | yığın (dizi) |
|---|---|---|
| 3 | push | [3] |
| 2 | push | [2, 3] |
| 1 | atla (1 ≤ kök 2) | [2, 3] |
| 5 | değiştir (2 çıkar, 5 girer) | [3, 5] |
| 6 | değiştir (3 çıkar, 6 girer) | [5, 6] |
| 4 | atla (4 ≤ kök 5) | [5, 6] |

Sonuçta kök 5'tir ve bu doğru cevaptır. Kodun tam olarak bu çıktıyı verdiği sistemli olarak kontrol edilmiştir.

**Bunu AI'sız yazabilir misin?** Aynı problemi, heapq kullanmadan, 10.7'deki kendi `sift_up` ve `sift_down` fonksiyonlarınla yaz. Sonra `k = 1` için bu çözümün sıradan bir `max` çağrısıyla aynı olduğunu göster.

### Örnek 4 (★★★): İki düğümün en düşük ortak atası (LCA)

**Problem:** Bir ikili ağaçta iki değer `p` ve `q` verildiğinde, her ikisinin de altında yer alan **en düşük** (köke en uzak) düğümü bul. Bu düğüm, `p` ve `q`'nun en düşük ortak atası (Lowest Common Ancestor, LCA) olur. Bir düğüm kendi kendinin atasıdır kabul edilir.

**Adım 1 — Anla.** Girdi bir ağaç, iki değer, çıktı bir düğüm. Bu ağaç bir BST olmak zorunda değil; sıralama bilgisine güvenemeyiz. Kenar durumlar: `p` ya da `q` ağaçta yok; `p` ile `q`'dan biri diğerinin atası olabilir.

**Adım 2 — Örnekle.** Şekil 10.2'deki ağaçta LCA(4, 7) = 6 olmalıdır: 4 ve 7, 6'nın iki çocuğudur. LCA(1, 13) = 8'dir, çünkü 1 sol tarafta, 13 sağ tarafta. Bu örnekler, bir düğümün iki tarafında da `p` ya da `q` varsa o düğümün cevap olduğunu gösteriyor.

**Adım 3 — Kaba çöz.** Her düğüm için `p` ve `q`'nun atalarını bir listeye yaz, sonra iki listede ilk ortak elemanı bul. Bu O(n) bellek ve O(n) zaman kullanır, ama ata listelerini tutmak gerekir.

**Adım 4 — Örüntü.** Postorder gezinmesiyle, her düğüm için sol ve sağ alt ağaçların sonuçlarına bakabiliriz. Bir düğümde: (a) düğüm `p` ya da `q`'ya eşitse, ona döneriz; (b) sol ve sağ alt ağaçların ikisi de bir şey bulduysa, o düğüm LCA'dır; (c) yalnızca birinden sonuç geldiyse onu yukarı taşırız.

**Adım 5 — İyileştir.** Bu tek bir postorder gezinmesidir: her düğüm bir kez ziyaret edilir, ek bellek yalnızca özyineleme yığınıdır. O(n) zaman, O(h) bellek.

```python
def lca(d, p, q):
    if d is None or d.deger in (p, q):
        return d
    sol = lca(d.sol, p, q)
    sag = lca(d.sag, p, q)
    if sol is not None and sag is not None:
        return d
    return sol if sol is not None else sag
```

**Adım 6 — Doğrula.** Şekil 10.2'deki ağaçta `lca(T, 4, 7)` çağrısını izleyelim. Düğümler, ziyaret sırasıyla (postorder) verilmiştir:

| düğüm | eşleşme | sol sonuç | sağ sonuç | döndürülen |
|---|---|---|---|---|
| 4 | p ya da q | - | - | 4 |
| 7 | p ya da q | - | - | 7 |
| 6 | yok | 4 | 7 | 6 (iki taraf dolu) |
| 1 | yok | yok | yok | yok |
| 3 | yok | yok | 6 | 6 |
| 13 | yok | yok | yok | yok |
| 14 | yok | yok | yok | yok |
| 10 | yok | yok | yok | yok |
| 8 | yok | 6 | yok | 6 |

Kökün döndürdüğü 6 doğrudur. Kodun bu sonucu verdiği programla da doğrulanmıştır.

**Bunu AI'sız yazabilir misin?** Ağaç bir BST ise LCA'yı çok daha hızlı bulabilirsin: `p` ve `q` ikisi de kökün solundaysa sola, ikisi de sağındaysa sağa, ayrıldıklarında ise kök cevaptır. Bu yöntemin O(h) olduğunu neden söyleyebildiğini açıkla ve bunun neden genel ikili ağaçta işe yaramadığını düşün.

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Ağaç kodu, özellikle silme ve rotasyon, hatayı ancak elinle yazdığında görünür hâle gelir. Kodu yazmadan "anladım" deme; ilk test başarısız olduğunda ne yapacağını da kendin bul.
:::

### Proje 1 (★★): AVL ağacı kütüphanesi

**Amaç:** 10.6'daki AVL kodunu tam bir kütüphaneye dönüştürmek: ekleme, arama, silme ve dengeyi her işlemden sonra doğrulayan bir test takımı.

**Yapılacak / Beklenen davranış:**

1. `avl_ekle` ve `avl_ara` fonksiyonlarını yaz. Yinelenen anahtarı reddet ve bunu dönüş değeriyle bildir.
2. `avl_sil` fonksiyonunu yaz. Silme, BST silmesi gibi başlar (10.5); ardından yukarı doğru dengeyi düzelt. Silmede bf'nin rotasyon sonrası değişebileceğini unutma.
3. Her işlemden sonra tüm düğümlerin `|bf| ≤ 1` olduğunu ve yüksekliklerin doğru hesaplandığını kontrol eden bir `dogrula` fonksiyonu yaz.
4. 100 000 rastgele tamsayı ile ekleme ve silme yap; sonunda inorder çıktısının sıralı olduğunu doğrula.

**Önerilen yaklaşım:** Rotasyon fonksiyonlarını baştan yazmak yerine 10.6'daki haliyle başla. Silmede en zor kısım, bir alt ağaçtan düğüm çıkınca dengenin hangi yönde bozulduğunu bilmektir; bunu çocukların `bf` değerine bakarak karar verebilirsin. Test için rastgele sayı üretecini sabit bir tohumla (`srand(42)`) başlat ki hatalar tekrarlanabilir olsun.

**Başarı kriterleri:**

- Her testten sonra `dogrula` başarılı; hiçbir düğümde `|bf| > 1` yok.
- 100 000 ekleme sonrası ağacın yüksekliği `1,44 · log2(100000) ≈ 24` sınırının altında.
- WSL2 içinde `-fsanitize=address,undefined` ile hiçbir bellek hatası ya da sızıntı raporu yok.

### Proje 2 (★★★): Trie tabanlı otomatik tamamlama

**Amaç:** Kullanıcının yazdığı önek için, sıklığına göre en olası ilk `k` kelimeyi döndüren bir otomatik tamamlama motoru yazmak.

**Yapılacak / Beklenen davranış:**

1. Her kelimenin bir kullanım sıklığı olsun. `ekle(kelime, sikilik)` ve `ilk_k(onek, k)` fonksiyonlarını yaz.
2. `ilk_k`, önek düğümünü bulduktan sonra alt ağaçtaki tüm kelimeleri topla; sonra en sık `k` tanesini döndür.
3. Büyük bir kelime listesiyle (ör. 50 000 kelime) çalışıp aramanın tek bir önek için ortalama süresini ölç.

**Önerilen yaklaşım:** Tüm alt ağacı toplamak yerine, Örnek 3'teki `k`-elemanlı min-heap fikrini kullan. Alt ağacı gezerken her kelimeyi heap'e at; heap'in boyutu `k`'yı geçerse en küçüğü at. Bu sayede bellek O(k)'da kalır. Bir sonraki adım olarak, sık kullanılan önekler için her düğümde en iyi `k` kelimeyi önceden tutmayı (önbellek) düşünebilirsin; bu, Bölüm 9'daki önbellek fikrine bağlanır.

**Başarı kriterleri:**

- `ilk_k("ev", 3)` gibi bir sorgu, sıklığa göre doğru sıralı üç kelimeyi döndürür; beraberlikte sözlük sırası tutarlıdır.
- Ölçüm tablosu, önek uzunluğu ve sonuç sayısı ile süre arasındaki ilişkiyi gösterir.
- Trie'ın bellek kullanımı kelime listesinin boyutuyla orantılı olarak raporlanır ve bu raporun nedeni açıklanır.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kendin düşün, sonra kodla.

1. ★ Bir ikili ağaçtaki yaprak sayısını özyinelemeli olarak bul. Yaprağın ne olduğunu kodunda tanımla.
2. ★ İki ikili ağacın yapı ve değer olarak aynı olup olmadığını kontrol et.
3. ★★ Bir ikili ağacı ayna görüntüsüne çevir (sol ve sağ çocukları yer değiştir). Bunu hem özyinelemeli hem de yinelemeli yap.
4. ★★ Level-order gezinmesiyle her seviyenin ortalamasını hesapla. (Mülakat)
5. ★★ Sıralı bir diziden yükseklik farkı en fazla bir olan bir BST kur. Ortadaki elemanı kök al. (Mülakat)
6. ★★ Bir BST'de k'ıncı en küçük elemanı, inorder gezinmesini erken durdurarak bul. (Mülakat)
7. ★★ Bir dizide en sık geçen k elemanı, bir heap kullanarak bul. (Mülakat)
8. ★★ k adet sıralı listeyi tek bir sıralı listede birleştir; bir min-heap kullan. (Mülakat)
9. ★★★ Bir ikili ağaçta kökten bir yaprağa giden ve değerleri toplamı verilen sayıya eşit olan bir yol var mı? (Mülakat)
10. ★★★ Bir ikili ağacı diziye (ya da metne) çevir ve bu diziden aynı ağacı geri kur. Boş çocukları bir işaretle temsil et. (Mülakat)
11. ★★★ AVL ağacında silmeden sonra hangi düğümlerde denge bozulabilir? Silinen düğümün yolunu takip ederek, hangi rotasyonların yeterli olduğunu ve neden tek bir yukarı geçişin yetmeyebileceğini açıkla.
12. ★ Bir trie'da kaç farklı kelime saklandığını, düğümlerdeki bayrakları dolaşmadan (ekleme sırasında tuttuğun bir sayaçla) O(1)'de cevaplayacak şekilde değiştir.

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir kaynağı okuyacaksın: CPython 3.12'nin standart kütüphanesindeki `heapq` modülü. Dosya, Python 3.12.10 kurulumunun `Lib\heapq.py` dosyasıdır (`C:\Users\...\Python312\Lib\heapq.py`). Aşağıdaki kesitler kaynaktan birebir alınmıştır; yalnızca yorum satırları çıkarılmıştır, kod satırları değiştirilmemiştir. Yorumlar okunursa kaynağı daha iyi anlayacaksın.

Önce sift-up karşılığı olan `_siftdown`:

```python
def _siftdown(heap, startpos, pos):
    newitem = heap[pos]
    while pos > startpos:
        parentpos = (pos - 1) >> 1
        parent = heap[parentpos]
        if newitem < parent:
            heap[pos] = parent
            pos = parentpos
            continue
        break
    heap[pos] = newitem
```

Dikkat: bu fonksiyon adına rağmen aşağı değil **yukarı** iter. Yeni eleman köke doğru yükseltilir; bu, bizim `sift_up`'ımızdır. CPython geliştiricileri, `heappush` için bu adı seçmiş. Adlandırma kafa karıştırıcı olabilir; kaynağı okurken anlamı ada değil koda bakarak çıkar.

Sonra `_siftup`, bizim `sift_down`'ımızdan farklı bir strateji izler:

```python
def _siftup(heap, pos):
    endpos = len(heap)
    startpos = pos
    newitem = heap[pos]
    childpos = 2*pos + 1
    while childpos < endpos:
        rightpos = childpos + 1
        if rightpos < endpos and not heap[childpos] < heap[rightpos]:
            childpos = rightpos
        heap[pos] = heap[childpos]
        pos = childpos
        childpos = 2*pos + 1
    heap[pos] = newitem
    _siftdown(heap, startpos, pos)
```

Bu fonksiyon, yeni elemanı hemen yerine koymak yerine önce küçük çocukları yukarı çekerek **yaprağa kadar** iner; sonra boşalan yaprağa yeni elemanı koyup `_siftdown` ile yukarı taşır. Bu "alttan yukarı" yöntem, çıkarma sırasında yeni elemanın (son eleman olduğu için genelde büyüktür) genellikle aşağıya kadar ineceğini bildiği için karşılaştırmadan tasarruf eder. Kaynak kodda bu gerekçe ayrıntılı yorumlanmış; burada yalnızca yapıya bakıyoruz.

Son olarak `heapify`:

```python
def heapify(x):
    n = len(x)
    for i in reversed(range(n//2)):
        _siftup(x, i)
```

**Sorular — cevaplamadan geçme:**

1. `_siftdown` içindeki `(pos - 1) >> 1` ifadesi, 10.7'deki hangi formüle eşdeğerdir? Neden `>> 1` kullanmak, bölme işleminden daha hızlı olabilir ve bunun her derleyicide garanti olup olmadığını düşün.
2. `_siftdown`'daki `while` döngüsü, yeni elemanın yukarı taşınması sırasında neden `heap[pos] = parent` yazıp hemen takas yapmıyor? Bu, takas yerine kaç yazma işlemi kazandırır? (İpucu: her takas üç atamadır.)
3. `_siftup` neden `if rightpos < endpos and not heap[childpos] < heap[rightpos]` koşuluyla sağ çocuğu seçiyor? Koşul eşitlik durumunda hangi çocuğu seçer ve bu, kararlılık (stability) hakkında ne söyler?
4. `_siftup` bir yaprağa kadar iner. Bizim `sift_down`'ımız ise yeni elemanın doğru yerini bulunca durur. Bir çıkarma işleminde son elemanın genelde büyük olduğu göz önüne alındığında, hangi yaklaşımın daha az karşılaştırma yapması beklenir ve bunun bir "en kötü durum" garantisi olup olmadığını açıkla.
5. `heapify` döngüsü neden `n//2`'den geriye doğru gidiyor? Dizinin son yarısındaki (yapraklar) elemanların neden sift-down'a ihtiyacı yoktur?
6. Python 3.12 kaynağında `_siftup` ve `_siftdown` dışında `_heapify_max` gibi max-heap yardımcıları da var. Alt çizgiyle başlayan bir adın Python'da ne anlama geldiğini açıkla; bu yardımcıların Python 3.14'te kamuya açılmadan önce neden doğrudan kullanılmaması gerektiğini tartış.

## Bölüm Özeti

Bu bölümde dallanan veri yapılarını öğrendik ve Bölüm 9'daki sıra eksikliğini doldurduk:

- **Ağaç**, döngüsüz ve bağlantılı bir yapıdır; `n` düğümlü ağacın `n - 1` kenarı vardır. Derinlik köke, yükseklik en uzun alt yola olan kenar sayısıdır.
- **Dört gezinme:** inorder, preorder ve postorder yalnızca kökün ziyaret sırasında farklılaşır; level-order ise Bölüm 8'deki kuyrukla seviye seviye ilerler. Yineleme sürümleri için açık yığın kullanılır.
- **BST**, sol alt ağaç < kök < sağ alt ağaç kuralını sağlar. Arama, ekleme ve silme O(h)'dir; silmenin üç durumunda inorder halef kilit rol oynar.
- **Dengesizlik** BST'yi bağlı listeye çevirir ve O(n)'e düşürür; sıralı girdi bu durumun en yaygın nedenidir.
- **AVL**, bf değerini `-1, 0, 1` aralığında tutan dengeli bir BST'dir. Dört rotasyon türü (LL, RR, LR, RL) dengeyi düzeltir ve yükseklik `≈ 1,44 · log2 n` ile sınırlıdır; bu nedenle işlemler O(log n)'dir.
- **Heap**, dizide saklanan tam ikili ağaçtır; çocuklar `2i+1` ve `2i+2`'dir. Sift-up ve sift-down ile ekleme ve çıkarma O(log n)'dir; heapify ise O(n)'dir.
- **Öncelik kuyruğu**, heap ile gerçeklenir; Python'da `heapq` yalnızca min-heap sağlar ve max-heap için sayıları negatife çevirmek gerekir.
- **Trie**, anahtarları karakter karakter saklar; önek sorguları ve otomatik tamamlama için idealdir. Bedeli bellektir.

**Sonraki bölümde:** Ağaçlar, aslında kenarlarla bağlanmış düğümlerin özel bir hâlidir: döngüsüz ve bağlantılı. Bölüm 11'de bu fikri genelleştirip **graph**'a (çizge) geçeceğiz. Döngüler, yönlü ve ağırlıklı kenarlar, komşuluk listesi ile komşuluk matrisi arasındaki farkı ve "ne zaman graph düşünmeliyim?" sorusunun cevabını ele alacağız. Ağacın bir graph olduğunu, graph'ın ise ağaçtan çok daha esnek olduğunu göreceksin.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Bir ikili ağacın yüksekliği ile düğüm sayısı arasındaki ilişki nedir? `n` düğümlü bir ağacın yüksekliği hangi aralıkta olabilir?
2. BST'de silme neden üç ayrı duruma ayrılır? İki çocuklu düğümü silerken neden halef kullanılır, neden doğrudan çocuğu yukarı çekemeyiz?
3. Sıralı bir diziyi BST'ye eklemek neden kötüdür? Bu problemi önlemek için hangi iki yaklaşım kullanılır?
4. AVL ağacında LR durumu neden tek bir rotasyonla düzelmez? Çift rotasyonun iki adımını sen anlat.
5. Heap'in dizi gösterimi neden mümkündür? Bir düğümün çocuklarının indeksini nasıl bulursun ve bu formül neden yalnızca tam ağaçlarda geçerlidir?
6. Heapify neden O(n)'dir? Naif olarak her elemanı tek tek eklemekten neden daha hızlıdır?
7. Öncelik kuyruğunda eşit öncelikli elemanların FIFO sırasını korumak neden ayrı bir çaba gerektirir?
8. Hash tablosu ile trie, önek sorgularında hangi açıdan farklı davranır? Hangi durumda hangisini seçersin ve neden?
:::
