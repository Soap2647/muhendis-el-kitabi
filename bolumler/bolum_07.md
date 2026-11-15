%% kisim_no: III
%% kisim_ad: Veri Yapıları
%% kisim_ayrac: evet
%% bolum_no: 7
%% baslik: Array & Linked List

## Giriş: Veriyi nereye koyacaksın?

Bölüm 5'te bir söz vermiştim: veri yapısı seçimi, "hangisi daha iyi" sorusu değil, **"verime nasıl erişeceğim"** sorusudur. Kısım III boyunca o karar ağacının her dalını tek tek inşa edeceğiz. İlk durak, hepsinin atası olan iki yapı: **dizi** ve **bağlı liste**.

Bunlar basit görünür — biri "yan yana kutular", diğeri "birbirini gösteren düğümler". Ama aralarındaki fark, bilgisayar biliminin en temel ödünleşimini (trade-off) içerir ve bu ödünleşim yukarıya doğru her katmanı etkiler: Python'un `list`'i, C++'ın `vector`'ü, veritabanı indeksleri, dosya sistemleri, hatta `MertOS`'un bellek yöneticisi. İkisini gerçekten anlarsan, üstlerine gelecek her yapı (yığın, kuyruk, hash tablosu, ağaç) çok daha kolay oturur — çünkü hepsi bu ikisinin üzerine kurulur.

Bir de bu bölümde sık atlanan bir gerçeği masaya yatıracağız: **Big-O her şeyi anlatmaz.** Kitaplar "bağlı listede araya ekleme O(1), dizide O(n)" der ve öğrenci "demek ki bağlı liste daha iyi" sonucunu çıkarır. Gerçek dünyada ise dizi neredeyse her zaman kazanır — sebebi Bölüm 25'te ayrıntısıyla göreceğin bellek hiyerarşisidir. Bu bölüm o çelişkiyi çözecek.

::: not
Kısım III'te her veri yapısını üç katmanda göreceksin: **kavram** (nasıl çalışır), **uygulama** (C ile sıfırdan yaz), **karar** (ne zaman kullanılır). Üçü de gerekli. Yalnız kavramı bilen mülakatta tökezler; yalnız kütüphaneyi kullanan performans sorununu çözemez.
:::

## 7.1 Dizi: bitişik belleğin gücü

**Dizi (array)**, aynı türden elemanların bellekte **kesintisiz, yan yana** durduğu yapıdır. Bölüm 2'de tanışmıştın; şimdi neden bu kadar güçlü olduğunu formülüyle görelim.

