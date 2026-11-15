/* b53_mergesort.c - paralel birlestirme siralamasi: gorev + esik.
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_mergesort.c -o msort
 * Kullanim: ./msort <thread>        (ornek: ./msort 8)
 * Birlestirme seri yapilir: T_inf = O(n) (metinde anlatilir).
 * Dogruluk: her paralel sonuc, seri siralamanin birebir kopyasiyla
 * karsilastirilir (kararli birlestirme: esitlikte sol taraf once).
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N (1L << 24)     /* 16.7 milyon int */
#define TEKRAR 3

static long ESIK;

static void birlestir(int *a, int *t, long lo, long mid, long hi) {
    long i = lo, j = mid, k = lo;
    while (i < mid && j < hi)
        t[k++] = (a[j] < a[i]) ? a[j++] : a[i++];
    while (i < mid) t[k++] = a[i++];
    while (j < hi) t[k++] = a[j++];
    memcpy(a + lo, t + lo, (size_t)(hi - lo) * sizeof *a);
}

static void sirali(int *a, int *t, long lo, long hi) {
    if (hi - lo < 2) return;
    long mid = lo + (hi - lo) / 2;
    sirali(a, t, lo, mid);
    sirali(a, t, mid, hi);
    birlestir(a, t, lo, mid, hi);
}

/* Esik altinda seri, uzerinde iki gorev. */
static void paralel(int *a, int *t, long lo, long hi) {
    if (hi - lo <= ESIK) {
        sirali(a, t, lo, hi);
        return;
    }
    long mid = lo + (hi - lo) / 2;
    #pragma omp task shared(a, t)
    paralel(a, t, lo, mid);
    #pragma omp task shared(a, t)
    paralel(a, t, mid, hi);
    #pragma omp taskwait
    birlestir(a, t, lo, mid, hi);
}

static unsigned int xs = 53u;
static unsigned int xorshift(void) {
    xs ^= xs << 13;
    xs ^= xs >> 17;
    xs ^= xs << 5;
    return xs;
}

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    int p = argc > 1 ? atoi(argv[1]) : 8;
    int *ilk = malloc(N * sizeof *ilk);
    int *a = malloc(N * sizeof *a);
    int *t = malloc(N * sizeof *t);
    int *ref = malloc(N * sizeof *ref);
    if (!ilk || !a || !t || !ref) return 1;
    for (long i = 0; i < N; i++) ilk[i] = (int)(xorshift() >> 2);
    memcpy(ref, ilk, N * sizeof *ilk);
    double tr[TEKRAR];
    for (int r = 0; r < TEKRAR; r++) {
        memcpy(a, ilk, N * sizeof *ilk);
        double t0 = omp_get_wtime();
        sirali(a, t, 0, N);
        tr[r] = omp_get_wtime() - t0;
    }
    memcpy(ref, a, N * sizeof *a);  /* seri sonuc referans */
    qsort(tr, TEKRAR, sizeof tr[0], karsilastir);
    double tseri = tr[TEKRAR / 2];
    printf("# N=%ld thread=%d tekrar=%d\n", N, p, TEKRAR);
    printf("esik,medyan_s,hizlanma,dogru\n");
    printf("seri,%.4f,1.00,evet\n", tseri);
    long esikler[] = {1L << 8, 1L << 12, 1L << 16, 1L << 20, N};
    for (int k = 0; k < 5; k++) {
        ESIK = esikler[k];
        double tp[TEKRAR];
        int dogru = 1;
        for (int r = 0; r < TEKRAR; r++) {
            memcpy(a, ilk, N * sizeof *ilk);
            double t0 = omp_get_wtime();
            #pragma omp parallel num_threads(p)
            #pragma omp single
            paralel(a, t, 0, N);
            tp[r] = omp_get_wtime() - t0;
            if (memcmp(a, ref, N * sizeof *a) != 0) dogru = 0;
        }
        qsort(tp, TEKRAR, sizeof tp[0], karsilastir);
        printf("%ld,%.4f,%.2f,%s\n", ESIK, tp[TEKRAR / 2],
               tseri / tp[TEKRAR / 2], dogru ? "evet" : "HAYIR");
    }
    free(ilk); free(a); free(t); free(ref);
    return 0;
}
