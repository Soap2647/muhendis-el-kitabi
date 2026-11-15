/* b53_olcek.c - Amdahl (guclu) ve Gustafson (zayif) olcegi.
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_olcek.c -o olcek
 * Kullanim: ./olcek guclu 0.10     (sabit toplam is, seri kesir 0.10)
 *           ./olcek zayif 0.10     (is p ile buyur, seri kesir 0.10)
 * Cikti: CSV. Medyan sure saniye cinsinden.
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NG 400000000UL   /* guclu: toplam iterasyon */
#define N0 100000000UL   /* zayif: 1 birimlik temel is */
#define BIRIM 4096       /* guclu: paralel birim sayisi */
#define ZKOK 256         /* zayif: is parcacigi basina birim */
#define TEKRAR 5

static unsigned long out[BIRIM];
static volatile unsigned long sink;

/* Tamsayi karma dongusu: bellek kullanmaz, yalnizca ALU. */
static unsigned long kur(unsigned long n, unsigned long tohum) {
    unsigned long s = tohum;
    for (unsigned long i = 0; i < n; i++)
        s = (s * 31UL + i) ^ (s >> 7);
    return s;
}

/* Once seri kisim (tek is parcacigi), sonra p parcacikla birim. */
static double kos(unsigned long seri, unsigned long birim,
                  int nb, int p) {
    double t0 = omp_get_wtime();
    sink = kur(seri, 1);
    #pragma omp parallel for num_threads(p) schedule(static)
    for (int b = 0; b < nb; b++)
        out[b] = kur(birim, (unsigned long)b);
    unsigned long t = 0;
    for (int b = 0; b < nb; b++) t ^= out[b];
    sink ^= t;
    return omp_get_wtime() - t0;
}

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static double medyan(double *v, int n) {
    qsort(v, n, sizeof v[0], karsilastir);
    return v[n / 2];
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "kullanim: %s guclu|zayif s\n", argv[0]);
        return 1;
    }
    int zayif = strcmp(argv[1], "zayif") == 0;
    double s = atof(argv[2]);
    int pler[] = {1, 2, 4, 6, 8, 10, 12, 14, 16};
    int np = (int)(sizeof pler / sizeof pler[0]);
    printf("# mod=%s seri=%.2f tekrar=%d\n", argv[1], s, TEKRAR);
    if (!zayif) {
        double t1 = 0;
        printf("p,medyan_s,hizlanma,verim\n");
        for (int k = 0; k < np; k++) {
            double t[TEKRAR];
            unsigned long seri = (unsigned long)(s * NG);
            unsigned long birim =
                (unsigned long)((1.0 - s) * NG / BIRIM);
            for (int r = 0; r < TEKRAR; r++)
                t[r] = kos(seri, birim, BIRIM, pler[k]);
            double m = medyan(t, TEKRAR);
            if (pler[k] == 1) t1 = m;
            printf("%d,%.4f,%.3f,%.3f\n", pler[k], m, t1 / m,
                   t1 / m / pler[k]);
        }
    } else {
        printf("p,medyan_tp_s,medyan_tseq_s,");
        printf("olceklenmis_hizlanma,verim\n");
        unsigned long seri = (unsigned long)(s * N0);
        int nb_taban = ZKOK;
        for (int k = 0; k < np; k++) {
            int p = pler[k];
            int nb = nb_taban * p;     /* is p ile buyur */
            unsigned long birim =
                (unsigned long)((1.0 - s) * N0 / ZKOK);
            double tp[TEKRAR], ts[TEKRAR];
            for (int r = 0; r < TEKRAR; r++) {
                tp[r] = kos(seri, birim, nb, p);   /* paralel */
                ts[r] = kos(seri, birim, nb, 1);  /* tek iplik */
            }
            double mp = medyan(tp, TEKRAR), ms = medyan(ts, TEKRAR);
            printf("%d,%.4f,%.4f,%.3f,%.3f\n", p, mp, ms, ms / mp,
                   ms / mp / p);
        }
    }
    return 0;
}
