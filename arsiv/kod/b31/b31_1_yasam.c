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
