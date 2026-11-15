/* b28_9_epoll.c: G/Ç çoğullama. Kipler:
 *   tetik      seviye/kenar tetikleme ve EAGAIN
 *   olcek N    poll ve epoll, N pipe, tek aktif fd (ns/çağrı)
 *   olay       N=1000 pipe'ı tek epoll döngüsünde dinle */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <poll.h>
#include <sys/epoll.h>
#include <sys/resource.h>

static void boru_ac(int b[2])
{
    if (pipe(b) < 0) { perror("pipe"); exit(1); }
}

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + t.tv_nsec;
}

static void tetik(void)
{
    int bl[2];
    struct epoll_event ev, out;
    char c;

    /* Seviye tetikleme (LT): veri kaldıysa tekrar bildirir */
    boru_ac(bl);
    int ep = epoll_create1(0);
    ev.events = EPOLLIN; ev.data.fd = bl[0];
    epoll_ctl(ep, EPOLL_CTL_ADD, bl[0], &ev);
    if (write(bl[1], "ab", 2) != 2) return;
    epoll_wait(ep, &out, 1, 0);
    if (read(bl[0], &c, 1) != 1) return;     /* yalnız 1 bayt */
    int n2 = epoll_wait(ep, &out, 1, 0);
    printf("LT: ikinci epoll_wait hazır=%d (1 bayt kaldı)\n", n2);
    close(ep); close(bl[0]); close(bl[1]);

    /* Kenar tetikleme (ET): yalnız yeni veri gelişinde bildirir */
    boru_ac(bl);
    ep = epoll_create1(0);
    ev.events = EPOLLIN | EPOLLET; ev.data.fd = bl[0];
    epoll_ctl(ep, EPOLL_CTL_ADD, bl[0], &ev);
    if (write(bl[1], "ab", 2) != 2) return;
    epoll_wait(ep, &out, 1, 0);
    if (read(bl[0], &c, 1) != 1) return;
    int n3 = epoll_wait(ep, &out, 1, 0);
    printf("ET: ikinci epoll_wait hazır=%d (1 bayt kaldı!)\n", n3);
    close(ep); close(bl[0]); close(bl[1]);

    /* EAGAIN: boş, engellemeyen pipe'tan okuma */
    boru_ac(bl);
    fcntl(bl[0], F_SETFL, O_NONBLOCK);
    ssize_t r = read(bl[0], &c, 1);
    printf("boş pipe read=%zd errno=%s\n", r,
           errno == EAGAIN ? "EAGAIN" : "diğer");
    close(bl[0]); close(bl[1]);
}

static void olcek(int n)
{
    int (*bl)[2] = malloc(n * sizeof *bl);
    struct pollfd *pf = malloc(n * sizeof *pf);
    int ep = epoll_create1(0);
    for (int i = 0; i < n; i++) {
        boru_ac(bl[i]);
        pf[i].fd = bl[i][0];
        pf[i].events = POLLIN;
        struct epoll_event ev = { .events = EPOLLIN, .data.u32 = i };
        epoll_ctl(ep, EPOLL_CTL_ADD, bl[i][0], &ev);
    }
    int son = n - 1;                 /* tek aktif fd: sonuncusu */
    const int R = 2000;
    double tp = 0, te = 0;
    struct epoll_event out;
    char c;
    for (int r = 0; r < R; r++) {
        if (write(bl[son][1], "x", 1) != 1) return;
        double t0 = simdi_ns();
        poll(pf, n, 0);
        tp += simdi_ns() - t0;
        if (read(bl[son][0], &c, 1) != 1) return;

        if (write(bl[son][1], "x", 1) != 1) return;
        t0 = simdi_ns();
        epoll_wait(ep, &out, 1, 0);
        te += simdi_ns() - t0;
        if (read(bl[son][0], &c, 1) != 1) return;
    }
    printf("%d,%.0f,%.0f\n", n, tp / R, te / R);
    for (int i = 0; i < n; i++) {
        close(bl[i][0]); close(bl[i][1]);
    }
    close(ep);
    free(bl); free(pf);
}

static void olay(void)
{
    enum { N = 1000, TUR = 20, K = 5 };
    int (*bl)[2] = malloc(N * sizeof *bl);
    int ep = epoll_create1(0);
    for (int i = 0; i < N; i++) {
        boru_ac(bl[i]);
        fcntl(bl[i][0], F_SETFL, O_NONBLOCK);
        struct epoll_event ev = { .events = EPOLLIN, .data.u32 = i };
        epoll_ctl(ep, EPOLL_CTL_ADD, bl[i][0], &ev);
    }
    srand(28);
    long yazilan = 0, okunan = 0, hazir = 0;
    struct epoll_event olaylar[64];
    char t[64];
    for (int tur = 0; tur < TUR; tur++) {
        for (int k = 0; k < K; k++) {        /* K rastgele yazma */
            int id = rand() % N;
            if (write(bl[id][1], "veri", 4) == 4) yazilan += 4;
        }
        int m = epoll_wait(ep, olaylar, 64, 0);
        hazir += m;
        for (int i = 0; i < m; i++) {        /* hazırları boşalt */
            int id = (int)olaylar[i].data.u32;
            ssize_t r;
            while ((r = read(bl[id][0], t, sizeof t)) > 0)
                okunan += r;
        }
    }
    printf("N=%d pipe, tur=%d, toplam hazır olay=%ld\n",
           N, TUR, hazir);
    printf("yazılan=%ld bayt, okunan=%ld bayt, doğru=%d\n",
           yazilan, okunan, yazilan == okunan);
    for (int i = 0; i < N; i++) {
        close(bl[i][0]); close(bl[i][1]);
    }
    close(ep);
    free(bl);
}

int main(int argc, char **argv)
{
    struct rlimit rl;
    getrlimit(RLIMIT_NOFILE, &rl);
    rl.rlim_cur = rl.rlim_max;
    setrlimit(RLIMIT_NOFILE, &rl);

    const char *kip = argc > 1 ? argv[1] : "tetik";
    if (strcmp(kip, "tetik") == 0) tetik();
    else if (strcmp(kip, "olcek") == 0) {
        if (argc < 3) return 1;
        olcek(atoi(argv[2]));
    }
    else if (strcmp(kip, "olay") == 0) olay();
    return 0;
}
