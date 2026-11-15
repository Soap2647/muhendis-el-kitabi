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
