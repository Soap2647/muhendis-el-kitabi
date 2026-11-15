%% kisim_no: VI
%% kisim_ad: İşletim Sistemi & Mimari
%% bolum_no: 27
%% baslik: Senkronizasyon

## Giriş: İki kişi aynı hesaba aynı anda para yatırınca

Bir bankada iki gişe aynı müşterinin hesabına aynı anda 100 TL yatırdığını düşün. Her gişe önce bakiyeyi okur (1000), kendi tarafında 1100'ü hesaplar, sonra yazar. İki yazmadan sonuncusu kazanır ve bakiye 1100 olur. Olması gereken 1200'dü. Kimse hata yapmadı; iki işlem birbirinin ortasına girdi ve birinin yazdığı değer diğeri tarafından ezildi. Bilgisayar biliminde buna **yarış koşulu** (race condition) denir ve modern dünyadaki her çok çekirdekli sistemin günlük ekmeğidir.

Bu bölüm Kısım VI'nın, yani donanım ve işletim sistemi tarafının, bir sonraki adımıdır. Bölüm 26'da bir süreç içinde iş parçacıklarının (thread) nasıl oluşturulduğunu ve çalıştırıldığını gördük. Burada tek bir soruya odaklanıyoruz: birden fazla iş parçacığı aynı belleğe eriştiğinde, bunu nasıl doğru yaparız? İş parçacığı API'sinin (`pthread_create`, `pthread_join`) kendisini yeniden öğretmeyeceğiz; doğrudan senkronizasyona gireceğiz.

Bu konunun mülakattaki ve savunma sanayiindeki yeri açık. Gerçek zamanlı bir uçuş kontrol bilgisayarında bir sensör tamponunu okuyan görev ile yazan görev arasında yanlış bir sıra, yanlış bir irtifa değerine yol açabilir. Bölüm 6'da gördüğümüz heisenbug'ların büyük bölümü tam olarak bu ailedendir: testte görünmez, yük altında ve farklı bir çekirdek sayısında ortaya çıkar. Bölüm 6'nın sözünü tutuyoruz: paylaşılan durumu kilitlerle, atomik işlemlerle ve doğru bellek sıralamasıyla koruyacağız.

::: not
Bu bölümdeki her ölçüm bu makinede, WSL2 altındaki Ubuntu 24.04 ve gcc 13.3 ile yapıldı. İşlemci AMD Ryzen 7 6800H; 16 mantıksal çekirdek (`nproc` = 16). Her ölçüm beş tekrarın medyanıdır. Sayılar bu donanıma özgüdür; yorumu bölümde ayrıca yapılıyor. Ölçüm yapan her kodun tam listesi bölüm içinde yer alıyor, böylece kendi makinende tekrarlayabilirsin.
:::

## 27.1 Yarış koşulu ve kritik bölge

Bir sayacı artıran en basit kod şudur:

```c
sayac++;
```

Tek satır görünüyor, ama işlemci bunu tek adımda yapmaz. Derleyicinin ürettiği assembly'ye bakalım. Aşağıdaki liste, `sayac++` içeren bir fonksiyonun gcc `-O0` ile derlenmiş hâli (kısaltılmış):

```text
art_plain:
	movq	plain_sayac(%rip), %rax
	addq	$1, %rax
	movq	%rax, plain_sayac(%rip)
	ret
```

Üç komut var: **oku** (`movq` ile bellekten yazmaca), **artır** (`addq` ile yazmaçta), **yaz** (`movq` ile yazmaçtan belleğe). Bu üçlüye **oku-değiştir-yaz** (read-modify-write, RMW) diyoruz. Bu üç adımın arasına başka bir iş parçacığı girebilir. Şekil 27.1'deki senaryoda iki iş parçacığı da sayacı 0 iken okur, ikisi de 1 yazmaya çalışır ve bir artış kaybolur.

![Şekil 27.1: Oku-değiştir-yaz serpiştirmesi. İki iş parçacığı da sayacı 0 olarak okur; iki artış yapılır ama sayaç yalnız 1 olur.](gorseller/b27_rmw_serpistirme.png)

Bu senaryoyu gerçek bir programla ölçelim. Her iş parçacığı sayacı on milyon kez artırır. Kod, dört farklı artırma yöntemini deneyebilir: düz `plain`, `volatile`, C11 atomik işlem `atomic` ve bir `pthread_mutex` ile korunan `mutex`. Programın tamamı aşağıda; ilk kısım global değişkenleri ve artırma fonksiyonlarını içerir.

```c
/* b27_rmw.c - sayac++ yaris kosulu ve kayip guncelleme.
 * Derleme: gcc -O0 -Wall -Wextra -std=c11 -pthread b27_rmw.c
 * Kullanim: ./a.out <mod> <thread_sayisi>
 *   mod: plain | volatile | atomic | mutex
 */
#define _POSIX_C_SOURCE 200809L
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>

#define ITER 10000000L

static long plain_sayac;
static volatile long vol_sayac;
static atomic_long at_sayac;
static long mtx_sayac;
static pthread_mutex_t kilit = PTHREAD_MUTEX_INITIALIZER;

static void art_plain(void)    { plain_sayac++; }
static void art_volatile(void) { vol_sayac++; }
static void art_atomic(void)   { atomic_fetch_add(&at_sayac, 1); }

static void art_mutex(void)
{
    pthread_mutex_lock(&kilit);
    mtx_sayac++;
    pthread_mutex_unlock(&kilit);
}

typedef void (*artis_fn)(void);

struct is_arg {
    artis_fn f;
    long n;
};

```

Her artırma fonksiyonu bir işaretçi üzerinden çağrılır. Bu, derleyicinin döngüyü tamamen silip tek bir `sayac += N` ile değiştirmesini engeller; ölçümün dürüst kalması için bunu bilerek yaptık. Sonraki kısım, her iş parçacığının döngüsünü ve zamanlamayı içerir.

```c
static void *is_parcacik(void *p)
{
    struct is_arg *a = p;
    for (long i = 0; i < a->n; i++)
        a->f();
    return NULL;
}

static double simdi(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

```

Ana fonksiyon, mod ve iş parçacığı sayısını komut satırından alır ve sonucu yazar:

```c
int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "kullanim: %s <mod> <thread>\n", argv[0]);
        return 1;
    }
    const char *mod = argv[1];
    int t = atoi(argv[2]);
    artis_fn f;
    if (!strcmp(mod, "plain"))         f = art_plain;
    else if (!strcmp(mod, "volatile")) f = art_volatile;
    else if (!strcmp(mod, "atomic"))   f = art_atomic;
    else if (!strcmp(mod, "mutex"))    f = art_mutex;
    else { fprintf(stderr, "bilinmeyen mod\n"); return 1; }

    pthread_t th[64];
    struct is_arg a = { f, ITER };
    double t0 = simdi();
    for (int i = 0; i < t; i++)
        pthread_create(&th[i], NULL, is_parcacik, &a);
    for (int i = 0; i < t; i++)
        pthread_join(th[i], NULL);
    double dt = simdi() - t0;

    long gercek;
    if (f == art_plain)         gercek = plain_sayac;
    else if (f == art_volatile) gercek = vol_sayac;
    else if (f == art_atomic)   gercek = atomic_load(&at_sayac);
    else                        gercek = mtx_sayac;

    long beklenen = (long)t * ITER;
    printf("mod=%-8s thread=%d n=%ld\n", mod, t, ITER);
    printf("beklenen = %ld\n", beklenen);
    printf("gercek   = %ld\n", gercek);
    printf("kayip    = %ld (%.2f%%)\n", beklenen - gercek,
           100.0 * (beklenen - gercek) / beklenen);
    printf("sure     = %.3f s\n", dt);
    return 0;
}
```

Programı iki iş parçacığıyla dört modda çalıştırdık. Çıktı:

```term
$ ./rmw plain 2
mod=plain    thread=2 n=10000000
beklenen = 20000000
gercek   = 10835261
kayip    = 9164739 (45.82%)
sure     = 0.160 s

$ ./rmw volatile 2
mod=volatile thread=2 n=10000000
beklenen = 20000000
gercek   = 11210785
kayip    = 8789215 (43.95%)
sure     = 0.141 s

$ ./rmw atomic 2
mod=atomic   thread=2 n=10000000
beklenen = 20000000
gercek   = 20000000
kayip    = 0 (0.00%)
sure     = 0.218 s

$ ./rmw mutex 2
mod=mutex    thread=2 n=10000000
beklenen = 20000000
gercek   = 20000000
kayip    = 0 (0.00%)
sure     = 0.279 s

$ ./rmw plain 1
mod=plain    thread=1 n=10000000
beklenen = 10000000
gercek   = 10000000
kayip    = 0 (0.00%)
sure     = 0.014 s
```

Sonuçlar üç şeyi açıkça gösteriyor. Birincisi, düz `sayac++` yarışından **%48,9** oranında bir kayıp var: yirmi milyon artıştan yaklaşık on milyonu kaybolmuş. İkincisi, `volatile` de aynı kaybı veriyor. `volatile` derleyiciye "bu değer başka yerden değişebilir" der; her okumayı bellekten yaptırır. Ama artırmanın üç adımını tek bir bölünmez işleme çevirmez. Üçüncüsü, `atomic` ve `mutex` sürümleri tam sonucu veriyor. Atomik sürümde süre 0,22 saniye, mutex'te 0,29 saniye. Tek iş parçacığında (`plain 1`) kayıp sıfır, çünkü yarışacak kimse yok.

Atomik sürümün assembly'sine de bakalım. `atomic_fetch_add` sonucu kullanmadığı için gcc bunu `lock add` olarak derledi:

```term
$ gcc -O0 -S b27_rmw.c   (art_atomic, yalnizca govde)
art_atomic:
	endbr64
	pushq	%rbp
	movq	%rsp, %rbp
	lock addq	$1, at_sayac(%rip)
	nop
	popq	%rbp
	ret
```

`lock` öneki, bu komutun bellek okuma-değiştirme-yazma işlemini tüm çekirdeklere karşı bölünmez yapar. Bu, Bölüm 25'te gördüğümüz önbellek tutarlılığının donanım karşılığıdır: çekirdek, önbellek satırının sahipliğini alıp işlemi tamamlar.

Bir kavramı açıkça tanımlayalım: **kritik bölge** (critical section), paylaşılan bir kaynağa erişen ve aynı anda yalnız bir iş parçacığının çalışmasını istediğimiz kod parçasıdır. `sayac++` tek başına bir kritik bölgedir. Kilidi, atomik işlemi ya da doğru sıralamayı, kritik bölgenin dışarıdan bölünmez görünmesi için kullanırız.

::: dikkat
"Tek satır, tek komut" sezgisine güvenme. Bir komut bile atomik olmayabilir. Örneğin x86'da `add [bellek], 1` (`lock` öneki olmadan) tek bir makine komutudur ama çok çekirdekte bölünmez değildir: işlemci içinde okuma ve yazma ayrı mikro işlemlerdir. Atomikliği garanti eden tek şey donanım desteğidir (`lock` öneki, `xchg`, `cmpxchg`) ya da bir kilittir.
:::

## 27.2 Doğru senkronizasyonun üç şartı

Paylaşılan kaynağı korumanın bir yolu olmalı. "Çalışıyor gibi" görünen bir yöntem yetmez. İyi bir senkronizasyon protokolü üç şartı birden sağlamalıdır:

1. **Karşılıklı dışlama** (mutual exclusion): aynı anda en fazla bir iş parçacığı kritik bölgede olabilir.
2. **İlerleme** (progress): kritik bölgede kimse yoksa, bekleyen bir iş parçacığı sonsuza kadar bloke edilmemelidir. Yani karar, bekleyenler arasında yapılmalıdır, dışarıdan bir "kilit" kimseyi sonsuza dek tutmamalıdır.
3. **Sınırlı bekleme** (bounded waiting): bir iş parçacığı kritik bölgeye girmek istediğinde, diğerlerinin o bölgeye girme sayısı üst sınırla sınırlı olmalıdır. Aksi hâlde bir iş parçacığı sonsuza dek açlık (starvation) çeker.

