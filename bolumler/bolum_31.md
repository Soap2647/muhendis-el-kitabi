%% kisim_no: VII
%% kisim_ad: Ağ
%% bolum_no: 31
%% baslik: Socket Programming

## Giriş: Ağ, dosya okumanın bir uzantısıdır

Bölüm 28'de bir dosyayı açmanın, okumanın ve yazmanın aslında bir çekirdek çağrısı olduğunu gördük: `open` bir tanımlayıcı döndürür, `read` ve `write` o tanımlayıcı üzerinden çalışır. Ağda da durum aynıdır. Bir TCP bağlantısı açtığında işletim sistemi sana yine bir tanımlayıcı verir ve bu tanımlayıcıya `read` ile `write` yapabilirsin. Bu yüzden ağ programlamanın ilk ve en önemli fikri, bildiğin dosya G/Ç kavramlarının bir uzantısı olduğudur. Asıl zorluk, karşıdaki tarafın bir dosya değil, başka bir makinedeki süreç olmasıdır: gecikir, kaybolur, yarıda kesilir ve bayt sırası farklı olabilir.

Bu bölüm soketleri üç katmanda ele alır. Birincisi TCP'nin yaşam döngüsüdür: sunucu nasıl dinler, istemci nasıl bağlanır ve bağlantı nasıl kapanır. İkincisi TCP'nin bir **bayt akışı** olmasıdır; mesaj sınırı yoktur, bu yüzden mesajları kendimiz çerçevelemek zorundayız. Üçüncüsü, aynı anda birçok istemciye nasıl hizmet edileceğidir: süreç, iş parçacığı, havuz, olay döngüsü ya da `asyncio`. Bölümün sonunda UDP'ye geçeriz; bağlantısız, sınırları koruyan ama kayıp ve sıra bozulmasına açık bir taşıma katmanıdır ve güvenilirliği kendi elimizle kuracağız.

Savunma sanayiinde bu konu her yerde karşına çıkar. Bir İHA ile yer istasyonu arasındaki telemetri, bir sensör ağından gelen paketler, bir komut kanalının yanıtları; hepsi bir soket üzerinden, bir bayt akışı ya da datagram olarak taşınır. Paketin bir kısmının kaybolması, bir baytın bozulması ya da iki paketin birleşmesi, uçuş yazılımı için bir hata değil bir **beklenen durumdur** ve kodun bunu bilerek karşılaması gerekir. Mülakatlarda da "TCP ile UDP farkı nedir?" sorusunun ardından hemen "peki TCP üzerinde bir mesaj protokolü nasıl kurarsın?" gelir; bu bölüm o soruya cevap verecek kadar derin.

::: not
Bu bölümdeki her ağ deneyi yalnızca `127.0.0.1` (loopback) üzerinde yapıldı; dış ağa hiçbir paket çıkmadı. Ölçümler Windows 11 üzerinde WSL2 (Ubuntu 24.04.4, çekirdek 6.6.87.2, gcc 13.3.0, Python 3.12.3) içinde alındı. Windows tarafında `fork` ve `epoll` yoktur; bu yüzden Linux'a özgü kodlar WSL2'de çalıştırıldı (bkz. Bölüm 26.6). Sayıların mutlak değerleri makineye bağlıdır; yönü ve nedenini anlamak önemlidir.
:::

## 31.1 Soket: bir dosya tanımlayıcısı ve bir adres

**Soket (socket)**, bir ağ uç noktasının işletim sistemindeki temsilidir. `socket()` çağrısı çekirdekte bir soket nesnesi oluşturur ve bize küçük bir tamsayı döndürür. Bu tamsayı Bölüm 28'deki fd tablosunun bir girdisidir; `close` ile kapanır, `fork` sonrası miras kalır ve `dup` ile çoğaltılabilir. Yani bir soketi kapatmayı unutursan, dosya tanımlayıcı sızıntısı aynı şekilde yaşanır.

Bir soketin "nereye" bağlandığını anlatmak için adres gerekir. IPv4 için C'de `struct sockaddr_in` kullanılır: adres ailesi, port ve IP adresi. Port ve adres **ağ bayt sırası (big-endian)** ile yazılır, bu yüzden makine sırasından ağ sırasına çevirmek için `htons` (host to network short) ve `htonl` (host to network long) çağrılır. Bölüm 1.5'te gördüğümüz endianness sorunu tam olarak buradadır: x86 ve çoğu ARM işlemci küçük ucu önce (little-endian) saklar, ağ ise büyük ucu önce ister.

![Şekil 31.1: Ağ bayt sırası. Little-endian bellekte 0x1F90 değeri 90 1F olarak durur; htons bu değeri ağa 1F 90 olarak çevirir.](gorseller/b31_bayt_sirasi.png)

Aşağıdaki kipin çıktısı, bu çevirinin baytları nasıl değiştirdiğini gösterir. Kodun tamamı 31.2'de yer alıyor; burada yalnızca `bayt` kipi çalıştırıldı.

```term
$ ./b31_1_yasam bayt
host port 8080 = 0x1F90
bellek (host)    90 1F
htons (ag)       1F 90
ag sirasi 0x1A2B3C4D icin htonl = 0x4D3C2B1A
htonl bellek     1A 2B 3C 4D
```

Çıktıda iki şeyi okumalısın. Birincisi, `htons(8080)` sonucu belleğe `90 1F` olarak yazılmış (host), ama ağa `1F 90` olarak çıkmıştır: yani aynı sayının bayt sırası ters çevrildi. İkincisi, `htonl` 32 bitlik değerin dört baytını da tersine çevirdi. Kural basit: ağa giden her çok baytlı sayı çevrilir, ağdan gelen her çok baytlı sayı geri çevrilir. Bu sözleşme ihlal edilirse EV Dashboard'daki 439 milyonluk hız 1,3 milyar gibi okunur; gösterge yanlış değer gösterir ama program çökmez. Bu yüzden bayt sırası hatalarını bulmak, çökme hatalarından daha zordur.

Adres çözümlemede modern yol `getaddrinfo`'dur. İsim ya da sayısal adres ile port bilgisini verirsin, IPv4 ve IPv6 için uygun yapıları sana listeler. Kodun IPv4'e bağımlı kalmaması için tercih edilen yol budur; yalnızca `sockaddr_in` kullanan kod IPv6 ortamında sessizce çalışmaz. Bölüm 31.2'deki `adres_coz` fonksiyonu bu çağrıyı sarmalar.

## 31.2 TCP sunucu ve istemcinin yaşam döngüsü

TCP sunucusunun standart yaşam döngüsü altı adımdır: `socket` ile uç nokta yaratılır, `bind` ile bir adrese bağlanır, `listen` ile bağlantı kabul etmeye başlar, `accept` ile bir bağlantıyı alır, `recv` ve `send` ile veri alışverişi yapılır ve `close` ile kapanır. İstemci tarafı daha kısadır: `socket` ve `connect`, ardından aynı veri alışverişi ve `close`. Şekil 31.2 iki tarafın çağrı sırasını yan yana gösterir.

