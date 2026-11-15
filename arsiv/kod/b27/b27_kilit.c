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
