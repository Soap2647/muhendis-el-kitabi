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