Üç şart birbirinden bağımsız değildir ama farklı hataları yakalar. Karşılıklı dışlama olmazsa veri bozulur (yukarıdaki kayıp artışlar). İlerleme olmazsa sistem kilitlenir (27.11'de göreceğiz). Sınırlı bekleme olmazsa bazı görevler hiç çalışamaz. Bu üç şartı aynı anda, yalnızca okuma ve yazma ile sağlayan klasik algoritma Peterson'dır; bir sonraki kısımda onu inceliyoruz.

## 27.3 Peterson algoritması: iki iş parçacığı için üç şartı birden

Dekker ve Peterson'ın algoritmaları, yalnızca okuma ve yazma kullanarak iki iş parçacığı için karşılıklı dışlamayı sağlamanın klasik yollarıdır. Peterson'ın (1981) fikri iki parçadır. Her iş parçacığının bir **bayrağı** var: "kritik bölgeye girmek istiyorum". Ayrıca ortak bir **sıra** (`tur`) değişkeni var: "son olarak sıra bende kalsın, yani önce diğerinin girmesine izin ver" anlamında. Bir iş parçacığı girmek istediğinde bayrağını kaldırır, sırayı karşı tarafa verir ve karşı taraf bayrağını kaldırmış değilse ya da sıra kendisindeyse girer.

Bu yapı üç şartı da sağlar. Karşılıklı dışlama: iki iş parçacığı da içeri girmek isterse sıra değişkeni yalnız birini içeri alır. İlerleme: kritik bölgede kimse yoksa, bekleyen iş parçacığı bayrağı diğerinin kaldırmış olması ya da sıranın kendisinde olması yüzünden kilitlenmez. Sınırlı bekleme: sıra her girişte karşı tarafa geçtiği için bekleyen iş parçacığı en fazla bir giriş bekler.

Algoritmanın varsayımı, bellek işlemlerinin programda yazıldığı sırada, herkes tarafından aynı sırayla görülmesidir. Buna **sıralı tutarlılık** (sequential consistency) denir ve Lamport'un 1979 tanımıdır. Modern işlemciler bu varsayımı çoğu zaman bozar. Bunu aşağıda ölçeceğiz.

Algoritmanın C karşılığı için derleme makrolarını ve iki yardımcıyı ilk bloğa koyuyoruz. `MO_S` yazmalar, `MO_L` okumalar için bellek sıralamasını belirler; derleme sırasında `-D` ile seçilir. Bu sayede aynı kod, farklı sıralamalarla iki kez derlenip karşılaştırılabilir.

```c
/* b27_bellek.c - bellek siralamasi deneyleri.
 * Derleme (ornek):
 *   gcc -O2 -std=c11 -pthread -DMO_S=memory_order_relaxed \
 *       -DMO_L=memory_order_relaxed b27_bellek.c -o sb_rel
 * Kullanim: ./sb_rel <sb|mp|peterson> <iterasyon>
 *   sb       : store buffering (x=y=0 litmus testi)
 *   mp       : mesaj gecirme (veri + bayrak)
 *   peterson : Peterson algoritmasi, kritik bolgede ihlal sayisi
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef MO_S
#define MO_S memory_order_seq_cst
#endif
#ifndef MO_L
#define MO_L memory_order_seq_cst
#endif

static int N;
static const char *ISIM;

static double simdi(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

/* ---------- store buffering ---------- */
static atomic_int *sx, *sy;
static int *r1, *r2;
static pthread_barrier_t bar;
```

Peterson'ın kilitleme ve bırakma fonksiyonları aşağıda. `kilitle`, bayrağını kaldırır, sırayı karşı tarafa verir ve karşı taraf istiyor ve sıra onda ise bekler. `birak` yalnızca bayrağı indirir.

```c
static atomic_int bayrak2[2];
static atomic_int tur;
static atomic_int icerideki;
static long ihlal_sayisi[2];
static int K;

static void kilitle(int i)
{
    int j = 1 - i;
    atomic_store_explicit(&bayrak2[i], 1, MO_S);
    atomic_store_explicit(&tur, j, MO_S);
    while (atomic_load_explicit(&bayrak2[j], MO_L) == 1 &&
           atomic_load_explicit(&tur, MO_L) == j)
        ;
}

static void birak(int i)
{
    atomic_store_explicit(&bayrak2[i], 0, MO_S);
}

static void *pet_is(void *p)
{
    int i = *(int *)p;
    for (int k = 0; k < K; k++) {
        kilitle(i);
        if (atomic_fetch_add(&icerideki, 1) != 0)
            ihlal_sayisi[i]++;
        atomic_fetch_sub(&icerideki, 1);
        birak(i);
    }
    return NULL;
}

```

Ana fonksiyon (ve Peterson testi) aşağıda. Test her iş parçacığını `K` kez kritik bölgeye sokar. Kritik bölgede `icerideki` sayacını artırır; artış öncesi değer sıfırdan farklıysa, yani başka biri de içerideyse bu bir ihlaldir. Sayaç ve kontrol `seq_cst` kullanır ki ölçüm aracı kendi sonuçlarını bozmasın. Ana fonksiyon üç deneyi (`sb`, `mp`, `peterson`) komut satırından seçer; `sb` ve `mp` kısımları bu bölümün ilerisinde ayrıca açıklanıyor.

```c
static void deney_peterson(void)
{
    static int id[2] = {0, 1};
    pthread_t a, b;
    double t0 = simdi();
    pthread_create(&a, NULL, pet_is, &id[0]);
    pthread_create(&b, NULL, pet_is, &id[1]);
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    double dt = simdi() - t0;
    long top = ihlal_sayisi[0] + ihlal_sayisi[1];
    printf("peterson giris=%d (her is parcacigi)\n", K);
    printf("ihlal (ayni anda iceride) = %ld\n", top);
    printf("sure = %.3f s\n", dt);
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr,
                "kullanim: %s <sb|mp|peterson> <n>\n", argv[0]);
        return 1;
    }
    ISIM = argv[1];
    N = atoi(argv[2]);
    K = N;
    if (!strcmp(ISIM, "sb"))            deney_sb();
    else if (!strcmp(ISIM, "mp"))       deney_mp();
    else if (!strcmp(ISIM, "peterson")) deney_peterson();
    else { fprintf(stderr, "bilinmeyen deney\n"); return 1; }
    return 0;
}
```

Testi iki sürümle derledik. `bel_sc` tüm atomik işlemler için varsayılan `seq_cst` kullanır. `bel_rlx` her yerde `relaxed` (gevşek) kullanır, yani yalnızca atomiklik ister, sıra garantisi istemez. İki sürümü iki milyon giriş için çalıştırdık:

```term
$ ./bel_rlx sb 1000000
sb  iterasyon=1000000
(r1,r2)=(0,0): 25  <- sirali tutarlilikta
olmaz
(r1,r2)=(0,1): 500752
(r1,r2)=(1,0): 499138
(r1,r2)=(1,1): 85
sure = 17.453 s

$ ./bel_sc sb 1000000
sb  iterasyon=1000000
(r1,r2)=(0,0): 0  <- sirali tutarlilikta
olmaz
(r1,r2)=(0,1): 496640
(r1,r2)=(1,0): 503231
(r1,r2)=(1,1): 129
sure = 15.815 s

$ ./bel_rlx mp 1000000
mp  iterasyon=1000000
bayrak gorunup veri eski: 0
sure = 0.453 s

$ ./bel_ra mp 1000000
mp  iterasyon=1000000
bayrak gorunup veri eski: 0
sure = 0.449 s

$ ./bel_rlx peterson 2000000
peterson giris=2000000 (her is parcacigi)
ihlal (ayni anda iceride) = 2
sure = 0.410 s

$ ./bel_sc peterson 2000000
peterson giris=2000000 (her is parcacigi)
ihlal (ayni anda iceride) = 0
sure = 0.443 s
```

Burada dikkat edilecek nokta şu: `relaxed` sürümde, Peterson'ın algoritması kâğıt üzerinde doğru olmasına rağmen ihlaller gözlendi. Bir çalıştırmada iki, önceki çalıştırmalarda beş ve yedi ihlal görüldü; yani sayı her seferinde değişiyor, ama sıfır değil. `seq_cst` sürümünde ise her çalıştırmada sıfır. Ölçülen ihlal sayısı iki milyon girişte birkaç tanedir; bu yüzden tek bir çalıştırma sıfır verebilir ve yanıltıcı olabilir. Bu tür bir hatanın neden bu kadar nadir olduğunu aşağıda açıklayacağız.

::: dikkat
Peterson'ı bugün bir üretim sisteminde kullanma. Donanım atomik komutları ve mutex zaten var; Peterson'ın değeri, neden çalışmadığını anlamak ve sıralama kavramını somutlaştırmaktır.
:::

## 27.4 Modern CPU'da Peterson neden bozulur: store buffering

Peterson'ın `relaxed` sürümünde iki iş parçacığı da şu sırayla çalışır: kendi bayrağını yazar, sonra karşı tarafın bayrağını okur. Bir iş parçacığı kendi bayrağını yazdığında, bu yazma hemen belleğe değil, işlemcinin **mağaza tamponuna** (store buffer) konur. Tampon, yazmaları sırayla belleğe gönderen küçük bir kuyruktur; Bölüm 25'te önbellek hiyerarşisini gördükten sonra bunu bir önbellek ayrıntısı olarak düşünebilirsin. Karşı iş parçacığı kendi bayrağını yazarken, ilk iş parçacığının yazması hâlâ tamponda olabilir. Her iki taraf da karşı tarafın bayrağını **eski** değerde (sıfır) görür ve ikisi de içeri girer.

Bunu en küçük hâliyle, iki değişkenli bir **litmus testi** olarak görebiliriz. Hem `x` hem `y` başta sıfırdır. Birinci iş parçacığı `x = 1` yazar, sonra `y`'yi okur. İkinci iş parçacığı `y = 1` yazar, sonra `x`'i okur. Sıralı tutarlılıkta iki okumadan en az biri yeni değeri görmek zorundadır; yani `(r1, r2) = (0, 0)` sonucu imkânsızdır. Şekil 27.2 bu sonucun nasıl ortaya çıktığını gösteriyor.

![Şekil 27.2: Store buffering. Her çekirdeğin yazması önce kendi tamponunda bekler; okumalar bellekten yapılır ve ikisi de eski değeri görebilir.](gorseller/b27_store_buffering.png)

Bu testi `relaxed` ve `seq_cst` sürümleriyle bir milyon kez çalıştırdık. İki iş parçacığı her turda bir bariyerle aynı anda başlatılır. Test kodunun tamamı aşağıda; ilk blok, iki iş parçacığının ilk fonksiyonlarını içerir.

```c

static void *sb_t1(void *p)
{
    (void)p;
    for (int i = 0; i < N; i++) {
        pthread_barrier_wait(&bar);
        atomic_store_explicit(&sx[i], 1, MO_S);
        r1[i] = atomic_load_explicit(&sy[i], MO_L);
    }
    return NULL;
}

static void *sb_t2(void *p)
{
    (void)p;
    for (int i = 0; i < N; i++) {
        pthread_barrier_wait(&bar);
        atomic_store_explicit(&sy[i], 1, MO_S);
        r2[i] = atomic_load_explicit(&sx[i], MO_L);
    }
    return NULL;
}

```

Sonraki blok, ana deney fonksiyonunu ve sonuçları sayan kısmı içerir.

```c
static void deney_sb(void)
{
    sx = calloc(N, sizeof *sx);
    sy = calloc(N, sizeof *sy);
    r1 = calloc(N, sizeof *r1);
    r2 = calloc(N, sizeof *r2);
    pthread_barrier_init(&bar, NULL, 2);
    pthread_t a, b;
    double t0 = simdi();
    pthread_create(&a, NULL, sb_t1, NULL);
    pthread_create(&b, NULL, sb_t2, NULL);
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    double dt = simdi() - t0;
    long h[2][2] = {{0, 0}, {0, 0}};
    for (int i = 0; i < N; i++)
        h[r1[i]][r2[i]]++;
    printf("sb  iterasyon=%d\n", N);
    printf("(r1,r2)=(0,0): %ld  <- sirali tutarlilikta\n"
           "olmaz\n", h[0][0]);
    printf("(r1,r2)=(0,1): %ld\n", h[0][1]);
    printf("(r1,r2)=(1,0): %ld\n", h[1][0]);
    printf("(r1,r2)=(1,1): %ld\n", h[1][1]);
    printf("sure = %.3f s\n", dt);
}

/* ---------- mesaj gecirme (message passing) ---------- */
```

Ölçüm sonuçları, `bellek_term` çıktısının ilk iki bölümünde. Özet:

| Sürüm | (r1, r2) = (0, 0) sayısı (10^6 turda) |
|---|---|
| relaxed (3 çalıştırma) | 25, 19, 9 |
| seq_cst | 0 |

`relaxed` sürümde `(0, 0)` sonucu 10^6 turun yaklaşık onda biri kadar, yani on ila yirmi beş kez görüldü. `seq_cst` sürümünde hiç görülmedi. Bu, x86 mimarisinin davranışıyla tutarlıdır: x86'nın bellek modeli TSO (Total Store Order) olarak bilinir ve bu modelde gözlemlenebilen tek yeniden sıralama, bir yazmanın sonraki bir okumadan sonra görünmesidir (StoreLoad). Diğer tüm sıralama ihlalleri x86'da yasaktır. Bu, Peterson'ın neden iki milyonda birkaç hata verdiğini açıklar: yalnızca bu tek yeniden sıralama, ve yalnızca iki iş parçacığı tam o pencerede çakışınca olur.

Sıralama sorununun çözümü `seq_cst` ile gelir. Bu sıralama, atomik işlemlerin tüm iş parçacıkları tarafından aynı toplam sırada görülmesini sağlar. x86'da bunun karşılığı, yazmayla okuma arasına bir bariyer (`mfence`) ya da `lock` öneki koymaktır. Bunu derleyici sizin yerinize yapar.

## 27.5 Bellek modeli: relaxed, acquire, release, seq_cst

C11 ve C++11, her atomik işlem için bir **bellek sıralaması** (memory order) seçmenize izin verir. Bu seçim, atomik olmayan erişimlerin de nasıl sıralanacağını etkiler. Tablo, sık kullanılan dört seviyeyi özetliyor:

| Sıralama | Garanti | Tipik kullanım |
|---|---|---|
| `relaxed` | Yalnız atomiklik. Diğer erişimlerle sıra garantisi yok | sayaç, istatistik |
| `acquire` (okuma) | Bu okumadan sonraki erişimler, bu okumadan önce yapılamaz | kilit alma, bayrak okuma |
| `release` (yazma) | Bu yazmadan önceki erişimler, bu yazmadan sonra görünmez olamaz | kilit bırakma, bayrak yazma |
| `seq_cst` | Tüm `seq_cst` işlemler için tek bir toplam sıra | varsayılan; Peterson |

`acquire` ve `release` çiftinin ne zaman gerektiğini en iyi mesaj geçirme örneği gösterir. Üretici bir **veri** değişkenine yazar ve sonra bir **bayrak** kaldırır. Tüketici bayrağı bekler ve sonra veriyi okur. Sorun şu: bayrak yazılmış olabilir ama veri yazısı, bayrağın görünmesinden sonra başka bir çekirdeğe ulaşabilir. Bu durumda tüketici eski veriyi okur.

`release` yazması, kendisinden önceki yazmaların bayrakla birlikte görünür olmasını sağlar. `acquire` okuması, bayrağı gördüğünde kendisinden sonraki okumaların eski veriyi görmemesini sağlar. Birlikte, aralarında bir "bu bayrakla görünür olma" ilişkisi kurarlar. Şekil 27.3 bu eşleşmeyi gösteriyor.

![Şekil 27.3: Release ve acquire eşleşmesi. Release yazması veriyi bayrakla birlikte yayınlar; acquire okuması bayrağı görünce veriyi de görür.](gorseller/b27_acq_rel.png)

Bu ilişkiyi ölçmek için `mp` (message passing) testini yazdık. Üretici `veri[i] = 42` yazar, ardından `bayrak[i]`'yi `MO_S` ile yazar. Tüketici `bayrak[i]` sıfır olduğu sürece döner, sonra `veri[i]`'yi okur. Eğer bayrak görüldüğünde veri eski çıkarsa, `okunan[i] != 42` ihlali sayılır.

```c
static int *veri;
static atomic_int *bayrak;
static int *okunan;

static void *mp_uretici(void *p)
{
    (void)p;
    for (int i = 0; i < N; i++) {
        pthread_barrier_wait(&bar);
        veri[i] = 42;
        atomic_store_explicit(&bayrak[i], 1, MO_S);
    }
    return NULL;
}

static void *mp_tuketici(void *p)
{
    (void)p;
    for (int i = 0; i < N; i++) {
        pthread_barrier_wait(&bar);
        while (atomic_load_explicit(&bayrak[i], MO_L) == 0)
            ;
        okunan[i] = veri[i];
    }
    return NULL;
}

```

Test fonksiyonları ve sonuç yazımı aşağıda.

```c
static void deney_mp(void)
{
    veri = calloc(N, sizeof *veri);
    bayrak = calloc(N, sizeof *bayrak);
    okunan = calloc(N, sizeof *okunan);
    pthread_barrier_init(&bar, NULL, 2);
    pthread_t a, b;
    double t0 = simdi();
    pthread_create(&a, NULL, mp_uretici, NULL);
    pthread_create(&b, NULL, mp_tuketici, NULL);
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    double dt = simdi() - t0;
    long ihlal = 0;
    for (int i = 0; i < N; i++)
        if (okunan[i] != 42)
            ihlal++;
    printf("mp  iterasyon=%d\n", N);
    printf("bayrak gorunup veri eski: %ld\n", ihlal);
    printf("sure = %.3f s\n", dt);
}

/* ---------- Peterson ---------- */
```

Ölçüm sonuçları, `bellek_term` çıktısının üçüncü ve dördüncü bölümünde. Hem `relaxed` hem `release/acquire` sürümünde, bir milyon iterasyonda sıfır ihlal görüldü. Bu, bu makinede gözlemlenen sonuçtur; kanıt değildir. Dürüst yorum şudur: x86'nın TSO modeli, mesaj geçirme örüntüsünde yazmaların sırasını zaten korur. Bu yüzden `relaxed` bile burada gözlenemez. ARM ve benzeri zayıf bellek modeli mimarilerinde (genel bilgi) aynı kod, `relaxed` ile gerçekten yanlış veri okuyabilir. Bu makinede ARM test edemediğimiz için bu iddiayı ölçmedik.

Bu noktada MertOS'a bakmanın zamanı geldi. Klavye sürücüsü (`kernel/drivers/keyboard.cpp`, 83-97. satırlar) bir ring buffer'ı şöyle işler: kesme işleyicisi `m_tail`'i, ana döngü `m_head`'i ilerletir ve ikisi de `volatile int` olarak tanımlıdır (`keyboard.hpp`, 93-94. satırlar). Bu yapı tek üretici (kesme), tek tüketici (ana döngü) durumu için doğru çalışır; ama `volatile` atomiklik ve bellek sıralaması sağlamaz. x86'da TSO nedeniyle çoğu zaman yeterlidir; ARM'da ise yetersiz kalır. Benzer şekilde `kernel/ipc/message_queue.hpp` dosyası kendini "lock-free" olarak tanımlar, ama sıra için yalnızca derleyici bariyeri kullanır (`asm volatile("" : : : "memory")`). Bu bariyer derleyicinin yeniden sıralamasını engeller, işlemcinin değil. Bu iki kodu düzeltmenin yolu, `tail` yazımını `release`, `head`'i okumayı `acquire` ile yapmaktır; bunu Kendin Yap bölümünde bir proje olarak bırakıyoruz.

## 27.6 Donanım desteği: atomik komutlar, C11 ve C++

Peterson gibi yalnızca okuma ve yazma kullanan algoritmalar, modern işlemcilerde pahalı ve kırılgan olur. Bunun yerine işlemciler, bir bellek konumunu **bölünmez** biçimde okuyup değiştiren komutlar sunar. x86'da en önemlileri şunlardır:

- **`lock` öneki**: arkasındaki komutu (`add`, `inc`, `cmpxchg`, `xadd` gibi) bölünmez yapar. Önbellek satırının sahipliğini alır, işlemi bitirir, sonra bırakır. 27.1'deki `lock addq` bunun bir örneğiydi.
- **`xchg`**: bir yazmacı bellek konumuyla takas eder. Bellek operandı varsa `lock` ima edilir; bu yüzden `xchg` ile yazılmış bir spinlock doğrudur.
- **`cmpxchg`** (compare-and-swap, CAS): "bellek konumu beklediğime eşitse, yeni değeri yaz ve başarılı de; değilse mevcut değeri bana bildir" der. Bu, kilitsiz (lock-free) yapıların temel taşıdır; 27.15'te Treiber yığınında kullanacağız.

CAS'in anlamını kâğıt üzerinde şöyle yazabiliriz (tek bir bölünmez adım olarak):

```text
atomik {
    eger (*p == beklenen) { *p = yeni; return DOGRU; }
    beklenen = *p;  return YANLIS;
}
```

C11 bu işlemleri `<stdatomic.h>` ile sunar. `atomic_fetch_add` bir artırma yapar ve eski değeri döndürür; `atomic_compare_exchange_weak` bir CAS yapar. C++11 ise `std::atomic<T>` şablonuyla aynı kavramları verir: `fetch_add`, `compare_exchange_weak` ve `load`/`store`. İki dil de bellek sıralamasını parametre olarak alır.

Kısa bir örnek: iki iş parçacığının aynı sayacı kilitsiz artırması.

```c
#include <stdatomic.h>

atomic_long sayac;

void artir(void)
{
    /* oku-artir-yaz tek bolunmez islem: lock add */
    atomic_fetch_add_explicit(&sayac, 1, memory_order_relaxed);
}
```

`weak` ve `strong` CAS arasındaki fark, sahte başarısızlıktır. `compare_exchange_weak`, değer eşit olsa bile başarısız olabilir; bu, ARM gibi LL/SC mimarilerde (genel bilgi) daha verimli bir kodlamaya izin verir. Döngü içinde kullanılması gerekir: başarısızlıkta `beklenen` yeni değerle güncellenir ve döngü tekrar dener. x86'da `weak` ve `strong` genellikle aynı kodu üretir.

Bu komutların bedelini de görmek gerekir. Atomik işlem, önbellek satırını çekirdekler arasında taşır; çekişme arttıkça bu taşıma maliyeti toplanır. Bunu aşağıdaki kilit ölçümünde göreceğiz.

## 27.7 Kilitler: spinlock, mutex ve ölçümlü karşılaştırma

Atomik komutlarla bir kilit yazabiliriz. En basit kilit, **test-and-set** (TAS) kilididir: kilidi `exchange` ile 1 yapar ve eski değer 0 ise kilidi almış oluruz; değilse tekrar deneriz. Bu, meşgul bekleme yapan bir **spinlock**'tur: bekleyen iş parçacığı CPU'yu sürekli döndürerek yer.

TAS'ın sorunu, her denemenin bir `lock` komutu olması ve bu yüzden önbellek satırını sürekli çekişmesidir. **TTAS** (test-and-test-and-set) bunu düzeltir: önce kilidi sıradan bir okumayla izler (bu yalnızca paylaşılan bir önbellek satırını okur), kilit boşalınca bir kez `exchange` dener. Bir de **geri çekilme** (backoff) ekleriz: başarısızlıkta bekleme süresini ikiye katlarız ve bu, çekişmeyi dağıtır. Aşağıdaki kod, TAS ve TTAS'ı, ölçüm programının geri kalanıyla birlikte veriyor.

```c
/* b27_kilit.c - kilit maliyeti olcumu.
 * Derleme: gcc -O2 -std=c11 -pthread b27_kilit.c -o kilit
 * Kullanim: ./kilit <mod> <thread> <islem_per_thread>
 *   mod: atomik | mutex | tas | ttas
 * Cikti: tek satir, islem basina nanosaniye.
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static long paylasilan;              /* kilitle korunan sayac */
static atomic_long atomik_sayac;
static pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER;
static atomic_int tas_bayrak;
static atomic_int ttas_bayrak;
/* MOD: 0 atomik, 1 mutex, 2 tas, 3 ttas */
static int MOD;
static long K;                       /* thread basina islem */

```

Atomik `exchange` ve TTAS'ın bekleme döngüsü aşağıda. `__builtin_ia32_pause`, x86'da döngü içinde bir "beklemeyi ipucu" komutudur (`pause`): işlemciye bunun bir meşgul bekleme olduğunu söyler ve kardeş iş parçacığına kaynak bırakır.

```c
static void tas_kilitle(void)
{
    while (atomic_exchange_explicit(&tas_bayrak, 1,
                                    memory_order_acquire))
        ;
}

static void tas_birak(void)
{
    atomic_store_explicit(&tas_bayrak, 0, memory_order_release);
}

static void ttas_kilitle(void)
{
    int geri = 1;
    for (;;) {
        if (!atomic_exchange_explicit(&ttas_bayrak, 1,
                                      memory_order_acquire))
            return;
        while (atomic_load_explicit(&ttas_bayrak,
                                    memory_order_relaxed)) {
#if defined(__x86_64__) || defined(__i386__)
            __builtin_ia32_pause();
#endif
        }
        for (int i = 0; i < geri; i++)
#if defined(__x86_64__) || defined(__i386__)
            __builtin_ia32_pause();
#else
            ;
#endif
        if (geri < 1024)
            geri *= 2;             /* ustel geri cekilme */
    }
}

static void ttas_birak(void)
{
    atomic_store_explicit(&ttas_bayrak, 0, memory_order_release);
}

```

Ölçüm döngüsü, her iş parçacığında kilit dışında küçük bir iş (20 eklemeli bir döngü) yapar, sonra kilit altında paylaşılan sayacı artırır. Yerel `volatile` değişken her iş parçacığının kendi yığınında olduğu için burada sahte paylaşım yaratmaz (sahte paylaşımı 27.14'te bilerek ölçeceğiz). Her mod için işlem başına süre nanosaniye olarak yazılır.

```c
static void *is_parcacigi(void *p)
{
    (void)p;
    volatile long yerel = 0;       /* her thread kendi yigininda */
    for (long i = 0; i < K; i++) {
        /* kilit disi kisa is: kilidi tutma suresini gercekci kilar */
        for (int j = 0; j < 20; j++)
            yerel += j;
        switch (MOD) {
        case 0:
            atomic_fetch_add_explicit(&atomik_sayac, 1,
                                      memory_order_relaxed);
            break;
        case 1:
            pthread_mutex_lock(&mtx);
            paylasilan++;
            pthread_mutex_unlock(&mtx);
            break;
        case 2:
            tas_kilitle();
            paylasilan++;
            tas_birak();
            break;
        default:
            ttas_kilitle();
            paylasilan++;
            ttas_birak();
            break;
        }
    }
    return NULL;
}

static double simdi(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

```

Ana fonksiyon modu ve iş parçacığı sayısını alır, süreyi ölçer ve sonucu doğrular: kilitli modlarda sayaç tam olmalıdır.

```c
int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr,
                "kullanim: %s <mod> <thread> <islem>\n",
                argv[0]);
        return 1;
    }
    if (!strcmp(argv[1], "atomik")) MOD = 0;
    else if (!strcmp(argv[1], "mutex")) MOD = 1;
    else if (!strcmp(argv[1], "tas")) MOD = 2;
    else if (!strcmp(argv[1], "ttas")) MOD = 3;
    else { fprintf(stderr, "bilinmeyen mod\n"); return 1; }
    int t = atoi(argv[2]);
    K = atol(argv[3]);

    pthread_t th[64];
    double t0 = simdi();
    for (int i = 0; i < t; i++)
        pthread_create(&th[i], NULL, is_parcacigi, NULL);
    for (int i = 0; i < t; i++)
        pthread_join(th[i], NULL);
    double dt = simdi() - t0;

    long toplam = (long)t * K;
    /* dogruluk: kilitli modlarda sayac tam olmali */
    long dogru = (MOD == 0) ? atomic_load(&atomik_sayac) : paylasilan;
    if (dogru != toplam)
        fprintf(stderr, "UYARI: sayac %ld != %ld\n", dogru, toplam);
    printf("%.2f\n", dt * 1e9 / toplam);
    return 0;
}
```

Her kombinasyonu (dört mod, 1, 2, 4, 8, 16 iş parçacığı) beş kez çalıştırdık ve medyanı aldık. Tablo, işlem başına medyan süreyi gösteriyor (düşük olan iyi):

| İş parçacığı | atomik | pthread_mutex | TTAS | TAS |
|---|---|---|---|---|
| 1 | 5,7 ns | 11,4 ns | 6,3 ns | 6,4 ns |
| 2 | 11,2 ns | 33,3 ns | 24,4 ns | 37,1 ns |
| 4 | 9,8 ns | 36,5 ns | 39,4 ns | 68,8 ns |
| 8 | 11,1 ns | 40,5 ns | 63,8 ns | 134,4 ns |
| 16 | 12,6 ns | 34,1 ns | 75,3 ns | 239,3 ns |

![Şekil 27.4: Kilit maliyeti. Atomik sayaç en ucuz; TAS spinlock çekişme arttıkça hızla kötüleşiyor; pthread_mutex 2 iş parçacığından sonra düz bir eğri çiziyor.](gorseller/b27_kilit_olcum.png)

Bu sonuçları dikkatle okumak gerekir. Birincisi, atomik sayaç bir kilit değildir; tek bir artırmayı yapar, bu yüzden en ucuz olması beklenir. Bu karşılaştırma, "kilitsiz hangi durumda mümkünse kazanır" sorusunun cevabını verir, ama her problem tek bir sayaca indirgenemez. İkincisi, TAS ve TTAS sayıları çekişme ile birlikte artıyor; spinlock tek iş parçacıklı durumda kilitten daha ucuzdur (6 ns'ye karşı 11 ns) ama iki iş parçacığında bile mutex'in gerisinde kalır ve 16'da mutex'in altı katından fazla yavaşlar. Üçüncüsü, `pthread_mutex` iki iş parçacığından sonra neredeyse sabit kalır. Bunun nedeni, glibc'nin (genel bilgi) çekişme olduğunda bekleyen iş parçacığını çekirdeğe, bir **futex** üzerinden uyutmasıdır; bekleyen iş parçacıkları CPU'yu döndürmez ve önbellek satırını çekişmez. Bu, bu iş yükü ve bu makine için geçerli bir gözlemdir; bir spinlock'un her zaman kötü olduğu anlamına gelmez. Kritik bölge çok kısa ve çekişme düşükse (ya da bekleme süresi bir bağlam değişiminden kısaysa) spinlock kazanır. Gerçek zamanlı çekirdekler bu yüzden spinlock kullanır; ama bu, kesme bağlamında ve kritik bölgenin nanosaniyelerle ölçüldüğü durumdur.

Dördüncüsü, bu sayılar 16 mantıksal çekirdekte ölçüldü; Ryzen 6800H'de bu, 8 fiziksel çekirdek ve eş zamanlı çoklu iş parçacığıdır (SMT). 9 ve üzeri iş parçacığında iki mantıksal çekirdek aynı fiziksel çekirdeği paylaşır; bu da eğrinin şeklini etkiler.

::: ipucu
Kilit seçimi için sezgisel bir kural: çekişme yoksa spinlock ya da mutex fark etmez; çekişme varsa ve bekleme uzunsa mutex; bekleme nanosaniyelerle ölçülüyorsa ve bir kesme işleyicisinde bile kullanıyorsan spinlock. Her zaman ölç; bu tablo kuralın değil, bu makinenin sonucudur.
:::

## 27.8 Okuyucu-yazıcı kilidi ve semafor

Bir kilit her zaman tek kişiyi içeri alır. Oysa çoğu veri yapısı çok okunur, az yazılır: bir yapılandırma tablosu, bir sensör kalibrasyonu. Bu durumda **okuyucu-yazıcı kilidi** (reader-writer lock) daha uygundur. Kural basittir: birden çok okuyucu aynı anda girebilir, yazıcı ise tek başına girer ve o sırada ne okuyucu ne başka yazıcı olabilir. POSIX bunu `pthread_rwlock_t` ile sağlar.

Bu kilidin bir tuzağı vardır: **yazıcı açlığı**. Okuyucular sürekli geliyorsa ve her biri kilidi kısa süre de olsa tutuyorsa, yazıcı hiç sırasını alamayabilir. Bu, Bölüm 27.2'deki sınırlı bekleme şartının ihlalidir. Bazı gerçekleştirmeler yazıcıya öncelik verir, bazıları okuyucuya; hangisinin kullanıldığı kitaplığa ve platforma bağlıdır. Bu makinede okuyucu-yazıcı kilidi için bir ölçüm yapmadık; bu bölümde yalnızca kavramı ve tuzağını anlatıyoruz.

**Semafor** (semaphore), Dijkstra'nın (1960'lar) tanıttığı sayan bir yapıdır. İçinde bir tamsayı tutar. `P` (wait, `sem_wait`) işlemi sayıyı bir azaltır; sayı sıfırsa bekler. `V` (post, `sem_post`) sayıyı bir artırır ve bekleyenlerden birini uyandırır. Sayı 1 ile başlarsa **ikili semafor** bir kilit gibi davranır; ama semaforun asıl gücü sayan biçimidir: "kaç tane kaynak var?" sorusunu doğrudan modeller.

Sınırlı bir tamponda iki semafor kullanılır: `bos` (kaç boş hücre var, başta kapasite) ve `dolu` (kaç dolu hücre var, başta 0). Üretici önce `bos`'u bekler, yazar, `dolu`'yu artırır. Tüketici tersini yapar. Bu yapının tam kodu aşağıdaki sınırlı tampon programında (27.10) yer alıyor.

## 27.9 Koşul değişkeni: neden `while` ve neden kilitle

Sınırlı tamponda şöyle bir sorun var: tampon doluysa üretici ne yapmalı? Kilidi tutarak bekleyen bir döngü (`while (dolu) ;`) kilidi asla bırakmaz ve tüketici hiç çalışamaz. Kilidi bırakıp bir süre uyuyan bir döngü ise (`while (dolu) sleep(1)`) gecikme ve yanıt süresi sorunu yaratır. **Koşul değişkeni** (condition variable) bu ikilemi çözer: `pthread_cond_wait(&c, &kilit)` üç şeyi atomik olarak yapar. Kilidi bırakır, iş parçacığını bir kuyruğa koyup uyutur ve uyanınca kilidi yeniden alır. "Kilidi bırak ve uyu" adımı bölünmez olduğu için, sinyal ile uyuma arasında kaçan bir uyandırma (lost wakeup) olmaz.

Bu bölümde tek bir kural var: **koşulu her zaman bir `while` döngüsünde, kilit altında kontrol et.** Nedenleri iki tanedir. Birincisi, POSIX koşul değişkenleri **sahte uyanmaya** (spurious wakeup) izin verir: iş parçacığı kimse sinyal göndermediği hâlde uyanabilir. İkincisi, sinyal ile uyanış arasında başka bir iş parçacığı veriyi alabilir; uyanan iş parçacığı artık koşulun sağlanmadığını görmelidir. `if` yazan bir kod bu iki durumda bozulur.

Aşağıdaki kodun ilk kısmı, dairesel tamponun veri yapısını ve başlatma fonksiyonunu içerir. `Tampon` yapısı, Bölüm 7.7'deki dairesel tamponla aynı mantıkta (`bas`, `kuyruk`), ama bu sefer `sayi` alanıyla dolu hücre sayısını da tutar ve bir mutex ile iki koşul değişkeni taşır.

```c
/* b27_tampon.c - sinirli tampon: mutex + iki condvar, ve semafor.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread b27_tampon.c
 * Sahte uyanma deneyi icin: -DIF_HATASI ekle (if ile bekleme).
 * Kullanim:
 *   ./a.out kv <uretici> <tuketici> <adet>   (condvar)
 *   ./a.out sem <uretici> <tuketici> <adet>  (semafor)
 *   ./a.out sahte                            (sahte uyanma)
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define KAPASITE 16

typedef struct {
    int veri[KAPASITE];
    int bas;                 /* okunacak indeks */
    int kuyruk;              /* yazilacak indeks */
    int sayi;                /* dolu hucre sayisi */
    pthread_mutex_t kilit;
    pthread_cond_t bos_degil;   /* tuketici bekler */
    pthread_cond_t dolu_degil;  /* uretici bekler */
} Tampon;

```

Koyma ve alma fonksiyonları, koşulun `while` içinde kontrol edildiğini gösteriyor. `koy` tampon doluyken `dolu_degil` koşulunda bekler; `al` tampon boşken `bos_degil` koşulunda bekler. Her iki fonksiyon da bir değişiklikten sonra karşı tarafı uyandırır.

```c
static void tampon_baslat(Tampon *t)
{
    t->bas = t->kuyruk = t->sayi = 0;
    pthread_mutex_init(&t->kilit, NULL);
    pthread_cond_init(&t->bos_degil, NULL);
    pthread_cond_init(&t->dolu_degil, NULL);
}

static void tampon_koy(Tampon *t, int x)
{
    pthread_mutex_lock(&t->kilit);
    while (t->sayi == KAPASITE)            /* while: sahte uyanma */
        pthread_cond_wait(&t->dolu_degil, &t->kilit);
    t->veri[t->kuyruk] = x;
    t->kuyruk = (t->kuyruk + 1) % KAPASITE;
    t->sayi++;
    pthread_cond_signal(&t->bos_degil);
    pthread_mutex_unlock(&t->kilit);
}

static int tampon_al(Tampon *t)
{
    pthread_mutex_lock(&t->kilit);
    while (t->sayi == 0)
        pthread_cond_wait(&t->bos_degil, &t->kilit);
    int x = t->veri[t->bas];
    t->bas = (t->bas + 1) % KAPASITE;
    t->sayi--;
    pthread_cond_signal(&t->dolu_degil);
    pthread_mutex_unlock(&t->kilit);
    return x;
}

/* ---------- semafor surumu ---------- */
```

Bu kuralın neden önemli olduğunu göstermek için bir deney yaptık. Program bir tüketici iş parçacığı başlatır; tüketici tampon boşken bekler. Ana iş parçacığı, veri koymadan koşul değişkenine bir **sahte uyandırma** (broadcast) gönderir. Tüketici `if` ile yazılmış sürümde uyanır, koşulu tekrar kontrol etmez ve boş tampondan okumaya çalışır. `while` sürümünde ise koşul yeniden kontrol edilir ve tüketici tekrar uyur; ana iş parçacığı veriyi koyduğunda doğru değeri alır. Deneyin kodu iki sürümü de üretir (`-DIF_HATASI` ile `if` sürümü).

```c
static void uyku_ms(long ms)
{
    struct timespec t = { ms / 1000, (ms % 1000) * 1000000L };
    nanosleep(&t, NULL);
}

static Tampon st;
/* tuketici kilit altinda isaretler */
static int bekliyor;
static int hata_sayisi;

static void *sahte_tuketici(void *p)
{
    (void)p;
    pthread_mutex_lock(&st.kilit);
    bekliyor = 1;
#ifdef IF_HATASI
    if (st.sayi == 0)                     /* yanlis: if */
        pthread_cond_wait(&st.bos_degil, &st.kilit);
    if (st.sayi == 0) {                   /* uyandi ama tampon bos */
        hata_sayisi++;
        printf("HATA: uyandi ama tampon BOS (sahte uyanma)\n");
        pthread_mutex_unlock(&st.kilit);
        return NULL;
    }
#else
    while (st.sayi == 0)                  /* dogru: while */
        pthread_cond_wait(&st.bos_degil, &st.kilit);
#endif
    int x = st.veri[st.bas];
    st.bas = (st.bas + 1) % KAPASITE;
    st.sayi--;
    printf("tuketici aldi: %d\n", x);
    pthread_mutex_unlock(&st.kilit);
    return NULL;
}

```

Deneyin ana fonksiyonu, tüketicinin beklemeye geçtiğini ve sahte uyandırmanın ardından veriyi koyduğunu sırayla yönetir.

```c
static void sahte_deney(void)
{
    tampon_baslat(&st);
    bekliyor = 0;
    pthread_t t;
    pthread_create(&t, NULL, sahte_tuketici, NULL);
    /* tuketici beklemeye gecene kadar bekle */
    for (;;) {
        pthread_mutex_lock(&st.kilit);
        int b = bekliyor;
        pthread_mutex_unlock(&st.kilit);
        if (b) break;
        uyku_ms(1);
    }
    uyku_ms(20);                        /* cond_wait'e tam otursun */
    /* 1) veri yok, ama sinyal var: sahte uyanma */
    pthread_mutex_lock(&st.kilit);
    pthread_cond_broadcast(&st.bos_degil);
    pthread_mutex_unlock(&st.kilit);
    uyku_ms(50);
    /* 2) simdi gercek veri koy ve sinyal ver */
    pthread_mutex_lock(&st.kilit);
    st.veri[st.kuyruk] = 7;
    st.kuyruk = (st.kuyruk + 1) % KAPASITE;
    st.sayi++;
    pthread_cond_signal(&st.bos_degil);
    pthread_mutex_unlock(&st.kilit);
    pthread_join(t, NULL);
    printf("hata sayisi = %d\n", hata_sayisi);
}

```

Sonuç, deneyin iki sürümü için:

```term
$ ./tampon sahte
tuketici aldi: 7
hata sayisi = 0

$ ./tampon_if sahte
HATA: uyandi ama tampon BOS (sahte uyanma)
hata sayisi = 1
```

`while` sürümü tek bir değer (7) alır, hata sayısı sıfırdır. `if` sürümü bir HATA üretir: uyanmış ama tampon boş. Bu, gerçek bir sistemde bir üretici henüz yazmadan tüketicinin eski ya da çöp bir değer okuması demektir. Dikkat: bu deney sahte uyanmayı zorla üretir; gerçek sistemde sahte uyanma nadirdir. Hata yine de `if` ile yazılmış koda gizlidir ve yük altında çıkar.

## 27.10 Üretici-tüketici: sınırlı tampon ve monitör

Üretici-tüketici problemi, Bölüm 7.7 ve Bölüm 8'de gördüğümüz kuyruk desenini eşzamanlı hâle getirir: bir taraf veri üretir, diğer taraf tüketir, ortada sınırlı bir tampon durur. Tampon dolunca üretici, boşalınca tüketici bekler. İki koşul değişkeni (ya da iki semafor) bu iki bekleme durumunu ayırır. Şekil 27.5 yapıyı gösteriyor.

![Şekil 27.5: Sınırlı tampon. Tek bir mutex tamponu korur; iki koşul değişkeni üreticinin ve tüketicinin beklediği durumları ayırır.](gorseller/b27_tampon_condvar.png)

Bu yapı, bir **monitör**dür. Monitör kavramı, bir kilidi ve onunla ilişkili koşulları tek bir nesnede paketleyen soyutlamadır: nesnenin her yöntemi kilit altında çalışır ve koşul beklemek kilidi otomatik olarak bırakır. Java'nın `synchronized` ve `wait`/`notify` mekanizması, Python'un `threading.Condition` sınıfı ve C'deki bu tampon birer monitördür. Monitörün gücü, kilit disiplinini nesnenin içine koymasıdır: kullanıcı kilidi unutamaz. Kod okuma bölümünde CPython'un `queue.Queue` sınıfının tam olarak bu şekilde yazıldığını göreceksin.

Semafor sürümü aynı tamponu iki semaforla yazar. Semafor sürümünde kilit yalnızca indeksleri korumak için kullanılır; beklemeyi semaforlar yapar.

```c
typedef struct {
    int veri[KAPASITE];
    int bas, kuyruk;
    pthread_mutex_t kilit;
    sem_t bos;               /* kac bos hucre var */
    sem_t dolu;              /* kac dolu hucre var */
} SemTampon;

static void semtampon_baslat(SemTampon *t)
{
    t->bas = t->kuyruk = 0;
    pthread_mutex_init(&t->kilit, NULL);
    sem_init(&t->bos, 0, KAPASITE);
    sem_init(&t->dolu, 0, 0);
}

static void semtampon_koy(SemTampon *t, int x)
{
    sem_wait(&t->bos);                     /* P(bos) */
    pthread_mutex_lock(&t->kilit);
    t->veri[t->kuyruk] = x;
    t->kuyruk = (t->kuyruk + 1) % KAPASITE;
    pthread_mutex_unlock(&t->kilit);
    sem_post(&t->dolu);                    /* V(dolu) */
}

static int semtampon_al(SemTampon *t)
{
    sem_wait(&t->dolu);
    pthread_mutex_lock(&t->kilit);
    int x = t->veri[t->bas];
    t->bas = (t->bas + 1) % KAPASITE;
    pthread_mutex_unlock(&t->kilit);
    sem_post(&t->bos);
    return x;
}

/* ---------- test: P uretici, C tuketici ---------- */
```

Test harness'i, `P` üreticiyi ve `C` tüketiciyi başlatır. Üreticiler her biri `M` benzersiz değer üretir. Tüketiciler değerleri toplar. Bitişte `C` adet "zehirli hap" (`-1`) koyulur; her tüketici bir tanesini alınca çıkar. FIFO sıra sayesinde tüm gerçek değerler zehirli haplardan önce alınmış olur.

```c
static Tampon kv;
static SemTampon sm;
static int MOD;                           /* 0 kv, 1 sem */
static int M;                             /* uretici basina adet */
static int P, C;

typedef struct {
    long toplam;
    long adet;
} Sonuc;

static void *uretici(void *p)
{
    long id = (long)p;
    for (int i = 0; i < M; i++) {
        int deger = (int)(id * M + i);     /* benzersiz deger */
        if (MOD == 0) tampon_koy(&kv, deger);
        else semtampon_koy(&sm, deger);
    }
    return NULL;
}

static void *tuketici(void *p)
{
    Sonuc *s = p;
    for (;;) {
        int x = (MOD == 0) ? tampon_al(&kv) : semtampon_al(&sm);
        if (x < 0) break;                  /* zehirli hap: dur */
        s->toplam += x;
        s->adet++;
    }
    return NULL;
}

static void sonuc_yaz(Sonuc *top, long beklenen_adet,
                       long beklenen_top)
{
    int tam = (top->adet == beklenen_adet) &&
              (top->toplam == beklenen_top);
    printf("alinan adet=%ld (beklenen %ld)\n",
           top->adet, beklenen_adet);
    printf("toplam     =%ld (beklenen %ld)\n",
           top->toplam, beklenen_top);
    printf("sonuc: %s\n", tam ? "DOGRU" : "HATA");
}

static int dogrulama_calistir(int mod, int p, int c, int m)
{
    MOD = mod; P = p; C = c; M = m;
    if (MOD == 0) tampon_baslat(&kv);
    else semtampon_baslat(&sm);

    pthread_t up[32], tp[32];
    static Sonuc son[32];
    memset(son, 0, sizeof son);
    for (long i = 0; i < P; i++)
        pthread_create(&up[i], NULL, uretici, (void *)i);
    for (long i = 0; i < C; i++)
        pthread_create(&tp[i], NULL, tuketici, &son[i]);
    for (int i = 0; i < P; i++)
        pthread_join(up[i], NULL);
    /* uretici bitti: C tuketiciyi durdurmak icin C zehirli hap */
    for (int i = 0; i < C; i++) {
        if (MOD == 0) tampon_koy(&kv, -1);
        else semtampon_koy(&sm, -1);
    }
    for (int i = 0; i < C; i++)
        pthread_join(tp[i], NULL);

    Sonuc top;
    memset(&top, 0, sizeof top);
    for (int i = 0; i < C; i++) {
        top.toplam += son[i].toplam;
        top.adet += son[i].adet;
    }
    long beklenen_top = 0;
    for (long id = 0; id < P; id++)
        for (long i = 0; i < M; i++)
            beklenen_top += id * M + i;
    sonuc_yaz(&top, (long)P * M, beklenen_top);
    return top.adet == (long)P * M && top.toplam == beklenen_top;
}

/* ---------- sahte uyanma: if ile bekleyen tuketici ---------- */
```

Ana fonksiyon, test ve sahte uyanma deneyini komut satırından seçer.

```c
int main(int argc, char **argv)
{
    if (argc < 2) return 1;
    if (!strcmp(argv[1], "sahte")) {
        sahte_deney();
        return 0;
    }
    if (argc < 5) return 1;
    int mod = !strcmp(argv[1], "sem");
    int ok = dogrulama_calistir(mod, atoi(argv[2]), atoi(argv[3]),
                                atoi(argv[4]));
    return ok ? 0 : 2;
}
```

Doğrulama, toplam ve adet kontrolüyle yapılır: alınan değer adedi ve değerlerin toplamı, üretilenle birebir tutmalı. Üç üretici ve üç tüketici, her üretici için 200.000 değer (toplam 600.000) ile çalıştırıldı:

```term
$ ./tampon kv 3 3 200000
alinan adet=600000 (beklenen 600000)
toplam     =179999700000 (beklenen 179999700000)
sonuc: DOGRU

$ ./tampon sem 3 3 200000
alinan adet=600000 (beklenen 600000)
toplam     =179999700000 (beklenen 179999700000)
sonuc: DOGRU
```

Her iki sürüm de tutarlı sonuç verdi. Aynı programı TSan ile, daha küçük bir girdiyle çalıştırdığımızda da veri yarışı uyarısı çıkmadı (aşağıda 27.17'de).

Bu bölümde iki tuzağı özellikle not et. Birincisi, tek bir mutex ile iki koşul değişkeni kullanmak, hem üreticilerin hem tüketicilerin aynı kilide girmesi demektir; bu, yük altında bir darboğaz olabilir. Burada bunu kabul ediyoruz ve sadeliği seçiyoruz. İkincisi, dairesel tamponda `kuyruk` ve `bas` indekslerini kilit olmadan kullanan kilitsiz SPSC tasarımı (7.7'deki yapı) yalnız bir üretici ve bir tüketici için doğrudur; çok üreticili bir durumda kilit ya da daha karmaşık bir yapı gerekir.

## 27.11 Kilitlenme (deadlock)

Kilitler doğru olsa bile birbirine bağlanabilir. İki kilit kullanan iki iş parçacığını düşün. Birinci iş parçacığı A'yı alır, ikinci B'yi alır; sonra birinci B'yi, ikinci A'yı ister. İkisi de karşı tarafın tuttuğu kilidi bekler ve hiçbiri ilerleyemez. Bu durum **kilitlenme** (deadlock) olarak adlandırılır ve Bölüm 27.2'deki ilerleme şartının ihlalidir.

Kilitlenmenin dört koşulu 1971'de Coffman ve arkadaşları tarafından tanımlandı (genel bilgi). Dördü birlikte sağlandığında kilitlenme mümkündür:

1. **Karşılıklı dışlama**: bir kaynak aynı anda yalnız bir sahibe ait olabilir.
2. **Tut ve bekle**: bir iş parçacığı bir kaynağı tutarken başka bir kaynak için bekleyebilir.
3. **Önleme yok**: bir kaynak, sahibi tarafından gönüllü olarak bırakılmadan alınamaz.
4. **Döngüsel bekleme**: bekleyen iş parçacıklarının oluşturduğu bir döngü vardır.

Dört koşuldan birini kırmak kilitlenmeyi önler. Pratikte en yaygın yöntem dördüncüyü kırmaktır: kilitleri her zaman önceden belirlenmiş bir sırayla almak. Döngü oluşmaz çünkü hiçbir iş parçacığı küçük numaralı bir kilidi, daha büyük numaralı bir kilidi tuttuğu hâlde almaz.

Bu durumu bir **kaynak tahsis grafiğiyle** gösterebiliriz: kilitler ve iş parçacıkları düğüm, "sahiplik" ve "bekleme" kenarları da ok. Döngü varsa kilitlenme vardır. Şekil 27.6 iki iş parçacıklı klasik döngüyü gösteriyor.

![Şekil 27.6: Kaynak tahsis grafiğinde döngü. T1, A'yı tutuyor ve B'yi bekliyor; T2, B'yi tutuyor ve A'yı bekliyor. Döngü kırılmadıkça kimse ilerleyemez.](gorseller/b27_kaynak_grafi.png)

### Banka havalesi: deadlock'u üret, tespit et, düzelt

Klasik bir örnek olarak iki hesap arasında havale yapalım. Her hesabın bir kilidi var. Havale fonksiyonu, kaynak hesabın kilidini alır, bir süre bekler (bu, iki kilit arasındaki pencereyi genişleten yapay bir gecikme), sonra hedef hesabın kilidini alır. İki iş parçacığı zıt yönde havale yapıyor: A'dan B'ye ve B'den A'ya.

Tespit için bir numara kullanıyoruz: kilit alırken `pthread_mutex_timedlock` ile bir saniye zaman aşımı koyuyoruz. Kilit bu sürede alınamazsa "kilitlenme şüphesi" yazıp programı çıkarıyoruz. Dikkat: zaman aşımı bir **kanıt değil, bir şüphedir**. Yavaş bir sistemde de zaman aşımı olabilir; bu yüzden gerçek sistemlerde kilit grafını izleyen araçlar kullanılır (genel bilgi). Burada basitlik için zaman aşımı yeterli.

Programın ilk kısmı, zaman aşımlı kilit alma fonksiyonunu ve gecikmeleri içerir.

```c
/* b27_kilitlenme.c - kilitlenme (deadlock): uretim, tespit, onlem.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread b27_kilitlenme.c
 * Kullanim:
 *   ./a.out banka-bozuk
 *   ./a.out banka-sirali
 *   ./a.out filozof-bozuk
 *   ./a.out filozof-sirali
 *   ./a.out filozof-trylock
 * Tespit: 1 saniye icinde kilit alinamazsa "zaman asimi" yazilir ve
 * program 3 koduyla cikar. Zaman asimi kanit degil, suphedir.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define ZAMAN_ASIMI_SN 1
#define N 5

static void uyku_ms(long ms)
{
    struct timespec t = { ms / 1000, (ms % 1000) * 1000000L };
    nanosleep(&t, NULL);
}

static void uyku_us(long us)
{
    struct timespec t = { us / 1000000L, (us % 1000000L) * 1000L };
    nanosleep(&t, NULL);
}

/* Kilidi zaman asimiyla al; asilirsa kilitlenme suphesi raporla. */
static void kilitle(pthread_mutex_t *m, const char *ad)
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec += ZAMAN_ASIMI_SN;
    if (pthread_mutex_timedlock(m, &ts) == ETIMEDOUT) {
        printf("ZAMAN ASIMI: %s kilidi %d sn alinamadi\n",
               ad, ZAMAN_ASIMI_SN);
        printf("-> kilitlenme suphesi (cikis kodu 3)\n");
        fflush(stdout);
        _exit(3);
    }
}

/* ---------- banka havalesi ---------- */
```

Havale fonksiyonu ve hesap yapısı aşağıda. `SIRALI` bayrağı, kilitleri kimlik sırasına göre alıp almayacağımızı belirler: bu, döngüsel bekleme koşulunu kırar.

```c
typedef struct {
    pthread_mutex_t kilit;
    long bakiye;
    int id;
} Hesap;

static Hesap h[2];
static int SIRALI;
static long TUR;

static void havale(Hesap *a, Hesap *b, long miktar)
{
    Hesap *ilk = a, *ikinci = b;
    /* sirali: kilitleri her zaman kimlik sirasiyla al */
    if (SIRALI && b->id < a->id) {
        ilk = b;
        ikinci = a;
    }
    kilitle(&ilk->kilit, ilk->id ? "hesap B" : "hesap A");
    uyku_ms(1);             /* ara sicaklik: penceyi genis tut */
    kilitle(&ikinci->kilit, ikinci->id ? "hesap B" : "hesap A");
    a->bakiye -= miktar;
    b->bakiye += miktar;
    pthread_mutex_unlock(&ikinci->kilit);
    pthread_mutex_unlock(&ilk->kilit);
}

```

İş parçacıkları ve banka testi, aşağıda. Testin toplamı korunmalıdır: iki hesabın bakiyesi toplamı başta 2000 olmalıdır; havaleler para yaratmaz ya da yok etmez.

```c
static void *banka_t1(void *p)
{
    (void)p;
    for (long i = 0; i < TUR; i++)
        havale(&h[0], &h[1], 1);      /* A -> B */
    return NULL;
}

static void *banka_t2(void *p)
{
    (void)p;
    for (long i = 0; i < TUR; i++)
        havale(&h[1], &h[0], 1);      /* B -> A */
    return NULL;
}

static void banka(int sirali)
{
    SIRALI = sirali;
    TUR = 200;
    for (int i = 0; i < 2; i++) {
        pthread_mutex_init(&h[i].kilit, NULL);
        h[i].bakiye = 1000;
        h[i].id = i;
    }
    pthread_t a, b;
    pthread_create(&a, NULL, banka_t1, NULL);
    pthread_create(&b, NULL, banka_t2, NULL);
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    long toplam = h[0].bakiye + h[1].bakiye;
    printf("kilitlenme yok; toplam bakiye = %ld (beklenen 2000)\n",
           toplam);
}

/* ---------- yemek yiyen filozoflar ---------- */
```

Sıralı olmayan sürüm kilitlenir, sıralı sürüm bitirir. Sonuçlar, `kilitlenme_term` çıktısının ilk iki bölümünde (ve kalanı filozoflarda):

```term
$ ./kilitlenme banka-bozuk
ZAMAN ASIMI: hesap A kilidi 1 sn alinamadi
-> kilitlenme suphesi (cikis kodu 3)
cikis kodu: 3

$ ./kilitlenme banka-sirali
kilitlenme yok; toplam bakiye = 2000 (beklenen 2000)
cikis kodu: 0

$ ./kilitlenme filozof-bozuk
ZAMAN ASIMI: catal (sag) kilidi 1 sn alinamadi
-> kilitlenme suphesi (cikis kodu 3)
cikis kodu: 3

$ ./kilitlenme filozof-sirali
kilitlenme yok; toplam yemek = 250 (beklenen 250)
cikis kodu: 0

$ ./kilitlenme filozof-trylock
kilitlenme yok; toplam yemek = 250 (beklenen 250)
cikis kodu: 0
```

Bozuk sürümde iki iş parçacığı da zaman aşımına uğradı (ilk satır hesap A, ikinci hesap B için yazdı; bu iki zaman aşımının neredeyse aynı anda olduğunu gösterir). Sıralı sürüm kilitlenmeden ve bakiye toplamı 2000 olarak bitti. Dikkat edilecek nokta: sıralı sürümde aynı yapay gecikme (1 ms) hâlâ var. Yani sıralama, gecikme kadar güçlü bir tetikleyiciyi bile etkisiz kılar.

### Yemek yiyen filozoflar: döngüsel bekleme klasiği

Dijkstra'nın (genel bilgi) beş filozof ve beş çatal problemi, kilitlenme için mükemmel bir oyuncaktır. Her filozof sol ve sağ çatalı almak ister; bütün filozoflar aynı anda sol çatalı alırsa kimse sağ çatalı alamaz. Şekil 27.7'de durum gösterilmiştir.

![Şekil 27.7: Yemek yiyen filozoflar. Herkes sol çatalını aldığında her sağ çatal, sağındaki filozofun elindedir: döngüsel bekleme.](gorseller/b27_filozof.png)

Aşağıdaki kod üç strateji içerir: `bozuk` (sol, sonra sağ; yapay gecikmeyle), `sirali` (küçük numaralı çatal önce) ve `trylock` (ilk kilidi al, ikincisini `pthread_mutex_trylock` ile dene; başarısızsa geri çek ve rastgele bekle). Filozof fonksiyonu, üç stratejinin tamamını tek yerde içerir.

```c
static pthread_mutex_t cat[N];
static long yemek[N];
/* MODF: 0 bozuk, 1 sirali, 2 trylock */
static int MODF;
static long FTUR;

static void *filozof(void *p)
{
    int i = (int)(long)p;
    int sol = i, sag = (i + 1) % N;
    unsigned tohum = 17u + (unsigned)i;
    for (long t = 0; t < FTUR; t++) {
        if (MODF == 0) {
            kilitle(&cat[sol], "catal (sol)");
            uyku_ms(1);               /* herkes solu almis olsun */
            kilitle(&cat[sag], "catal (sag)");
        } else if (MODF == 1) {
            int a = sol < sag ? sol : sag;
            int b = sol < sag ? sag : sol;
            kilitle(&cat[a], "catal (kucuk)");
            uyku_ms(1);
            kilitle(&cat[b], "catal (buyuk)");
        } else {
            for (;;) {
                kilitle(&cat[sol], "catal (sol)");
                if (pthread_mutex_trylock(&cat[sag]) == 0)
                    break;
                pthread_mutex_unlock(&cat[sol]);
                /* rastgele geri cekilme */
                uyku_us(rand_r(&tohum) % 500);
            }
        }
        yemek[i]++;                   /* yemek */
        pthread_mutex_unlock(&cat[sag]);
        pthread_mutex_unlock(&cat[sol]);
    }
    return NULL;
}

```

Ana fonksiyon ve filozof stratejilerinin seçimi, aşağıda.

```c
static void filozoflar(int mod)
{
    MODF = mod;
    FTUR = 50;
    for (int i = 0; i < N; i++)
        pthread_mutex_init(&cat[i], NULL);
    pthread_t th[N];
    for (long i = 0; i < N; i++)
        pthread_create(&th[i], NULL, filozof, (void *)i);
    for (int i = 0; i < N; i++)
        pthread_join(th[i], NULL);
    long toplam = 0;
    for (int i = 0; i < N; i++)
        toplam += yemek[i];
    printf("kilitlenme yok; toplam yemek = %ld (beklenen %ld)\n",
           toplam, (long)N * FTUR);
}

int main(int argc, char **argv)
{
    if (argc < 2) return 1;
    if (!strcmp(argv[1], "banka-bozuk")) banka(0);
    else if (!strcmp(argv[1], "banka-sirali")) banka(1);
    else if (!strcmp(argv[1], "filozof-bozuk")) filozoflar(0);
    else if (!strcmp(argv[1], "filozof-sirali")) filozoflar(1);
    else if (!strcmp(argv[1], "filozof-trylock")) filozoflar(2);
    else { fprintf(stderr, "bilinmeyen mod\n"); return 1; }
    return 0;
}
```

Sonuçlar, kilitlenme terminal çıktısının son üç bölümünde. Bozuk stratejide hiçbir filozof yemek yiyemedi ve zaman aşımı devreye girdi. Sıralı ve `trylock` stratejilerinde 250 yemeğin tamamı (her filozof için 50) yendi.

Sıralı stratejinin sağlamlığını test etmek için aynı programı 30 kez daha çalıştırdık: hiçbiri zaman aşımına uğramadı. Ancak geliştirme sırasında sıralı sürümde bir kez 1 saniyelik bir zaman aşımı görüldü ve sonraki denemelerde tekrarlanmadı. Bunun nedeni kanıtlanmadı; WSL2 sanal makinesinin kısa bir duraklaması olabilir. Bu, zaman aşımı tabanlı tespitin doğasında olan belirsizliğin pratik bir örneği: zaman aşımı, kilitlenme ile yük altındaki yavaşlığı ayırt edemez.

## 27.12 Livelock ve açlık

Kilitlenmenin iki kardeşi vardır. **Livelock** (canlı kilitlenme), iş parçacıkları bloke olmadan ama sonuç üretmeden sürekli tepki vererek döngüye girdiğinde oluşur. Örneğin iki kişi dar bir koridorda karşılaşır, ikisi de aynı yöne çekilir ve tekrar karşılaşırlar. `trylock` stratejisi bu tuzağa düşebilir: iki filozof da aynı anda ilk çatalı alıp ikinciyi alamayınca bırakır ve aynı anda tekrar dener. Bunu önleyen şey **rastgele** geri çekilme süresidir: yukarıdaki kodda `rand_r` ile yapılıyor. Rastgelelik, simetriyi kırar. Deterministik bir geri çekilme (her zaman 1 ms) livelock'a yol açabilirdi.

**Açlık** (starvation), bir iş parçacığının kaynağı süresiz alamamasıdır; diğerleri kaynağı sürekli alıyorsa oluşur. Sıralı kilit stratejisinde açlık mümkündür: 0 numaralı çatalı sürekli kapan bir filozof, 4 numaralı filozofu (0'ı da ister) uzun süre bekletebilir. Bu bölümdeki 50 yemeklik test buna karşı sınır koyar, ama bir garanti vermez. Bir açlık-serbest (starvation-free) kilit için kuyruk tabanlı adil bir sıra gerekir; Linux çekirdeğindeki bilet (ticket) tabanlı ve kuyruk tabanlı spinlock'lar bu amaçla tasarlanmıştır (genel bilgi; ayrıntılar sürüme bağlıdır).

Bu bölümün dersi şudur: kilitlenme ilerleme şartını, livelock ilerleme şartının **anlamlı** bir biçimini, açlık sınırlı bekleme şartını kırar. Üçü de "hiçbir şey olmuyor gibi görünür" ama nedenleri farklıdır; tanı için farklı araçlar gerekir.

## 27.13 Öncelik terslemesi (priority inversion)

Bölüm 26'da zamanlayıcının öncelikli iş parçacıklarını önce çalıştırdığını gördük. Peki yüksek öncelikli bir iş parçacığı, düşük öncelikli bir iş parçacığının tuttuğu bir kilidi beklerse ne olur? Düşük öncelikli olan kilidi bırakmak için CPU'ya ihtiyaç duyar; ama CPU, ondan daha yüksek öncelikli ama kilitle hiç ilgisi olmayan bir orta öncelikli iş parçacığına verilmiştir. Sonuç: en önemli iş parçacığı, en önemsiz olanın bekletilmesi yüzünden, orta öncelikli bir iş parçacığının süresi kadar bekler. Buna **öncelik terslemesi** (priority inversion) denir.

Bu, savunma ve gerçek zamanlı sistemlerde ciddi bir sorundur. Bir uçuş kontrol görevi, bir sensör veri yolu kilidi beklerken, orta öncelikli bir telemetri görevi CPU'yu tutuyorsa, uçuş kontrolü zamanında çalışamaz. Bu tür bir hatanın tanısı zordur çünkü her görev kendi açısından doğru davranmaktadır.

**Mars Pathfinder olayı** (1997, genel bilgi): NASA'nın Mars Pathfinder iniş aracı, VxWorks gerçek zamanlı işletim sisteminde çalışıyordu. Yüksek öncelikli bir veri yolu yönetim görevi, düşük öncelikli bir ölçüm görevinin tuttuğu ortak bir mutex'i bekledi. Orta öncelikli iletişim görevi CPU'yu tekrar tekrar aldı. Yüksek öncelikli görev zamanında çalışamayınca bir bekçi zamanlayıcısı (watchdog) sistemi sıfırladı. Çözüm, mutex'te **öncelik kalıtımının** açılmasıydı; bu özellik kapalı geliyordu ve yerden yükleme ile etkinleştirildi (genel bilgi, ayrıntılar kaynaklara göre değişebilir).

**Öncelik kalıtımı** (priority inheritance), kilidi tutan düşük öncelikli iş parçacığının önceliğini, kilidi bekleyenlerin en yükseğine geçici olarak yükseltmesidir. Kilit bırakıldığında eski önceliği geri döner. Böylece orta öncelikli görev, kilidi tutanı kesemez. POSIX bunu `PTHREAD_PRIO_INHERIT` protokolüyle sunar.

Bu senaryoyu gerçek bir zamanlayıcıda ölçmek istedik. Ancak gerçek zamanlı zamanlama (SCHED_FIFO) için ayrıcalık gerekir, ve bu ortamda izin verilmiyor. Aşağıdaki kontrol programı, bu kısıtı ve kalıtım API'sinin kullanılabilirliğini doğrular.

```c
/* b27_oncelik_kontrol.c - SCHED_FIFO ve PTHREAD_PRIO_INHERIT izni */
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
int main(void)
{
    struct sched_param sp = { .sched_priority = 10 };
    int r = sched_setscheduler(0, SCHED_FIFO, &sp);
    printf("SCHED_FIFO: %s\n", r == 0 ? "izinli" : strerror(errno));
    pthread_mutexattr_t a;
    pthread_mutexattr_init(&a);
    int p = pthread_mutexattr_setprotocol(&a, PTHREAD_PRIO_INHERIT);
    printf("PRIO_INHERIT ayari: %s\n",
           p == 0 ? "tamam" : strerror(p));
    int q;
    pthread_mutexattr_getprotocol(&a, &q);
    printf("protokol degeri = %d (PTHREAD_PRIO_INHERIT=%d)\n", q,
           PTHREAD_PRIO_INHERIT);
    return 0;
}
```

Çıktı:

```term
SCHED_FIFO: Operation not permitted
PRIO_INHERIT ayari: tamam
protokol degeri = 1 (PTHREAD_PRIO_INHERIT=1)
```

SCHED_FIFO reddedildi (`Operation not permitted`), ama `PTHREAD_PRIO_INHERIT` ayarı kabul edildi ve değeri 1 olarak okundu. Yani kalıtım API'si kullanılabilir, ama gerçek zamanlı bir öncelik ortamı kurulamadı. Bu nedenle senaryoyu **deterministik bir simülasyonla** gösteriyoruz: tek CPU, sabit öncelikli ve önleyici (preemptive) bir zamanlayıcı, tek bir mutex. Simülasyon, Mars olayındaki üç görevin yapısını taşır: düşük öncelikli `L` kilidi tutar, yüksek öncelikli `H` kilidi ister, orta öncelikli `M` araya girer.

Simülasyonun ilk kısmı, görev modelini ve etkin önceliği hesaplar. Kalıtım etkinse, kilidi tutan görev, kilidi bekleyenlerin en yüksek önceliğini alır.

```python
# -*- coding: utf-8 -*-
"""b27_oncelik_sim.py - oncelik terslemesi ve kalitim simulasyonu.

Tek CPU, sabit oncelikli, onleyici zamanlayici; tek muteks.
Gercek zamanli zamanlama (SCHED_FIFO) bu ortamda izinli degil;
senaryo bu yuzden deterministik bir simulasyonla gosterilir.
Zaman birimi = 1 tick.

Calistirma: python -I b27_oncelik_sim.py
"""


class Gorev:
    def __init__(self, ad, oncelik, varis, islem):
        self.ad = ad
        self.taban = oncelik        # sabit (baz) oncelik
        self.varis = varis          # ne zaman hazir olur
        # islem: ("cpu", n) | ("kilit",) | ("birak",)
        self.islem = list(islem)
        self.kilit_bekliyor = False
        self.bitti = False


def etkin_oncelik(g, muteks, kalitim):
    p = g.taban
    if kalitim and muteks["sahip"] is g and muteks["bekleyen"]:
        p = max([p] + [w.taban for w in muteks["bekleyen"]])
    return p


```

Zamanlayıcının çekirdeği aşağıda. Her tick'te, bloke olmayan en yüksek etkin öncelikli görev seçilir; kilit işlemleri zaman harcamadan yapılır. Kilit bırakıldığında kilit, bekleyenlerin en yükseğine doğrudan geçer.

```python
def simul(kalitim):
    muteks = {"sahip": None, "bekleyen": []}
    L = Gorev("L", 1, 0, [("kilit",), ("cpu", 3), ("birak",)])
    H = Gorev("H", 3, 1, [("kilit",), ("cpu", 1), ("birak",)])
    M = Gorev("M", 2, 2, [("cpu", 4)])
    gorevler = [L, H, M]
    satirlar = []
    h_bekleme = 0
    t = 0
    while not all(g.bitti for g in gorevler):
        notlar = ""
        secilen = None
        # bloke olan gorev ayni tick'te yerini birakir
        while secilen is None:
            hazir = [g for g in gorevler
                     if g.varis <= t and not g.bitti
                     and not g.kilit_bekliyor]
            if not hazir:
                break
            g = max(hazir,
                    key=lambda x: etkin_oncelik(x, muteks, kalitim))
            while g.islem and g.islem[0][0] != "cpu":
                op = g.islem.pop(0)
                if op[0] == "kilit":
                    if muteks["sahip"] is None:
                        muteks["sahip"] = g
                        notlar += " [%s aldi]" % g.ad
                    else:
                        g.kilit_bekliyor = True
                        muteks["bekleyen"].append(g)
                        notlar += " [%s bekliyor]" % g.ad
                        g.islem.insert(0, op)
                        break
                else:  # birak
                    muteks["sahip"] = None
                    notlar += " [%s birakti]" % g.ad
                    if muteks["bekleyen"]:
                        en = max(muteks["bekleyen"],
                                 key=lambda x: x.taban)
                        muteks["bekleyen"].remove(en)
                        en.kilit_bekliyor = False
                        en.islem.pop(0)
                        muteks["sahip"] = en
                        notlar += " -> %s'e gecti" % en.ad
            if g.kilit_bekliyor:
                continue            # bu gorev bekliyor; yeniden sec
            secilen = g
```

Döngünün geri kalanı, bloke olan görevin aynı tick içinde yerini başka bir göreve bırakmasını ve tamamlanma durumunu işler.

```python
        if secilen is None:
            satirlar.append("t=%d  CPU bos%s" % (t, notlar))
            t += 1
            continue
        g = secilen
        if g.islem and g.islem[0][0] == "cpu":
            n = g.islem[0][1]
            if n == 1:
                g.islem.pop(0)
            else:
                g.islem[0] = ("cpu", n - 1)
        if not g.islem:
            g.bitti = True
            notlar += " [%s bitti]" % g.ad
        if H.kilit_bekliyor:
            h_bekleme += 1
        sahip = muteks["sahip"].ad if muteks["sahip"] else "-"
        bekleyen = ",".join(w.ad for w in muteks["bekleyen"]) or "-"
        satirlar.append("t=%d  CPU: %s  sahip: %s  bekleyen: %s%s"
                        % (t, g.ad, sahip, bekleyen, notlar))
        t += 1
    return satirlar, h_bekleme, t


```

Simülasyonun giriş ve çıktı kısmı aşağıda. İki senaryo, kalıtım olmadan ve kalıtımla birlikte ayrı ayrı çalıştırılır.

```python
def yazdir(baslik, satirlar, h_bekleme, bitis):
    print("== " + baslik)
    for s in satirlar:
        print(s)
    print("H'nin kilit bekleme suresi: %d tick" % h_bekleme)
    print("tum gorevler %d. tick'te bitti" % bitis)
    print()


if __name__ == "__main__":
    s1, b1, e1 = simul(kalitim=False)
    yazdir("Oncelik kalitimi YOK", s1, b1, e1)
    s2, b2, e2 = simul(kalitim=True)
    yazdir("Oncelik kalitimi VAR (PTHREAD_PRIO_INHERIT benzeri)",
           s2, b2, e2)
```

Çıktı:

```term
== Oncelik kalitimi YOK
t=0  CPU: L  sahip: L  bekleyen: - [L aldi]
t=1  CPU: L  sahip: L  bekleyen: H [H bekliyor]
t=2  CPU: M  sahip: L  bekleyen: H
t=3  CPU: M  sahip: L  bekleyen: H
t=4  CPU: M  sahip: L  bekleyen: H
t=5  CPU: M  sahip: L  bekleyen: H [M bitti]
t=6  CPU: L  sahip: L  bekleyen: H
t=7  CPU: L  sahip: H  bekleyen: - [L birakti] -> H'e gecti [L bitti]
t=8  CPU: H  sahip: H  bekleyen: -
t=9  CPU: H  sahip: -  bekleyen: - [H birakti] [H bitti]
H'nin kilit bekleme suresi: 6 tick
tum gorevler 10. tick'te bitti

== Oncelik kalitimi VAR (PTHREAD_PRIO_INHERIT benzeri)
t=0  CPU: L  sahip: L  bekleyen: - [L aldi]
t=1  CPU: L  sahip: L  bekleyen: H [H bekliyor]
t=2  CPU: L  sahip: L  bekleyen: H
t=3  CPU: L  sahip: H  bekleyen: - [L birakti] -> H'e gecti [L bitti]
t=4  CPU: H  sahip: H  bekleyen: -
t=5  CPU: H  sahip: -  bekleyen: - [H birakti] [H bitti]
t=6  CPU: M  sahip: -  bekleyen: -
t=7  CPU: M  sahip: -  bekleyen: -
t=8  CPU: M  sahip: -  bekleyen: -
t=9  CPU: M  sahip: -  bekleyen: - [M bitti]
H'nin kilit bekleme suresi: 2 tick
tum gorevler 10. tick'te bitti
```

Sonuç: kalıtım yokken H, kilidi 6 tick boyunca bekler; bu süre boyunca M, H'den önce CPU'yu alır (2–5. tick). Kalıtım varken L'nin önceliği 3'e yükselir; M araya giremez ve H'nin bekleme süresi 2 tick'e iner. Şekil 27.8 bu iki senaryoyu yan yana gösteriyor.

![Şekil 27.8: Öncelik terslemesi ve kalıtım. Taralı alan H'nin kilidi beklediği süredir. Kalıtım olmadan M, H'den önce çalışır; kalıtımla bekleme 6 tick'ten 2 tick'e iner.](gorseller/b27_oncelik_zaman.png)

::: not
Bu bir simülasyondur, gerçek zamanlayıcı ölçümü değildir. Simülasyon, zamanlama kararlarının mantığını gösterir; gerçek sistemde bağlam değişimi süreleri, kesmeler ve önbellek etkileri de vardır. Gerçek ölçüm için SCHED_FIFO yetkisi olan bir Linux makinesi ya da bir RTOS hedefi gerekir.
:::

## 27.14 Sahte paylaşım (false sharing)

Bölüm 25'te önbellek satırının 64 bayt olduğunu ve bütün bir satırın birlikte taşındığını gördük. Bu, iki iş parçacığı **farklı** değişkenleri yazsa bile, o değişkenler aynı satırdaysa çekişme yaşayacakları anlamına gelir. Bir iş parçacığı kendi sayacını artırdığında, satırın sahipliği diğer çekirdekten alınır; diğer iş parçacığı kendi sayacını artırmak için tekrar sahiplik ister. Satır çekirdekler arasında sürekli gidip gelir. Değerler doğru kalır (her biri kendi değişkenine yazar), ama hız çöker. Buna **sahte paylaşım** (false sharing) denir: paylaşım gerçek değil, yalnızca bellek düzeninden kaynaklanır.

Bunu ölçmek için iki düzen karşılaştırdık. Birincisi, sayaçların bitişik olduğu düzen: sekiz sayaç (her biri 8 bayt) tek 64 baytlık satıra sığar. İkincisi, her sayacın 64 bayt hizalandığı düzen: her sayaç kendi satırında. Her iş parçacığı kendi sayacını beş milyon kez `atomik` artırır. Atomik artırma, derleyicinin döngüyü silmesini engeller ve satırı her seferinde gerçekten yazar.

```c
/* b27_fs.c - sahte paylasim (false sharing) olcumu.
 * Derleme: gcc -O2 -std=c11 -pthread b27_fs.c -o fs
 * Kullanim: ./fs <yerlesim> <thread> <islem>
 *   yerlesim: bitisik  (sayaclar ayni onbellek satirinda)
 *             ayri     (her sayac 64 bayt hizali, kendi satirinda)
 * Cikti: tek satir, islem basina nanosaniye (thread basina).
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAKS 16
#define SATIR 64

struct bitisik {
    long sayac[MAKS];                    /* 8 * 16 = 128 bayt */
};

struct ayri {
    struct { long sayac; char dolgu[SATIR - sizeof(long)]; }
        kutu[MAKS] __attribute__((aligned(SATIR)));
};

static struct bitisik bit_v;
static struct ayri ayr_v;
static int MOD;                          /* 0 bitisik, 1 ayri */
static long K;
static int T;

```

Ölçüm fonksiyonu, her iş parçacığı için aynı sayacı artırır ve sonucu doğrular.

```c
static void *isci(void *p)
{
    long id = (long)p;
    for (long i = 0; i < K; i++) {
        if (MOD == 0)
            __atomic_fetch_add(&bit_v.sayac[id], 1, __ATOMIC_RELAXED);
        else
            __atomic_fetch_add(&ayr_v.kutu[id].sayac, 1,
                               __ATOMIC_RELAXED);
    }
    return NULL;
}

static double simdi(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

```

Ana fonksiyon düzeni, iş parçacığı sayısını ve işlem sayısını alır; her çalıştırma için işlem başına süreyi nanosaniye olarak yazar.

```c
int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr,
                "kullanim: %s <bitisik|ayri> <thread> <islem>\n",
                argv[0]);
        return 1;
    }
    MOD = !strcmp(argv[1], "ayri");
    T = atoi(argv[2]);
    K = atol(argv[3]);
    if (T < 1 || T > MAKS) return 1;

    pthread_t th[MAKS];
    double t0 = simdi();
    for (long i = 0; i < T; i++)
        pthread_create(&th[i], NULL, isci, (void *)i);
    for (int i = 0; i < T; i++)
        pthread_join(th[i], NULL);
    double dt = simdi() - t0;

    long toplam = 0;
    for (int i = 0; i < T; i++)
        toplam += MOD ? ayr_v.kutu[i].sayac : bit_v.sayac[i];
    if (toplam != (long)T * K) {
        fprintf(stderr, "HATA: toplam %ld\n", toplam);
        return 2;
    }
    printf("%.2f\n", dt * 1e9 / K);  /* her thread K islem yapti */
    return 0;
}
```

Beş tekrarın medyanı (işlem başına nanosaniye, düşük iyi):

| İş parçacığı | Bitişik | 64 bayt hizalı | Oran |
|---|---|---|---|
| 1 | 1,7 | 1,7 | 1× |
| 2 | 16,9 | 1,8 | 9,7× |
| 4 | 41,1 | 1,8 | 22× |
| 8 | 85,2 | 2,0 | 43× |
| 16 | 88,2 | 3,1 | 28× |

![Şekil 27.9: Sahte paylaşım. Bitişik sayaçlar iş parçacığı sayısıyla birlikte çok yavaşlıyor; hizalı sayaçlar neredeyse düz kalıyor.](gorseller/b27_false_sharing.png)

Bir iş parçacığında iki düzen aynıdır: çekişme yoktur. İki iş parçacığında bitişik düzen yaklaşık on kat yavaşlar. Sekiz iş parçacığında ise yaklaşık kırk üç kat. 16 iş parçacığında oran düşer, çünkü 16 mantıksal çekirdek 8 fiziksel çekirdeğe eşlenir ve ölçümün kendisi SMT'nin etkisini taşır; hizalı düzen de 16'da 3 ns'ye yükselir. Ölçüm, bu makinede ve bu iş yükünde, sahte paylaşımın bir hata değil, performans bedeli olduğunu gösteriyor.

Pratik sonuç: paylaşılan veriyi tasarlarken, birbirinden bağımsız ama sık yazılan değişkenleri ayrı önbellek satırlarına koy. Linux çekirdeği bunun için `____cacheline_aligned_in_smp` gibi makrolar kullanır (genel bilgi). C11'de `alignas(64)` bunu sağlar. Bölüm 25'in önbellek satırı bilgisi burada doğrudan kullanıldı.

## 27.15 Kilitsiz yığın (Treiber) ve ABA problemi

Kilitsiz (lock-free) bir yapıda hiçbir iş parçacığı diğerini bloke etmez; bir iş parçacığı takılsa bile sistemin geri kalanı ilerler. Bunun en bilinen örneği, 1986'da R. K. Treiber'in tanımladığı yığındır (genel bilgi). Yığın, tek bir `head` işaretçisiyle yönetilir. `push` ve `pop` işlemleri, `head`'i bir CAS ile değiştirir ve başarısızlıkta yeniden dener.

Aşağıdaki kod, düğümleri bir havuzdan indeksle tutan bir Treiber yığınıdır. İki sürüm var: `naif` (yalnız indeks, etiketsiz) ve `etiketli` (indeksle birlikte bir sayaç). Kod ayrıca iki iş parçacığının aynı düğümü çift sahiplenmesini (`sahiplik`) ve yığının bozulmasını ölçer. İlk kısım, havuz ve atomik alanları tanımlar.

```c
/* b27_yigin.c - kilitsiz (lock-free) Treiber yigini ve ABA.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread b27_yigin.c
 * Kullanim:
 *   ./a.out aba                 (adim adim ABA senaryosu)
 *   ./a.out naive <thread> <r> <pencere>  (etiketsiz head)
 *   ./a.out tagged <thread> <r> <pencere> (etiketli head)
 *   pencere=1: okuma ile CAS arasina sched_yield koyar
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sched.h>

#define DUGUM 64
#define NIL 0xFFFFFFFFu
#define PAKET(etiket, idx) (((uint64_t)(etiket) << 32) | (idx))
#define IDX(h) ((uint32_t)(h))
#define ETIKET(h) ((uint32_t)((h) >> 32))

static _Atomic uint32_t sonraki[DUGUM];   /* yiginda bir sonraki */
static _Atomic uint32_t bas_naif;         /* etiketsiz bas */
static _Atomic uint64_t bas_etiketli;     /* etiket + indeks */
/* 1'den fazlaysa cift sahiplik */
static _Atomic int sahiplik[DUGUM];
static _Atomic long cift_sahip;
static int MOD;                           /* 0 naif, 1 etiketli */
/* 1: okuma ile CAS arasina kesinti */
static int PENCERE;

/* ---------- etiketsiz (ABA'ya acik) ---------- */
```

Naif `push` ve `pop` aşağıda. `push` yeni düğümü `head`'in mevcut değerine bağlar ve CAS ile `head`'i yeni düğüme çevirir. `pop`, `head`'in sonrakini okur ve CAS ile onu `head` yapar.

```c
static void naif_it(uint32_t i)
{
    uint32_t eski = atomic_load(&bas_naif);
    do {
        atomic_store(&sonraki[i], eski);
    } while (!atomic_compare_exchange_weak(&bas_naif, &eski, i));
}

static uint32_t naif_cek(void)
{
    uint32_t eski = atomic_load(&bas_naif);
    for (;;) {
        if (eski == NIL)
            return NIL;
        uint32_t n = atomic_load(&sonraki[eski]);
        if (PENCERE) sched_yield();   /* ABA penceresini genislet */
        if (atomic_compare_exchange_weak(&bas_naif, &eski, n))
            return eski;
    }
}

/* ---------- etiketli (ABA'ya karsi) ---------- */
static void etiketli_it(uint32_t i)
{
    uint64_t eski = atomic_load(&bas_etiketli);
    uint64_t yeni;
    do {
        atomic_store(&sonraki[i], IDX(eski));
        yeni = PAKET(ETIKET(eski) + 1, i);
    } while (!atomic_compare_exchange_weak(&bas_etiketli,
                                           &eski, yeni));
}

```

Etiketli sürüm, `head`'i 64 bitlik bir pakete koyar: üst 32 bit bir etiket, alt 32 bit indeks. Her başarılı işlemde etiket artar.

```c
static uint32_t etiketli_cek(void)
{
    uint64_t eski = atomic_load(&bas_etiketli);
    for (;;) {
        uint32_t idx = IDX(eski);
        if (idx == NIL)
            return NIL;
        uint32_t n = atomic_load(&sonraki[idx]);
        uint64_t yeni = PAKET(ETIKET(eski) + 1, n);
        if (PENCERE) sched_yield();   /* ABA penceresini genislet */
        if (atomic_compare_exchange_weak(&bas_etiketli, &eski, yeni))
            return idx;
    }
}

/* ---------- ABA senaryosu: adim adim, tek iparcacik ---------- */
/* Burada CAS'i duz degiskenlerle taklit ediyoruz: amac durumu
 * adim adim gostermek; eszamanlilik yok. */
static uint32_t S[3];                     /* A=0, B=1, C=2 */
static uint32_t HEAD;
static const char *AD[3] = {"A", "B", "C"};

```

ABA problemini anlamadan Treiber'i anlamış sayılmazsın. Bir iş parçacığı `head`'in `A` olduğunu ve `A`'nın sonrakisinin `B` olduğunu okur. Sonra duraklar. Diğer iş parçacıkları `A`'yı ve `B`'yi çıkarır, `A`'yı geri iter. Şimdi `head` yine `A`'dır. Duraklamış iş parçacığının CAS'i `head == A` karşılaştırmasını yapar, başarılı olur ve `head`'i eski `sonraki`'ye, yani `B`'ye çevirir. Ama `B` artık yığında değildir! CAS yalnız **değere** bakar; değerin aynı kalıp kalmadığına, arada A→B→A gibi bir yolculuk olup olmadığına bakmaz. Bu ABA problemidir: A değer olarak geri döner, ama yapı artık farklıdır.

Şekil 27.10 senaryonun adımlarını ve iki sürümün farkını gösteriyor.

![Şekil 27.10: ABA senaryosu. Duraklamış iş parçacığının CAS'i, head'in yeniden A olmasını fark etmez; B'yi head yapar ve A'yı kaybeder.](gorseller/b27_aba.png)

Senaryoyu tek bir iş parçacığında adım adım göstermek için bir yardımcı fonksiyon yazdık. CAS'i düz bir karşılaştırma ve atamayla taklit eder; eşzamanlılık yoktur, amaç her adımın durumunu yazdırmaktır. Elle izleme tablosu da aşağıda, programın çıktısıyla birebir eşleşiyor.

| Adım | T1 | T2 | head | Yığın |
|---|---|---|---|---|
| 1 | `eski = A`, `sonraki = B` okur, duraklar | | A | A → B → C |
| 2 | | `pop` (A çıkar) | B | B → C |
| 3 | | `pop` (B çıkar) | C | C |
| 4 | | `push A` | A | A → C |
| 5 | `CAS(head, A, B)` başarılı | | B | B → C (A kayboldu) |
| 6 | | `push B`: `sonraki[B] = B` | B | B → B (döngü) |

Adım 5'te CAS başarılıdır çünkü `head` yine `A`'dır; ama `A` artık yığında değildir. Adım 6'da `B`'yi geri iten T2, `B`'nin sonrakisini kendisi yaptığı için yığın bir döngüye girer. Etiketli sürümde adım 5'teki CAS başarısız olur: T2'nin `pop`/`push` işlemleri etiketi 0'dan 3'e çıkarmıştır, T1'in beklediği `(0, A)` artık `(3, A)`'dır.

Stres testinin sonuçları, simülasyondan sonra verilmiştir. Naif sürüm, okuma ile CAS arasına bir `sched_yield` (pencere genişletici) konulduğunda belirgin biçimde bozuldu. Bu pencereyi kapalı bırakmak yalnız "normal" zamanlamayı temsil eder; ama ABA'nın tetiklenmesi için iş parçacığının o pencerede kesilmesi gerekir. Bu yüzden ölçümde pencereyi bilerek açtık.

```c
static void yaz_durum(const char *etiket)
{
    printf("%-30s head=", etiket);
    if (HEAD == NIL) { printf("NIL"); }
    else { printf("%s", AD[HEAD]); }
    printf("  zincir: ");
    uint32_t c = HEAD;
    int adim = 0;
    while (c != NIL && adim < 3) {
        printf("%s", AD[c]);
        c = S[c];
        if (c != NIL) printf(" -> ");
        adim++;
    }
    if (c != NIL) printf("...(dongu!)");
    printf("\n");
}

```

Simülasyon fonksiyonu aşağıda.

```c
static void aba_senaryosu(void)
{
    S[0] = 1; S[1] = 2; S[2] = NIL; HEAD = 0;   /* A -> B -> C */
    yaz_durum("baslangic:");

    uint32_t t1_eski = HEAD;                    /* T1: eski = A */
    uint32_t t1_sonraki = S[t1_eski];           /* T1: sonraki = B */
    printf("T1 eski=%s, sonraki=%s okudu, duraklatildi\n",
           AD[t1_eski], AD[t1_sonraki]);

    HEAD = S[HEAD]; /* T2 pop: A cikar, head = B */
    HEAD = S[HEAD]; /* T2 pop: B cikar, head = C */
    S[0] = HEAD; HEAD = 0;                      /* T2 push: A geri */
    yaz_durum("T2 A,B cikardi, A geri koydu:");

    if (HEAD == t1_eski) {                      /* T1 CAS(head,A,B) */
        HEAD = t1_sonraki;
        printf("T1 CAS basarili (head hala A!) -> head = B\n");
    }
    yaz_durum("T1 CAS sonrasi:");
    printf("A artik zincirde degil: sizdi.\n");

    S[1] = HEAD;                        /* T2 B'yi geri iter */
    HEAD = 1;
    yaz_durum("T2 B'yi geri itti:");
}

/* ---------- stres ---------- */
static int R;
static int TH;

```

Stres testi için yardımcı fonksiyonlar ve iş parçacığı döngüsü aşağıda. Her iş parçacığı düğüm çeker, kısa bir süre sahiplenir (rastgele `sched_yield`), sonra geri iter. Sahiplik sayacı iki iş parçacığının aynı düğümü sahiplenmesini yakalar.

```c
static uint64_t xorshift(uint64_t *s)
{
    uint64_t x = *s;
    x ^= x << 13; x ^= x >> 7; x ^= x << 17;
    return *s = x;
}

static void *isci(void *p)
{
    uint64_t rng = 0x9E3779B97F4A7C15ull ^ (uintptr_t)p;
    for (int r = 0; r < R; r++) {
        uint32_t i = (MOD == 0) ? naif_cek() : etiketli_cek();
        if (i == NIL) continue;
        if (atomic_fetch_add(&sahiplik[i], 1) != 0)
            atomic_fetch_add(&cift_sahip, 1);
        int bekle = (int)(xorshift(&rng) % 64);
        for (int k = 0; k < bekle; k++)
            sched_yield();
        atomic_fetch_sub(&sahiplik[i], 1);
        if (MOD == 0) naif_it(i); else etiketli_it(i);
    }
    return NULL;
}

```

Stres testinin ana kısmı, havuzu yığına koyar, iş parçacıklarını başlatır ve yığını bitişte boşaltarak yapının bütünlüğünü kontrol eder.

```c
static void stres(void)
{
    /* bas bos olmali: sifir degeri 0 numarali dugume isaret eder */
    atomic_store(&bas_naif, NIL);
    atomic_store(&bas_etiketli, PAKET(0, NIL));
    for (uint32_t i = 0; i < DUGUM; i++) {
        if (MOD == 0) naif_it(DUGUM - 1 - i);
        else etiketli_it(DUGUM - 1 - i);
    }
    pthread_t th[32];
    for (long i = 0; i < TH; i++)
        pthread_create(&th[i], NULL, isci, (void *)(i + 1));
    for (int i = 0; i < TH; i++)
        pthread_join(th[i], NULL);

    /* yigini bosalt; dongu ya da fazla eleman varsa bozulmus */
    int say = 0, dongu = 0;
    uint32_t c = (MOD == 0) ? bas_naif : IDX(bas_etiketli);
    while (c != NIL) {
        if (++say > DUGUM) { dongu = 1; break; }
        c = atomic_load(&sonraki[c]);
    }
    printf("%s thread=%d r=%d\n", MOD ? "etiketli" : "naif",
           TH, R);
    printf("cift sahiplik: %ld\n", atomic_load(&cift_sahip));
    if (dongu)
        printf("yigin: DONGU VAR (bozuldu)\n");
    else
        printf("yigin uzunlugu: %d (beklenen %d)\n", say, DUGUM);
}

```

Ana fonksiyon, test türünü ve pencereyi komut satırından alır.

```c
int main(int argc, char **argv)
{
    if (argc < 2) return 1;
    if (!strcmp(argv[1], "aba")) {
        aba_senaryosu();
        return 0;
    }
    if (argc < 5) return 1;
    MOD = !strcmp(argv[1], "tagged");
    TH = atoi(argv[2]);
    R = atoi(argv[3]);
    PENCERE = atoi(argv[4]);
    stres();
    return 0;
}
```

Sonuçlar, `yigin_term` çıktısında:

```term
$ ./yigin aba
baslangic:                     head=A  zincir: A -> B -> C
T1 eski=A, sonraki=B okudu, duraklatildi
T2 A,B cikardi, A geri koydu:  head=A  zincir: A -> C
T1 CAS basarili (head hala A!) -> head = B
T1 CAS sonrasi:                head=B  zincir: B -> C
A artik zincirde degil: sizdi.
T2 B'yi geri itti:             head=B  zincir: B -> B -> B -> ...(dongu!)

$ ./yigin naive 4 300000 0
naif thread=4 r=300000
cift sahiplik: 0
yigin uzunlugu: 64 (beklenen 64)

$ ./yigin naive 4 100000 1
naif thread=4 r=100000
cift sahiplik: 289057
yigin: DONGU VAR (bozuldu)

$ ./yigin naive 4 100000 1
naif thread=4 r=100000
cift sahiplik: 38
yigin uzunlugu: 59 (beklenen 64)

$ ./yigin tagged 4 100000 1
etiketli thread=4 r=100000
cift sahiplik: 0
yigin uzunlugu: 64 (beklenen 64)
```

Okuma:
- Simülasyonda ABA adım adım gözlendi: 5. adımda A kayboldu, 6. adımda yığın döngüye girdi.
- Naif sürüm, pencere açıkken her koşuda bozuldu. Çift sahiplik değerleri 32 ile 289.057 arasında ve yığın uzunluğu 59 ya da 60 (beklenen 64) ya da döngü. Değerler koşudan koşuya değişiyor; sabit bir sayı yok, ama bozulma her seferinde var. Pencere kapalıyken (`0`) iki koşuda da yığın sağlamdı.
- Etiketli sürüm, pencere açıkken bile hiçbir koşuda bozulmadı (çift sahiplik 0, uzunluk 64).

### Etiketin bedeli ve sınırları

Etiket, ABA'yı pratikte çok zor hâle getirir ama kesin olarak önlemez. 32 bitlik bir etiket, 4 milyar değişiklikten sonra tekrar eder; gerçek bir sistemde bu dar bir pencere de olabilir. Ayrıca bu örnekte düğümler yalnızca havuza geri döner ve hiçbir zaman `free` ile serbest bırakılmaz; gerçek dünyada bellek serbest bırakma (düğümü yığından çıkarıp başka bir iş parçacığının hâlâ okuyabileceği durumda bırakmak) ABA ile birlikte ayrı bir sorundur. Bu sorunu çözmek için hazard pointer ve epoch tabanlı geri kazanım gibi teknikler kullanılır (genel bilgi).

Bir başka önemli gözlem, bir sonraki bölümde ele alacağımız ThreadSanitizer ile ilgilidir: naif yığın ABA ile bozulurken TSan **hiçbir uyarı** vermedi (27.17). ABA bir veri yarışı değil, mantıksal bir yarıştır; tüm bellek erişimleri atomiktir. Bu nedenle araç, programın doğruluğunu garanti etmez.

## 27.16 RCU: okuyucuya neredeyse bedava, yazıcıya bekleme

Read-Copy-Update (RCU), Linux çekirdeğinde yaygın kullanılan bir tekniktir (genel bilgi). Fikir şudur: okuyucular kilit almaz, sadece `rcu_read_lock()` ile bir okuma bölgesine girer ve işaretçiyi okur. Yazıcı veriyi **kopyalar**, kopyayı değiştirir ve işaretçiyi atomik olarak yeni kopyaya çevirir. Eski kopya hemen serbest bırakılmaz: `synchronize_rcu()` çağrısı, sistemdeki tüm eski okuyucuların okuma bölgelerinden çıkmasını (bir "grace period") bekler, sonra eski kopyayı serbest bırakır.

Bu, okuma ağırlıklı verilerde (yönlendirme tabloları, dizin girdileri) okuyucunun maliyetini neredeyse sıfıra indirir; bedeli yazıcının beklemesi ve belleğin biraz daha uzun tutulmasıdır. RCU'yu bu bölümde ölçmedik; yalnızca kavramını anlatıyoruz. Bölüm 26'daki iş parçacığı kavramına ve bu bölümdeki bellek sıralamasına (`release`/`acquire`) dayanır: yayınlanan yeni işaretçinin okuyucu tarafından doğru veriyle görülmesi, tam da bu sıralamalarla sağlanır.

## 27.17 ThreadSanitizer: veri yarışını derleyici ile yakalamak

Bölüm 6'da ASan ve UBSan'ı tanıttık. Eşzamanlılık için ThreadSanitizer (TSan) var. `-fsanitize=thread` ile derlenen program, her bellek erişimini izler ve bir yazmanın başka bir iş parçacığının erişimiyle senkronizasyon olmadan çakıştığını raporlar. TSan, ASan ile birlikte kullanılamaz (genel bilgi); ayrı derlenir.

Yarışlı `sayac++` sürümünü (27.1) TSan ile çalıştırdık. Derleme komutu `gcc -O1 -g -fsanitize=thread`. Bu ortamda (WSL2, çekirdek 6.6) TSan ilk denemede "unexpected memory mapping" hatası verdi; `-no-pie` yardımcı olmadı, `setarch x86_64 -R` (adres alanı rastgeleleştirmesini kapatır) çözdü. Bu, WSL'e özgü bir kurulum notu; başka sistemlerde gerekmeyebilir.

```term
$ ./rmw_tsan plain 2
==================
WARNING: ThreadSanitizer: data race
  Read of size 8 at 0x555555558080 by thread T2:
    #0 art_plain b27_rmw.c:22
    #1 is_parcacik b27_rmw.c:44
  Previous write of size 8 at 0x555555558080 by thread T1:
    #0 art_plain b27_rmw.c:22
    #1 is_parcacik b27_rmw.c:44
  Location is global 'plain_sayac' of size 8
SUMMARY: ThreadSanitizer: data race b27_rmw.c:22 in art_plain
==================

$ ./rmw_tsan mutex 2
mod=mutex    thread=2 n=10000000
gercek   = 20000000
kayip    = 0 (0.00%)

$ ./tampon_tsan kv 3 3 20000
sonuc: DOGRU

$ ./yigin_tsan naive 4 20000 1
cift sahiplik: 0
yigin uzunlugu: 62 (beklenen 64)
uyari sayisi (naive ABA): 0
```

Çıktıda "WARNING: ThreadSanitizer: data race" satırı, iki erişimi (okuma ve önceki yazma), her birinin yığın izini ve bellek konumunu veriyor. Raporu okumak, hatayı bulmanın yarısıdır. Yukarıdaki çıktı, uzun yolları ve BuildId'leri kısaltılmış hâliyle veriyor; gerçek rapor tam hâlini gösterir.

Aynı programın mutex'li sürümü TSan'dan temiz geçti. Sınırlı tampon (27.10) ve ABA'lı yığın için de TSan uyarısı sayıldı: tampon için 0 uyarı; naif yığın için 0 uyarı, ama yapı bozuk. Bu son sonuç, aracın sınırını gösterir. TSan veri yarışlarını yakalar; mantıksal yarışları (ABA gibi) yakalamaz. Doğruluk kanıtı için hâlâ test ve akıl yürütme gerekir.

## 27.18 Python: GIL ve `x += 1`

Python'da iş parçacıkları vardır ama CPython, **GIL** (Global Interpreter Lock) adı verilen tek bir kilidi kullanarak aynı anda yalnız bir iş parçacığının Python bayt kodu çalıştırmasına izin verir. Bu, Python'un kendi nesne yapılarını korur. Ama GIL, **kullanıcı kodundaki yarışları** otomatik olarak önlemez. `x += 1` tek bir Python ifadesidir ama birden çok bayt kodu komutudur. Aşağıda `dis` çıktısında bunu görüyoruz.

```python
# -*- coding: utf-8 -*-
"""b27_gil.py - Python'da x += 1 ve GIL.

Calistirma: python -I b27_gil.py
Not: CPython 3.12.10. GIL, iplik degisimini yalnizca belirli bayt kodu
noktalarinda (ornegin fonksiyon girisi, geri atlama) yoklar.
"""
import dis
import sys
import threading

N = 1000000


def artir_global():
    global sayac
    for _ in range(N):
        sayac += 1


def kimlik(x):
    return x


def artir_cagrili():
    global sayac
    for _ in range(N):
        sayac = sayac + kimlik(1)   # cagri: iplik degisebilecek nokta


def artir_kilitli():
    global sayac
    for _ in range(N):
        with kilit:
            sayac += 1


```

Deney fonksiyonları ve ana kısım aşağıda. Dört sürüm var: düz `sayac += 1`, aynı sürüm daha sık iplik değişimiyle (`switchinterval = 1 µs`), bir fonksiyon çağrısı araya girmiş `sayac = sayac + kimlik(1)`, ve bir `threading.Lock` içinde `sayac += 1`.

```python
def kos(hedef, ipler=2):
    global sayac
    sayac = 0
    t = [threading.Thread(target=hedef) for _ in range(ipler)]
    for x in t:
        x.start()
    for x in t:
        x.join()
    return sayac


if __name__ == "__main__":
    print("Python", sys.version.split()[0])
    print("== x += 1 bayt kodu (global):")
    dis.dis(artir_global)
    beklenen = 2 * N
    kilit = threading.Lock()

    sayac = 0
    print("artir_global  : %d (beklenen %d)"
          % (kos(artir_global), beklenen))
    sys.setswitchinterval(1e-6)
    print("artir_global, switchinterval=1us: %d" % kos(artir_global))
    sys.setswitchinterval(0.005)
    print("artir_cagrili : %d (beklenen %d)"
          % (kos(artir_cagrili), beklenen))
    print("artir_kilitli : %d (beklenen %d)"
          % (kos(artir_kilitli), beklenen))
```

Sonuçlar:

```term
Python 3.12.10
== x += 1 bayt kodu (global):
 15           0 RESUME                   0

 17           2 LOAD_GLOBAL              1 (NULL + range)
             12 LOAD_GLOBAL              2 (N)
             22 CALL                     1
             30 GET_ITER
        >>   32 FOR_ITER                11 (to 58)
             36 STORE_FAST               0 (_)

 18          38 LOAD_GLOBAL              4 (sayac)
             48 LOAD_CONST               1 (1)
             50 BINARY_OP               13 (+=)
             54 STORE_GLOBAL             2 (sayac)
             56 JUMP_BACKWARD           13 (to 32)

 17     >>   58 END_FOR
             60 RETURN_CONST             0 (None)
artir_global  : 2000000 (beklenen 2000000)
artir_global, switchinterval=1us: 2000000
artir_cagrili : 1856776 (beklenen 2000000)
artir_kilitli : 2000000 (beklenen 2000000)
```

Üç gözlem var. Birincisi, `x += 1` bu sürümde (CPython 3.12.10) iki iş parçacığında kayıpsız çalıştı. Bunun nedeni şudur: 3.12'de iplik değişimi, GIL'in yoklandığı noktalarda olur (fonksiyon girişi ve geri atlama gibi); `LOAD_GLOBAL`, `BINARY_OP`, `STORE_GLOBAL` dizisinin ortasında yoklama yoktur. Bu, `dis` çıktısından okunabilir. İkincisi, bu bir **garanti değildir**: bu sonuç sürüme ve yapılandırmaya bağlıdır. Üçüncüsü, araya bir fonksiyon çağrısı girdiğinde yarış hemen görünür: ilk deneyde 1.054.166, ikinci deneyde 1.856.776 (iki milyon artıştan), yani yaklaşık yarısı ya da daha fazlası kayboldu. Çağrının girişindeki yoklama, iplik değişimini okuma ve yazma arasına taşır. `threading.Lock` sürümü doğrudur.

Ders: "Python'da GIL var, o halde `+=` güvenli" yanlıştır. GIL bayt kodu düzeyinde korur; kullanıcı kodunun değişmez bir işlem olmadığını bilmek senin sorumluluğundur. Python 3.13 ve sonrasında serbest iş parçacıklı (free-threaded) derleme deneysel olarak sunulur (genel bilgi); orada bu tür yarışlar daha sık görülebilir.

## 27.19 Gömülü dünya: kesme kapatma, volatile ve sınırlar

Tek çekirdekli bir mikrodenetleyicide (Bölüm 43-44'te göreceksin) iş parçacığı yoktur ama kesmeler vardır. Ana döngü ile kesme işleyicisi (ISR) arasında paylaşılan veri bir yarış oluşturur. Burada en sık kullanılan kilit, **kesmeleri kapatmaktır**: kritik bölgeye girmeden önce kesmeleri devre dışı bırak, çıkarken yeniden etkinleştir. ARM Cortex-M'de bu `PRIMASK` yazmacıyla yapılır (genel bilgi). x86'da `cli` ve `sti` komutları kullanılır.

Kesme bağlamında kurallar sıkıdır. Bir ISR içinde uyku, `malloc` ya da bir mutex beklemek yasaktır, çünkü ISR'ın bir iş parçacığı bağlamı yoktur. Bir spinlock de ISR içinde tehlikelidir: kilidi tutan iş parçacığı ISR tarafından kesilmişse, ISR o kilidi beklerse sistem kendi kendini kilitler.

MertOS deposunda (`D:\Mevcut Projeler\GitHub\Operating-System`, salt okunur) bu kalıbı arayınca şunları gördük. `kernel/arch/x86_64/idt.cpp`, 107. satırda `asm volatile("sti")` ile kesmeleri etkinleştirir. Aynı dosyanın 159. satırındaki `asm volatile("cli; hlt")` bir istisna işleyicisinde sistemi durdurur. `kernel/arch/x86_64/entry.asm` 243. satırda `cli` ile çekirdek dönüşünde durur; `kernel/process/context_switch.asm` 81. satırda bir sürecin bitişinde boşa döner. Bu üç kullanım da durma yoludur, kritik bölge değildir. Deponun sürücülerinde bir kesme kapatma kritik bölgesi bulamadık; klavye sürücüsünün halka tamponu (`pushEvent`, `popEvent`) ise tek üretici (ISR) ve tek tüketici (ana döngü) mantığına dayanır ve bu yüzden kesme kapatmadan çalışır. Bu, yalnızca x86 TSO altında ve bu tek üretici/tüketici düzeninde doğru; `volatile` burada senkronizasyon sağlamaz, sadece derleyicinin okumaları bellekten yapmasını sağlar.

`volatile` konusunda son bir not. `volatile`, derleyiciye "bu değer beklenmedik şekilde değişebilir" der. Ama atomiklik sağlamaz (27.1'de `volatile` sayacın yarışını ortadan kaldırmadığını gördük) ve bellek sıralaması da sağlamaz. Çok çekirdekli sistemlerde ya da ARM'da, paylaşılan değişkenler için `_Atomic` ve açık bellek sıralaması gerekir. Gömülü mülakatların en sevilen sorularından biri budur: "volatile bir senkronizasyon aracı mıdır?" Cevap hayırdır.

## Çözümlü Örnekler

Dört örnek, zorluk sırasına göre ilerler: ★, ★★, ★★, ★★★. Her biri Bölüm 5'in altı adımını izler: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Doğrulama adımında elle iz sürme tablosu var. Önce tabloyu kendi kafanda ya da bir kâğıtta doldurmaya çalış; sonra programla karşılaştır.

### Örnek 1 (★): İki artış, tek sonuç

Bir sayaç iki iş parçacığı tarafından birer kez artırılıyor. Başlangıçta sayaç 0. Sonuç 2 olmalı mı, 1 olabilir mi?

**Adım 1 — Anla.** Her iş parçacığı tek bir `sayac++` yapar. Sorunun sorusu şudur: iki artış birbirini ezer mi? Cevap, artışın kaç adımdan oluştuğuna bağlı. 27.1'de gördük: üç adım (oku, artır, yaz).

**Adım 2 — Örnekle.** Girdi yok; durum tek sayaçtır. Olası bir zamanlamayı yazmak için her iş parçacığının yerel yazmacını `r1` ve `r2` ile adlandırıyoruz.

**Adım 3 — Kaba çöz.** Kaba çözüm, zamanlamayı rastgele seçip sonuca bakmaktır. Bu, bir deneme olur ama bir kanıt olmaz. Daha iyi bir yol, en kötü zamanlamayı kurmaktır: iki iş parçacığı da okumayı bitirip yazmadan önce birbirini görmesin.

**Adım 4 — Örüntü.** Örüntü şudur: iki okuma aynı eski değeri görürse, iki yazma da aynı yeni değeri yazar ve bir artış kaybolur. Bu, okuma-yazma serpiştirmesinin genel durumudur.

**Adım 5 — İyileştir.** İyileştirme, üç adımın arasına girilemeyecek bir yapı koymaktır. Atomik `fetch_add` bu üçlüyü tek bir `lock add` komutuna indirir (27.6). İyileştirilmiş sürümde iki artış da görünür olmalıdır.

**Adım 6 — Doğrula.** Aşağıdaki tablo, en kötü zamanlamayı (düz sayaç) ve atomik sürümü yan yana gösteriyor:

| Adım | T1 (düz) | T2 (düz) | sayac | T1 (atomik) | T2 (atomik) | sayac (atomik) |
|---|---|---|---|---|---|---|
| 1 | `r1 = sayac` (0) | | 0 | `lock add` | | 0 → 1 |
| 2 | | `r2 = sayac` (0) | 0 | | `lock add` | 1 → 2 |
| 3 | `r1 = r1 + 1` (1) | | 0 | bitti | bitti | 2 |
| 4 | | `r2 = r2 + 1` (1) | 0 | | | 2 |
| 5 | `sayac = r1` | | 1 | | | 2 |
| 6 | | `sayac = r2` | 1 (kayıp!) | | | 2 |

Programın gerçek sonucu, rmw deneyinde iki iş parçacığı ile on milyonlu döngüde şuydu: düz sürüm 20.000.000 yerine yaklaşık 10.200.000; atomik sürüm 20.000.000. Tek iş parçacığında kayıp yok.

**Bunu AI'sız yazabilir misin?** Üç iş parçacığı, her biri `sayac++`'yı iki kez yapsın. Başlangıç 0 ise, düz sayaçla alabileceğin en küçük ve en büyük sonuçlar nedir? Her birini bir serpiştirme tablosuyla göster.

### Örnek 2 (★★): Sınırlı tampon: tek kilit, iki koşul

Kapasitesi 2 olan bir tamponu, tek üretici ve tek tüketici ile düşün. Üretici 1, 2, 3 değerlerini koyar; tüketici hepsini alır. Tampon dolunca üretici ne yapar, boşalınca tüketici ne yapar?

**Adım 1 — Anla.** Üretici `koy`, tüketici `al` yapar. Tampon iki hücrelidir. Doluluk sayısı `sayi` ile tutulur. Hedef: değerler kayıpsız, sırayla alınmalı ve hiçbir zaman dolu tampona yazılmamalı ya da boş tampondan okunmamalı.

**Adım 2 — Örnekle.** Kapasite 2, değerler 1, 2, 3. Başlangıçta `sayi = 0`.

**Adım 3 — Kaba çöz.** Kaba çözüm, kilit olmadan `if (sayi == 2) bekle;` yazmaktır. Bu, iki iş parçacığı aynı anda kontrol ettiğinde bozulur, ayrıca sahte uyanmaya karşı savunmasızdır (27.9).

**Adım 4 — Örüntü.** Örüntü şudur: bekleme koşulu kilit altında `while` ile kontrol edilmeli; bekleme ve uyanma koşul değişkeniyle, kilit bırakılarak yapılmalı. Bu, 27.9'un kuralıdır.

**Adım 5 — İyileştir.** Bir mutex ve iki koşul değişkeni (`bos_degil`, `dolu_degil`) kullan. Koy: `while (sayi == KAPASITE) bekle(dolu_degil)`; sonra yaz ve `bos_degil`'i sinyalle. Al: tersini yap.

**Adım 6 — Doğrula.** Tablo, tek tamponda (kapasite 2) üç değerin işlenişini gösteriyor:

| Adım | İşlem | veri (bas..kuyruk) | sayi | Ne olur |
|---|---|---|---|---|
| 1 | koy(1) | [1, _] | 1 | yazıldı |
| 2 | koy(2) | [1, 2] | 2 | yazıldı, şimdi dolu |
| 3 | koy(3) | [1, 2] | 2 | üretici `dolu_degil`'de bekler |
| 4 | al() | [_, 2] | 1 | 1 alındı; `dolu_degil` sinyali |
| 5 | (üretici uyanır) yaz 3 | [3, 2] | 2 | yazıldı |
| 6 | al() x2 | [_, _] | 0 | 2, 3 alındı |

Program sürümü, üç üretici ve üç tüketici ile 600.000 değer için toplamı ve adedi doğruladı (27.10). Bu tablo tek üretici/tek tüketici için en küçük durumu gösterir.

**Bunu AI'sız yazabilir misin?** Aynı tamponu yalnız bir koşul değişkeniyle (`bos_degil` ve `dolu_degil` yerine tek kondisyon) yaz. Hangi durumda uyandırılmamış bir iş parçacığı sonsuza kadar bekler? `broadcast` kullanmak bunu çözer mü, yoksa sadece gizler mi?

### Örnek 3 (★★): Banka havalesinde kilitlenme ve kilit sıralaması

İki hesap, iki kilit. Bir iş parçacığı A'dan B'ye, diğeri B'den A'ya havale yapıyor. Sistem neden kilitleniyor ve nasıl düzelir?

**Adım 1 — Anla.** Havale, kaynak hesabın kilidini alır, sonra hedefinkini. İki iş parçacığı zıt yönde. Kilitlenmenin dört koşulundan (27.11) hangileri var?

**Adım 2 — Örnekle.** T1: `kilitle(A)`, sonra `kilitle(B)`. T2: `kilitle(B)`, sonra `kilitle(A)`. Aralarında 1 ms bekleme olsun.

**Adım 3 — Kaba çöz.** Kaba çözüm, bekleme süresini artırmak ya da zaman aşımıyla yeniden denemektir. Bu bir olasılığı azaltır ama yapıyı değiştirmez; yük altında yine kilitlenir.

**Adım 4 — Örüntü.** Döngüsel bekleme oluşuyor: T1, A'yı tutup B'yi bekliyor; T2, B'yi tutup A'yı bekliyor. Döngüyü kıran tek şey, iki iş parçacığının aynı sırayla kilit almasıdır.

**Adım 5 — İyileştir.** Kilitleri hesap kimliğine göre sırala: küçük kimlik önce. Her iki iş parçacığı da A'yı önce alır. Döngü oluşmaz.

**Adım 6 — Doğrula.** Tablo, bozuk ve sıralı durumları zaman adımlarıyla yan yana koyuyor:

| Zaman | Bozuk: T1 | Bozuk: T2 | Sıralı: T1 | Sıralı: T2 |
|---|---|---|---|---|
| 0 | A kilitler | B kilitler | A kilitler | A bekler |
| 1 | B bekler (A tutulu) | A bekler (B tutulu) | B kilitler, havale | (A'da bekler) |
| 2 | ... ilerleme yok | ... ilerleme yok | bırakır | A'yı alır, B'yi alır |

Programın gerçek çıktısı, bozuk sürümde iki iş parçacığının da zaman aşımına uğradığını, sıralı sürümde bakiye toplamının 2000 olarak korunduğunu gösterdi (27.11). Dikkat: sıralı sürümde yapay 1 ms gecikme hâlâ var. Sıralama, gecikmenin tetiklediği kilitlenmeyi etkisiz kılar.

**Bunu AI'sız yazabilir misin?** Üç hesap A, B, C olsun. T1 A→B, T2 B→C, T3 C→A havalesi yapıyor. Kilitleri sıralamadan döngüsel bekleme nasıl oluşur? Sıralı kilit kuralını bu üç hesaba uygulayınca hangi sıra ortaya çıkar?

### Örnek 4 (★★★): Treiber yığınında ABA'yı elle izlemek

Bir CAS tabanlı yığında, değerin aynı olması durumunun aynı olduğu anlamına gelmez. Bu örnek, ABA'yı tek bir iş parçacığı üzerinde adım adım izler ve etiketli işaretçinin neden çözdüğünü gösterir.

**Adım 1 — Anla.** Yığın `A → B → C`. T1 `pop` için `head`'in A ve sonrakinin B olduğunu okur, duraklar. T2 A ve B'yi çıkarır, A'yı geri iter. Sonra T1 devam eder.

**Adım 2 — Örnekle.** Naif sürüm, T1'in CAS'i `(head == A)` karşılaştırmasını yapar. Etiketli sürüm, `(etiket, indeks)` çiftini karşılaştırır.

**Adım 3 — Kaba çöz.** Kaba çözüm, düğümleri hiç yeniden kullanmamaktır (her düşüş yeni bellek). Bu ABA'yı önler ama bellek yönetimi sorununu büyütür: düğümleri nasıl serbest bırakacaksın?

**Adım 4 — Örüntü.** ABA'nın kökü, CAS'in yalnız değere bakmasıdır. Değerin yeniden aynı çıkması bir değişikliğin olmadığını göstermez. Çözüm, değere ek bilgi koymak: bir sayaç.

**Adım 5 — İyileştir.** `head`'i `(etiket << 32) | indeks` olarak 64 bitte tut. Her başarılı `push` ve `pop` etiketi bir artırır. CAS, paketin tamamını karşılaştırır.

**Adım 6 — Doğrula.** Elle izleme tablosu, etiketli sürümde CAS'in neden başarısız olduğunu gösteriyor:

| Adım | İşlem | head (etiket, indeks) | Yığın |
|---|---|---|---|
| 0 | başlangıç | (0, A) | A → B → C |
| 1 | T1 okur: eski = (0, A), sonraki = B | (0, A) | duraklar |
| 2 | T2 pop A | (1, B) | B → C |
| 3 | T2 pop B | (2, C) | C |
| 4 | T2 push A | (3, A) | A → C |
| 5 | T1 `CAS((0,A) → (1,B))` | (3, A) | başarısız: 0 ≠ 3 |

Programın etiketli sürümü, pencere açıkken 100.000 işlemle dört iş parçacığında hiçbir koşuda bozulmadı (27.15). Naif sürüm aynı koşulda bozuldu.

**Bunu AI'sız yazabilir misin?** Etiket 8 bit olsaydı, kaç işlemden sonra etiket tekrar eder? Dört iş parçacığının her biri bir milyon işlem yapıyorsa, bu tekrarın bir ABA penceresi açma olasılığı ne olur? Yanıtını bir hesapla destekle, ama bu hesabın neyi varsaydığını da yaz.

## Kendin Yap Projeleri

::: dikkat
Bu iki proje AI olmadan yazılmalıdır. Kod yazmadan önce tasarımı kâğıda çiz: hangi değişken hangi iş parçacığı tarafından yazılıyor, hangi sıralamayla, ve hangi koşulda uyandırılıyor. Kodu yazdıktan sonra TSan ile çalıştır; uyarı çıkarsa kanıt olarak kullan.
:::

### Proje 1 (★★): İş parçacığı havuzu

**Amaç.** Sabit sayıda işçi iş parçacığı çalıştıran, görevleri bir kuyrukta bekleten ve düzgün kapanabilen bir iş parçacığı havuzu yaz.

**Beklenen davranış.** `havuz_baslat(n)` ile `n` işçi oluşturulur. `havuz_gonder(fonk, arg)` bir görevi kuyruğa koyar; boş bir işçi onu alıp çalıştırır. `havuz_kapat()` yeni görev kabul etmez, kuyrukta kalanları bitirir, tüm işçileri `join` eder ve kaynakları serbest bırakır. Kapanış sırasında hiçbir görev kaybolmaz, hiçbir işçi takılı kalmaz.

**Önerilen yaklaşım (ipucu).** Kuyruk için 27.10'daki sınırlı tampon yapısını kullan: bir mutex, iki koşul değişkeni (`bos_degil`, `dolu_degil`) ve bir `kapaniyor` bayrağı. Kapanışta işçileri uyandırmak için `broadcast` kullan ve her işçi `kapaniyor && kuyruk_boş` olduğunda çıksın. Bayrağı kilit altında oku ve yaz. Görevlerin sonuçlarını yazarken bir ortak sayaç varsa onu atomik yap (27.6).

**Başarı kriterleri.**
- 10.000 küçük görev (her biri bir toplam sayacını artırır) altı işçiyle çalıştırıldığında sayaç tam 10.000.
- `havuz_kapat()` sonrası tüm işçiler çıkmış; `gönder` çağrısı kapanıştan sonra hata döndürür.
- TSan (`-fsanitize=thread`, gerekiyorsa `setarch x86_64 -R`) hiçbir uyarı vermez.
- 1, 2, 4, 8 işçi ile aynı görev kümesi için süre ölçülür ve tablo halinde raporlanır; medyan kullanılır. Hızlanmanın nerede durduğunu ve nedenini yaz (çekirdek sayısı, kuyruk kilidi çekişmesi).

### Proje 2 (★★★): MertOS klavye sürücüsü için kesme-güvenli SPSC tamponu

**Amaç.** MertOS'taki klavye sürücüsünün halka tamponunu, kilitsiz ve tek üretici (kesme işleyicisi) tek tüketici (ana döngü) için doğru hâle getir. Mevcut kod (`kernel/drivers/keyboard.cpp`, 83-97. satırlar) `volatile int` indekslerle çalışıyor. Bu, x86'da çoğu zaman doğru görünür ama bellek sıralaması garantisi vermez; ARM'da yanlış olabilir.

**Beklenen davranış.** `pushEvent` (üretici) ve `popEvent` (tüketici) birbirini bloklamadan çalışır. Dolu tamponda `pushEvent` olayı sessizce düşürür ve bunu sayar. Boş tamponda `popEvent` `false` döner. Tampon kapasitesi derleme anında sabittir ve `malloc` kullanılmaz.

**Önerilen yaklaşım (ipucu).** İndeksleri `_Atomic` (C11) ya da `std::atomic` (C++11) yap. Üreticide, veriyi yazdıktan sonra `tail`'i `release` ile yayınla; tüketicide `tail`'i `acquire` ile oku, sonra veriyi oku, sonra `head`'i `release` ile ilerlet. Kesme işleyicisinin yerine bir iş parçacığı koyarak test et: üretici iş parçacığı çok hızlı yazsın, tüketici iş parçacığı ayrı bir hızda okusun. Doğruluk için her değerin tam bir kez alındığını ve sırasının korunduğunu denetle. `message_queue.hpp`'deki yorumu (`asm volatile("" ...)`) değiştirmek de bu projenin parçasıdır.

**Başarı kriterleri.**
- 10 milyon olayla, üretici ve tüketici ayrı iş parçacıklarında, hiçbir olay kaybolmadan (dolu düşürmeler sayılmış) ve her olayın sırası korunarak çalışır.
- TSan uyarısı yok; `volatile` kullanılan eski sürümde ise TSan ya da testin yarış gösterdiği bir senaryo yazılmıştır.
- Kodda her atomik işlemin bellek sıralaması gerekçesiyle belirtilmiştir (her satır için bir yorum).
- Proje raporunda, neden x86'da `relaxed` ile bile çalışabileceğini ve neden ARM'da çalışmayabileceğini (genel bilgi) iki paragrafta açıkla.

## Ek Alıştırmalar

Aşağıdaki alıştırmalar cevapsız. Önce kâğıtta düşün, sonra kodla doğrula.

1. ★ Üç iş parçacığı, her biri `sayac += 2` yapıyor. Düz sayaçla alabileceğin en küçük sonuç nedir? Serpiştirme tablosuyla göster.
2. ★ `volatile int` ile `_Atomic int` arasındaki farkı, iki iş parçacığının bir bayrağı yazıp okuduğu bir örnekte açıkla. Hangisi sıralamayı garanti eder?
3. ★ Bir `pthread_mutex_t` kilidini iki kez kilitleyen bir iş parçacığı ne olur? Varsayılan mutex ile hata denetimli (`PTHREAD_MUTEX_ERRORCHECK`) mutex'in farklı davranışını yaz.
4. ★★ Okuyucu-yazıcı kilidinde yazıcı açlığını gösteren bir senaryo yaz: sürekli gelen okuyucular varsa yazıcı ne zaman girer? Bu davranışı önlemek için hangi kuralı koyarsın?
5. ★★ Sınırlı tampon için `if` yerine `while` kullanmanın gerekli olduğu bir durum tarif et. Bu durumu bir deneyle (27.9'daki sahte uyanma kodunu değiştirerek) göster. (Mülakat)
6. ★★ Peterson algoritmasını üç iş parçacığına genellemeye çalış. Hangi şart bozulur? Bunun yerine filtre algoritması ya da bakerin algoritması gibi bir yapı öner. (Mülakat)
7. ★★ İki kilidi (A ve B) kullanan bir fonksiyonu, kilitleri ters sırada alan iki iş parçacığıyla çağıran bir program yaz. Kilitlenmeyi zaman aşımıyla tespit et; sonra sıralamayla düzelt. Kilitlenmenin dört koşulundan hangisini kırdığını belirt.
8. ★★ Bir `rwlock` içinde okuyucu sayısını atomik bir sayaçla tutan ve yazıcıyı bekleten basit bir yapı yaz. Yazıcı beklerken yeni okuyucuları kabul etmeyen bir kural eklersen açlık nasıl değişir? (Mülakat)
9. ★★★ Bir CAS döngüsünün (`while (!cas(...))`) ilerleme garantisi var mı? Lock-free ile wait-free farkını bir örnekle açıkla. Treiber yığınının pop işlemi hangisine girer? (Mülakat)
10. ★★★ Sahte paylaşım ölçümünü (27.14) değiştir: sayaçları 64 yerine 128 bayt hizala. Fark artar mı, azalır mı? Neden? Bu, önbellek satırının donanımdaki boyutuyla (ve adjacent-line prefetch gibi bir donanım özelliğiyle) nasıl ilişkili olabilir? (Mülakat)
11. ★★★ Bir DCL (double-checked locking) deseni yaz: tembel başlatılan bir tekil nesne. Önce `volatile` ile, sonra `acquire/release` ile yaz. Hangi sürümün ARM'da yanlış olabileceğini açıkla. (Mülakat)
12. ★★★ Bir gerçek zamanlı sistemde öncelik kalıtımı yerine öncelik tavanı (priority ceiling) protokolü kullanılabilir. Bu iki protokolün farkını, bir kilit tutma örneğinde zaman çizelgesiyle göster. Hangisi zincirleme bloklamayı önler? (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: CPython 3.12.10 sürümünün `Lib/queue.py` dosyası. Dosya, `https://raw.githubusercontent.com/python/cpython/v3.12.10/Lib/queue.py` adresinden indirildi (326 satır, SHA-256 `f6c37fc3...193f0`). Aşağıdaki kesit, kilit ve iki koşul değişkeninin kurulumunu ve `put`/`get` yöntemlerinin bloklayan dallarını içerir. 70 karakteri aşan satırlar işaretlenerek kesildi; başka değişiklik yok.

```python
# CPython 3.12.10, Lib/queue.py (kesit, birebir satirlar).
# 70 karakteri asan satirlar '# ... kesildi' ile degistirildi.
        # --- Queue.__init__: kilit ve kosul degiskenleri (42-50) ---
        # --- (42-50 satirlari) ---
        self.mutex = threading.Lock()

        # Notify not_empty whenever an item is added to the queue; a
        # thread waiting to get is notified then.
        self.not_empty = threading.Condition(self.mutex)

        # Notify not_full whenever an item is removed from the queue;
        # a thread waiting to put is notified then.
        self.not_full = threading.Condition(self.mutex)
        # --- Queue.put, bloklayan dal (133-152) ---
        with self.not_full:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() >= self.maxsize:
                        raise Full
                elif timeout is None:
                    while self._qsize() >= self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
        # ... kesildi (kaynakta 142. satir: uzun hata dali)
                else:
                    endtime = time() + timeout
                    while self._qsize() >= self.maxsize:
                        remaining = endtime - time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()
        # --- Queue.get, bloklayan dal (165-183) ---
        with self.not_empty:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
        # ... kesildi (kaynakta 173. satir: uzun hata dali)
            else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self._get()
            self.not_full.notify()
            return item
```

**Sorular — cevaplamadan geçme:**

1. `Queue`, tek bir `threading.Lock` (`mutex`) ve bunu paylaşan üç koşul değişkeni kuruyor. Neden üç ayrı koşul değişkeni var, tek bir tanesi neden yetmez? `not_full` ve `not_empty` hangi olaya tepki verir?
2. `put` içinde `while self._qsize() >= self.maxsize:` döngüsü neden `if` değil? Sahte uyanma ve "uyanıp da yerinin çalındığı" durum arasındaki farkı yaz.
3. `put` ve `get` içinde `self.not_empty.notify()` ve `self.not_full.notify()` çağrıları, değişiklikten hemen sonra, kilit altında yapılıyor. Bunu kilit dışına taşıyan bir sürüm yazılsa ne kaybolur? (Koşulu kontrol edip beklemeye geçen bir iş parçacığı için sinyalin "kaçması" senaryosunu düşün.)
4. `self.not_full.wait()` çağrılırken kilit otomatik bırakılır ve uyanınca geri alınır. Kilidi bırakmanın bu adımı olmazsa kodun ne tür bir kilitlenmeye yol açacağını anlat (27.11'deki dört koşulla ilişkilendir).
5. `get` ve `put`'taki `timeout` dallarını, döngü içindeki `remaining = endtime - time()` ile birlikte düşün. Yanlış sürüm `endtime`'ı döngü dışında değil de içinde hesaplasaydı ne olurdu?
6. Bu sınıf bir **monitör** mü? Bölüm 27.10'daki kendi tamponumuzla karşılaştır: hangi kilit disiplini sınıfın içine konmuş, hangisi kullanıcıya bırakılmış? `queue.Queue` yerine kendi tamponunu yazarken hangi hatayı yapmak kolaydır?

## Bölüm Özeti

- Yarış koşulu, paylaşılan verinin birden çok iş parçacığı tarafından senkronizasyonsuz değiştirilmesidir. `sayac++` tek satır görünse de oku-değiştir-yaz üç adımıdır; düz sayaç yüzde 48 kayıp verdi, atomik sürüm vermedi.
- Doğru bir senkronizasyonun üç şartı vardır: karşılıklı dışlama, ilerleme ve sınırlı bekleme. Peterson bunları iki iş parçacığı için kâğıtta sağlar, ama modern CPU'da store buffering nedeniyle `relaxed` ile bozulur; `seq_cst` ile düzelir.
- Bellek sıralaması (`relaxed`, `acquire`, `release`, `seq_cst`) yalnızca atomik işlemin kendisini değil, çevresindeki erişimlerin görünürlüğünü de belirler. Mesaj geçirme için `release`/`acquire` çifti gerekir; x86 TSO bunu çoğu zaman gizler, ARM gizlemez.
- Kilitler: spinlock çekişmesiz en ucuzdur ama çekişme arttıkça hızla kötüleşir; mutex bekleyenleri uyutarak yüksek çekişmede daha öngörülebilirdir. Koşul değişkeni, `while` içinde ve kilit altında kullanılmalıdır.
- Kilitlenme dört koşulun birleşimidir; en pratik önlem kilitleri sıralı almaktır. Livelock ve açlık ilerlemenin farklı biçimleridir.
- Öncelik terslemesi, gerçek zamanlı sistemlerde öncelik kalıtımıyla önlenir. Mars Pathfinder bu sorunun gerçek bir örneğidir.
- Sahte paylaşım, bağımsız değişkenlerin aynı önbellek satırında olmasıyla yaşanır; ölçümde on katı aşan bir yavaşlama gördük.
- Kilitsiz Treiber yığını, ABA problemine açıktır. Etiketli işaretçi bunu çözer. ThreadSanitizer veri yarışlarını yakalar, mantıksal yarışları (ABA) yakalamaz.
- Python'da GIL, `x += 1`'i garanti etmez; fonksiyon çağrısı araya girince yarış ortaya çıkar. `threading.Lock` doğru çözümdür.
- Gömülü sistemlerde kritik bölge kesmeleri kapatarak sağlanır; `volatile` senkronizasyon değildir.

**Sonraki bölümde:** Bölüm 28, File System & I/O ile bu kısımdaki donanım ve eşzamanlılık konularını dosya sistemi ve giriş-çıkış tarafına taşıyacağız. Bir dosyaya iki iş parçacığının aynı anda yazması, bu bölümdeki kilitlerle nasıl düzenlenir; kernel bu işi nasıl yapar, ve fsync gibi çağrılar veriyi diske kadar nasıl garanti eder? Bu soruların cevabı, bu bölümde gördüğümüz sıralama ve kalıcılık kavramlarının bir devamıdır.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. `counter++` neden tek bir işlem değildir? Bir x86 makine komutunun bile atomik olmayabileceğini bir örnekle açıkla.
2. Peterson algoritması sıralı tutarlılıkta doğrudur. Modern bir x86 işlemcide ne değişir ve bu neden tek bir `mfence` ile düzelir?
3. Mutex ile spinlock arasındaki seçimi, kritik bölgenin süresi ve çekişme düzeyi üzerinden savun. Bir kesme işleyicisinde hangisi kullanılabilir?
4. Kilitlenmenin dört koşulunu say. Bir sistemde kilitlenmeyi önlemek için hangisini kırarsın ve neden?
5. Öncelik terslemesi nedir? Öncelik kalıtımı bunu nasıl çözer, ve kalıtım neden yalnız mutex üzerinde tanımlıdır?
6. ABA problemini bir yığın örneğiyle anlat. Etiketli işaretçi ne zaman yetmez?
7. `volatile` ile `_Atomic` arasındaki fark nedir? Bir gömülü sistemde `volatile` bayrak kullanmak ne zaman kabul edilebilir, ne zaman tehlikelidir?
8. ThreadSanitizer bir veri yarışını yakalayabilir ama ABA'yı yakalayamaz. Bu iki hatanın doğasındaki fark nedir ve doğruluğu kanıtlamak için ne gerekir?
:::
