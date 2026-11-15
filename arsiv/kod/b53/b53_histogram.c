/* b53_histogram.c - histogram: yaris, atomic ve yerel + birlestirme.
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_histogram.c -o hist
 * Kullanim: ./hist <thread>      (ornek: ./hist 8)
 * Veri: xorshift32, tohum 53. Kova sayisi 16 (cok cekisme icin az).
 * Surum 1 (yaris) KASITLI olarak tanimsiz davranis icerir; yalnizca
 * kayip guncellemeyi gostermek icindir.
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 20000000L
#define KOVA 16
#define TEKRAR 3

static unsigned char veri[N];
static long h0[KOVA], h1[KOVA], h2[KOVA], h3[KOVA];

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

static void sifirla(long *h) { memset(h, 0, KOVA * sizeof *h); }

static void yaris(void) {
    sifirla(h1);
    #pragma omp parallel for
    for (long i = 0; i < N; i++)
        h1[veri[i]]++;   /* KASITLI YARIS: kayip guncelleme */
}

static void atomik(void) {
    sifirla(h2);
    #pragma omp parallel for
    for (long i = 0; i < N; i++) {
        #pragma omp atomic
        h2[veri[i]]++;
    }
}

static void yerel(void) {
    sifirla(h3);
    #pragma omp parallel
    {
        long my[KOVA];
        memset(my, 0, sizeof my);  /* yerel kutu */
        #pragma omp for
        for (long i = 0; i < N; i++)
            my[veri[i]]++;
        #pragma omp critical       /* birlestirme, bir kez */
        for (int k = 0; k < KOVA; k++)
            h3[k] += my[k];
    }
}

static void sirali(void) {
    sifirla(h0);
    for (long i = 0; i < N; i++) h0[veri[i]]++;
}

static int dogru(const long *ref, const long *h) {
    int hata = 0;
    for (int k = 0; k < KOVA; k++)
        if (ref[k] != h[k]) hata++;
    return hata;
}

static double olc(void (*f)(void), int p) {
    double t[TEKRAR];
    omp_set_num_threads(p);
    for (int r = 0; r < TEKRAR; r++) {
        double t0 = omp_get_wtime();
        f();
        t[r] = omp_get_wtime() - t0;
    }
    qsort(t, TEKRAR, sizeof t[0], karsilastir);
    return t[TEKRAR / 2];
}

int main(int argc, char **argv) {
    int p = argc > 1 ? atoi(argv[1]) : 8;
    for (long i = 0; i < N; i++)
        veri[i] = (unsigned char)(xorshift() % KOVA);
    /* Sirali referans: dogruluk icin ve hiz tabani icin */
    double tsira = olc(sirali, 1);
    long toplam_ref = 0;
    for (int k = 0; k < KOVA; k++) toplam_ref += h0[k];
    printf("# N=%ld kova=%d thread=%d tekrar=%d\n",
           N, KOVA, p, TEKRAR);
    printf("surum,medyan_s,kova_toplami,yanlis_kova\n");
    printf("sirali,%.4f,%ld,0\n", tsira, toplam_ref);

    double ts = olc(yaris, p);
    long toplam1 = 0;
    for (int k = 0; k < KOVA; k++) toplam1 += h1[k];
    printf("yaris,%.4f,%ld,%d\n", ts, toplam1, dogru(h0, h1));

    double ta = olc(atomik, p);
    long toplam2 = 0;
    for (int k = 0; k < KOVA; k++) toplam2 += h2[k];
    printf("atomik,%.4f,%ld,%d\n", ta, toplam2, dogru(h0, h2));

    double ty = olc(yerel, p);
    long toplam3 = 0;
    for (int k = 0; k < KOVA; k++) toplam3 += h3[k];
    printf("yerel,%.4f,%ld,%d\n", ty, toplam3, dogru(h0, h3));
    printf("referans_toplam=%ld\n", toplam_ref);
    return 0;
}