![Şekil 7.1: Dizinin bellek düzeni ve adres aritmetiği. Elemanlar bitişik olduğu için i'inci elemanın adresi tek bir çarpma-toplamayla hesaplanır. Dizinin O(1) erişimi bu formülden gelir.](gorseller/b07_array.png)

Sihir tek satırda: `&dizi[i] = taban_adres + i × eleman_boyutu`. Bu formül, dizinin **rastgele erişim (random access)** yeteneğinin tamamıdır. `dizi[0]`'a ulaşmak ile `dizi[999999]`'a ulaşmak aynı süreyi alır: bir çarpma, bir toplama, bir bellek okuma. Kaç eleman olduğu hiç fark etmez — **O(1)**.

Bedeli de aynı formülden doğar: *bitişiklik korunmak zorundadır*. Ortadan bir eleman silersen boşluk kalır ve formül bozulur; o yüzden sonrakileri kaydırmak gerekir. Başa eleman eklersen tüm dizi bir sağa kayar. Bu işlemler **O(n)**'dir.

C'de sabit boyutlu dizi, Bölüm 1'in stack segmentinde yaşar:

```c
int notlar[100];              // 400 bayt, yığında (stack)
notlar[42] = 88;              // O(1): adres hesapla, yaz
```

Bunun iki sert kısıtı var. Birincisi **boyut derleme anında sabittir**: 100 yazdıysan 101. öğrenci geldiğinde yapacak bir şey yoktur. İkincisi **stack sınırlıdır** (tipik olarak birkaç MB); `int dev[10000000]` yazarsan program açılır açılmaz çöker. Büyük ve boyutu değişken veriler heap'e taşınır — ve bu bizi 7.3'teki dinamik diziye götürecek.

## 7.2 Bitişikliğin gizli ödülü: cache

Şimdi ders kitaplarının çoğunun atladığı, ama sahada her şeyi belirleyen konuya gelelim.

Bölüm 1'de CPU'nun yazmaçlarını "en hızlı bellek" diye tanıtmıştım. Yazmaçlar ile RAM arasında bir de **önbellek (cache)** katmanı vardır: küçük ama çok hızlı. CPU RAM'den veri isterken tek bir bayt getirmez; **cache satırı (cache line)** denen bir blok — tipik olarak 64 bayt — birden getirir. Mantık şu varsayıma dayanır: *bir adrese eriştiysen, komşularına da erişeceksin.* Buna **uzamsal yerellik (spatial locality)** denir.

Dizi bu varsayımın vücut bulmuş hâlidir. Diziyi baştan sona gezerken, ilk elemanı istediğinde CPU aslında 16 tane `int`'i birden getirir; sonraki 15 erişim **bedavaya** gelir. Şimdi aynı işi atlayarak yaparsan ne olur:

![Şekil 7.2: Uzamsal yerelliğin bedeli. İki döngü de aynı sayıda elemanı toplar — Big-O ikisine de O(n²) der. Ama satır sırayla gezen her cache satırından tam yararlanır; sütun sırayla gezen her erişimde yeni satır getirtir ve getirdiğinin çoğunu çöpe atar.](gorseller/b07_cache.png)

Bunu ölçebilirsin ve ölçmelisin. İki döngü, aynı matris, aynı toplama sayısı:

```c
/* A: satır sırayla — bellek sırasıyla aynı */
for (int i = 0; i < N; i++)
    for (int j = 0; j < N; j++)
        toplam += m[i][j];

/* B: sütun sırayla — her adımda N*4 bayt atlıyor */
for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++)
        toplam += m[i][j];
```

Büyük `N` için B, A'dan donanıma göre değişmekle birlikte çoğu zaman **birkaç kat** yavaştır. Tek bir satırın yerini değiştirdin, kod aynı sonucu veriyor, karmaşıklık aynı — ama program belirgin biçimde yavaşladı. Bu, algoritma analizinin sınırıdır: **Big-O işlem sayısını sayar, o işlemlerin maliyetini eşit varsayar.** Gerçekte bellekten okuma, cache'ten okumaktan çok daha pahalıdır.

**Kendin ölç.** Her iki döngüyü `clock()` (`<time.h>`) ile sarıp geçen süreleri yazdır; `N = 4096` gibi büyük bir değer seç. Bu matris 64 MB tutar, yığına (stack) sığmaz; global ya da `malloc` ile ayır (7.1'deki stack uyarısı). Toplamı mutlaka `printf` ile yazdır: sonucu kullanılmayan bir döngüyü derleyici tamamen silebilir. Farkı hem `-O0` hem `-O2` ile dene; oranı kendi makinende gör.

::: baglanti
Cache hiyerarşisinin tamamı — L1/L2/L3, cache satırı, TLB, zamansal yerellik — **Bölüm 25**'in konusu. Burada bilmen gereken tek şey şu: *bitişik bellek hızlıdır ve bu, Big-O'nun görmediği bir avantajdır.* Bu cümle, 7.8'deki "hangisini seçmeli" kararının merkezinde duracak.
:::

## 7.3 Dinamik dizi: büyüyen bitişiklik

Sabit boyut kısıtını nasıl aşarız? Bölüm 2'de `realloc` ile elle yaptığın şeyi sistemleştirerek: **dinamik dizi (dynamic array)**. Python'da `list`, C++'ta `vector`, Java'da `ArrayList` — hepsi bu yapıdır.

Fikir iki sayıyı ayırmaktır:

- **boyut (size):** şu an kaç eleman var.
- **kapasite (capacity):** kaç eleman için yer ayrılmış.

Ekleme yaparken kapasite yetiyorsa iş basit: elemanı yaz, boyutu artır — **O(1)**. Kapasite dolduysa: daha büyük bir blok ayır, her şeyi kopyala, eskisini bırak — **O(n)**. Kritik soru şudur: *ne kadar büyütmeli?*

### Neden ikiye katlıyoruz: amortize analiz

Naif cevap "her seferinde bir tane daha ekle"dir ve felakettir. Her ekleme kopyalama gerektirir; n ekleme için toplam iş `1 + 2 + 3 + ... + n = n(n+1)/2` yani **O(n²)**. Bin eleman için yarım milyon kopyalama.

Doğru cevap **çarpımsal büyümedir**: kapasiteyi ikiye katla. Şimdi hesabı yapalım, çünkü bu bölümün matematiksel kalbi burası. n eleman eklerken kopyalamalar yalnız 2'nin kuvvetlerinde olur ve toplam kopyalama sayısı:

`1 + 2 + 4 + 8 + ... + n/2 + n < 2n`

Geometrik seri, son terimin iki katını aşmaz. Yani **n ekleme için toplam iş 3n mertebesindedir** (n yazma + 2n'den az kopyalama). Ekleme *başına* düşen ortalama iş: sabit.

![Şekil 7.3: Amortize O(1)'in anatomisi. Solda tek tek ekleme maliyeti: çoğu ekleme 1 birim, 2'nin kuvvetlerinde sivri kopyalama uçları. Sağda kümülatif ortalama: sivri uçlara rağmen ekleme başına ortalama maliyet ~3'te sabitleniyor.](gorseller/b07_growth.png)

Buna **amortize (itfa edilmiş) O(1)** denir ve dikkatli bir ifadedir: *tek bir* eklemenin O(n) sürebileceğini kabul eder, ama *uzun vadede ortalamanın* sabit olduğunu söyler. Restoran benzetmesi: her gün 10 lira yemek yiyorsun ama ayda bir 300 liralık aidat ödüyorsun; günlük ortalaman yine de sabittir.

Bölüm 3'te CPython'un `list_resize` kaynağını okumuştuk; hatırla, oradaki büyüme `newsize + (newsize >> 3) + 6` idi — yani **%12.5 büyüme**. Neden 2 değil? Çünkü ödünleşim iki uçludur:

| Büyüme çarpanı | Kopyalama sıklığı | Boşa giden bellek |
|---|---|---|
| ×2 (libstdc++ vector) | Az | En kötü ihtimalle %50 |
| ×1.5 (Java ArrayList, MSVC vector) | Orta | Daha az |
| ×1.125 (CPython) | Daha sık | Çok az |

Hangisinin doğru olduğu, ne için optimize ettiğine bağlıdır. Python milyonlarca küçük liste tutar; belleği israf etmemek, birkaç kopyalamadan daha önemlidir. C++ `vector` genelde büyük ve performans kritik verilerde kullanılır; hız önceliklidir. **İkisi de doğru** — farklı kısıtlara verilmiş farklı cevaplar.

::: dikkat
Dinamik dizide büyüme, elemanların **adreslerini değiştirir**. Bir elemanın adresini (ya da C++'ta bir iterator'ü) saklayıp sonra `push_back` çağırırsan, sakladığın işaretçi sarkan (dangling) hâle gelir — Bölüm 2'nin klasik hatası, yeni kılıkta. Bu yüzden dinamik dizilerde işaretçi değil **indeks** sakla.
:::

## 7.4 Bağlı liste: dağınık düğümler

Bağlı liste tam ters felsefeyi benimser: bitişikliği tümden bırakır. Her eleman kendi başına bir **düğümdür (node)**; veriyi ve bir sonrakinin adresini tutar. Elemanlar bellekte nerede olursa olsun, zincir işaretçilerle kurulur.

```c
typedef struct Dugum {
    int veri;
    struct Dugum *sonraki;    /* zincirin halkası */
} Dugum;
```

Bunun bedeli hemen görünür: `liste[500]`'e ulaşmak için baştan başlayıp 500 adım yürümen gerekir — **O(n) erişim**. Adres formülü yoktur, çünkü bitişiklik yoktur. Ayrıca her eleman için fazladan bir işaretçi (64-bit sistemde 8 bayt) ödersin. Hizalama (Bölüm 2.7'deki dolgu) yüzünden 64-bit sistemde bir düğüm 16 bayt tutar: 4 bayt `int`, 4 bayt dolgu, 8 bayt işaretçi. Yani 4 baytlık bir `int` listesi, verinin **4 katı** bellek tüketir; üstüne `malloc`'un her blok için tuttuğu yönetim başlığı genellikle eklenir.

Karşılığında ne kazanırsın? **Yapısal esneklik.** Araya eleman eklemek ya da silmek, hiçbir şeyi kaydırmadan, yalnız birkaç işaretçiyi değiştirerek yapılır:

![Şekil 7.4: Bağlı listede araya ekleme — işaretçi cerrahisi. Kritik nokta sıradır: önce yeni düğümün `sonraki`'si bağlanır, sonra önceki düğümün işaretçisi yeni düğüme çevrilir. Ters sırada yapılırsa listenin kuyruğuna giden tek bağ kopar ve o kısım kaybolur.](gorseller/b07_insert.png)

Temel işlemleri yazalım. Başa ekleme, bağlı listenin en parlak anıdır — dizide O(n) olan iş burada O(1):

```c
Dugum *basa_ekle(Dugum *bas, int deger) {
    Dugum *yeni = malloc(sizeof(Dugum));
    if (!yeni) return bas;             /* bellek yoksa dokunma */
    yeni->veri = deger;
    yeni->sonraki = bas;               /* 1) yeniyi bağla */
    return yeni;                       /* 2) yeni baş bu */
}
```

Araya ekleme, Şekil 7.4'teki sırayı harfiyen uygular:

```c
void sonrasina_ekle(Dugum *once, int deger) {
    if (!once) return;
    Dugum *yeni = malloc(sizeof(Dugum));
    if (!yeni) return;
    yeni->veri = deger;
    yeni->sonraki = once->sonraki;     /* 1) ÖNCE bağla */
    once->sonraki = yeni;              /* 2) SONRA kopar */
}
```

Silme ise önceki düğümü gerektirir — tek yönlü listenin en can sıkıcı yanı:

```c
void sonrasini_sil(Dugum *once) {
    if (!once || !once->sonraki) return;
    Dugum *gidecek = once->sonraki;
    once->sonraki = gidecek->sonraki;  /* zinciri köprüle */
    free(gidecek);                     /* sonra serbest bırak */
}
```

Bu üç fonksiyon, bağlı listelerin klasik hata üçlüsünü de gösteriyor: **(1)** `NULL` kontrolünü atlamak, **(2)** işaretçileri yanlış sırada değiştirip zinciri kaybetmek, **(3)** düğümü `free` etmeyi unutup sızıntı yaratmak ya da `free` sonrası hâlâ okumak (Bölüm 2'nin sarkan işaretçisi). Bölüm 6'nın araçları burada iş başında: bir bağlı liste kodunu valgrind/ASan olmadan yazmak, gözü kapalı ameliyat yapmaktır.

Bir uyarı daha: "araya ekleme O(1)" ifadesi eksiktir. Doğrusu şudur: **eklenecek yerin bir öncesindeki düğüm elindeyse O(1)**. Değilse önce onu bulman gerekir ve arama O(n)'dir. Mülakatta bu ayrımı yapabilmek, ezberle anlamayı ayıran çizgidir.

## 7.5 Nöbetçi düğüm: kenar durumu tasarımla yok etmek

Yukarıdaki kodda bir rahatsızlık var: baş düğüm hep özel muamele istiyor. `basa_ekle` yeni bir baş döndürmek zorunda, silme fonksiyonu "silinen baş mıydı?" diye ayrı bir dal istiyor. Bölüm 6'da öğrendik ki **her özel durum, bir hata yuvasıdır**.

Zarif çözüm: listenin başına **veri taşımayan sahte bir düğüm** koymak. Buna **nöbetçi (sentinel)** ya da *dummy head* denir:

![Şekil 7.5: Nöbetçi düğüm. Solda nöbetçisiz liste: "boş mu?" ve "baş mı değişiyor?" kontrolleri her fonksiyona sızar. Sağda nöbetçili liste: gerçek verinin öncesinde her zaman bir düğüm olduğu için, tüm işlemler tek bir kod yolundan geçer.](gorseller/b07_sentinel.png)

Nöbetçiyle silme fonksiyonu tek yola iner ve `if` zinciri kaybolur:

```c
/* nobetci->sonraki gerçek listenin başıdır */
void deger_sil(Dugum *nobetci, int deger) {
    Dugum *p = nobetci;                /* baş özel durumu YOK */
    while (p->sonraki) {
        if (p->sonraki->veri == deger) {
            Dugum *gidecek = p->sonraki;
            p->sonraki = gidecek->sonraki;
            free(gidecek);
            return;
        }
        p = p->sonraki;
    }
}
```

Karşılaştır: nöbetçisiz sürümde "baş silinecekse `bas`'ı güncelle, değilse öncekini bul" diye iki ayrı dal yazman gerekirdi. Bir düğümlük bellek harcayarak bir sınıf hatayı ortadan kaldırdın. Bu, veri yapısı tasarımının genel bir ilkesidir: **kodu düzeltmek yerine, hatanın var olamayacağı bir yapı kur.**

## 7.6 Çift yönlü ve dairesel listeler

Tek yönlü listenin iki eksiği vardı: geriye gidememek ve silme için önceki düğüme muhtaç olmak. İkisini de çözen varyantlar var.

![Şekil 7.6: İki varyant. Çift yönlü listede her düğüm hem sonrakini hem öncekini tutar; elindeki bir düğümü, listeyi hiç taramadan O(1)'de silebilirsin. Dairesel listede son düğüm başa döner; NULL yoktur, gezinme sonsuza dek sürebilir.](gorseller/b07_doubly.png)

**Çift yönlü liste (doubly linked list)** her düğüme bir `onceki` işaretçisi ekler:

```c
typedef struct DDugum {
    int veri;
    struct DDugum *onceki, *sonraki;
} DDugum;

void dugumu_sil(DDugum *d) {           /* d elimizde: O(1) */
    if (d->onceki) d->onceki->sonraki = d->sonraki;
    if (d->sonraki) d->sonraki->onceki = d->onceki;
    free(d);
}
```

Araya ekleme de aynı mantıkla yazılır. Dört işaretçi değişir ve sıra yine Şekil 7.4'ün ilkesine uyar: önce yeni düğüm bağlanır, sonra çevrilir:

```c
void sonrasina_ekle(DDugum *once, int deger) {
    if (!once) return;
    DDugum *yeni = malloc(sizeof(DDugum));
    if (!yeni) return;
    yeni->veri = deger;
    yeni->onceki = once;               /* 1) yeni, geri bağlanır */
    yeni->sonraki = once->sonraki;     /* 2) ve ileri bağlanır */
    if (once->sonraki)
        once->sonraki->onceki = yeni;  /* 3) ileridekine geri bağ */
    once->sonraki = yeni;              /* 4) öndekine ileri bağ */
}
```

Bedeli düğüm başına fazladan 8 bayt ve her işlemde iki kat işaretçi bakımıdır. Ödülü, "elimdeki düğümü sil" işleminin gerçekten O(1) olmasıdır — ve bu, çok işe yarar. En bilinen örneği **LRU önbelleğidir**: hash tablosu (Bölüm 9) düğüme O(1) erişim verir, çift yönlü liste o düğümü listeden koparıp başa taşımayı O(1) yapar. İkisi birlikte, Bölüm 5'in "yapıları birleştir" ilkesinin en zarif örneğidir.

**Dairesel liste (circular linked list)** ise son düğümü başa bağlar. `NULL` diye bir uç yoktur. Sırayla dönen işler için doğaldır: işletim sisteminin round-robin zamanlayıcısı (Bölüm 26), müzik çalarda "tekrarla" modu, çok oyunculu bir oyunda sıra dağıtımı. Bir sonraki adım hep `p = p->sonraki`'dir; ama `NULL` ucu olmadığı için "liste bitti" diyecek bir koşul da yoktur. Tüm listeyi bir kez gezmek için başlangıç düğümünü (`bas`) referans alır ve ona geri döndüğümüzde dururuz. Bu yüzden döngü `while` yerine `do ... while` ile yazılır: ilk adım her zaman atılır, kontrol sonra yapılır. Bu koşulu unutursan döngü sonsuza kadar döner:

```c
int dairesel_say(Dugum *bas) {
    if (!bas) return 0;            /* boş liste */
    int n = 0;
    Dugum *p = bas;
    do {
        n++;
        p = p->sonraki;
    } while (p != bas);            /* başa döndük: dur */
    return n;
}
```

Boş liste `NULL` ile temsil edildiği için ilk satır onu ayırır. Tek düğüm kendine bağlıysa döngü bir kez döner ve `1` sonucunu verir.

## 7.7 Dairesel tampon: iki dünyanın en iyisi

Şimdi gömülü sistemlerin ve `MertOS`'un en çok kullandığı yapıya geldik. **Dairesel tampon (ring buffer / circular buffer)**, sabit boyutlu bir *dizi* üzerinde dairesel liste davranışını taklit eder — bellek ayırmadan.

![Şekil 7.7: Dairesel tampon. Sabit bir dizi ve iki indeks: baş (okunacak yer) ve kuyruk (yazılacak yer). İndeksler dizinin sonuna gelince modülo işlemiyle başa sarar. Bellek ayırma ve kaydırma olmadığı için ekleme ve çıkarma O(1)'dir.](gorseller/b07_ring.png)

Sırrı Bölüm 2'de tanıştığın `%` operatöründe:

```c
#define BOYUT 64              /* fiziksel hücre sayısı */

typedef struct {
    char veri[BOYUT];
    volatile unsigned bas;    /* yalnız TÜKETİCİ yazar */
    volatile unsigned kuyruk; /* yalnız ÜRETİCİ yazar */
} Tampon;                     /* ilk değerler 0 olsun */

/* ÜRETİCİ (örn. kesme işleyicisi) */
int yaz(Tampon *t, char c) {
    unsigned sonraki = (t->kuyruk + 1) % BOYUT;
    if (sonraki == t->bas) return 0;   /* dolu */
    t->veri[t->kuyruk] = c;
    t->kuyruk = sonraki;               /* veriyi yazdıktan SONRA */
    return 1;
}

/* TÜKETİCİ (örn. çekirdek döngüsü) */
int oku(Tampon *t, char *c) {
    if (t->bas == t->kuyruk) return 0; /* boş */
    *c = t->veri[t->bas];
    t->bas = (t->bas + 1) % BOYUT;     /* okuduktan SONRA */
    return 1;
}
```

Bu yapı neden gömülü dünyanın vazgeçilmezi? Üç sebepten: **çalışma anında bellek ayırmaz** (kesme işleyicisi içinde `malloc` çağıramazsın — Bölüm 44), **kaydırma yapmaz** (dizinin O(n) silme derdi yok), ve **boyutu öngörülebilir** (gerçek zamanlı sistemlerde belirsizlik düşmandır).

Karşılaşacağın her yerde aynı desen: klavye tuş tamponu (`MertOS`'ta yazdığın), UART alım tamponu (Bölüm 45), ses/video akış tamponları, ağ paket kuyrukları, üretici-tüketici problemi (Bölüm 27).

Burada gizli bir tuzak var. Akla ilk gelen tasarım bir `adet` sayacı tutmaktır; ama bu sayacı hem üretici (kesme) hem tüketici güncelliyor. `adet++` tek satır görünse de işlemci genelde üç adım çalıştırır: oku, artır, yaz. Kesme bu üç adımın ortasında gelirse iki taraf da aynı eski değeri okur ve bir güncelleme kaybolur. Buna **yarış koşulu (race condition)** denir; hata nadirdir, bu yüzden testte yakalanması zordur.

Tek üretici ve tek tüketici varsayımında güvenli tasarım sayacı bırakıp yalnız iki indeksi tutar: `kuyruk` yalnız üreticinin, `bas` yalnız tüketicinin yazdığı alandır. Dolu ile boşu ayırmak için bir hücre hep boş bırakılır; bu yüzden kapasite `BOYUT - 1`'dir. Yukarıdaki kod bu tasarımdır.

Dikkat: bu güvence yalnız tek üretici ve tek tüketici için geçerlidir; ikinci bir üretici eklersen yapı bozulur. Ayrıca `volatile` derleyiciye "bu değer başka yerden değişebilir" der ve her okumayı bellekten yaptırır; ama işlemcinin ve derleyicinin bellek işlemlerini yeniden sıralamasına karşı garanti vermez. Çok çekirdekli sistemlerde C11 `_Atomic` türleri gerekir. Tek çekirdekli bir MCU'da kesme ile ana döngü arasında `volatile` pratikte çoğu zaman yeterlidir; ama bu bir garanti değildir. Bellek sıralaması ve kilitsiz programlamanın tam resmi Bölüm 27'nin konusudur. Bu ayrıntı, gömülü mülakatlarının favori sorularındandır.

## 7.8 Karar: hangisi, ne zaman?

Şimdi hepsini bir tabloda toplayalım. `n` eleman sayısı olmak üzere:

| İşlem | Dizi / dinamik dizi | Bağlı liste |
|---|---|---|
| `i`'inci elemana erişim | **O(1)** | O(n) |
| Arama (sırasız) | O(n) | O(n) |
| Sona ekleme | O(1)* amortize | O(1) (kuyruk elindeyse) |
| Başa ekleme | O(n) | **O(1)** |
| Ortaya ekleme (yer biliniyor) | O(n) | **O(1)** |
| Ortadan silme (düğüm elinde) | O(n) | **O(1)** (çift yönlüyse) |
| Bellek ek yükü | Yok (kapasite fazlası) | Eleman başına 8-16 bayt |
| Cache davranışı | **Mükemmel** | Kötü |
| Adres kararlılığı | Büyümede bozulur | Kalıcı |

Tabloya bakıp "bağlı liste ekleme/silmede kazanıyor" demek kolay. Ama pratikte **dizi neredeyse her zaman kazanır** ve sebebini artık biliyorsun: 7.2'deki cache gerçeği.

Düşün: bağlı listede araya ekleme O(1) ama *o yeri bulmak* için O(n) yürümen gerekir ve bu yürüyüşün her adımı bellekte rastgele bir sıçramadır — her düğüm ayrı bir cache ıskası. Dizide ise arama O(n)'dir ama bu tarama bellekte doğrusal ve cache dostudur; ardından yapılan kaydırma da öyle. Sonuç: on binlerce elemana kadar, `vector`'e ortadan ekleme, `list`'e ortadan eklemeden **daha hızlıdır**. C++'ın yaratıcısı Bjarne Stroustrup bu ölçümü ünlü bir konuşmada gösterdikten sonra, "bağlı liste kullanmayın" tavsiyesi sektörde yaygınlaştı.

O hâlde bağlı liste ne zaman doğru seçim? Dürüst liste kısadır ama gerçektir:

- **Düğüm işaretçileri kalıcı olmalıysa.** Dizinin büyümesi adresleri bozar; bağlı listede bir düğümün adresi ömrü boyunca sabittir. Çekirdek kodunun bağlı listeyi sevmesinin baş sebebi budur.
- **Araya alma/çıkarma (splice) çok sıksa ve konum zaten elindeyse.** LRU önbelleği, zamanlayıcı kuyrukları, oyun motorlarındaki nesne listeleri.
- **Girişken (intrusive) yapı gerektiğinde.** Nesnenin kendisi düğüm alanını içerir; ayrıca bellek ayırmaya gerek kalmaz — Linux çekirdeğinin tüm listeleri böyledir ve Kod Okuma egzersizinde bunu göreceksin.
- **Bellek parçalıysa ya da tek büyük blok ayrılamıyorsa.** Gömülü sistemlerde 1 MB bitişik blok bulmak, 1000 tane 1 KB blok bulmaktan zor olabilir.

Genel kural olarak şunu aklında tut: **varsayılanın dizi olsun; bağlı listeyi gerekçeyle seç.** Ve gerekçeni yazarken Bölüm 5'in dersini hatırla — gerekçe "Big-O'da daha iyi görünüyor" değil, ölçüme ya da somut bir kısıta dayanmalı.

## Çözümlü Örnekler

### Örnek 1 (★): Sıralı diziden tekrarları yerinde silmek

**Problem:** Sıralı bir dizide tekrar eden elemanları, **ek dizi kullanmadan** (yerinde) sil ve kalan eleman sayısını döndür. `[1,1,2,2,2,3]` → `[1,2,3]`, dönüş `3`.

**Adım 1 — Anla.** Girdi sıralı — bu bedava bilgi, tekrarlar bitişik demek. Yerinde çalışacağız, yani dizinin ilk `k` elemanı sonuç olacak; gerisi umurumuzda değil.

**Adım 2 — Örnekle.** Kenar durumlar: boş dizi (`0` dönmeli), tek eleman (`1`), hepsi aynı (`1`). Asıl örneği Adım 6'da elle izleyeceğiz.

**Adım 3 — Kaba çöz.** Kaba kuvvet: her tekrarı bulunca sonrakileri sola kaydır — her kaydırma O(n), toplam O(n²).

**Adım 4 — Örüntü.** Sıralı dizi + yerinde düzenleme → **iki işaretçi**. Ama burada işaretçiler uçlardan değil, ikisi de soldan sağa gider: biri *okur*, biri *yazar*.

**Adım 5 — İyileştir.** `yaz` bir sonraki benzersiz elemanın konumu; `oku` diziyi tarar. Yeni bir değer görünce yazıp `yaz`'ı ilerletiriz:

```c
int tekrarlari_sil(int *dizi, int n) {
    if (n == 0) return 0;
    int yaz = 1;                       /* ilk eleman hep kalır */
    for (int oku = 1; oku < n; oku++) {
        if (dizi[oku] != dizi[yaz - 1]) {   /* yeni değer mi? */
            dizi[yaz] = dizi[oku];
            yaz++;
        }
    }
    return yaz;
}
```

**Adım 6 — Doğrula.** `[1,1,2,2,2,3]` üzerinde iz sürelim:

| oku | dizi[oku] | dizi[yaz−1] | yeni mi? | dizi (baş kısmı) | yaz |
|---|---|---|---|---|---|
| 1 | 1 | 1 | hayır | 1,1,2,2,2,3 | 1 |
| 2 | 2 | 1 | evet | 1,**2**,2,2,2,3 | 2 |
| 3 | 2 | 2 | hayır | — | 2 |
| 4 | 2 | 2 | hayır | — | 2 |
| 5 | 3 | 2 | evet | 1,2,**3**,2,2,3 | 3 |

Dönüş `3`, dizinin ilk üç elemanı `1,2,3`. Doğru. Boş dizi: `0` döner. Tek eleman: döngüye girmez, `1` döner. Karmaşıklık: tek geçiş **O(n)** zaman, **O(1)** ek bellek — ve tarama tamamen cache dostu.

**Bunu AI'sız yazabilir misin?** Değiştir: her elemandan *en fazla iki tane* kalsın (`[1,1,1,2]` → `[1,1,2]`). Hangi satır değişir? (İpucu: `dizi[yaz-1]` yerine hangi karşılaştırma?)

### Örnek 2 (★★): Kendi dinamik dizin

**Problem:** C'de `push_back` yapabilen, kapasitesini ikiye katlayarak büyüyen bir dinamik dizi yaz. Sonra amortize davranışı gerçekten ölç.

**Adım 1 — Anla.** Dinamik dizinin iki sayısı var: `boyut` (şu an kaç eleman) ve `kapasite` (kaç eleman için yer ayrılmış). Ekleme sırasında dolulukta büyütme yapılacak; amacımız hem doğru çalışmak hem de amortize davranışı ölçmek.

**Adım 2 — Örnekle.** Kapasite 0 iken ilk eleman için blok ayrılır; sonraki üç eleman aynı bloğa yazılır, beşincide blok yine dolar ve büyür. Bu iz Adım 6'da tabloda izlenecek.

**Adım 3 — Kaba çöz.** Her ekleme kapasiteyi yalnız bir artırsa, n ekleme n kopyalama gerektirir; toplam `1 + 2 + ... + n`, yani O(n²) olur.

**Adım 4 — Örüntü.** Kapasiteyi ikiye katlarsak kopyalamalar yalnız 2'nin kuvvetlerinde olur; 7.3'teki geometrik seri toplamı `2n`'in altında tutar. Örüntü: seyrek ama büyük büyütme.

**Adım 5 — İyileştir.** Büyütme sırasında hata olursa elindeki blok kaybolmamalı. Bölüm 2 Örnek 3'ün dersini hatırla: `realloc` sonucu **geçici işaretçiye** alınmalı; başarısızlıkta eski blok sağlam kalır. Son hâli şöyle:

```c
typedef struct {
    int *veri;
    size_t boyut, kapasite;
    size_t kopyalama;          /* ölçüm için: toplam kopyalanan */
} Dizi;

void dizi_baslat(Dizi *d) {
    d->veri = NULL;
    d->boyut = d->kapasite = d->kopyalama = 0;
}

int dizi_ekle(Dizi *d, int deger) {
    if (d->boyut == d->kapasite) {              /* doldu: büyüt */
        size_t yeni_kap = d->kapasite ? d->kapasite * 2 : 4;
        int *yeni = realloc(d->veri, yeni_kap * sizeof(int));
        if (!yeni) return 0;                    /* eski blok sağlam */
        d->kopyalama += d->boyut;               /* n eleman taşındı */
        d->veri = yeni;
        d->kapasite = yeni_kap;
    }
    d->veri[d->boyut++] = deger;
    return 1;
}

void dizi_bitir(Dizi *d) {
    free(d->veri);
    dizi_baslat(d);
}
```

**Adım 6 — Doğrula.** Önce elle izleyelim. Kapasite 0 ile başlayıp beş ekleme yapıyoruz:

| ekleme | boyut (öncesi) | kapasite (öncesi) | büyüme? | kopyalama (toplam) | boyut (sonrası) |
|---|---|---|---|---|---|
| 1 | 0 | 0 | evet → 4 | 0 | 1 |
| 2 | 1 | 4 | hayır | 0 | 2 |
| 3 | 2 | 4 | hayır | 0 | 3 |
| 4 | 3 | 4 | hayır | 0 | 4 |
| 5 | 4 | 4 | evet → 8 | 4 | 5 |

Beşinci eklemede `boyut == kapasite` olduğu için 4 eleman taşınır: kopyalama 4, `2n = 10`'un altında. Şimdi aynı yapıyı bir milyon eleman için ölçelim. Ölçüm kodu Adım 5'teki kütüphanenin altına gelir; dosyanın başına `#include <stdio.h>` ve `#include <stdlib.h>` ekle:

```c
int main(void) {
    Dizi d;
    dizi_baslat(&d);
    for (int i = 0; i < 1000000; i++)
        dizi_ekle(&d, i);
    printf("1000000 ekleme sonrası:\n");
    printf("  kapasite   : %zu\n", d.kapasite);
    printf("  kopyalama  : %zu\n", d.kopyalama);
    printf("  ekleme başına ortalama: %.2f kopyalama\n",
           (double)d.kopyalama / 1000000);
    dizi_bitir(&d);
    return 0;
}
```

```term
$ ./dinamik_dizi
1000000 ekleme sonrası:
  kapasite   : 1048576
  kopyalama  : 1048572
  ekleme başına ortalama: 1.05 kopyalama
```

Kopyalama toplamı `4 + 8 + ... + 524288 = 1048572`; bu, `n`'in yaklaşık 1.05 katı ve `2n` sınırının çok altında. Ekleme başına ortalama sabit kalıyor: amortize O(1). Şimdi büyütme satırını `d->kapasite + 1` yapıp `n = 100000` ile tekrar dene; kopyalama sayısının yaklaşık `n²/2 = 5·10⁹` civarına fırladığını göreceksin. (`n = 10⁶` ile bu deney çok uzun sürer.) Aradaki fark, "çarpımsal büyüme" kararının tek satırlık ama devasa etkisidir.

**Bunu AI'sız yazabilir misin?** İki ek işlev tasarla: `dizi_sil(d, i)` (i'inci elemanı sil) ve `dizi_kucult(d)` (çok boşaldıysa kapasiteyi yarıya indir). İkincisinde bir tuzak var: kapasite tam yarıda küçültülürse, sınırda gidip gelen ekle/sil çağrıları her seferinde kopyalama tetikler ("çırpınma"). Nasıl önlersin? (İpucu: küçültme eşiğini büyütme eşiğinden farklı seç.)

### Örnek 3 (★★): Bağlı listeyi tersine çevir

**Problem:** Tek yönlü bir bağlı listeyi, yeni düğüm oluşturmadan, yerinde tersine çevir. `10→20→30→NULL` olsun `30→20→10→NULL`.

Bu, mülakat tarihinin en klasik sorusudur ve işaretçi düşüncesini ölçer.

**Adım 1 — Anla.** Liste bir zincir ve düğümler bellekte dağınık. Yeni düğüm ayırmak yasak; yalnız işaretçileri değiştireceğiz. Hedef: `10→20→30→NULL` zincirini `30→20→10→NULL`'a çevirmek.

**Adım 2 — Örnekle.** Elle yapalım: `10`'un `sonraki`'si `20` yerine `NULL` olmalı; `20`'ninki `10`; `30`'unki `20`. Yani her düğümün oku *geriye* dönecek. Ama bir düğümün okunu çevirdiğim an, ileriye gitme yolumu kaybediyorum — demek ki **çevirmeden önce sonrakini bir yerde saklamalıyım.**

**Adım 3 — Kaba çöz.** Düğümleri bir diziye kopyalayıp tersten yeniden bağlamak çalışır; ama O(n) ek bellek ister. Biz yerinde çözüm arıyoruz.

**Adım 4 — Örüntü.** Üç işaretçiyle yürüyoruz: `onceki` (arkada bıraktığım), `simdiki` (üzerinde çalıştığım), `ileri` (kaybetmemek için sakladığım).

**Adım 5 — İyileştir.** Bu desenle yerinde ters çevirme:

```c
Dugum *ters_cevir(Dugum *bas) {
    Dugum *onceki = NULL;
    Dugum *simdiki = bas;
    while (simdiki) {
        Dugum *ileri = simdiki->sonraki;  /* 1) yolu sakla */
        simdiki->sonraki = onceki;        /* 2) oku çevir */
        onceki = simdiki;                 /* 3) ilerle */
        simdiki = ileri;
    }
    return onceki;                        /* yeni baş */
}
```

**Adım 6 — Doğrula.** `10→20→30` üzerinde:

| tur | onceki | simdiki | ileri | işlem sonrası zincir |
|---|---|---|---|---|
| 1 | NULL | 10 | 20 | 10→NULL |
| 2 | 10 | 20 | 30 | 20→10→NULL |
| 3 | 20 | 30 | NULL | 30→20→10→NULL |
| son | 30 | NULL | — | `onceki` = yeni baş |

Kenar durumlar: boş liste (`bas == NULL`) → döngüye girmez, `NULL` döner; tek düğüm → bir tur döner, aynı düğüm baş kalır. İkisi de doğru — ve dikkat et, **hiçbir özel `if` yazmadık**; döngünün yapısı kenar durumları kendiliğinden karşılıyor. İyi bir işaretçi kodunun imzası budur. Karmaşıklık: **O(n) zaman, O(1) bellek.**

**Bunu AI'sız yazabilir misin?** Aynı işi özyinelemeli (recursive) yaz. Sonra sor: özyinelemeli sürüm 1 milyon düğümlük listede ne olur? (İpucu: Bölüm 1'deki stack segmenti ve Bölüm 15'in konusu.)

### Örnek 4 (★★★): Döngü tespiti — tavşan ve kaplumbağa

**Problem:** Bir bağlı listede döngü olup olmadığını **O(1) ek bellekle** tespit et. (Döngü varsa liste sonsuza kadar dolaşır; naif bir `while (p) p = p->sonraki;` asla bitmez.)

**Adım 1 — Anla.** Döngü varsa liste sonsuza dek dolaşır; naif `while (p)` asla bitmez. Görev, döngünün varlığını **O(1) ek bellekle** söylemek.

**Adım 2 — Örnekle.** Şöyle bir liste düşünelim: `1→2→3→4`, sonra `4`'ten `2`'ye dönüyor. Döngü `2`'de başlar ve uzunluğu `3`'tür. Bu örneği Adım 6'da izleyeceğiz.

**Adım 3 — Kaba çöz.** Kaba çözüm kolay: gördüğün her düğümü bir kümede (hash set) tut; tekrar görürsen döngü var. O(n) zaman ama **O(n) bellek**. Problem bize O(1) bellek dayatıyor, yani "gördüklerimi saklama" fikri elenmiş oluyor. Yeni bir açı gerekiyor.

**Adım 4 — Örüntü.** Bölüm 5'in iki işaretçi deseni, burada farklı bir biçimde beliriyor: iki işaretçi **farklı hızlarda** ilerlesin. Sezgi bir yarış pistinden gelir: pist kapalı (döngü) ise, hızlı koşan yavaşı er ya da geç *tur bindirerek* yakalar. Pist açık uçlu ise hızlı olan sondan çıkar ve buluşma hiç olmaz.

**Adım 5 — İyileştir.** Kaplumbağa bir adım, tavşan iki adım atar:

```c
int dongu_var_mi(Dugum *bas) {
    Dugum *yavas = bas, *hizli = bas;
    while (hizli && hizli->sonraki) {
        yavas = yavas->sonraki;            /* 1 adım */
        hizli = hizli->sonraki->sonraki;   /* 2 adım */
        if (yavas == hizli) return 1;      /* karşılaştılar */
    }
    return 0;                              /* hizli sona ulaştı */
}
```

**Adım 6 — Doğrula.** Önce örneğimizi elle izleyelim:

| tur | yavas | hizli | eşit mi? |
|---|---|---|---|
| 0 | 1 | 1 | (kontrol yok) |
| 1 | 2 | 3 | hayır |
| 2 | 3 | 2 | hayır |
| 3 | 4 | 4 | **evet → döngü var** |

Tur 0 yalnızca başlangıç durumudur; kontrol ilk ilerlemeden sonra yapılır. Tur 3'te `hizli` iki adım atarak `2 → 3 → 4` yolunu izler ve `yavas` ile aynı düğümde buluşur. Döngüsüz `1→2→3→NULL` listesinde ise `hizli` tur 1'de `3`'e ulaşır; `3`'ün sonrası `NULL` olduğu için `while` koşulu bozulur ve `0` döner.

**Neden çalışıyor?** Ezberlememen için kanıt eskizini görelim. Döngü varsa her iki işaretçi de sonunda döngünün içine girer. Girdikten sonra aralarındaki mesafeye `d` diyelim (döngü uzunluğu `L` modunda). Her turda hızlı 2, yavaş 1 ilerlediğinden **aralarındaki fark her adımda tam olarak 1 azalır**. 1'er azalan bir mesafe eninde sonunda 0 olur — yani buluşurlar, hem de en fazla `L` adımda. Döngü yoksa hızlı olan `NULL`'a çarpar ve döngü biter.

Bu, "atlayan işaretçi asla yavaşın üstünden atlayamaz mı?" endişesini de çürütür: fark 1'er azaldığı için 2'den 0'a geçer, asla üstünden atlamaz.

Kenar durumlar: boş liste → `while` koşulu ilk turda yanlış, `0` döner. Tek düğüm kendine bağlıysa → ilk turda ikisi de aynı düğüme gelir, `1` döner. Karmaşıklık: **O(n) zaman, O(1) bellek.**

**Bunu AI'sız yazabilir misin?** Bir adım ileri: döngünün *başladığı düğümü* bul. (İpucu: buluşma noktasından sonra bir işaretçiyi başa al, ikisini de birer adım ilerlet; buluştukları yer döngünün girişidir. Bunun neden doğru olduğunu kâğıtta mesafe hesabıyla göstermeye çalış — Floyd'un algoritmasının en güzel kısmı burasıdır.)

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Bu iki proje, veri yapılarını "kullanmak" ile "anlamak" arasındaki farkı kapatacak. İkisi de doğrudan `MertOS`'a katkı olarak yazılabilir.
:::

### Proje 1 (★★): Tam bir dinamik dizi kütüphanesi

**Amaç:** Örnek 2'yi gerçek bir kütüphaneye çevir ve teoriyi ölçümle kanıtla.

**Yapılacak:** `dizi.h` / `dizi.c` ikilisi (Bölüm 2.11'in başlık disiplini: include guard, bildirimler başlıkta, tanımlar `.c`'de). İşlevler: `baslat`, `ekle`, `al(i)`, `yaz(i, deger)`, `sil(i)`, `boyut`, `bitir`. Sınır dışı indeks kontrolü `assert` ile (Bölüm 6.10).

Sonra bir ölçüm programı yaz: n = 10³, 10⁴, 10⁵, 10⁶ için (a) toplam kopyalama sayısını, (b) geçen süreyi tabloya dök. Aynı ölçümü büyüme stratejisi `×2`, `×1.5` ve `+1` için tekrarla.

**Önerilen yaklaşım:** Yapıyı Örnek 2'deki `Dizi` üzerine kur. `sil(i)` için `i`'den sonraki elemanları birer sola kaydırıp `boyut`'u azalt. Büyüme stratejisini bir parametre olarak geçirirsen aynı ölçüm döngüsünü üç kez çalıştırabilirsin. Kopyalama sayacını ölçüm için ayrı tut; süreyi `clock()` ile ölç. `+1` stratejisinde `n = 10⁶` çok uzun sürer; `10⁵` ile başla.

**Başarı kriterleri:** `×2` ile kopyalama toplamı her zaman `2n`'in altında; `+1` ile ölçüm `n²/2` eğrisine oturuyor (grafiğe dökersen daha net); `valgrind` sızıntı raporu temiz; `sil(i)` sonrası kalan elemanların sırası korunuyor; Makefile ile tek komutta derlenip test ediliyor (Bölüm 4).

### Proje 2 (★★★): MertOS için tampon ve girişken liste

**Amaç:** Çekirdek düzeyinde kullanılabilir iki yapı yaz — biri gerçek zamanlı, diğeri genel amaçlı.

**Bölüm A — Dairesel tampon:** 7.7'deki tamponu, `MertOS`'un klavye sürücüsüne uygun hâle getir. Ek gereksinimler: (1) `malloc` kullanma, boyut derleme anında sabit olsun; (2) tek üretici (kesme işleyicisi) ve tek tüketici (çekirdek döngüsü) senaryosunda güvenli olsun — bunun için `bas` ve `kuyruk` indekslerinin her birini hangi tarafın yazdığına dikkat et; `volatile` ile `_Atomic` arasındaki farkı araştır (Bölüm 27 ve Bölüm 43); (3) dolu tamponda yazma denemesi veriyi bozmasın, sessizce başarısız olsun.

**Bölüm B — Girişken (intrusive) çift yönlü liste:** Linux'un `list_head` yaklaşımını kendin kur. Fikir şu: liste düğümü *veriyi içermez*; veri yapısı listenin düğümünü *içerir*.

```c
typedef struct Baglanti {
    struct Baglanti *onceki, *sonraki;
} Baglanti;

typedef struct {
    int pid;
    char ad[16];
    Baglanti liste;        /* düğüm, verinin İÇİNDE */
} Surec;
```

Böylece süreç eklemek için ayrıca düğüm ayırmana gerek kalmaz. Zorluk: elindeki `Baglanti*`'dan onu içeren `Surec*`'e nasıl geri dönersin? Cevap Kod Okuma egzersizindeki `container_of` makrosunda — ama önce **kendin çözmeye çalış** (ipucu: `offsetof` makrosu ve Bölüm 2.7'deki struct yerleşimi).

**Başarı kriterleri:** Tampon 64 tuşluk yükte veri kaybetmiyor ve dolu/boş durumları doğru ayırt ediliyor; liste ile 1000 süreç eklenip silinebiliyor, hiçbir ek `malloc` çağrılmıyor; `container_of` benzeri dönüşümün doğru çalıştığını `assert` ile kanıtlıyorsun; her iki yapı da nöbetçi düğüm ya da eşdeğer bir tasarımla özel durumlardan arındırılmış.

### Ek Alıştırmalar

Bu problemlerin cevabı kitapta yok. Önce kâğıtta dene; takılırsan ilgili kavrama dön, koda ancak çözümünü kurduktan sonra bak.

1. **(★)** İki sıralı bağlı listeyi, yeni düğüm ayırmadan tek sıralı liste hâline getir. Bu, merge adımının kendisidir.
2. **(★)** Tek bağlı listede ortadaki düğümü tek geçişte bul. İki işaretçiden yavaş olanı bir, hızlı olanı iki adım ilerlet.
3. **(★)** Tek bağlı listede sondan k'ıncı düğümü tek geçişte bul. (İpucu: iki işaretçi arasında k adımlık bir fark aç.)
4. **(★★)** Sıralı bağlı listeden tekrar eden düğümleri ek bellek kullanmadan sil.
5. **(★★)** İki bağlı listenin kesişim düğümünü bul. Kesişim değer eşitliği değil, düğümün kendisinin (adresinin) paylaşılmasıdır.
6. **(★)** Bir diziyi k adım sağa döndür; ek dizi kullanma. (İpucu: üç ters çevirme.)
7. **(★★)** Bir dizinin ön toplam (prefix sum) dizisini kur. Sonra herhangi bir `[l, r]` aralığının toplamını O(1)'de sorgula.
8. **(★★)** `n × n` bir matrisi yerinde 90° saat yönünde döndür. Ek matris kullanma.
9. **(★★)** Sıralı bir dizide toplamı verilen hedef olan iki elemanı bul. İki işaretçiyle O(n) yeter.
10. **(★★)** Sırasız bir dizide en uzun ardışık sayılar dizisinin uzunluğunu O(n) sürede bul. (Sıralamak O(n log n) verir; O(n) için bir küme düşün.)
11. **(★★)** `n` kişi dairesel dizilmiş; her `k`'ıncı kişi elenir. Son kalanın konumunu bul. (Dairesel liste: 7.6.)
12. **(★★★)** LRU önbelleği tasarla: `get` ve `put` O(1) olsun. (Hash tablosu ile çift yönlü listeyi birlikte kullan; 7.6'daki LRU notu.)

## Kod Okuma Egzersizi

Bugünkü kesit, Linux çekirdeğinin `include/linux/list.h` dosyasından — dünyanın en çok çalıştırılan bağlı liste uygulaması. Çekirdekteki her süreç, her dosya, her aygıt bu listelerle bağlanır.

**Kaynak:** Linux çekirdeği 6.6 LTS, `include/linux/list.h` (sadeleştirilmiş kesit; gerçek 6.6 kodunda `__list_add_valid` debug kontrolü ve `WRITE_ONCE` bulunur, burada çıkarıldı; `({ })` ve `typeof` GCC uzantılarıdır). Önce ekleme ve silmenin çekirdeği:

```c
struct list_head {
    struct list_head *next, *prev;
};

/* İki düğüm arasına yeni düğüm ekle */
static inline void __list_add(struct list_head *new,
                              struct list_head *prev,
                              struct list_head *next)
{
    next->prev = new;
    new->next = next;
    new->prev = prev;
    prev->next = new;
}

/* Düğümü listeden çıkar */
static inline void __list_del(struct list_head *prev,
                              struct list_head *next)
{
    next->prev = prev;
    prev->next = next;
}
```

Ve çekirdeğin en ünlü makrosu — bir üye alanının adresinden, onu içeren yapının adresine dönmek:

```c
#define container_of(ptr, type, member) ({          \
    const typeof(((type *)0)->member) *__mptr = (ptr); \
    (type *)((char *)__mptr - offsetof(type, member)); })

#define list_entry(ptr, type, member) \
    container_of(ptr, type, member)
```

**Sorular — cevaplamadan geçme:**

- `struct list_head` içinde **veri alanı yok**. Bu tasarım (girişken liste), klasik "düğüm veriyi tutar" yaklaşımına göre hangi iki avantajı sağlar? (İpucu: kaç kez `malloc` çağrılıyor, ve bir yapı aynı anda iki farklı listeye girebilir mi?)
- `__list_add`'deki dört atamanın sırası önemli mi? Sırayı değiştirsen hangi durumda liste bozulur? (Şekil 7.4'ün dersini uygula ve `prev`/`next`'in aynı düğüm olduğu durumu ayrıca düşün.)
- Çekirdek listeleri **dairesel** ve nöbetçili: boş liste, kendini gösteren tek bir `list_head`'dir. `__list_del`'de neden hiç `NULL` kontrolü yok — bu tasarım nasıl gerekli kılmıyor? (7.5 ve 7.6'yı birleştir.)
- `container_of` ne yapıyor? `offsetof(type, member)` neyi hesaplar ve neden `(char *)`'a dönüştürme yapılıyor? (İpucu: Bölüm 2.5'teki işaretçi aritmetiğinde adım uzunluğunu tür belirliyordu.)
- `((type *)0)->member` ifadesi neden çökmeye yol açmıyor? (İpucu: bu ifadenin *değeri* hiç okunmuyor; yalnız `typeof` ile *türü* soruluyor — derleme anında çözülüyor.)
- Son olarak tasarım sorusu: çekirdek neden `void *veri` tutan genel bir liste yerine bu makro hilesini seçti? Tür güvenliği ve performans açısından ne kazandı?

## Bölüm Özeti

Kısım III'ün ilk bölümünde iki temel yapıyı ve aralarındaki ödünleşimi kurduk:

- **Dizi bitişik bellektir.** `taban + i × boyut` formülü O(1) rastgele erişim verir; bedeli, araya ekleme/silmede O(n) kaydırmadır.
- **Bitişikliğin gizli ödülü cache'tir.** CPU 64 baytlık satırlar hâlinde okur; sıralı gezinme bedava komşular kazandırır. Aynı Big-O'ya sahip iki döngü arasında donanıma göre değişen, çoğu zaman birkaç katlık bir fark buradan çıkar — **Big-O sabit çarpanları görmez.**
- **Dinamik dizi** boyut ve kapasiteyi ayırır. Çarpımsal büyüme (×2) sayesinde n ekleme toplam `< 3n` iş yapar: **amortize O(1)**. Sabit artışlı büyüme O(n²)'dir. CPython %12.5 büyür — bellek/hız ödünleşiminin farklı bir cevabı.
- **Bağlı liste** bitişikliği bırakır: düğüm başına ek işaretçi maliyeti ve O(n) erişim karşılığında, *konum elindeyken* O(1) ekleme/silme. İşaretçi sırası kritiktir: **önce bağla, sonra kopar.**
- **Nöbetçi düğüm**, "boş liste" ve "baş değişiyor" özel durumlarını tasarımla ortadan kaldırır — hata düzeltmek yerine hatayı imkânsız kılmak.
- **Çift yönlü liste** elindeki düğümü O(1) siler (LRU önbelleğinin yarısı); **dairesel liste** uç kavramını kaldırır (round-robin).
- **Dairesel tampon**, sabit dizi + modülo ile O(1) ekleme/çıkarma verir, hiç bellek ayırmadan — gömülü sistemlerin ve `MertOS`'un vazgeçilmezi.
- **Karar:** varsayılanın dizi olsun, bağlı listeyi gerekçeyle seç (kalıcı adres, sık splice, girişken yapı, parçalı bellek).

**Sonraki bölümde:** Bu iki yapının üzerine ilk soyutlamaları koyuyoruz. **Bölüm 8 — Stack & Queue**'da erişimi *kasıtlı olarak kısıtlayarak* nasıl güç kazandığımızı göreceğiz: yığın ve kuyruğun iki farklı gerçeklemesi, Bölüm 1'de tanıştığın çağrı yığınının (call stack) gerçek mekaniği, BFS'in neden kuyruk istediği ve monotonik yığın deseni.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. Dizide erişim neden O(1)? Formülü yazabilir misin — ve bu formül bağlı listede neden yazılamaz?
2. "Amortize O(1)" ne demektir? Neden "her ekleme O(1)" demek yanlış olur?
3. Dinamik dizi neden sabit sayıda değil de çarpımsal büyür? Sabit artışta toplam maliyet ne olur?
4. Bağlı listede "araya ekleme O(1)" ifadesinin eksik bıraktığı şey nedir?
5. Big-O'ya göre daha kötü olan dizi, pratikte bağlı listeyi neden çoğu zaman yener?
6. Dairesel tamponda "dolu" ve "boş" durumları nasıl ayırt edilir? En az iki farklı çözüm söyle.
7. Nöbetçi düğüm hangi tür hataları ortadan kaldırır? Bedeli nedir?
:::
