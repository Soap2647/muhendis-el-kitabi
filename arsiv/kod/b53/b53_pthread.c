/* b53_pthread.c - pthreads ile elle bolme, OpenMP ve is parcacigi
 * olusturma maliyeti.
 * Derleme: gcc -O2 -std=c11 -pthread -fopenmp b53_pthread.c -o pth
 * Kullanim: ./pth <thread>          (ornek: ./pth 8)
 * Is: her i icin kucuk bir karma hesabi; sonuc XOR ile birlesir
 * (XOR degisme siralidan bagimsizdir, bu yuzden dogrulama tam olur).
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 100000000UL
#define TEKRAR 5
#define OVH_TEKRAR 2000

static unsigned long hesapla(unsigned long i) {
    unsigned long s = i + 1;
    for (int k = 0; k < 4; k++) s = (s * 31UL) ^ (s >> 7);
    return s;
}

struct is { unsigned long lo, hi, sonuc; };

static void *calis(void *arg) {
    struct is *x = arg;
    unsigned long s = 0;
    for (unsigned long i = x->lo; i < x->hi; i++) s ^= hesapla(i);
    x->sonuc = s;
    return NULL;
}

static unsigned long elle(int p) {   /* pthreads ile bolme */
    pthread_t th[64];
    struct is is[64];
    unsigned long pay = N / (unsigned long)p;
    for (int k = 0; k < p; k++) {
        is[k].lo = k * pay;
        is[k].hi = (k == p - 1) ? N : (k + 1) * pay;
        pthread_create(&th[k], NULL, calis, &is[k]);
    }
    unsigned long toplam = 0;
    for (int k = 0; k < p; k++) {
        pthread_join(th[k], NULL);
        toplam ^= is[k].sonuc;
    }
    return toplam;
}

static unsigned long openmp(int p) {         /* OpenMP statik bolme */
    unsigned long toplam = 0;
    #pragma omp parallel for num_threads(p) schedule(static) \
            reduction(^:toplam)
    for (unsigned long i = 0; i < N; i++) toplam ^= hesapla(i);
    return toplam;
}

static unsigned long sirali(void) {
    unsigned long toplam = 0;
    for (unsigned long i = 0; i < N; i++) toplam ^= hesapla(i);
    return toplam;
}

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    int p = argc > 1 ? atoi(argv[1]) : 8;
    /* 1. Olusturma + birlestirme maliyeti (is: sifir iş). */
    double ov[OVH_TEKRAR];
    for (int r = 0; r < OVH_TEKRAR; r++) {
        pthread_t th[64];
        struct is bos = {0, 0, 0};
        double t0 = omp_get_wtime();
        for (int k = 0; k < p; k++)
            pthread_create(&th[k], NULL, calis, &bos);
        for (int k = 0; k < p; k++)
            pthread_join(th[k], NULL);
        ov[r] = omp_get_wtime() - t0;
    }
    qsort(ov, OVH_TEKRAR, sizeof ov[0], karsilastir);
    printf("# thread=%d N=%lu\n", p, N);
    printf("olusturma_birlestirme_medyan_us=%.1f\n",
           ov[OVH_TEKRAR / 2] * 1e6);
    /* 2. Hesap: sirali, pthreads, OpenMP. */
    double tr[TEKRAR], to[TEKRAR], ts[TEKRAR];
    unsigned long r1 = 0, r2 = 0, r3 = 0;
    for (int r = 0; r < TEKRAR; r++) {
        double t0 = omp_get_wtime();
        r1 = sirali();
        ts[r] = omp_get_wtime() - t0;
        t0 = omp_get_wtime();
        r2 = elle(p);
        tr[r] = omp_get_wtime() - t0;
        t0 = omp_get_wtime();
        r3 = openmp(p);
        to[r] = omp_get_wtime() - t0;
    }
    qsort(ts, TEKRAR, sizeof ts[0], karsilastir);
    qsort(tr, TEKRAR, sizeof tr[0], karsilastir);
    qsort(to, TEKRAR, sizeof to[0], karsilastir);
    printf("surum,medyan_s,hizlanma,ayni_sonuc\n");
    printf("sirali,%.4f,1.00,-\n", ts[TEKRAR / 2]);
    printf("pthreads,%.4f,%.2f,%s\n", tr[TEKRAR / 2],
           ts[TEKRAR / 2] / tr[TEKRAR / 2],
           r2 == r1 ? "evet" : "HAYIR");
    printf("openmp,%.4f,%.2f,%s\n", to[TEKRAR / 2],
           ts[TEKRAR / 2] / to[TEKRAR / 2],
           r3 == r1 ? "evet" : "HAYIR");
    return 0;
}