![Şekil 31.2: Sunucu ve istemcinin çağrı sırası. Sunucu accept'te bekler; istemcinin connect çağrısı üç yollu el sıkışmayı tamamlayınca accept döner ve veri akışı başlar.](gorseller/b31_yasam.png)

Bu sıranın her adımının bir nedeni vardır. `bind` soketi bir port ve arayüzle ilişkilendirir. `listen` çekirdeğe "bu soket yeni bağlantıları kabul edecek" der ve tamamlanmış bağlantıların bekleyeceği kuyruğun boyutunu (backlog) belirler. `accept` bu kuyruktan bir bağlantıyı alır ve **yeni bir soket** döndürür: dinleme soketi yeni bağlantılar için açık kalır, bağlantının kendisi ise ayrı bir tanımlayıcıda yaşar. Bu ayrım, aynı anda birçok bağlantıyı yönetebilmenin temelidir.

Aşağıdaki C programı, yukarıdaki çağrıların tümünü gerçek soketlerle yapar. Aynı dosya dört ayrı kipte çalışır: `sunucu` ile tek istemciye yanki yapan bir sunucu, `istemci` ile mesaj gönderen bir istemci ve Bölüm 31.6'da kullanılacak hata kipleri. Derleme: `gcc -O2 -Wall -Wextra -std=c11 b31_1_yasam.c -o b31_1_yasam`. Program dört bölümde verilmiştir; kod satır sınırını aşmasın diye bloklar arasına kısa açıklamalar konmuştur.

Önce başlık, yardımcı fonksiyonlar ve adres çözümleme gelir. `_DEFAULT_SOURCE` tanımı, glibc'nin `MSG_NOSIGNAL` gibi POSIX dışı sabitleri görmesi için gereklidir. `adres_coz` içindeki `AI_NUMERICSERV` bayrağı, port parametresinin bir sayı olduğunu ve servis adı aranmayacağını söyler.

```c
/* b31_1_yasam.c: TCP soket yasam dongusu ve hata kipleri.
 * Derleme (WSL2 Ubuntu, gcc 13):
 *   gcc -O2 -Wall -Wextra -std=c11 b31_1_yasam.c -o b31_1_yasam
 * Kipler:
 *   sunucu PORT         tek istemciye yanki yapar, sonra kapanir
 *   istemci PORT MSJ    sunucuya MSJ gonderir, yaniti yazar
 *   bayt                htons/htonl ile bellek baytlarini gosterir
 *   bindhata            TIME_WAIT ve SO_REUSEADDR farkini gosterir
 *   zaman               SO_RCVTIMEO ile recv zaman asimi
 *   pipe_hata           MSG_NOSIGNAL: send EPIPE dondurur
 *   pipe_yok            SIGPIPE yok sayilir: send EPIPE dondurur
 *   pipe_olum           varsayilan SIGPIPE: surec olur
 */
#define _DEFAULT_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <netdb.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>
```

Kodun devamında `adres_coz` ve `tam_gonder` gelir. `tam_gonder` bir döngü içinde `send` çağırır, çünkü `send` her zaman tüm baytları yazmayabilir; dönen değer yazılan bayt sayısıdır. Bu, Bölüm 28.5'teki kısa yazma kuralının soketlere uygulanmasıdır.

```c
/* Adresi coz: AI_NUMERICSERV ile port sayi olarak verilir. */
static int adres_coz(const char *port, struct addrinfo **res)
{
    struct addrinfo ip;
    memset(&ip, 0, sizeof ip);
    ip.ai_family = AF_UNSPEC;      /* IPv4 ya da IPv6 */
    ip.ai_socktype = SOCK_STREAM;  /* TCP */
    ip.ai_flags = AI_NUMERICSERV;
    int e = getaddrinfo("127.0.0.1", port, &ip, res);
    if (e != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(e));
        return -1;
    }
    return 0;
}

/* Tum baytlari gonderene kadar dongu: kisa send'e karsi. */
static int tam_gonder(int s, const char *b, size_t n, int bayrak)
{
    size_t top = 0;
    while (top < n) {
        ssize_t k = send(s, b + top, n - top, bayrak);
        if (k < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        top += (size_t)k;
    }
    return 0;
}
```

`cift_kur`, testler için yardımcı bir fonksiyondur. Loopback üzerinde bir dinleyici açar, kernelin bir port seçmesini sağlar (bind'e port 0 verilir), bir istemci bağlar ve sunucu tarafındaki kabul edilmiş soketi döndürür. Bu sayede aynı süreçte hem sunucuyu hem istemciyi sınayabiliriz. Dinleyiciye `SO_REUSEADDR` verilmesi, kabul edilen soketin bu bayrağı miras almasını sağlar; bu, Bölüm 31.6'da önemli olacak.

```c
/* Loopback'te bir TCP cifti kur. Dinleyici kapatilir, kabul edilen
 * soket ve istemci soketi dondurulur. reuse != 0 ise dinleyiciye
 * SO_REUSEADDR konur; kabul edilen soket bu bayragi miras alir. */
static int cift_kur(int *istemci_fd, int *sunucu_fd, int reuse,
                    struct sockaddr_in *sa_out)
{
    struct addrinfo *ai;
    if (adres_coz("0", &ai) != 0) return -1;
    int ls = socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
    int on = 1;
    if (reuse)
        setsockopt(ls, SOL_SOCKET, SO_REUSEADDR, &on, sizeof on);
    if (ls < 0 || bind(ls, ai->ai_addr, ai->ai_addrlen) < 0) {
        perror("socket/bind");
        return -1;
    }
    freeaddrinfo(ai);
    socklen_t sl = sizeof *sa_out;
    /* kernel port secer */
    getsockname(ls, (struct sockaddr *)sa_out, &sl);
    listen(ls, 4);
    int cl = socket(AF_INET, SOCK_STREAM, 0);
    connect(cl, (struct sockaddr *)sa_out, sizeof *sa_out);
    int ac = accept(ls, NULL, NULL);
    close(ls);
    *istemci_fd = cl;
    *sunucu_fd = ac;
    return 0;
}
```

Sunucu fonksiyonu bir istemciyi kabul eder ve gelen her parçayı geri yollar. Döngünün çıkış koşulu önemlidir: `recv` sıfır döndüğünde karşı taraf yazmayı bitirmiş ve bir FIN göndermiştir. Hata durumunda `recv` -1 döndürür ve `errno` nedenini söyler. Dinleme soketi `listen` ile açıldıktan sonra port, dinleyici kapatılana kadar meşguldür.

```c
static int sunucu(const char *port)
{
    struct addrinfo *ai;
    if (adres_coz(port, &ai) != 0) return 1;
    int ls = socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
    if (ls < 0) { perror("socket"); return 1; }
    int on = 1;
    setsockopt(ls, SOL_SOCKET, SO_REUSEADDR, &on, sizeof on);
    if (bind(ls, ai->ai_addr, ai->ai_addrlen) < 0) {
        perror("bind");
        return 1;
    }
    freeaddrinfo(ai);
    if (listen(ls, 16) < 0) { perror("listen"); return 1; }
    printf("dinleniyor 127.0.0.1:%s\n", port);

    int c = accept(ls, NULL, NULL);
    if (c < 0) { perror("accept"); return 1; }
    char buf[256];
    ssize_t n;
    /* recv 0: karsi taraf yazmayi kapatmis (FIN) demektir. */
    while ((n = recv(c, buf, sizeof buf, 0)) > 0) {
        if (tam_gonder(c, buf, (size_t)n, MSG_NOSIGNAL) < 0) {
            perror("send");
            break;
        }
    }
    if (n < 0) perror("recv");
    close(c);
    close(ls);
    return 0;
}
```

İstemci önce `connect` ile bağlanır, sonra mesajı gönderir. Dikkat edilmesi gereken satır `shutdown(s, SHUT_WR)`dır: bu çağrı yalnızca yazma yönünü kapatır ve karşı tarafa "daha veri yok" sinyali verir, ama okuma yönü açık kalır. Sunucu yanıtını tamamen yazdıktan sonra kendi kapanışını yapar. Bu **yarım kapanış (half close)** deseni, istek-yanıt protokollerinde sık kullanılır.

```c
static int istemci(const char *port, const char *msg)
{
    struct addrinfo *ai;
    if (adres_coz(port, &ai) != 0) return 1;
    int s = socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
    if (s < 0) { perror("socket"); return 1; }
    if (connect(s, ai->ai_addr, ai->ai_addrlen) < 0) {
        perror("connect");
        return 1;
    }
    freeaddrinfo(ai);
    if (tam_gonder(s, msg, strlen(msg), MSG_NOSIGNAL) < 0) {
        perror("send");
        return 1;
    }
    /* Yarim kapanis: yazmayi bitirdik, okumaya devam ediyoruz. */
    shutdown(s, SHUT_WR);
    char buf[256];
    ssize_t n;
    while ((n = recv(s, buf, sizeof buf, 0)) > 0)
        fwrite(buf, 1, (size_t)n, stdout);
    putchar('\n');
    close(s);
    return 0;
}
```

Sunucu ve istemciyi aynı komutta çalıştırıp yankıyı görelim. Sunucu arka planda başlatılır, kısa bir bekleme sonra istemci çağrılır; sunucu istemci kapandığında kendiliğinden biter.

```term
$ ./b31_1_yasam sunucu 9031 & istemci 9031
dinleniyor 127.0.0.1:9031
merhaba soket
```

Çıktıda iki satır var. `dinleniyor` satırı sunucudan gelir; `merhaba soket` ise istemcinin aldığı yanıttır. Sunucu, istemciden gelen baytları aynen geri göndermiştir. Bu basit yankı programı bile bir protokol içerir: istemci mesajın bittiğini `shutdown` ile bildirir, sunucu `recv` sıfırı görünce çıkar. Protokolü değiştirirsen (örneğin satır sonu bekleyen bir sunucu yazarsan) istemci ve sunucu birlikte değişmek zorundadır; buna protokol sözleşmesi denir.

Kodun kalanı `bayt`, `bindhata`, `zaman` ve `pipe_*` kiplerini içerir. Bunları Bölüm 31.6'da çalıştıracağız; programın derlenebilmesi için kodun tamamı burada yer almalı.

```c
static void bayt_yaz(const char *ad, const void *p, size_t n)
{
    const unsigned char *b = p;
    printf("%-16s", ad);
    for (size_t i = 0; i < n; i++) printf(" %02X", b[i]);
    printf("\n");
}

static int bayt(void)
{
    uint16_t port = 8080;
    uint16_t pn = htons(port);
    uint32_t v = 0x1A2B3C4D;
    uint32_t vn = htonl(v);
    printf("host port 8080 = 0x%04X\n", port);
    bayt_yaz("bellek (host)", &port, sizeof port);
    bayt_yaz("htons (ag)", &pn, sizeof pn);
    printf("ag sirasi 0x%08X icin htonl = 0x%08X\n", v, vn);
    bayt_yaz("htonl bellek", &vn, sizeof vn);
    return 0;
}
```

```c
/* Sunucu once kapatir: aktif kapatan taraf TIME_WAIT'e girer.
 * Ardindan ayni portu yeniden baglamayi dener. */
static int yeniden_baglan(int reuse)
{
    int ac, cl;
    struct sockaddr_in sa;
    if (cift_kur(&cl, &ac, reuse, &sa) != 0) return 1;
    close(ac);
    close(cl);

    int s = socket(AF_INET, SOCK_STREAM, 0);
    int on = 1;
    if (reuse)
        setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &on, sizeof on);
    if (bind(s, (struct sockaddr *)&sa, sizeof sa) < 0)
        printf("SO_REUSEADDR=%d: bind hatasi: %s\n", reuse,
               strerror(errno));
    else
        printf("SO_REUSEADDR=%d: bind basarili\n", reuse);
    close(s);
    return 0;
}
```

```c
static int bindhata(void)
{
    yeniden_baglan(0);   /* ayar yok: yeniden baslatma basarisiz */
    yeniden_baglan(1);   /* ayar var: yeniden baslatma basarili */
    return 0;
}

static long ms_simdi(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1000L + t.tv_nsec / 1000000L;
}

static int zaman(void)
{
    int ist, sun;
    struct sockaddr_in sa;
    if (cift_kur(&ist, &sun, 0, &sa) != 0) return 1;
    struct timeval tv = { 1, 0 };   /* 1 saniye */
    setsockopt(sun, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
    long t0 = ms_simdi();
    char buf[16];
    ssize_t n = recv(sun, buf, sizeof buf, 0);
    long gecen = ms_simdi() - t0;
    if (n < 0)
        printf("recv -1, errno=%s, sure ~%ld ms\n",
               errno == EAGAIN ? "EAGAIN" : strerror(errno),
               gecen / 100 * 100);
    close(ist);
    close(sun);
    return 0;
}
```

```c
/* Karsi taraf kapandiktan sonra yazmayi dener. Bayrak ve SIGPIPE
 * ayari sonucu belirler. */
static int pipe_dene(int bayrak)
{
    int ist, sun;
    struct sockaddr_in sa;
    if (cift_kur(&ist, &sun, 0, &sa) != 0) return 1;
    close(ist);            /* karsi taraf kapandi */
    usleep(50000);         /* RST'nin ulasmasi icin kisa bekleme */
    char buf[1024];
    memset(buf, 'x', sizeof buf);
    for (int i = 1; i <= 5; i++) {
        ssize_t n = send(sun, buf, sizeof buf, bayrak);
        if (n < 0) {
            printf("send #%d: -1, errno=%s\n", i, strerror(errno));
            break;
        }
        printf("send #%d: %zd bayt\n", i, n);
        usleep(20000);
    }
    close(sun);
    return 0;
}
```

```c
int main(int argc, char **argv)
{
    /* tamponsuz: olum oncesi cikti kaybolmasin */
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc < 2) {
        fprintf(stderr, "kullanim: %s sunucu|istemci|...\n",
                argv[0]);
        return 1;
    }
    const char *kip = argv[1];
    if (strcmp(kip, "sunucu") == 0 && argc == 3)
        return sunucu(argv[2]);
    if (strcmp(kip, "istemci") == 0 && argc == 4)
        return istemci(argv[2], argv[3]);
    if (strcmp(kip, "bayt") == 0) return bayt();
    if (strcmp(kip, "bindhata") == 0) return bindhata();
    if (strcmp(kip, "zaman") == 0) return zaman();
    if (strcmp(kip, "pipe_hata") == 0) return pipe_dene(MSG_NOSIGNAL);
    if (strcmp(kip, "pipe_yok") == 0) {
        signal(SIGPIPE, SIG_IGN);
        return pipe_dene(0);
    }
    if (strcmp(kip, "pipe_olum") == 0) {
        printf("SIGPIPE varsayilan: surec olur\n");
        return pipe_dene(0);
    }
    fprintf(stderr, "bilinmeyen kip: %s\n", kip);
    return 1;
}
```

## 31.3 TCP bir bayt akışıdır: mesaj sınırı yoktur

TCP'nin en çok yanlış anlaşılan özelliği şudur: TCP bir **bayt akışı** taşır, mesaj taşımaz. İstemci iki kez `send` çağırdığında karşı taraf iki ayrı mesaj değil, tek bir bayt dizisi görür. Gönderim sınırları çekirdeğin tamponlarında kaybolur; alıcının `recv` çağrısı, o anda tamponda ne varsa (en fazla istenen kadar) döndürür. Bu, Şekil 31.3'ün üst kısmında görülen durumdur: iki ayrı `send`, tek bir `recv` ile okunabilir.

Bunun tersi de doğrudur. Tek bir büyük `send` alıcıda birkaç `recv` çağrısına bölünebilir. Şekil 31.3'ün alt kısmı, 10 000 baytlık tek bir gönderimin `recv(1024)` ile on parçaya ayrıldığını gösterir. Ağ yolunda MTU sınırları, çekirdek tamponları ve TCP'nin tıkanıklık denetimi, bu parçalanmayı belirler; programın bunlara bağlı olmaması gerekir.

![Şekil 31.3: Bayt akışında mesaj sınırlarının kaybı. Üstte iki gönderim tek alımda birleşiyor; altta tek gönderim on okumaya bölünüyor.](gorseller/b31_akis.png)

Bunu gerçek bir TCP bağlantısında görelim. Aşağıdaki program, loopback üzerinde iki ayrı `sendall` ve tek bir büyük gönderim yapar ve alıcının okuma sayılarını ölçer.

```term
$ python3 b31_cerceve.py kisa
iki sendall -> tek recv: b'ilk mesajikinci mesaj'
10000 bayt, recv(1024): 10 cagri, en buyuk parca 1024
son parca boyutu: 784, toplam: 10000
```

İlk satır, `ilk mesaj` ve `ikinci mesaj` gönderimlerinin tek bir `recv(4096)` ile birleşerek geldiğini kanıtlar. Gönderimler arasında `sleep(0.2)` olmasının nedeni, iki gönderimin de alıcının tamponuna ulaşmasını beklemektir; bu bekleme olmadan birleşme her zaman gözlenmeyebilir, ama birleşmenin mümkün olduğu bilinmelidir. İkinci satırda 10 000 baytın `recv(1024)` ile tam 10 çağrıda okunduğunu görüyorsun. Toplam bayt sayısı doğru, ama çağrı sınırları gönderimle uyuşmuyor. Bu, TCP'de "bir `recv` = bir mesaj" varsayımının neden yanlış olduğunun en kısa kanıtıdır.

Bu gerçek, bir sonraki bölümde ele alacağımız çerçevelemenin (framing) nedenidir. Mesaj sınırlarını protokol kendi içinde taşımalıdır; uzunluk önekleri ya da ayraçlar bunun iki yoludur.

## 31.4 Çerçeveleme: uzunluk önekli ve ayraçlı protokoller

**Çerçeveleme (framing)**, bir bayt akışının içinde mesaj sınırlarını belirleme yöntemidir. İki temel yol vardır. **Uzunluk önekli (length-prefixed)** çerçevelemede her mesaj, kendi uzunluğunu taşıyan sabit boyutlu bir alanla başlar; alıcı önce uzunluğu okur, sonra o kadar bayt bekler. **Ayraçlı (delimited)** çerçevelemede mesajlar özel bir bayt dizisiyle (genellikle satır sonu `\n`) ayrılır; alıcı ayraç görene kadar okur. Şekil 31.3 iki düzeni yan yana gösterir.

![Şekil 31.4: Çerçeveleme düzenleri. Uzunluk önekinde alıcı 4 bayt okuyup yükü bekler; ayraçlıda alıcı satır sonunu arar.](gorseller/b31_cerceve.png)

Uzunluk önekli yöntemin iki kuralı vardır ve ikisi de bir tuzağa karşı korur. Birincisi, uzunluk alanı **ağ bayt sırasında** yazılır (`!I` biçimi). Uzunluk alanı bir C struct'ından doğrudan kopyalanırsa, iki makine farklı bayt sıralarında olduğunda alıcı 3 baytlık yükü 50 331 648 baytlık sanabilir. İkincisi, alıcı uzunluğu **bellek ayırmadan önce** sınırlamalıdır. 4 bayt ile 4 GiB'lık bir uzunluk iddiası, saldırgan elinde kolay bir bellek tüketme aracıdır. Bu yüzden `MAKS` sınırı koyduk.

Aşağıdaki Python modülü, bu iki yöntemi ve tüm zor noktaları birlikte gösterir. Bu modül bir kütüphane gibi tasarlandı: `tam_oku` kısa okumalara karşı döngü kurar, `cerceve_gonder` ve `cerceve_al` uzunluk önekli çerçeveyi yönetir, `SatirOkuyucu` ayraçlı akışı işler. `ParcaliSoket` ise gerçek bir ağ olmadan, belirlenmiş parçalarda gelen baytları simüle eden bir sahte soket sağlar; böylece testler her çalıştırmada aynı sonucu verir.

```python
# -*- coding: utf-8 -*-
"""b31_cerceve.py: TCP uzerinde cerceveleme (framing) kutuphanesi.

Kullanim:
  python b31_cerceve.py test     # sahte soketle deterministik testler
  python b31_cerceve.py kisa     # kisa okuma, birlesen mesajlar
"""

import random
import socket
import struct
import sys
import threading
import time

MAKS = 1 << 20  # tek cerceve icin ust sinir: 1 MiB


class ParcaliSoket:
    """Gelen baytlari parcalar halinde teslim eden sahte soket.
    recv(n) en fazla bir parca dondurur ve n'den fazlasini vermez."""

    def __init__(self, parcalar):
        self.parcalar = [bytearray(p) for p in parcalar]

    def recv(self, n):
        if not self.parcalar:
            return b""  # karsi taraf kapandi
        ilk = self.parcalar[0]
        k = min(n, len(ilk))
        cikti = bytes(ilk[:k])
        del ilk[:k]
        if not ilk:
            self.parcalar.pop(0)
        return cikti
```

*Kodun devamı (b31_cerceve.py, satır 37–72):*

```python

def tam_oku(s, n):
    """Tam n bayt okuyana kadar recv dongusu (kisa okumaya karsi)."""
    parcalar = []
    kalan = n
    while kalan > 0:
        b = s.recv(kalan)
        if not b:
            raise EOFError("karsi taraf yarim cercevede kapandi")
        parcalar.append(b)
        kalan -= len(b)
    return b"".join(parcalar)


def cerceve_gonder(s, yuk):
    """Uzunluk onekli cerceve: 4 bayt ag sirali uzunluk + yuk."""
    if len(yuk) > MAKS:
        raise ValueError("yuk sinirin uzerinde: %d" % len(yuk))
    s.sendall(struct.pack("!I", len(yuk)) + yuk)


def cerceve_al(s):
    (n,) = struct.unpack("!I", tam_oku(s, 4))
    if n > MAKS:  # guvenlik: bellek ayirmadan once sinir
        raise ValueError("cerceve uzunlugu sinirin uzerinde: %d" % n)
    return tam_oku(s, n)


def naif_cerceve_al(s):
    """YANLIS: tek recv cagrisi. Kisa okumada hatali sonuc verir."""
    (n,) = struct.unpack("!I", s.recv(4))
    return s.recv(n)


class SatirOkuyucu:
    """Ayraclı (satir sonu) cerceveleme; tamponu kendi tutar."""
```

*Kodun devamı (b31_cerceve.py, satır 74–113):*

```python
    def __init__(self, s):
        self.s = s
        self.tampon = bytearray()

    def satir(self):
        while True:
            i = self.tampon.find(b"\n")
            if i >= 0:
                satir = bytes(self.tampon[:i])
                del self.tampon[: i + 1]
                return satir
            parca = self.s.recv(4096)
            if not parca:
                if self.tampon:
                    raise EOFError("yarim satir")
                return None
            self.tampon += parca


def test():
    rnd = random.Random(31)
    # 1) Uzunluk onekli: rastgele bolunmus akis
    mesajlar = [
        bytes(rnd.getrandbits(8) for _ in range(rnd.randint(0, 300)))
        for _ in range(200)
    ]
    akis = b"".join(struct.pack("!I", len(m)) + m for m in mesajlar)
    kesim = sorted(rnd.sample(range(1, len(akis)), 500))
    parca, onceki = [], 0
    for k in kesim:
        parca.append(akis[onceki:k])
        onceki = k
    parca.append(akis[onceki:])
    s = ParcaliSoket(parca)
    alinan = [cerceve_al(s) for _ in mesajlar]
    assert alinan == mesajlar, "uzunluk onekli cerceve hatali"
    print(
        "uzunluk onekli: %d mesaj, %d parcaya bolunmus akis: tamam"
        % (len(mesajlar), len(parca))
    )
```

*Kodun devamı (b31_cerceve.py, satır 115–149):*

```python
    # 2) Naif okuyucu: baslik 2+2 bolunurse yanlis olur
    try:
        naif_cerceve_al(ParcaliSoket([b"\x00\x00", b"\x00\x03abc"]))
        print("naif: hata yok (beklenmiyordu)")
    except struct.error as e:
        print("naif: struct.error -> %s" % e)

    # 3) Ayni bolunmus akis, dogru okuyucu ile sorunsuz
    s = ParcaliSoket([b"\x00\x00", b"\x00\x03abc"])
    print("dogru: %r" % cerceve_al(s))

    # 4) Ayracli akis: satir sonu bolunsa bile dogru satirlar
    metin = "birinci\nikinci satır\nüçüçü\n".encode("utf-8")
    kesim = sorted(rnd.sample(range(1, len(metin)), 9))
    parca, onceki = [], 0
    for k in kesim:
        parca.append(metin[onceki:k])
        onceki = k
    parca.append(metin[onceki:])
    oku = SatirOkuyucu(ParcaliSoket(parca))
    satirlar = []
    while True:
        s_ = oku.satir()
        if s_ is None:
            break
        satirlar.append(s_)
    assert satirlar == metin.split(b"\n")[:-1], satirlar
    print("ayracli: %d satir, parcalara ragmen dogru" % len(satirlar))

    # 5) Sinir: asiri buyuk uzunluk reddedilir (bellek ayrilmadan)
    try:
        cerceve_al(ParcaliSoket([struct.pack("!I", 0xFFFFFFFF)]))
    except ValueError as e:
        print("sinir: reddedildi -> %s" % e)
    print("TUM TESTLER GECTI")
```

*Kodun devamı (b31_cerceve.py, satır 151–185):*

```python

def kisa():
    """Gercek TCP: iki gonderim tek recv'de birlesir; tek gonderim
    birden cok recv'e bolunur."""
    ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ls.bind(("127.0.0.1", 0))
    ls.listen(4)
    port = ls.getsockname()[1]
    istemci = socket.create_connection(("127.0.0.1", port))
    sunucu, _ = ls.accept()

    # Iki ayri sendall: TCP bunlari tek bir bayt akisi olarak tutar.
    istemci.sendall(b"ilk mesaj")
    istemci.sendall(b"ikinci mesaj")
    time.sleep(0.2)  # ikisi de alici tamponuna gelsin
    print("iki sendall -> tek recv: %r" % sunucu.recv(4096))

    # Tek 10000 baytlik gonderim, recv(1024) ile okunur.
    istemci.sendall(b"A" * 10000)
    toplam, cagri, boyutlar = 0, 0, []
    while toplam < 10000:
        b = sunucu.recv(1024)
        boyutlar.append(len(b))
        toplam += len(b)
        cagri += 1
    print(
        "10000 bayt, recv(1024): %d cagri, en buyuk parca %d"
        % (cagri, max(boyutlar))
    )
    print("son parca boyutu: %d, toplam: %d" % (boyutlar[-1], toplam))

    istemci.close()
    sunucu.close()
    ls.close()
```

*Kodun devamı (b31_cerceve.py, satır 187–195):*

```python

if __name__ == "__main__":
    kip = sys.argv[1] if len(sys.argv) > 1 else "test"
    if kip == "test":
        test()
    elif kip == "kisa":
        kisa()
    else:
        print("kullanim: test | kisa")
```

Testlerin çıktısına bakalım. İlk satır, 200 mesajın 500 rastgele noktadan bölünmüş bir akışta bile doğru okunduğunu söyler. İkinci satır, aynı bölünmüş akışın naif okuyucuda nasıl patladığını gösterir: `s.recv(4)` tek seferde iki bayt döndürdüğünde `struct.unpack` hata verir. Üçüncü satır aynı parçalar `tam_oku` ile okunduğunda sorunun kalmadığını gösterir.

```term
$ python3 b31_cerceve.py test
uzunluk onekli: 200 mesaj, 501 parcaya bolunmus akis: tamam
naif: struct.error -> unpack requires a buffer of 4 bytes
dogru: b'abc'
ayracli: 3 satir, parcalara ragmen dogru
sinir: reddedildi -> cerceve uzunlugu sinirin uzerinde: 4294967295
TUM TESTLER GECTI
```

Bu çıktıdan iki sonuç çıkar. Birincisi, `recv` sayısı ile mesaj sayısı arasında bir ilişki yoktur; doğru okuyucu yalnızca toplam baytları sayar. İkincisi, sınır denetimi bir güvenlik özelliğidir: `0xFFFFFFFF` uzunluk iddiası, yük okunmadan reddedildi. Bölüm 31.11'de bu denetimin neden yeterli olmadığını ve Bölüm 32'nin hangi katmanları ekleyeceğini tartışacağız.

## 31.5 İkili serileştirme: struct, dolgu ve sürümlü başlık

Mesajın içeriği bir sayı, bir alan ve bir bayrak olduğunda onu nasıl baytlara çevireceğin bir tasarım kararıdır. En kolay yol, C struct'ını `send(&s, sizeof s)` ile doğrudan göndermektir. Bu yol üç nedenle yanlıştır. Birincisi **dolgu (padding)**: Bölüm 2.7'de gördüğün gibi derleyici alanları hizalar ve aralarına görünmez baytlar koyar; bu baytların içeriği tanımsızdır. İkincisi **bayt sırası**: struct little-endian olarak yazılır ve ağ alıcısı bunu yanlış okur. Üçüncüsü **taşınabilirlik**: aynı struct, farklı bir derleyicide ya da mimaride farklı ofsetlere sahip olabilir. Bölüm 20.10'da bellek düzeninin maliyetini görmüştük; burada aynı düzen bir sözleşme olarak dışarıya çıkar.

Aşağıdaki C programı, bu tuzağı gerçek ofsetlerle gösterir. İki struct yazılmıştır: birincisi alanları doğal sırasında bırakır, ikincisi büyükten küçüğe sıralar. Sonra aynı alanları bir ağ tamponuna açıkça, sabit ofsetlerle yazan bir fonksiyon gelir.

```c
/* b31_2_yapi.c: C struct hizalamasi ve ikili serilestirme tuzagi.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 b31_2_yapi.c -o b31_2_yapi
 * Ortam: WSL2 Ubuntu 24.04, x86-64, gcc 13. Sonuclar bu mimaride
 * gecerlidir; baska mimari/derleyicide ofsetler farkli olabilir.
 */
#include <arpa/inet.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Dogal hizalama: derleyici alanlari hizalar, bosluk birakir. */
struct kotu {
    uint8_t tip;
    uint32_t uzunluk;
    uint16_t sira;
};

/* Ayni alanlar, buyukten kucuge siralanmis: bosluk azalir. */
struct iyi {
    uint32_t uzunluk;
    uint16_t sira;
    uint8_t tip;
};

```

```c
static void hex_yaz(const char *ad, const void *p, size_t n)
{
    const unsigned char *b = p;
    printf("%-22s", ad);
    for (size_t i = 0; i < n; i++) printf(" %02X", b[i]);
    printf("\n");
}

/* Alanlari TELL ofsetlere, ag sirasiyla yaz. Bellek duzeni
 * ve hizalama bu fonksiyonda hic rol oynamaz. */
static size_t paket_yaz(uint8_t *tampon, uint8_t tip,
                        uint32_t uzunluk, uint16_t sira)
{
    tampon[0] = tip;                    /* 1 bayt, sira yok */
    uint32_t un = htonl(uzunluk);
    memcpy(tampon + 1, &un, 4);         /* 4 bayt, ag sirasi */
    uint16_t sn = htons(sira);
    memcpy(tampon + 5, &sn, 2);         /* 2 bayt, ag sirasi */
    return 7;                           /* toplam: dolgu yok */
}
```

```c
int main(void)
{
    printf("sizeof(struct kotu) = %zu\n", sizeof(struct kotu));
    printf("  ofset tip=%zu uzunluk=%zu sira=%zu\n",
           offsetof(struct kotu, tip), offsetof(struct kotu, uzunluk),
           offsetof(struct kotu, sira));
    printf("sizeof(struct iyi)  = %zu\n", sizeof(struct iyi));
    printf("  ofset uzunluk=%zu sira=%zu tip=%zu\n",
           offsetof(struct iyi, uzunluk), offsetof(struct iyi, sira),
           offsetof(struct iyi, tip));

    /* Dolgu baytlari belirsizdir: once tamamini sifirla. */
    struct kotu k;
    memset(&k, 0, sizeof k);
    k.tip = 2;
    k.uzunluk = 3;
    k.sira = 7;
    hex_yaz("kotu (ham struct)", &k, sizeof k);

    uint8_t p[7];
    size_t n = paket_yaz(p, 2, 3, 7);
    hex_yaz("paket_yaz (ag)", p, n);

    /* Ham struct'i karsi tarafta okuyan bir makine (ayni derleyici,
     * ayni hizalama) bile dolgu yuzunden yanlis ofsetten okur. */
    uint32_t okunan_uzunluk;
    const uint8_t *ham = (const uint8_t *)&k;
    memcpy(&okunan_uzunluk, ham + offsetof(struct kotu, uzunluk), 4);
    printf("ham struct icinde uzunluk (LE bellek): 0x%08X\n",
           okunan_uzunluk);
    uint32_t agdan;
    memcpy(&agdan, p + 1, 4);
    printf("ag baytlarindan uzunluk (ntohl): %u\n", ntohl(agdan));
    return 0;
}
```

Derleyip çalıştıralım. Çıktının ilk satırları iki struct'ın boyutunu ve ofsetlerini verir; sonraki satırlar aynı verinin iki farklı yolla nasıl baytlandığını gösterir.

```term
$ ./b31_2_yapi
sizeof(struct kotu) = 12
  ofset tip=0 uzunluk=4 sira=8
sizeof(struct iyi)  = 8
  ofset uzunluk=0 sira=4 tip=6
kotu (ham struct)      02 00 00 00 03 00 00 00 07 00 00 00
paket_yaz (ag)         02 00 00 00 03 00 07
ham struct icinde uzunluk (LE bellek): 0x00000003
ag baytlarindan uzunluk (ntohl): 3
```

`kotu` struct'ı 12 bayt tutar, oysa alanlarının toplamı yalnızca 7 bayttır. Ham struct dökümünde `03 00 00 00` dizisi, uzunluğun little-endian yazıldığını gösterir; ağ tamponundaki `00 00 00 03` ise büyük uçlu sıradır. Ham struct gönderilseydi alıcı 3 yerine `0x03000000` (50 331 648) okurdu. İyi tasarlanmış struct, alanları büyükten küçüğe sıralayarak dolguyu 8 bayta indirir (`iyi`), ama bu yine bayt sırası sorununu çözmez. Doğru yol, alanları tek tek ağ sırasına çevirip yazmaktır (`paket_yaz`).

Python tarafında aynı sorun `struct` modülüyle görünür: `@` (yerel düzen, hizalamalı) ve `!` (ağ düzeni, hizasız) biçimlerinin boyutları farklıdır. Kontrol edelim:

```term
$ python3 -c "from struct import calcsize as c;print(c('@BI'),c('!BI'))"
8 5
```

`@BI` 8 bayt, `!BI` 5 bayt verir. Fark, yerel düzenin `I` (4 bayt) alanını 4'ün katı bir adrese hizalamak için 3 bayt dolgu eklemesidir. Ağ protokollerinde dolgu istemediğimiz için `!` ile başlamak kuraldır.

Gerçek bir protokolde yalnızca alanları sabitlemek yetmez; protokol sürümü de değişebilmelidir. Bu yüzden her mesajın başına bir **başlık** koyarız: sihirli sayı (sıradan bir akışı ayırt etmek için), sürüm (protokol değişince eski ve yeni tarafın birbirini tanıması için), mesaj türü, yük uzunluğu ve bir sağlama değeri (CRC-32). Aşağıdaki modül 12 baytlık bu başlığı tanımlar ve CRC'yi başlığın da üzerinden hesaplar; böylece tür alanındaki tek bir bit bozulması da yakalanır.

```python
# -*- coding: utf-8 -*-
"""b31_baslik.py: surumlenebilir mesaj basligi (12 bayt) + CRC-32.
Kullanim: python b31_baslik.py   (testleri calistirir)"""

import struct
import zlib

BASLIK = struct.Struct("!HBBII")  # sihir, surum, tur, uzunluk, crc
SIHIR = 0xB31C
SURUM = 1
MAKS = 1 << 20


def paketle(tur, yuk):
    ust = struct.pack("!HBBI", SIHIR, SURUM, tur, len(yuk))
    crc = zlib.crc32(yuk, zlib.crc32(ust))  # CRC basligi da kapsar
    return ust + struct.pack("!I", crc) + yuk


def coz(b):
    if len(b) < BASLIK.size:
        raise ValueError("kisa paket")
    sihir, surum, tur, n, crc = BASLIK.unpack_from(b, 0)
    if sihir != SIHIR:
        raise ValueError("sihir uyusmuyor: 0x%04X" % sihir)
    if surum != SURUM:
        raise ValueError("desteklenmeyen surum: %d" % surum)
    if n > MAKS:
        raise ValueError("uzunluk sinirin ustunde: %d" % n)
    yuk = bytes(b[BASLIK.size : BASLIK.size + n])
    if len(yuk) != n:
        raise ValueError("eksik paket")
    ust = struct.pack("!HBBI", sihir, surum, tur, n)
    if zlib.crc32(yuk, zlib.crc32(ust)) != crc:
        raise ValueError("CRC uyusmuyor")
    return tur, yuk
```

*Kodun devamı (b31_baslik.py, satır 38–57):*

```python

if __name__ == "__main__":
    print("BASLIK boyutu:", BASLIK.size)
    p = paketle(3, b"merhaba")
    print("paket:", p.hex(" "))
    print("coz:", coz(p))
    for ad, bozuk in [
        ("tur bayti", p[:3] + bytes([p[3] ^ 1]) + p[4:]),
        ("yuk biti", p[:-1] + bytes([p[-1] ^ 0x10])),
        ("sihir", b"\x00" + p[1:]),
    ]:
        try:
            coz(bozuk)
            print(ad, "kabul edildi")
        except ValueError as e:
            print("%-10s reddedildi: %s" % (ad, e))
    try:
        coz(struct.pack("!HBBII", SIHIR, SURUM, 1, 0xFFFFFFFF, 0))
    except ValueError as e:
        print("asiri uzunluk reddedildi: %s" % e)
```

Testte başlığın üç ayrı bozulmayı nasıl yakaladığını görüyoruz: tür baytındaki tek bit, yük içindeki tek bit ve sihir. Son satır, 4 GiB'lık uzunluk iddiasının okunmadan reddedildiğini gösterir.

```term
$ python3 b31_baslik.py
BASLIK boyutu: 12
paket: b3 1c 01 03 00 00 00 07 43 b7 b1 aa 6d 65 72 68 61 62 61
coz: (3, b'merhaba')
tur bayti  reddedildi: CRC uyusmuyor
yuk biti   reddedildi: CRC uyusmuyor
sihir      reddedildi: sihir uyusmuyor: 0x001C
asiri uzunluk reddedildi: uzunluk sinirin ustunde: 4294967295
```

Çıktıdaki `paket` satırı, 12 baytlık başlık ve altı baytlık yükün tam dökümüdür: `b3 1c` sihir, `01` sürüm, `03` tür, `00 00 00 06` uzunluk ve ardından CRC. CRC'nin tür baytını da kapsaması önemlidir: CRC yalnızca yükü koruyan bir tasarımda `tür` alanı sessizce değişebilirdi. Sürüm alanı, yeni bir alan eklemek istediğinde alıcının eski mesajları reddetmesini ya da yeni alanı yok saymasını sağlar. Bu, Bölüm 45'te UART paketlerini tasarlarken de aynı şekilde karşına çıkacak.

## 31.6 Hata kipleri: TIME_WAIT, zaman aşımı, EPIPE ve SIGPIPE

Ağ programının hata durumları, yerel dosya G/Ç'den daha çoktur. Bir bağlantı beklenmedik biçimde kapanabilir, bir yazma karşı tarafın yokluğunda başarısız olabilir, bir okuma sonsuza kadar bekleyebilir. Bu kısımda en sık karşılaşılanları gerçek programla üretiyoruz.

**Adres kullanımda hatası (`EADDRINUSE`)** sunucu yeniden başlatıldığında en tanıdık hatadır. Sebebi TCP'nin kapanış protokolüdür: bağlantıyı önce kapatan taraf, bağlantı tuple'ını (yerel IP ve port, uzak IP ve port) bir süre `TIME_WAIT` durumunda tutar. Bu durum Bölüm 29'da ayrıntılı anlatılır; burada yalnızca sonucunu görüyoruz: aynı yerel port, bu süre dolana kadar yeniden bağlanamaz. Linux'ta bu süre varsayılan olarak 60 saniyedir (genel bilgi). `SO_REUSEADDR` bayrağı bu kısıtı gevşetir. Aşağıdaki kip iki senaryoyu yan yana çalıştırır: birincisinde sunucu bayrak olmadan kurulur, ikincisinde bayrakla.

```term
$ ./b31_1_yasam bindhata
SO_REUSEADDR=0: bind hatasi: Address already in use
SO_REUSEADDR=1: bind basarili
```

Çıktı iki şeyi kanıtlar. Bayrağı olmayan sunucu, aynı portu yeniden bağlamaya çalıştığında `Address already in use` hatası alır. Bayrağı olan sunucu ise başarılı olur. Dikkat edilmesi gereken nokta, bayrağın **her iki tarafta da** olması gerektiğidir: kabul edilen soket dinleyiciden bayrağı miras aldığı için, TIME_WAIT durumundaki soketin de bayrağı vardır. Bu yüzden sunucu kodunda `setsockopt(SO_REUSEADDR)`ı `bind`'den önce çağırmak kuraldır. Windows'ta bu bayrağın anlamı farklıdır ve güvenlik riski taşıyabilir; genel bilgi olarak Bölüm 31.11'e bırakıyoruz.

**Zaman aşımı** ikinci büyük sınıftır. Karşı taraf yanıt vermezse `recv` sonsuza kadar bekleyebilir. Soket seviyesinde `SO_RCVTIMEO` ile bir süre sınırı koyarsın; süre dolduğunda `recv` -1 döndürür ve `errno` `EAGAIN` (ya da `EWOULDBLOCK`) olur. Python'da `settimeout` aynı davranışı sağlar, ama CPython bunu soketi engellemeyen kipe alıp kendi bekleme döngüsüyle uygular; yani Python'da `SO_RCVTIMEO` doğrudan kullanılmaz.

```term
$ ./b31_1_yasam zaman
recv -1, errno=EAGAIN, sure ~1000 ms
```

Çıktıda süre yaklaşık bir saniye olarak ölçüldü (100 ms'e yuvarlanmış). Bu süre sınırı, Bölüm 28'deki engellemeyen G/Ç ile aynı mantıktadır: `EAGAIN`, "şu an veri yok, sonra tekrar dene" demektir ve hatalı değildir.

**Kapanmış bir bağlantıya yazmak** en tehlikeli kenardır. Karşı taraf bağlantıyı kapattığında yerel tarafın ilk yazması çoğu zaman başarılı görünür: veri çekirdek tamponuna girer ve ağa çıkar. Karşı taraf bunu kabul edemediğinde bir RST (reset) paketi döner. İkinci yazma, bağlantının artık yok olduğunu öğrenir ve `EPIPE` (Broken pipe) alır. Ama bu hata, varsayılan olarak **SIGPIPE** sinyali ile birlikte gelir ve SIGPIPE'ın varsayılan davranışı süreci sonlandırmaktır. Bu, Bölüm 26'daki sinyal bilgisine doğrudan bağlanır: sinyal, yazmayı yapan iş parçacığının yanına gelir ve kodun hiç hata kontrolü yapmadığı bir programı öldürür.

Üç davranışı yan yana görelim: `MSG_NOSIGNAL` bayrağıyla, SIGPIPE'ı yok sayarak ve hiçbir koruma olmadan.

```term
$ ./b31_1_yasam pipe_hata
send #1: 1024 bayt
send #2: -1, errno=Broken pipe
```

```term
$ ./b31_1_yasam pipe_olum; echo "cikis=$?"
SIGPIPE varsayilan: surec olur
send #1: 1024 bayt
cikis=141
```

İlk çıktıda birinci yazma başarılı (1024 bayt), ikincisi `EPIPE` ile başarısız. Program kontrolünü kaybetmez. İkinci çıktıda ise `SIGPIPE` teslim edildi ve süreç sonlandı; kabuğun gördüğü çıkış kodu 141'dir. 141, sonlandırıcı sinyalin numarasının (13) 128 ile toplamıdır. `MSG_NOSIGNAL` Linux'a özgü bir bayraktır; macOS'ta `SO_NOSIGPIPE` soket seçeneği kullanılır (genel bilgi). CPython ise başlangıçta SIGPIPE'ı yok sayar; bu yüzden Python'da bu tuzağa düşmezsin, yazma `BrokenPipeError` fırlatır (genel bilgi).

**Yarım kapanış ve kısa yazma** son iki kenardır. `send` yalnızca bir kısmını yazabilir; bu yüzden `tam_gonder` gibi bir döngü şarttır (Bölüm 31.2). Karşı tarafın tamamen kapanması ise `recv`'in 0 döndürmesiyle anlaşılır, ama bu, yalnızca karşı tarafın yazmayı bitirdiği anlamına gelir; sen hâlâ yazabilirsin. Bu ayrım `shutdown(SHUT_WR)` ile istemci tarafında kullanılır ve sunucu yanıtını bitirdikten sonra kapanır.

## 31.7 Eşzamanlı sunucu modelleri: altı model, tek kod

Gerçek bir sunucu aynı anda birçok istemciye hizmet vermek zorundadır. Bunun altı yaygın yolu vardır ve hepsi aynı protokolü konuşabilir. Bölüm 26.13'te süreç ve iş parçacığı modellerini kısaca görmüştük; burada hepsini **aynı yanki protokolü** ile yazıp yan yana koyuyoruz.

**İteratif (iteratif)** modelde sunucu tek bir bağlantıyı kabul eder, bitene kadar hizmet eder, sonra bir sonrakini kabul eder. Kodu en basittir, ama bir bağlantı kapanmadıkça diğerleri bekler. **Süreç başına (fork)** modelde her bağlantı için `fork` ile bir çocuk süreç yaratılır; çocuk bağlantıyı işler, ebeveyn yeni bağlantıları kabul eder. Süreçler bellek ayrımı sağlar, ama her süreç bedeli yüksektir. **İş parçacığı başına (thread)** modelde aynı iş, süreç yerine iş parçacığında yapılır; bellek paylaşılır ama CPython'da GIL yüzünden Python iş parçacıkları aynı anda bayt kodu çalıştıramaz (Bölüm 26.12). **İş parçacığı havuzu (havuz)** modelde sabit sayıda işçi iş parçacığı vardır ve bağlantılar bir kuyruktan alınır; kaynak kullanımı sınırlıdır, ama bir işçi bir bağlantıya bağlı kaldığı sürece başka bağlantılar kuyrukta bekler.

Olay tabanlı iki model, epoll (Linux) ve `asyncio` (Python), tek bir iş parçacığında çalışır. Dinleme soketini ve tüm bağlantıları çoğullayan bir döngü, yalnızca hazır olanlara hizmet eder. Bu, Bölüm 28.12'de gördüğümüz ve Örnek 4'te uyguladığımız modelin soketlere taşınmış hâlidir. Bu modellerin kodu 31.8'de ayrıca açıklanır.

Şekil 31.5, altı modelin kavramsal farkını özetler. Sayılar 31.9'da ölçülecek.

![Şekil 31.5: Altı sunucu modelinin karşılaştırması. Bekleme sütunu iş parçacığının uyuduğu yeri, ölçek sınırı sütunu sistemi zorlayan kaynağı gösterir.](gorseller/b31_modeller_kiyas.png)

Altı modelin tek kaynak dosyası aşağıdadır. Modeller `SUNUCULAR` sözlüğünde toplanır; `sunucu MODEL PORT` kipiyle tek bir modeli başlatabilir, `olc` kipiyle hepsini ölçebilirsin. Protokol, Bölüm 31.4'teki uzunluk önekli çerçevedir; yük 64 bayt ve sunucu yankılar. Kod WSL2'de Python 3.12.3 ile çalışır, çünkü `fork` ve `epoll` Linux'a özgüdür.

```python
# -*- coding: utf-8 -*-
"""b31_modeller.py: ayni yanki sunucusunun 6 eszamanlilik modeli.

Protokol: uzunluk onekli cerceve (b31_cerceve), 64 baytlik yuk, yanki.
Kullanim (WSL2, Linux'ta calistirilir: fork ve epoll Linux'a ozgu):
  python3 b31_modeller.py sunucu MODEL PORT
  python3 b31_modeller.py olc CSV_YOLU       # tum modelleri olcer
  python3 b31_modeller.py tek MODEL N         # tek olcum
Modeller: iteratif, fork, thread, havuz, epoll, asyncio
"""

import asyncio
import multiprocessing as mp
import os
import random
import select
import signal
import socket
import struct
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b31_cerceve import cerceve_al, cerceve_gonder, tam_oku

MODELLER = ["iteratif", "fork", "thread", "havuz", "epoll", "asyncio"]
YUK_BOYU = 64
HAVUZ_ISCI = 16
BEKLEME_BACKLOG = 1024


def dinleyici(port):
    ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ls.bind(("127.0.0.1", port))
    ls.listen(BEKLEME_BACKLOG)
    return ls
```

*Kodun devamı (b31_modeller.py, satır 42–76):*

```python

# ---------- Sunucu modelleri (bloklayan kod) ---------------- #


def baglanti_dongusu(c):
    """Tek bir baglantida: al, yanki, tekrarla. Karsi taraf kapaninca
    donus. Bloklayici soket: her cagri bu is parcacigini uyutur."""
    try:
        while True:
            yuk = cerceve_al(c)
            cerceve_gonder(c, yuk)
    except (EOFError, ConnectionError, OSError):
        pass
    finally:
        c.close()


def sunucu_iteratif(port):
    ls = dinleyici(port)
    while True:
        c, _ = ls.accept()
        baglanti_dongusu(c)  # bitene kadar baskasina bakmaz


def sunucu_fork(port):
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)  # zombi olusmasin
    ls = dinleyici(port)
    while True:
        c, _ = ls.accept()
        pid = os.fork()
        if pid == 0:  # cocuk: dinleyiciyi kapat, isi yap
            ls.close()
            baglanti_dongusu(c)
            os._exit(0)
        c.close()  # ebeveyn: kopyasini kapat
```

*Kodun devamı (b31_modeller.py, satır 78–113):*

```python

def sunucu_thread(port):
    ls = dinleyici(port)
    while True:
        c, _ = ls.accept()
        threading.Thread(
            target=baglanti_dongusu, args=(c,), daemon=True
        ).start()


def sunucu_havuz(port):
    ls = dinleyici(port)
    havuz = ThreadPoolExecutor(max_workers=HAVUZ_ISCI)
    while True:
        c, _ = ls.accept()
        havuz.submit(
            baglanti_dongusu, c
        )  # is = baglanti; havuz sinirli


# ---------- Olay tabanli modeller -------------------------- #


class Baglanti:
    __slots__ = ("soket", "gelen", "giden", "kapanacak")

    def __init__(self, soket):
        self.soket = soket
        self.gelen = bytearray()  # okunmamis ham bayt
        self.giden = bytearray()  # henuz gonderilmemis cikti
        self.kapanacak = False


def sunucu_epoll(port):
    ls = dinleyici(port)
    ls.setblocking(False)
```

*Kodun devamı (b31_modeller.py, satır 115–150):*

```python
    ep = select.epoll()
    ep.register(ls.fileno(), select.EPOLLIN)
    baglar = {}
    dinl = ls.fileno()
    while True:
        for fd, olay in ep.poll():
            if fd == dinl:
                while True:  # kenar degil ama tum bekleyenleri al
                    try:
                        c, _ = ls.accept()
                    except BlockingIOError:
                        break
                    c.setblocking(False)
                    c.setsockopt(
                        socket.IPPROTO_TCP, socket.TCP_NODELAY, 1
                    )
                    baglar[c.fileno()] = Baglanti(c)
                    ep.register(c.fileno(), select.EPOLLIN)
                continue
            b = baglar[fd]
            if olay & (select.EPOLLERR | select.EPOLLHUP):
                _kapat(ep, baglar, fd)
                continue
            if olay & select.EPOLLIN:
                _oku_cerceveleri(b)
                if b.kapanacak and not b.giden:
                    _kapat(ep, baglar, fd)
                    continue
            if b.giden:
                _yaz(b)
            if b.giden:
                ep.modify(fd, select.EPOLLIN | select.EPOLLOUT)
            else:
                ep.modify(fd, select.EPOLLIN)
                if b.kapanacak:
                    _kapat(ep, baglar, fd)
```

*Kodun devamı (b31_modeller.py, satır 152–187):*

```python

def _oku_cerceveleri(b):
    """Olan tum baytlari oku; tam cerceveleri yanki kuyruguna koy."""
    while True:
        try:
            parca = b.soket.recv(65536)
        except BlockingIOError:
            break
        if not parca:  # karsi taraf FIN gonderdi
            b.kapanacak = True
            break
        b.gelen += parca
    while len(b.gelen) >= 4:
        (n,) = struct.unpack_from("!I", b.gelen, 0)
        if len(b.gelen) < 4 + n:
            break  # yarim cerceve: sonraki olayi bekle
        yuk = bytes(b.gelen[4 : 4 + n])
        del b.gelen[: 4 + n]
        b.giden += struct.pack("!I", n) + yuk


def _yaz(b):
    """Yazmayi mumkun oldugu kadar yap; kalanlar giden'de kalir."""
    try:
        k = b.soket.send(b.giden)
        del b.giden[:k]
    except BlockingIOError:
        pass


def _kapat(ep, baglar, fd):
    ep.unregister(fd)
    baglar.pop(fd).soket.close()


async def _asyncio_el(reader, writer):
```

*Kodun devamı (b31_modeller.py, satır 189–198):*

```python
    try:
        while True:
            (n,) = struct.unpack("!I", await reader.readexactly(4))
            yuk = await reader.readexactly(n)
            writer.write(struct.pack("!I", n) + yuk)
            await writer.drain()
    except (asyncio.IncompleteReadError, ConnectionError):
        pass
    finally:
        writer.close()
```

*Kodun devamı (b31_modeller.py, satır 200–238):*

```python

async def _asyncio_ana(port):
    srv = await asyncio.start_server(
        _asyncio_el, "127.0.0.1", port, backlog=BEKLEME_BACKLOG
    )
    async with srv:
        await srv.serve_forever()


def sunucu_asyncio(port):
    asyncio.run(_asyncio_ana(port))


SUNUCULAR = {
    "iteratif": sunucu_iteratif,
    "fork": sunucu_fork,
    "thread": sunucu_thread,
    "havuz": sunucu_havuz,
    "epoll": sunucu_epoll,
    "asyncio": sunucu_asyncio,
}


# ---------- Yuk uretici (istemci) -------------------------- #


def _istemci_is(port, istek, yuk, gecikmeler):
    # Ilk isteğin gecikmesi baglanti kurulumunu da kapsar: sunucu
    # kuyrukta bekleyen istemciyi yavaslatir ve bu olcume girmelidir.
    t0 = time.perf_counter()
    s = socket.create_connection(("127.0.0.1", port))
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    for i in range(istek):
        if i:
            t0 = time.perf_counter()
        cerceve_gonder(s, yuk)
        cerceve_al(s)
        gecikmeler.append(time.perf_counter() - t0)
    s.close()
```

*Kodun devamı (b31_modeller.py, satır 240–276):*

```python

def _grup(port, baglanti, istek, tohum):
    """Bir surecte birden cok istemci iş parçacığı."""
    rnd = random.Random(tohum)
    yuk = bytes(rnd.getrandbits(8) for _ in range(YUK_BOYU))
    gecikmeler = []
    ths = [
        threading.Thread(
            target=_istemci_is, args=(port, istek, yuk, gecikmeler)
        )
        for _ in range(baglanti)
    ]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    return gecikmeler


def yuk_olc(port, n, istek, surec=4):
    """n eşzamanli baglanti, her biri istek kez yanki yapar."""
    pay = [
        n // surec + (1 if i < n % surec else 0) for i in range(surec)
    ]
    pay = [p for p in pay if p > 0]
    t0 = time.perf_counter()
    with mp.Pool(len(pay)) as pool:
        sonuclar = pool.starmap(
            _grup,
            [(port, p, istek, 31 + i) for i, p in enumerate(pay)],
        )
    sure = time.perf_counter() - t0
    gec = sorted(x for g in sonuclar for x in g)
    toplam = len(gec)
    p50 = gec[toplam // 2] * 1000
    p99 = gec[int(toplam * 0.99) - 1] * 1000
    return toplam / sure, p50, p99, gec[-1] * 1000
```

*Kodun devamı (b31_modeller.py, satır 278–313):*

```python

def _bekle(port):
    for _ in range(300):
        try:
            socket.create_connection(("127.0.0.1", port)).close()
            return
        except OSError:
            time.sleep(0.02)
    raise RuntimeError("sunucu acilmadi")


def tek_olcum(model, n, istek, port):
    p = subprocess.Popen(
        [
            sys.executable,
            os.path.abspath(__file__),
            "sunucu",
            model,
            str(port),
        ]
    )
    try:
        _bekle(port)
        return yuk_olc(port, n, istek)
    finally:
        p.terminate()
        p.wait()


def olc(csv_yolu):
    # Ayni yanki protokolu: N eşzamanli istemci, her biri 200 istek.
    # Tekrar: 3 kez; medyan alinir. Port: her olcum icin ayri.
    istek = 200
    dizi = [1, 16, 64, 256]
    satirlar = ["model,n,istek_s,p50_ms,p99_ms,maks_ms"]
    port = 9100
```

*Kodun devamı (b31_modeller.py, satır 315–336):*

```python
    for model in MODELLER:
        for n in dizi:
            sonuc = []
            for _ in range(3):
                port += 1
                sonuc.append(tek_olcum(model, n, istek, port))
            ist = sorted(s[0] for s in sonuc)[1]
            p50 = sorted(s[1] for s in sonuc)[1]
            p99 = sorted(s[2] for s in sonuc)[1]
            mks = sorted(s[3] for s in sonuc)[1]
            satir = "%s,%d,%.0f,%.3f,%.3f,%.3f" % (
                model,
                n,
                ist,
                p50,
                p99,
                mks,
            )
            print(satir, flush=True)
            satirlar.append(satir)
    with open(csv_yolu, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
```

*Kodun devamı (b31_modeller.py, satır 338–351):*

```python

if __name__ == "__main__":
    kip = sys.argv[1]
    if kip == "sunucu":
        SUNUCULAR[sys.argv[2]](int(sys.argv[3]))
    elif kip == "olc":
        olc(sys.argv[2])
    elif kip == "tek":
        m, n = sys.argv[2], int(sys.argv[3])
        ist, p50, p99, mks = tek_olcum(m, n, 200, 9500)
        print(
            "%s n=%d: %.0f istek/s, p50=%.3f ms, p99=%.3f ms, "
            "maks=%.3f ms" % (m, n, ist, p50, p99, mks)
        )
```

Modelin kalbi `baglanti_dongusu` fonksiyonudur: bir bağlantıda tekrar tekrar mesaj alır ve yankılar; karşı taraf kapanınca döner. Bu fonksiyonu altı modelin hepsi kullanır. Farklılık yalnızca onu **kimin, ne zaman** çağırdığındadır: iteratif modelde ana süreç, fork modelde çocuk süreç, thread modelde yeni bir iş parçacığı, havuz modelinde işçi, epoll ve asyncio'da ise olay döngüsü kendi durum makinesini kullanır.

## 31.8 Olay döngüsü: epoll ve asyncio

Bölüm 28'deki epoll örneğinde pipe'ların okuma uçlarını izlemiştik. Soketler de aynı şekilde çalışır: hazır olduklarında epoll bildirim verir. Ancak soketlerde bir yeni durum vardır: **yazma tarafı da engellenebilir.** Çekirdek gönderim tamponu dolduğunda `send` kısmi yazar ya da `EAGAIN` döndürür. Olay döngüsü bu durumu yönetmek zorundadır ve bunun yolu `EPOLLOUT` olayıdır.

Şekil 31.6 epoll sunucusunun durumlarını gösterir. Dinleme soketi `EPOLLIN` ile izlenir; yeni bağlantı geldiğinde tüm bekleyenleri kabul eder. Her bağlantı kendi durumunu taşır: gelen tampon, giden tampon ve kapanma bayrağı. Giden tampon dolu olduğunda maske `EPOLLIN|EPOLLOUT` olur; boşaldığında yalnızca `EPOLLIN`'e dönülür. Bu geri dönüş önemlidir: `EPOLLOUT` açık bırakılırsa, yazacak bir şey olmasa bile döngü her turda uyanır (sürekli uyanma).

![Şekil 31.6: epoll sunucusunun durum diyagramı. EPOLLOUT yalnızca giden tampon doluyken izlenir; boşalınca EPOLLIN'e dönülür.](gorseller/b31_epoll_durum.png)

Modeldeki `sunucu_epoll` fonksiyonu bu makinenin gerçeklemesidir (yukarıdaki kodun 111–150. satırları). Yazma yardımcı işlevi `_yaz`, göndermeyi mümkün olduğu kadar yapar ve kalanı tamponda bırakır; bunun doğruluğunu Örnek 4'te ayrıca sınayacağız.

Python'un `asyncio` modeli aynı işi farklı bir biçimde yapar. `asyncio.start_server`, her bağlantı için bir **görev (task)** oluşturur; görev `await reader.readexactly(n)` gibi çağrılarla askıya alınır ve olay döngüsü, veri hazır olduğunda görevi devam ettirir. Programcı durum makinesi yazmaz; ama aynı kaynak fikri geçerlidir: tek bir iş parçacığı, çok sayıda bekleyen bağlantı. Bu modelin ölçülen sonuçları epoll'a çok yakındır.

Bu iki modelin ortak sınırı şudur: tek bir çekirdek üzerinde çalışırlar (CPython'da GIL nedeniyle). Yük çok çekirdeğe yayılmak istediğinde süreç başına ya da çoklu sunucu süreci (örneğin Nginx'in worker süreçleri) gerekir. "C10K" problemi, yani on bin eşzamanlı bağlantıyı tek makinede tutabilme sorunu, bu olay tabanlı modellerle çözülmüştür; Dan Kegel'in 1999'da yayımladığı bu konu genel bilgidir.

## 31.9 Ölçüm: modeller yük altında

Şimdi modelleri ölçelim. Her ölçümde aynı yanki sunucusu, eşzamanlı n bağlantı ve her bağlantıda 200 istek kullanıldı. İstemciler aynı makinede, dört Python sürecine dağıtılmış iş parçacıklarıdır. Her gecikme, isteğin gönderilmesinden yanıtın alınmasına kadar geçen süredir; bağlantı kurulumu da ilk isteğin süresine dahil edildi. Her (model, n) çifti üç kez çalıştırıldı ve medyan alındı. Tablo bu ölçümün ham çıktısıdır.

| model | n | istek_s | p50_ms | p99_ms | maks_ms |
|---|---|---|---|---|---|
| iteratif | 1 | 10824 | 0.053 | 0.111 | 0.373 |
| iteratif | 16 | 15217 | 0.055 | 0.144 | 188.275 |
| iteratif | 64 | 13254 | 0.062 | 0.210 | 937.061 |
| iteratif | 256 | 15105 | 0.057 | 0.147 | 3347.741 |
| fork | 1 | 9286 | 0.059 | 0.137 | 1.683 |
| fork | 16 | 64032 | 0.099 | 0.628 | 14.860 |
| fork | 64 | 49316 | 0.688 | 3.775 | 50.061 |
| fork | 256 | 48504 | 2.788 | 15.931 | 255.551 |
| thread | 1 | 10001 | 0.060 | 0.140 | 0.584 |
| thread | 16 | 14330 | 0.857 | 3.683 | 12.347 |
| thread | 64 | 14502 | 3.036 | 15.185 | 186.016 |
| thread | 256 | 13628 | 8.359 | 44.116 | 2060.306 |
| havuz | 1 | 10380 | 0.056 | 0.145 | 0.481 |
| havuz | 16 | 13087 | 0.959 | 3.730 | 13.245 |
| havuz | 64 | 12589 | 1.070 | 4.429 | 759.288 |
| havuz | 256 | 12634 | 1.072 | 4.585 | 3895.659 |
| epoll | 1 | 8761 | 0.071 | 0.179 | 0.489 |
| epoll | 16 | 36327 | 0.337 | 0.771 | 1.595 |
| epoll | 64 | 38908 | 1.482 | 3.029 | 6.853 |
| epoll | 256 | 37015 | 6.348 | 11.112 | 47.289 |
| asyncio | 1 | 8695 | 0.072 | 0.168 | 0.581 |
| asyncio | 16 | 31189 | 0.429 | 0.674 | 2.078 |
| asyncio | 64 | 28615 | 1.734 | 5.485 | 10.452 |
| asyncio | 256 | 30376 | 7.878 | 12.767 | 65.543 |

Tabloda birkaç şeyi birlikte okumalısın. Önce tek bağlantı (n=1): tüm modeller 8,7–10,8 bin istek/s ve 0,05–0,07 ms medyan gecikme verir. Bu, tek bir isteğin çekirdek sistem çağrıları ve Python yükü dahil maliyetidir; modeller arasında fark yoktur, çünkü yalnızca bir istemci vardır. Fark n arttığında belirginleşir.

n=16'da `fork` en yüksek verimi (yaklaşık 64 bin istek/s) gösterir, `epoll` (yaklaşık 36 bin) ve `asyncio` (yaklaşık 31 bin) hemen arkasındadır. `iteratif` yaklaşık 15 bin'de kalır, çünkü bir anda yalnızca bir bağlantıya hizmet eder. `thread` ve `havuz` yaklaşık 13–14 bin'dedir. Bu sıralamanın nedeni CPython'un GIL'idir: iş parçacıkları Python kodunu aynı anda çalıştıramaz, bu yüzden çok çekirdekli makinede bile hızlanamazlar. `fork` ise her bağlantıyı ayrı bir süreçte, ayrı bir GIL ile işler ve 16 çekirdeği kullanabilir.

n=256'da tablo değişir. `fork` hâlâ en hızlı modeldir (yaklaşık 48 bin), ama artık sistemi zorlamaya başlamıştır: 256 süreç, 16 çekirdekte birbirini bekler. `epoll` (yaklaşık 37 bin) ve `asyncio` (yaklaşık 30 bin) tek çekirdekte kalır, ama gecikmeleri 6–8 ms medyanında bile çok daha öngörülebilir kalır. `havuz` modeli 16 işçiyle sınırlıdır; 256 bağlantı kuyrukta bekler ve maksimum gecikme birkaç saniyeye çıkar.

Maksimum gecikme sütunu, ortalamanın ve p99'un gizlediği kuyruk etkisini gösterir. `iteratif` modelde n=256 için maksimum gecikme 3,3 saniyedir: son sıradaki istemci, diğer 255 bağlantının tamamlanmasını bekledi. p99 değeri ise yalnızca 0,15 ms civarındadır, çünkü bekleyen istemcilerin her biri yalnızca bir istekte uzun süre bekler ve bu, 3200 örneğin %0,5'ini oluşturur. Yani yüzdelikler tek başına yanıltıcı olabilir; kuyruk davranışını görmek için maksimuma da bakmak gerekir. Bu bir mühendislik dersidir: bir hizmet seviyesi (SLA) "p99 < 10 ms" diyorsa, o sunucunun uçuş kayıt cihazı gibi bir sistem için yetersiz olabileceğini anlamalısın.

Ölçümün sınırlarını da açıkça söylemeliyiz. İstemciler de Python ve aynı makinede çalışıyor; bu yüzden gördüğümüz en yüksek değer (yaklaşık 64 bin istek/s) sunucunun kesin tavanı değildir, istemcinin ve sunucunun birlikte oluşturduğu bir tavandır. Sunucu ile istemci aynı 16 çekirdeği paylaştığı için ölçüm gürültülüdür; üç tekrarın medyanı alınmasının nedeni budur. Farklı bir makinede, C ile yazılmış bir yük üreticisiyle farklı sayılar çıkar. Ölçtüğümüz şey, aynı protokol için modeller arasındaki **yönü ve sıralamayı**dır.

Şekil 31.7 aynı verinin grafiğini verir. Sol panelde verim, sağ panelde p99 gecikme vardır; her iki eksen logaritmiktir.

![Şekil 31.7: Altı modelin n eşzamanlı bağlantıdaki verimi (solda) ve p99 gecikmesi (sağda). Veri engine/veri/b31_modeller.csv dosyasından okunur.](gorseller/b31_model_olcum.png)

## 31.10 UDP: bağlantısız datagram ve durdur-bekle

TCP'nin bayt akışı ve güvenilirlik garantisi bedava değildir: bağlantı kurulumu, sıra numaraları, yeniden iletim ve tıkanıklık denetimi gecikme ve ek yük getirir. **UDP (User Datagram Protocol)** bu garantilerin hiçbirini vermez. Her `sendto` bir **datagram** gönderir, her `recvfrom` tam bir datagram alır: UDP mesaj sınırlarını korur. Ama paketler kaybolabilir, kopyalanabilir, sırası değişebilir ve alıcıya hiç ulaşmayabilir. Bağlantı kurulumu yoktur, bu yüzden sunucu-istemci ayrımı da yoktur: her soket hem gönderebilir hem alabilir.

UDP'nin datagram boyutu sınırları vardır. IPv4'te bir UDP datagramının en büyük yükü 65 507 bayttır (genel bilgi). Ama bir datagram, geçtiği ağın MTU değerini (Ethernet için tipik 1500 bayt) aşarsa IP parçalanmasına (fragmentation) uğrar; parçalardan birinin kaybı tüm datagramı yok eder. Bu nedenle pratikte küçük datagramlar (birkaç yüz bayt) tercih edilir. Loopback'in MTU'su büyüktür, bu yüzden loopback'te parçalanmayı gözlemleyemeyiz; bu, Bölüm 29'da anlatılan ağ katmanı ayrıntısıdır.

Yayın (broadcast) ve çoklu yayın (multicast) UDP'nin ağ genelindeki iki kullanımıdır. Yayında bir datagram aynı alt ağdaki tüm hostlara gider (`SO_BROADCAST` gerekir); çoklu yayında bir grup adresine katılan hostlar alır (`IP_ADD_MEMBERSHIP`). Bu bölümde loopback dışına çıkmadığımız için bu iki mekanizmayı yalnızca genel bilgi olarak anlatıyoruz; savunma uygulamalarında sensör verisinin birden çok tüketiciye dağıtımı için kullanılırlar.

UDP ile güvenilir aktarım kurmanın en basit yolu **durdur-bekle (stop-and-wait)** protokolüdür. Gönderici bir paket yollar ve onayı bekler. Onay gelmezse zaman aşımından sonra aynı paketi yeniden yollar. Alıcı, her paketi onaylar; paketin sıra biti beklediği biriyse teslim eder, değilse yinelenmiş bir kopya olarak yok sayar. Sıra biti yalnızca 0 ve 1 olabilir, çünkü gönderici aynı anda en fazla bir onaylanmamış paket tutar. Şekil 31.6 tipik bir akışı gösterir: veri kaybolur, zaman aşımı olur, yeniden gönderilir; bu kez onay kaybolur, veri yinelenir ve alıcı onu yok sayarak yeniden onaylar.

![Şekil 31.8: UDP durdur-bekle zaman çizelgesi. Kayıplar çarpıyla, zaman aşımları metinle gösterilir; alıcı yinelenen veriyi teslim etmeden yeniden onaylar.](gorseller/b31_udp_zaman.png)

Protokolün tamamı aşağıdaki modülde yer alır. Veri paketi `[tür:1][sıra:1][yük]`, onay paketi `[tür:1][sıra:1]` biçimindedir. Kayıp simülasyonu, gönderen ve alan taraflarda ayrı ve sabit tohumlu bir rastgele sayı üreteci ile yapılır; bu sayede aynı tohum her çalıştırmada aynı kayıp desenini üretir. Gönderici yalnızca `socket.timeout` ile yeniden iletir; `MAKS_YENIDEN` sınırı sonsuz döngüye karşı emniyettir. Modül ayrıca bir **telemetri paketi** tanımlar: 28 baytlık ikili bir kayıt, gövdesi 24 bayt ve CRC-32 ile biter. Bu, İHA telemetrisinin basitleştirilmiş bir hâlidir: sıra, zaman, konum, irtifa ve batarya gerilimi taşır. Alıcı, CRC uymazsa paketi reddeder.

```python
# -*- coding: utf-8 -*-
"""b31_udp.py: UDP uzerinde durdur-bekle guvenilir aktarim
ve CRC'li telemetri paketi. Gercek UDP soketleri, yalnizca loopback.

Kullanim:
  python b31_udp.py test                # telemetri + iz tablosu
  python b31_udp.py olc CSV_YOLU        # kayip oranina gore olcum
"""

import random
import socket
import struct
import sys
import threading
import time
import zlib

VERI, ONAY = 0, 1
BASLIK = struct.Struct("!BB")  # tur, sira biti (0/1)
ZAMAN_ASIMI = 0.05  # saniye
MAKS_YENIDEN = 200  # emniyet siniri

# ---- Telemetri paketi: 24 bayt govde + 4 bayt CRC-32 ------ #
TELE_GOVDE = struct.Struct("!BBIIiiiH")  # surum, tur, sira, zaman,
# enlem, boylam, irtifa, batarya
TELE = struct.Struct("!BBIIiiiHI")  # govde + crc (28 bayt)


def telemetri_paketi(
    sira, zaman_ms, enlem, boylam, irtifa_cm, batarya_mv
):
    govde = TELE_GOVDE.pack(
        1, 0x01, sira, zaman_ms, enlem, boylam, irtifa_cm, batarya_mv
    )
    return govde + struct.pack("!I", zlib.crc32(govde))
```

*Kodun devamı (b31_udp.py, satır 37–72):*

```python

def telemetri_coz(p):
    if len(p) != TELE.size:
        raise ValueError("uzunluk hatali: %d" % len(p))
    govde, (crc,) = p[: TELE_GOVDE.size], struct.unpack("!I", p[-4:])
    if zlib.crc32(govde) != crc:
        raise ValueError("CRC uyusmuyor")
    surum, tur, sira, zm, enl, boy, irt, bat = TELE_GOVDE.unpack(
        govde
    )
    if surum != 1 or tur != 0x01:
        raise ValueError("bilinmeyen surum/tur")
    return {
        "sira": sira,
        "zaman_ms": zm,
        "enlem": enl / 1e7,
        "boylam": boy / 1e7,
        "irtifa_m": irt / 100.0,
        "batarya_V": bat / 1000.0,
    }


# ---- Durdur-bekle: gonderici ve alici ---------------------- #


def gonderici(alici_port, mesajlar, kayip_p, tohum, iz):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    s.settimeout(ZAMAN_ASIMI)
    rnd = random.Random(tohum)
    sira = 0
    yeniden = gonderim = 0
    for i, m in enumerate(mesajlar):
        deneme = 0
        while True:
            deneme += 1
```

*Kodun devamı (b31_udp.py, satır 74–98):*

```python
            gonderim += 1
            if rnd.random() < kayip_p:
                iz.append(("kayip", i, sira, deneme))
            else:
                s.sendto(
                    BASLIK.pack(VERI, sira) + m,
                    ("127.0.0.1", alici_port),
                )
                iz.append(("gonder", i, sira, deneme))
            try:
                while True:  # yanlis siradaki onayi at
                    cevap, _ = s.recvfrom(64)
                    tur, osira = BASLIK.unpack(cevap[:2])
                    if tur == ONAY and osira == sira:
                        break
                iz.append(("onay", i, sira, deneme))
                break
            except socket.timeout:
                yeniden += 1
                iz.append(("zaman_asimi", i, sira, deneme))
                if deneme >= MAKS_YENIDEN:
                    raise RuntimeError("cok fazla yeniden iletim")
        sira ^= 1
    s.close()
    return gonderim, yeniden
```

*Kodun devamı (b31_udp.py, satır 100–135):*

```python

def alici(s, adet, kayip_p, tohum, sonuc):
    s.settimeout(0.3)  # sessizlik = gonderici bitti
    rnd = random.Random(tohum)
    beklenen = 0
    teslim, kopya = [], 0
    adres = None
    while True:
        try:
            paket, adres = s.recvfrom(2048)
        except socket.timeout:
            break
        tur, sira = BASLIK.unpack(paket[:2])
        if tur != VERI:
            continue
        if sira == beklenen:
            teslim.append(paket[2:])
            beklenen ^= 1
        else:
            kopya += 1  # yinelenen veri: teslim etme
        if rnd.random() >= kayip_p:  # onayin kaybi da simule edilir
            s.sendto(BASLIK.pack(ONAY, sira), adres)
    # Son onay kaybolursa gonderici yeniden ister; alici, 0.3 sn
    # sessizlige kadar dinler ve yinelenen veriyi yeniden onaylar.
    s.close()
    sonuc.extend([teslim, kopya])


def aktar(mesajlar, kayip_p, tohum=31, iz=None):
    iz = [] if iz is None else iz
    dinle = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dinle.bind(("127.0.0.1", 0))  # alici once baglanir
    port = dinle.getsockname()[1]
    sonuc = []
    t = threading.Thread(
        target=alici,
```

*Kodun devamı (b31_udp.py, satır 137–151):*

```python
        args=(dinle, len(mesajlar), kayip_p, tohum + 1, sonuc),
    )
    t.start()
    t0 = time.perf_counter()
    gonderim, yeniden = gonderici(port, mesajlar, kayip_p, tohum, iz)
    t.join()
    sure = time.perf_counter() - t0
    teslim, kopya = sonuc
    return {
        "teslim": teslim,
        "gonderim": gonderim,
        "yeniden": yeniden,
        "kopya": kopya,
        "sure": sure,
    }
```

*Kodun devamı (b31_udp.py, satır 153–191):*

```python

def test():
    # 1) Telemetri paketi: gidis-donus ve bit bozulmasi
    p = telemetri_paketi(
        7, 123456, int(40.9 * 1e7), int(29.0 * 1e7), 15230, 22300
    )
    print("telemetri boyutu: %d bayt" % len(p))
    for k, v in telemetri_coz(p).items():
        print("  %s = %s" % (k, v))
    bozuk = bytearray(p)
    bozuk[10] ^= 0x04  # tek bit
    try:
        telemetri_coz(bytes(bozuk))
        print("bozuk: kabul edildi (beklenmiyordu)")
    except ValueError as e:
        print("bozuk paket reddedildi:", e)

    # 2) Kucuk stop-and-wait ornegi, %30 kayip, iz tablosu
    mesajlar = [("veri-%02d" % i).encode() for i in range(8)]
    iz = []
    r = aktar(mesajlar, 0.30, tohum=31, iz=iz)
    assert r["teslim"] == mesajlar, "sira/icerik hatali"
    print("\nIz (ilk 12 olay):")
    print(
        "%-12s %-4s %-4s %-6s" % ("olay", "mesaj", "sira", "deneme")
    )
    for olay in iz[:12]:
        print("%-12s %-4d %-4d %-6d" % olay)
    print(
        "\nmesaj=%d gonderim=%d yeniden=%d kopya=%d sure=%.2f s"
        % (
            len(mesajlar),
            r["gonderim"],
            r["yeniden"],
            r["kopya"],
            r["sure"],
        )
    )
    print("TESLIM DOGRU: sira ve icerik birebir ayni")
```

*Kodun devamı (b31_udp.py, satır 193–219):*

```python

def olc(csv_yolu):
    satirlar = ["kayip_p,mesaj,gonderim,yeniden,kopya,sure_s"]
    mesajlar = [("%04d" % i).encode() * 4 for i in range(200)]
    for kayip in [0.0, 0.05, 0.10, 0.20, 0.30]:
        r = aktar(mesajlar, kayip, tohum=31)
        assert r["teslim"] == mesajlar
        satir = "%.2f,%d,%d,%d,%d,%.3f" % (
            kayip,
            len(mesajlar),
            r["gonderim"],
            r["yeniden"],
            r["kopya"],
            r["sure"],
        )
        print(satir, flush=True)
        satirlar.append(satir)
    with open(csv_yolu, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


if __name__ == "__main__":
    kip = sys.argv[1] if len(sys.argv) > 1 else "test"
    if kip == "test":
        test()
    elif kip == "olc":
        olc(sys.argv[2])
```

Testin çıktısı iki şeyi gösterir: telemetri paketinin gidiş-dönüş doğruluğunu ve bozulmuş bir bitin CRC tarafından yakalandığını. Sonra sekiz mesajlık bir aktarım, %30 kayıpla, iz tablosuyla çalışır.

```term
$ python3 b31_udp.py test
telemetri boyutu: 28 bayt
  sira = 7
  zaman_ms = 123456
  enlem = 40.9
  boylam = 29.0
  irtifa_m = 152.3
  batarya_V = 22.3
bozuk paket reddedildi: CRC uyusmuyor

Iz (ilk 12 olay):
olay         mesaj sira deneme
kayip        0    0    1
zaman_asimi  0    0    1
kayip        0    0    2
zaman_asimi  0    0    2
gonder       0    0    3
zaman_asimi  0    0    3
gonder       0    0    4
zaman_asimi  0    0    4
kayip        0    0    5
zaman_asimi  0    0    5
kayip        0    0    6
zaman_asimi  0    0    6

mesaj=8 gonderim=20 yeniden=12 kopya=3 sure=0.91 s
TESLIM DOGRU: sira ve icerik birebir ayni
```

İz tablosunda her satır bir olaydır. `kayip` satırı, gönderenin paketi yollamadığı anlamına gelir (simülasyon). `zaman_asimi` satırı, gönderenin 50 ms bekleyip onay alamadığını gösterir ve yeniden iletim izler. Bu ilk on iki olayda, sıra 0 için altı deneme yapılıyor: beş kayıp ve bir başarılı gönderim. Son satır, sekiz mesajın sırası ve içeriğiyle birebir teslim edildiğini doğrular; bu, durdur-bekle protokolünün asıl garantisidir.

Kayıp oranının maliyetini ölçelim. Aynı protokolü 200 mesajla, kayıp oranlarını değiştirerek çalıştırdık. Tablodaki `kopya` sütunu, alıcının yinelenmiş olarak yok saydığı veri paketlerinin sayısıdır.

| kayip_p | mesaj | gonderim | yeniden | kopya | sure_s |
|---|---|---|---|---|---|
| 0.00 | 200 | 200 | 0 | 0 | 0.314 |
| 0.05 | 200 | 232 | 32 | 16 | 1.930 |
| 0.10 | 200 | 259 | 59 | 33 | 3.288 |
| 0.20 | 200 | 335 | 135 | 65 | 7.099 |
| 0.30 | 200 | 427 | 227 | 99 | 11.721 |

Tablo, kaybın maliyetini net gösterir. %0 kayıpta 200 mesaj 200 gönderimle ve hiç yeniden iletim olmadan biter. %30'da ise 427 gönderim gerekir ve süre 11,7 saniyeye çıkar. Süre ile yeniden iletim sayısı arasında neredeyse doğrusal bir ilişki vardır: toplam süre yaklaşık 0,31 saniye artı yeniden iletim sayısı çarpı 0,05 saniyedir (zaman aşımı). Bunu tablodan kendin doğrula: %20 satırında 0,31 + 135 × 0,05 = 7,06 saniye, ölçülen 7,10 saniyeye çok yakın. Yani gecikme, protokolün kendisinden çok zaman aşımı değerinden gelir; zaman aşımını çok büyük seçersen kayıp başına bedel artar, çok küçük seçersen gereksiz yeniden iletim yapılır.

Şekil 31.9 aynı ölçümün grafiğini verir: solda gönderim ve yeniden iletim sayıları, sağda toplam süre.

![Şekil 31.9: UDP durdur-bekle ölçümü. Kayıp oranı arttıkça gönderim ve yeniden iletim sayıları artar; süre, zaman aşımı sayısıyla doğru orantılı büyür.](gorseller/b31_udp_olcum.png)

Son olarak telemetri paketinin düzenine bakalım. Şekil 31.10, 28 baytlık paketin alanlarını ofsetleriyle gösterir.

![Şekil 31.10: Telemetri paketinin düzeni. Tüm çok baytlı alanlar ağ sırasındadır; CRC-32 son dört bayttır ve gövdenin üzerinden hesaplanır.](gorseller/b31_telemetri.png)

Bu paket, UDP üzerinde güvenilir bir telemetri akışının temel parçasıdır, ama yeterli değildir: durdur-bekle, her paket için bir onay bekler ve yüksek hacimli telemetride verimi düşürür. Gerçek sistemlerde pencereli protokoller (birden çok onaylanmamış paketi aynı anda uçuşta tutan) kullanılır; bu, TCP'nin pencere mekanizmasının sadeleştirilmiş bir hâlidir ve Bölüm 29'da ayrıntılı işlenir. Bu bölümün amacı, güvenilirliğin ne olduğunu ve bedelini kendi kodunla görmendir.

## 31.11 Windows farkı ve güvenlik notu

Windows'ta soket programlamanın üç farkı vardır (genel bilgi). Birincisi, Winsock kütüphanesi (`ws2_32`) kullanılmadan önce `WSAStartup` ile başlatılmalı ve iş bitince `WSACleanup` ile kapatılmalıdır. İkincisi, soket tanıtıcısı bir tamsayı değil `SOCKET` tipindedir ve kapatmak için `close` değil `closesocket` kullanılır; hata kodları `errno` yerine `WSAGetLastError()` ile okunur. Üçüncüsü, `fork` yoktur (Bölüm 26.6); eşzamanlılık için iş parçacıkları, `select`, `WSAPoll` ya da I/O tamamlama portları (IOCP) kullanılır. Bu bölümdeki Linux'a özgü kodları Windows'a taşımak, bu farkların her birini ayrıca ele almayı gerektirir.

Güvenlik açısından bu bölümün en önemli dersi, **ağdan gelen her baytın düşman olabileceğidir**. Uzunluk önekli bir çerçevede uzunluk, bellek ayırmadan önce sınırlanmalıdır (Bölüm 31.4). Ayraçlı akışta satır uzunluğu sınırlanmalıdır, yoksa satır sonu hiç gelmeyen bir saldırgan bellek tüketebilir. Ayrıştırma sırasında her alanın aralığı ve her CRC doğrulanmalıdır; bir bitin bozulması ile bilerek değiştirilmiş bir paket arasında CRC bir ayrım yapamaz. Bu yüzden CRC bir **bütünlük** denetimidir, **kimlik doğrulama** değildir. Gerçek bir saldırganın paket değiştirmesini engellemek için şifreleme ve kimlik doğrulama gerekir. TLS'in bu işi nasıl yaptığını Bölüm 32'de ayrıntılı göreceğiz; burada yalnızca fikir için tek satırlık bir sarmalama vardır: Python'da bir TCP soketi `ssl.wrap_socket` benzeri bir sarmalayıcı ile şifrelenir ve geri kalan kod çoğunlukla değişmez. Bu bölümdeki çerçeveleme ve durum makineleri, şifrelemenin altındaki taşıma katmanının mantığını anlamanı sağlar.

::: dikkat
Bu bölümdeki kodları kendi makinende çalıştırırken yalnızca `127.0.0.1` kullan. Sunucu kodlarını bir güvenlik duvarının dışına açık bir port üzerinde çalıştırmak, kimlik doğrulama olmadan bir hizmet sunmak demektir. Bölüm 31'deki sunucular bilerek hiçbir kimlik doğrulama içermez.
:::

## Çözümlü Örnekler

Bu bölümdeki dört örnek, altı adımlı çalışma yöntemiyle çözülür: Anla, Örnekle, Kaba çöz, Örüntü, İyileştir, Doğrula. Doğrulama adımında her örnek için bir elle iz tablosu vardır. Örnekler ★'ten ★★★'e doğru zorlaşır.

### Örnek 1 (★): Parça parça gelen baytlarla cerceve okuma

**Adım 1 — Anla.** Bir alıcı, uzunluk önekli çerçevelerden oluşan bir akışı okuyor. Akış iki çerçeve içerir: önce `hello` (5 bayt), sonra `wo` (2 bayt). Ama bu akış altı parçada gelir ve parçaların sınırları çerçeve sınırlarıyla uyuşmaz. Soru: alıcı, hangi `recv` çağrısını hangi bayt aralığıyla yapar ve her çerçevenin doğru yükünü nasıl alır?

**Adım 2 — Örnekle.** Akış, bayt bayt, `00 00 00 05 68 65 6C 6C 6F 00 00 00 02 77 6F` olarak yazılır. Parçalar: `00 00`, `00 05 68 65`, `6C`, `6C 6F 00 00 00`, `02 77`, `6F`. İlk çerçevenin uzunluğu 5'tir, yani beş yük baytı okunmalıdır. Hangi parçanın hangi çağrıda döndüğünü izlemek gerekir.

**Adım 3 — Kaba çöz.** En basit yöntem, her çerçeve için önce 4 bayt, sonra yük uzunluğu kadar bayt istemektir. Ama `recv` her zaman istenen kadar bayt döndürmez: ilk çağrıda yalnızca 2 bayt gelebilir, ikinci çağrıda kalan 2 bayt. Kaba çözüm, `tam_oku` içindeki döngüyle kısa okumaları birleştirir.

**Adım 4 — Örüntü.** Örüntü şudur: her okuma, *kalan* bayt sayısını ister ve dönen kadarını biriktirir. Bu, bir çerçevenin başlık ve yük okumasını bayt sınırlarından bağımsız yapar. Çerçeveler arasında hiçbir artık bayt kaybolmaz, çünkü her `recv` yalnızca istenen kadar okur; fazlası sonraki çağrıda gelir.

**Adım 5 — İyileştir.** Bu programda `ParcaliSoket.recv` her zaman en fazla bir parça döndürür; gerçek bir soket bundan da az verebilir. Gerçek ağda da `recv` daha az döndürebilir. Yani kod, sahte soketle olduğu kadar gerçek soketle de doğru çalışmalıdır. Bu yüzden iyileştirme yok, sadece kodun her `recv` çağrısını izlemesi için bir sarmalayıcı yazıyoruz. Sarmalayıcı, ikinci çerçeveyi okurken bile aynı kuralın geçerli olduğunu gösterir.

**Adım 6 — Doğrula.** Aşağıdaki çıktı, yukarıda elle çıkardığımız izin gerçek programla aynı olduğunu gösterir.

```python
# -*- coding: utf-8 -*-
"""Ornek 1: parcali akis icinde cerceve okuma izi."""
from b31_cerceve import ParcaliSoket, cerceve_al


class IzliSoket(ParcaliSoket):
    def recv(self, n):
        b = super().recv(n)
        print("  recv(%d) -> %r" % (n, b))
        return b


parcalar = [b"\x00\x00", b"\x00\x05he", b"l", b"lo\x00\x00\x00",
            b"\x02w", b"o"]
s = IzliSoket(parcalar)
for no in (1, 2):
    print("cerceve %d:" % no)
    print("  yuk = %r" % cerceve_al(s))
```

```term
$ python3 ornek1_iz.py
cerceve 1:
  recv(4) -> b'\x00\x00'
  recv(2) -> b'\x00\x05'
  recv(5) -> b'he'
  recv(3) -> b'l'
  recv(2) -> b'lo'
  yuk = b'hello'
cerceve 2:
  recv(4) -> b'\x00\x00\x00'
  recv(1) -> b'\x02'
  recv(2) -> b'w'
  recv(1) -> b'o'
  yuk = b'wo'
```

Elle izlediğimiz tablo:

| Çağrı | İstenen | Dönen | Biriken yük | Durum |
|---|---|---|---|---|
| 1 | 4 | `00 00` | — | başlığın 2 baytı var |
| 2 | 2 | `00 05` | — | başlık tamam: n = 5 |
| 3 | 5 | `he` | `he` | 3 bayt eksik |
| 4 | 3 | `l` | `hel` | 2 bayt eksik |
| 5 | 2 | `lo` | `hello` | ilk çerçeve tamam |
| 6 | 4 | `00 00 00` | — | sonraki başlık, 1 bayt eksik |
| 7 | 1 | `02` | — | başlık tamam: n = 2 |
| 8 | 2 | `w` | `w` | 1 bayt eksik |
| 9 | 1 | `o` | `wo` | ikinci çerçeve tamam |

Dikkat et: çağrı 6'da istenen 4 bayt, yalnızca 3 bayt döndürdü. Naif bir okuyucu bu üç baytı başlık sanıp `struct.unpack` ile açmaya kalksaydı hata verirdi. Doğru okuyucu eksik kalan bir baytı beklemeye devam eder.

**Bunu AI'sız yazabilir misin?** Boş bir dosyada, yalnızca `recv` fonksiyonunu taklit eden bir sahte soket yaz ve `[b"\x00", b"\x00\x03ab", b"c"]` parçalarından `abc` yükünü okuyan bir fonksiyon yaz. İz tablosunu kâğıtta çıkarmadan önce kodu çalıştırma. Sonucu tabloyla karşılaştır.

### Örnek 2 (★★): Sohbet sunucusunda yayın ve kopan istemci

**Adım 1 — Anla.** Bir sohbet sunucusu, bir kullanıcının mesajını diğer tüm bağlı kullanıcılara iletmelidir. Gönderen kendi mesajını geri almamalıdır. Bir kullanıcının bağlantısı kopmuşsa, sunucu onu listeden çıkarmalı ve diğerlerine hizmet etmeye devam etmelidir. Kopan bir istemciye yazmanın `BrokenPipeError` ile sonuçlandığını (Bölüm 31.6) hatırla.

**Adım 2 — Örnekle.** Üç kullanıcı var: `ali`, `ayse`, `mert`. `ayse` bağlantısını kesmiş. `ali` "merhaba" yazıyor. Beklenen: `mert` mesajı alır, `ayse` listeden çıkarılır, `ali` kendi mesajını almaz.

**Adım 3 — Kaba çöz.** Her kullanıcı için döngü ve gönderim. Kopan istemciyi bulmak için her gönderimi `try` içine koy. Sorun: döngü sırasında sözlükten silmek, döngüyü bozar. Kaba çözümde kopanları önce bir listede topla, sonra sil.

**Adım 4 — Örüntü.** Örüntü, *gözlem sırasında değiştirme* kuralıdır: iterasyon sırasında yalnızca not al, değişikliği döngü bittikten sonra yap. Bu, Python'da sözlük değiştirme hatasını önler ve kopan kullanıcıların güvenli biçimde ayıklanmasını sağlar.

**Adım 5 — İyileştir.** `list(kullanicilar.items())` ile döngünün kendi kopyasını alırız; böylece döngü içinde sözlük değişse bile güvenlidir. Gönderenin atlanması da açıkça yazılır.

**Adım 6 — Doğrula.** Programı çalıştırıp beklenen çıktıyla karşılaştırıyoruz. Elle iz tablosu:

| Adım | Olay | Sözlük (sonra) | Kopan |
|---|---|---|---|
| 1 | ali → ayse: BrokenPipe | ali, ayse, mert | ayse |
| 2 | ayse listeden silindi | ali, mert | ayse |
| 3 | ali → mert: "merhaba" | ali, mert | — |
| 4 | mert → ali: "nasilsin" (ayse yok) | ali, mert | — |

```python
# -*- coding: utf-8 -*-
"""Ornek 2: yayin ve istemci ayrilmasi (soket yerine sahte nesne)."""


class Sahte:
    def __init__(self, ad):
        self.ad = ad
        self.kutu = []
        self.acik = True

    def gonder(self, metin):
        if not self.acik:
            raise BrokenPipeError(self.ad)
        self.kutu.append(metin)


def yayinla(kullanicilar, gonderen, metin):
    kopuk = []
    for ad, soket in list(kullanicilar.items()):
        if ad == gonderen:
            continue                      # gonderene geri yollama yok
        try:
            soket.gonder("%s: %s" % (gonderen, metin))
        except BrokenPipeError:
            kopuk.append(ad)
    for ad in kopuk:                      # kopani listeden cikar
        del kullanicilar[ad]
    return kopuk


kullanicilar = {"ali": Sahte("ali"), "ayse": Sahte("ayse"),
                "mert": Sahte("mert")}
kullanicilar["ayse"].acik = False         # ayse baglantiyi kesti
print("kopan:", yayinla(kullanicilar, "ali", "merhaba"))
print("kullanicilar:", sorted(kullanicilar))
print("mert kutusu:", kullanicilar["mert"].kutu)
print("ali kutusu:", kullanicilar["ali"].kutu)
print("kopan:", yayinla(kullanicilar, "mert", "nasilsin"))
```

```term
$ python3 ornek2_sohbet.py
kopan: ['ayse']
kullanicilar: ['ali', 'mert']
mert kutusu: ['ali: merhaba']
ali kutusu: []
kopan: []
```

Çıktı, tabloyla birebir eşleşir: `ayse` kopan olarak bulundu ve silindi; `mert` yalnızca `ali`'nin mesajını aldı; `ali` kendi mesajını almadı. Son satırda kopan kimse yoktur, çünkü `ayse` zaten listede değildir.

**Bunu AI'sız yazabilir misin?** Bu fonksiyonu gerçek soketlerle yeniden yaz: her istemci için bir iş parçacığı ve bir kilit kullan. Kilitsiz çalıştırırsan ne olur? Bölüm 27'deki yarış koşulu kavramıyla açıkla.

### Örnek 3 (★★): Durdur-bekle protokolünde onay kaybı

**Adım 1 — Anla.** Durdur-bekle protokolünde sıra biti 0 ve 1 ile sınırlıdır. Bu sınırın neden yeterli olduğunu göstermek istiyoruz. Özel bir senaryo: ilk veri (sıra 0) alıcıya ulaşır, ama alıcının onayı kaybolur. Gönderici zaman aşımına uğrar ve veriyi yeniden yollar.

**Adım 2 — Örnekle.** Mesajlar A ve B. Sıra A için 0, B için 1. Alıcı başlangıçta beklenen sıra 0'dır.

**Adım 3 — Kaba çöz.** Naif bir yaklaşım, alıcının her gelen veriyi teslim etmesidir. Bu durumda A iki kez teslim edilir: onayın kaybolması yinelenmeye yol açar. Doğru çözüm, alıcıda bir "beklenen sıra" tutmaktır.

**Adım 4 — Örüntü.** Örüntü, *yinelenen veriyi teslim etme, ama onayla*: alıcı beklenen sıradaki veriyi teslim eder ve beklenenin tersini çevirir; beklenmeyen sıradaki veriyi yok sayar ama her zaman onaylar. Bu sayede gönderici, onayı kaybetse bile sonunda bir onay alır.

**Adım 5 — İyileştir.** Bir sorular: bir eski onay (örneğin gecikmeli gelen `onay(0)`), gönderici sıra 1'e geçtikten sonra gelirse ne olur? Gönderici sıra 1 bekliyor, eski onay sıra 0 taşıyor, eşleşmiyor ve yok sayılır. Bu, sıra bitinin neden yeterli olduğunu gösterir: gönderici yalnızca *o anki* sırayı bekler ve eski onaylar ayırt edilir.

**Adım 6 — Doğrula.** İz tablosu:

| Adım | Gönderici | Ağ | Alıcı (beklenen) | Teslim edilen |
|---|---|---|---|---|
| 1 | veri(0, A) gönder | ulaşır | 0: teslim, beklenen=1 | A |
| 2 | — | onay(0) KAYIP | — | A |
| 3 | 50 ms zaman aşımı, veri(0, A) yeniden | ulaşır | 1: yinelenen, onay(0) gönder | A |
| 4 | onay(0) alır, sıra=1 | ulaşır | — | A |
| 5 | veri(1, B) gönder | ulaşır | 1: teslim, beklenen=0 | A, B |
| 6 | onay(1) alır | ulaşır | — | A, B |

Tablo, A'nın bir kez teslim edildiğini doğrular: adım 3'teki yinelenen veri teslim edilmedi. Bu tabloyu, Bölüm 31.10'daki `kopya` sütunuyla karşılaştır: bu senaryoda bir kopya oluştu (adım 3).

**Bunu AI'sız yazabilir misin?** Bu tabloyu, onayın yerine veri paketinin kaybolduğu bir senaryo için yeniden çiz. Hangi adımda yinelenen veri oluşur? Oluşmazsa neden?

### Örnek 4 (★★★): epoll ile kısmi yazma ve EPOLLOUT

**Adım 1 — Anla.** Bir epoll sunucusu, bir istemciye 12 bayt yanıt göndermek istiyor. Alıcı tamponu yalnızca 6 bayt alabilir; sonra dolar. Sunucu ne yapmalı? Kaç kere `send` çağırmalı? Hangi epoll maskesini kullanmalı?

**Adım 2 — Örnekle.** Üç tur: ilk yazmada 6 bayt yer var, ikincisinde yer yok, üçüncüsünde alıcı boşalmış ve 6 bayt daha yer var.

**Adım 3 — Kaba çöz.** Döngüde `send` çağırıp hepsini zorla göndermek, bloklayan soketle çalışır ama epoll sunucusunda sunucuyu kilitler; diğer bağlantılara hizmet edilmez. Kaba çözüm, `send` dönünce kalanı bir tampona koymaktır.

**Adım 4 — Örüntü.** Örüntü: *yaz, kalanı tut, yalnızca yer açılınca tekrar dene.* Tamponda bekleyen baytlar varken maske `EPOLLIN|EPOLLOUT` olur; tampon boşalınca yalnızca `EPOLLIN`'e dönülür.

**Adım 5 — İyileştir.** Gerçek soketten `EAGAIN` hatası alındığında `_yaz` sessizce geri döner; böylece olay döngüsü bloklanmaz. Maske kararı, tamponun boş olup olmadığına göre verilir. Bu yöntemin tek kusuru, tampon büyüdüğünde bellek kullanımının artmasıdır; gerçek sunucularda üst sınır konur.

**Adım 6 — Doğrula.** Sahte bir soket, alıcının yer kapasitesini simüle eder. `_yaz` ve `maske` fonksiyonları gerçek modülden alınmıştır.

```python
# -*- coding: utf-8 -*-
"""Ornek 4: kismi yazma ve EPOLLOUT maskesi (sahte soket)."""
from b31_modeller import Baglanti, _yaz


class YavasSoket:
    def __init__(self):
        self.kapasite = 0                 # alicinin bos yeri (bayt)
        self.alinan = bytearray()

    def send(self, veri):
        if self.kapasite == 0:
            raise BlockingIOError()       # EAGAIN karsiligi
        k = min(self.kapasite, len(veri))
        self.alinan += veri[:k]
        self.kapasite -= k
        return k


def maske(b):
    return "EPOLLIN|EPOLLOUT" if b.giden else "EPOLLIN"


s = YavasSoket()
b = Baglanti(s)
b.giden += b"0123456789AB"
for ad, kap in [("1. yazma, 6 bayt yer", 6),
                ("2. yazma, yer yok", 0),
                ("3. alici bosaldi, 6 bayt", 6)]:
    s.kapasite = kap
    _yaz(b)
    print("%s: giden=%d maske=%s alinan=%r"
          % (ad, len(b.giden), maske(b), bytes(s.alinan)))
```

```term
$ python3 ornek4_yazma.py
1. yazma, 6 bayt yer: giden=6 maske=EPOLLIN|EPOLLOUT alinan=b'012345'
2. yazma, yer yok: giden=6 maske=EPOLLIN|EPOLLOUT alinan=b'012345'
3. alici bosaldi, 6 bayt: giden=0 maske=EPOLLIN alinan=b'0123456789AB'
```

Elle iz tablosu:

| Tur | Alıcı yeri | Yazılan | Kalan (giden) | Maske |
|---|---|---|---|---|
| 1 | 6 bayt | 6 bayt | 6 | EPOLLIN\|EPOLLOUT |
| 2 | 0 bayt | 0 bayt (EAGAIN) | 6 | EPOLLIN\|EPOLLOUT |
| 3 | 6 bayt | 6 bayt | 0 | EPOLLIN |

Dikkat et: tur 2'de `_yaz` bir hata fırlatmaz, sessizce geri döner. Tur 3'te kalan baytlar gönderilince maske `EPOLLIN`'e döner ve `EPOLLOUT` kapanır. Eğer maske açık kalsaydı, döngü her turda boş bir `EPOLLOUT` olayıyla uyanırdı.

**Bunu AI'sız yazabilir misin?** Bu kodu, bağlantı başına bir giden tampon tutacak şekilde gerçek bir epoll sunucusuna dönüştür. İki istemciden biri yanıtı okumazsa, diğer istemcinin hizmetini nasıl etkilemediğini göster.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan bir sistem üretmekten çok, paketin nasıl kaybolduğunu, bağlantının nasıl kapandığını ve bir sunucunun yük altında nasıl davrandığını kendi gözlemlerinle anlamak. Takıl, kâğıda çiz, küçük testler yaz; çözümü dışarıdan alma.
:::

### Proje 1 (★★): İHA telemetri yer istasyonu

**Amaç:** Sanal bir İHA'dan UDP üzerinden gelen telemetriyi alan, doğrulayan ve ağ kalitesini raporlayan bir yer istasyonu yaz. Ayrıca, komut göndermek için ayrı bir TCP kanalı ekle. Telemetri akışı kayıplıdır, komut kanalı güvenilirdir: bu iki taşıma katmanının neden birlikte kullanıldığını projede göreceksin.

**Beklenen davranış:** Simülatör saniyede 10 telemetri paketi üretir (Bölüm 31.10'daki 28 baytlık düzen). Simülatör paketleri rastgele olarak düşürür, sırasını değiştirir, bazılarını çoğaltır ve bazılarında bir bit bozar. Yer istasyonu her paketi CRC ile doğrular; geçerli paketlerden sıra numarası boşluklarını, yinelenenleri ve sıra dışı gelenleri sayar. Saniyede bir kez özet yazdırır: alınan, geçersiz, kayıp (tahmini), yinelenen ve ortalama alım aralığı. Ayrı bir TCP portunda yer istasyonu "hedef değiştir" gibi komutları gönderebilir; sunucu her komutu onaylar ve onay gelmezse komutu yeniden yollar.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Önce paketin düzenini kâğıda çiz ve `struct` biçimini `!` ile yaz. Sıra numarası boşluklarını bulmak için "beklenen sıra" değişkeni tut; sıra dışı bir paket geldiğinde onun kayıp mı, yoksa gecikmiş bir paket mi olduğuna nasıl karar vereceğini düşün. Simülatörde kayıp ve bozulmayı ayrı tohumlu rastgele sayı üreteçleriyle yap ki her deneyi tekrarlayabilesin. Komut kanalı için Bölüm 31.4'teki uzunluk önekli çerçeveyi kullan.

**Başarı kriterleri:**
- Simülatör %10 kayıp ve %5 bit bozulmasıyla 600 paket gönderdiğinde, yer istasyonunun raporladığı kayıp sayısı gerçek kayıpla %5'in içinde eşleşiyor.
- Hiçbir bozulmuş paket "geçerli" olarak sayılmıyor (CRC sınamasının başarısı, bozulan paketlerin tamamının yakalanmasıyla ölçülüyor).
- Komut kanalında kapatılan bağlantı ve yeniden iletim senaryosu, komutun en fazla bir kez uygulanmasıyla sonuçlanıyor (yinelenen komut yok).

### Proje 2 (★★★): Çok kullanıcılı sohbet sunucusu ve yük testi

**Amaç:** `asyncio` ile çalışan bir sohbet sunucusu yaz. Kullanıcılar bir rumuz ile bağlanır, herkese ya da tek bir kullanıcıya (özel mesaj) yazabilir, odalara katılabilir. Sunucu, kopan bağlantıları temizler ve yük altında ölçülebilir olmalıdır.

**Beklenen davranış:** Protokol satır tabanlı değildir; uzunluk önekli çerçeveler kullanır (Bölüm 31.4) ve her çerçeve bir tür alanı taşır: `giris`, `mesaj`, `pm`, `oda`, `cik`. Sunucu rumuz çakışmasını reddeder, bir odadaki mesajları yalnızca o odanın üyelerine iletir ve bir kullanıcının bağlantısı koptuğunda onu bütün odalardan çıkarır. Sunucu yavaş bir istemciyi (okumayan) diğerlerinden ayırmalıdır: bu istemcinin giden tamponu büyüdüğünde bağlantı kesilir, ama diğer istemciler etkilenmez.

**Önerilen yaklaşım (ipucu):** Her bağlantı için bir `asyncio` görevi ve bir giden kuyruk (`asyncio.Queue`) tut. Gönderici görev kuyruğu boşaltır; yazıcı tarafı `writer.drain()` ile geri basıncı (backpressure) uygular. Yükü ölçmek için ayrı bir istemci betiği yaz: 200 istemci, her biri 100 mesaj, her mesajın gecikmesini kaydet ve p50/p99 değerlerini yaz. Bölüm 31.9'daki ölçüm yaklaşımını kullan: aynı makinede çalışan istemcilerin sınırını unutma ve sonuçları raporlarken bunu belirt.

**Başarı kriterleri:**
- 200 eşzamanlı istemci ile 20 000 mesajlık yükte hiçbir mesaj kaybolmuyor ve her oda üyesi yalnızca kendi odasının mesajlarını alıyor.
- Yavaş bir istemci (okumayan) bağlıyken diğer istemcilerin p99 gecikmesi, yavaş istemci yokken ölçülene göre en fazla iki kat artıyor.
- Kopan bir istemci 5 saniye içinde tüm oda listelerinden çıkarılıyor; bu, sunucu günlüğünde ölçülebiliyor.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala.

1. **★ — Kısa okuma sayımı.** `send` 10 000 baytlık bir arabelleği yazarken 1460 baytlık parçalar halinde dönüyor. Kaç `send` çağrısı gerekir? `sendall` bunu nasıl yapar, sen yazsaydın hangi döngü gerekirdi?
2. **★ — Bayt sırası.** Ağ üzerinden 0x00000102 değeri `02 01 00 00` olarak gelirse, doğru ağ sırası hangisidir ve bu değer ana makinede hangi sayıya dönüşür? Bunu `htonl` olmadan ve `htonl` ile açıklayın.
3. **★ — Port ve bağlantı.** Bir sunucu 8080 portunda dinliyor. Aynı makinede ikinci bir sunucu aynı porta bağlanmaya çalışırsa ne olur? Dinleyen soket `SO_REUSEPORT` kullansaydı ne değişirdi?
4. **★★ — Mülakat: iki `recv`.** Bir istemci, `"abc\n"` ve `"def\n"` mesajlarını iki ayrı `send` ile gönderiyor. Alıcı `recv(2)` kullanıyor. Alıcının gördüğü ilk üç `recv` sonucunu sırasıyla yaz; bu sonuçların hangi koşullara bağlı olduğunu açıkla.
5. **★★ — Mülakat: yarım kapanış.** `shutdown(SHUT_WR)` çağıran bir istemci, sunucunun yanıtını almaya devam edebilir mi? Sunucu `recv` ile 0 gördüğünde ne yapmalı ve neden hemen `close` çağırmamalı?
6. **★★ — TIME_WAIT.** Yüksek trafikli bir istemci her istekte yeni bir TCP bağlantısı açıp kapatıyor ve kısa sürede port tükeniyor. Bu sorunun nedeni nedir ve istemci tarafında hangi yöntemlerle azaltılır? (Bölüm 29'daki kapanış dizisini hatırla.)
7. **★★ — Mülakat: ayraç içinde ayraç.** Bir satır tabanlı protokolde mesajlar `\n` ile ayrılıyor, ama yük içinde de `\n` olabilir. Bunu çözmek için iki yöntem öner ve her birinin bedelini yaz.
8. **★★ — Mülakat: blok mu, engelleme mi?** `accept` çağrısı blokluyken aynı anda bir sinyal gelirse ne olur? `EINTR` döndürmesi gerekir mi, yoksa kendiliğinden yeniden mi başlatılır? Kodunda bunu nasıl karşılarsın?
9. **★★ — `select` ve sınır.** `select` fonksiyonu fd_set boyutu nedeniyle yüksek tanımlayıcı numaralarında başarısız olabilir. Bu sınır, Bölüm 28'deki `poll` ve `epoll` karşılaştırmasıyla nasıl ilişkilidir?
10. **★★★ — Mülakat: asenkron bekleme.** Bir `asyncio` sunucusunda bir görev `time.sleep(5)` çağırıyor. Diğer 499 istemcinin gecikmesi ne olur? Bunu düzeltmek için iki yol öner ve birini uygula; sonucu ölçerek yaz.
11. **★★★ — Mülakat: CRC'nin sınırı.** CRC-32 bir paketteki tek bitlik bozulmayı yakalar. Bir saldırgan paketi değiştirip CRC'yi yeniden hesaplarsa ne olur? Bütünlük ile kimlik doğrulama arasındaki farkı bir cümleyle açıkla.
12. **★★★ — Mülakat: TCP mi UDP mi?** Bir İHA'dan gelen konum verisi her 100 ms'de bir gönderiliyor. Kayıp bir paketin yerine, gecikmiş ama doğru bir paket yeni olanı geçersiz kılıyorsa, hangi taşıma katmanı daha uygundur? Gerekçeni yaz ve bu kararın hangi varsayıma dayandığını belirt.

## Kod Okuma Egzersizi

Bugünkü kesit, Python'un `socketserver` modülünden alındı: iş parçacığı başına bağlantı modelinin kütüphane hâli. Kaynak, **CPython 3.12.10**'un `Lib/socketserver.py` dosyası. Dosya, makinedeki yerel 3.12.10 kurulumunun `Lib` dizininden alındı (`C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\socketserver.py`); internetten indirme yapılmadı. Kesit 690–715. satırlardan alındı: `ThreadingMixIn` sınıfının `process_request_thread`, `process_request` ve `server_close` metotları. Sınıf başındaki öznitelik tanımları (`daemon_threads`, `block_on_close`, `_threads`) kesitte yoktur; bunlara ilk soruda gerek var. Hiçbir satır değiştirilmedi.

```python
    def process_request_thread(self, request, client_address):
        """Same as in BaseServer but as a thread.

        In addition, exception handling is done here.

        """
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        """Start a new thread to process the request."""
        if self.block_on_close:
            vars(self).setdefault('_threads', _Threads())
        t = threading.Thread(target = self.process_request_thread,
                             args = (request, client_address))
        t.daemon = self.daemon_threads
        self._threads.append(t)
        t.start()

    def server_close(self):
        super().server_close()
        self._threads.join()
```

**Sorular — cevaplamadan geçme:**

1. `process_request` her bağlantı için yeni bir `threading.Thread` oluşturur. Bir istemci bağlandığında kaç iş parçacığı yaratılır ve bu, Bölüm 31.7'deki `thread` modeliyle aynı mı? Farkları yaz.
2. `t.daemon = self.daemon_threads` satırı, sunucu kapanırken iş parçacıklarına ne yapar? `daemon_threads = False` varsayılanıyla `server_close` içindeki `join` ne anlama gelir?
3. `process_request_thread` içindeki `finally` bloğu `shutdown_request` çağırır. Bu fonksiyon olmadan bağlantı hangi durumda kalırdı ve hangi kaynak sızardı? (Bölüm 31.2'deki `close` sözleşmesiyle karşılaştır.)
4. `vars(self).setdefault('_threads', _Threads())` satırı neden her örnek için ayrı bir liste oluşturuyor? `_threads` sınıf düzeyinde tek bir liste olsaydı hangi yarış koşulu ortaya çıkardı? (Bölüm 27'deki paylaşılan durum kavramına bağla.)
5. `handle_error` çağrısı yalnızca `Exception` yakalar. `BaseException` alt sınıfları (örneğin `SystemExit`) burada neden yakalanmaz ve bu tasarımın sonucu nedir?
6. Bu modelin `fork` modeline (`ForkingMixIn`) göre bellek ve güvenlik açısından farkı nedir? Bölüm 26.3'teki COW (kopyala-yaz) bilgisini kullanarak tahmin et, sonra kaynağın `ForkingMixIn` bölümünü açıp doğrula.

## Bölüm Özeti

- Soket, bir ağ uç noktasının çekirdekteki temsilidir ve bir dosya tanımlayıcısı olarak `read`, `write` ve `close` ile kullanılır (Bölüm 28). Port ve adres ağ bayt sırasında yazılır; `htons` ve `htonl` bu çeviriyi yapar.
- TCP sunucusu `socket`, `bind`, `listen`, `accept`, `recv`/`send` ve `close` sırasını izler; `accept` her bağlantı için yeni bir soket döndürür. `getaddrinfo` IPv4 ve IPv6'yı tek kodla kapsar.
- TCP bir bayt akışıdır: mesaj sınırı yoktur. `recv`'in bir çağrısı birden çok mesajı birleştirebilir ya da bir mesajı parçalara bölebilir. Mesaj sınırlarını uzunluk önekiyle ya da ayraçla protokolün kendisi taşır.
- Çerçeveleme için `tam_oku` gibi bir döngü şarttır; uzunluk alanı ağ sırasında yazılmalı ve bellek ayırmadan önce bir üst sınırla denetlenmelidir. Struct'ı ham olarak göndermek dolgu ve bayt sırası nedeniyle yanlıştır.
- `TIME_WAIT`, `EADDRINUSE`, `EPIPE`, `SIGPIPE` ve zaman aşımları ağ programının olağan hata kipleridir. `SO_REUSEADDR`, `MSG_NOSIGNAL` ve `SO_RCVTIMEO` bunları yönetmenin araçlarıdır.
- Eşzamanlılık modelleri (iteratif, fork, thread, havuz, epoll, asyncio) aynı protokolü farklı kaynak maliyetleriyle sunar. Ölçümde Python'da thread modeli GIL nedeniyle sınırlanırken, fork ve epoll daha yüksek verim verdi; maksimum gecikme, yüzdeliklerin gizlediği kuyruk etkisini gösterdi.
- UDP mesaj sınırlarını korur ama kayıp, sıra değişimi ve çoğaltmaya açıktır. Durdur-bekle protokolü, sıra biti ve zaman aşımıyla güvenilirliği tek başına kurar; kaybın maliyeti zaman aşımı sayısıyla doğru orantılı büyür.
- Kod, paket ve ölçümlerde her zaman bir CRC ya da başka bir denetim koy; ama CRC kimlik doğrulama değildir. Ağdan gelen her bayt düşman olabileceği için sınırlar, doğrulamalar ve şifreleme birlikte gerekir.

**Sonraki bölümde:** Bölüm 32 (Güvenlik) bu bölümde açık bıraktığımız soruları ele alıyor: bir paketin değiştirilmediğini nasıl kanıtlarsın, iki taraf bir anahtarı ağ üzerinden nasıl güvenle paylaşır ve TLS bu adımları nasıl birleştirir? Burada gördüğün `ssl` sarmalaması, o bölümde kriptografinin hangi bileşenlerinden oluştuğunu açıklandığında bir kara kutu olmaktan çıkacak.

::: mulakat
Aşağıdaki sorular cevapsızdır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Bir TCP sunucusunda `recv` 0 döndürdü. Bu, karşı tarafın öldüğü anlamına mı gelir? Yoksa başka ne anlama gelebilir ve sunucu ne yapmalı?
2. Bir istemci iki kez `send("abc")` çağırdı. Sunucu `recv(1024)` ile tek bir çağrıda `abcabc` aldı. Bu olur mu, nasıl olur, ve protokolünü buna göre nasıl tasarlarsın?
3. Uzunluk önekli bir protokolde alıcı uzunluğu 4 GiB olarak okudu. Bellek ayırmadan önce ne yapmalısın ve bu kontrolün hangi saldırıyı durdurduğunu açıkla.
4. Bir sunucu 10 000 eşzamanlı bağlantıyı tutmak istiyor. Süreç başına, iş parçacığı başına ve olay tabanlı modelleri, kaynak kullanımı ve kodun karmaşıklığı açısından karşılaştır.
5. UDP ile TCP arasında, bir telemetri akışı için neden UDP tercih edilebilir? Bu tercihin bedelini (kayıp, sıra değişimi, MTU) en az iki madde ile açıkla.
6. `EPOLLOUT` izlemesini açık bırakmak neden sorun yaratır? Tampon boşken bu maske hangi davranışa yol açar ve bunu nasıl ölçersin?
7. Bir sunucuda `SIGPIPE` alındığında süreç sonlanıyor. Bunu önlemek için hangi üç yöntem var ve hangisi çok iş parçacıklı bir programda daha güvenlidir?
8. Yük testinde ortalama gecikme 2 ms, p99 gecikme 4 ms, maksimum ise 3 saniye. Bu sonuçları nasıl yorumlarsın ve hangi ek ölçümü yaparsın?
