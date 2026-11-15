/* b53_bant.c - STREAM benzeri triad: bellek bant genisligi olcegi.
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_bant.c -o bant
 * Kullanim: ./bant
 * Triad: a[i] = b[i] + q * c[i]. STREAM sayimi: element basina
 * 24 bayt (2 okuma + 1 yazma, 8 bayt double). Gercekte yazma
 * oncesi satir okunduguna gore trafik daha fazladir (write-allocate).
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

#define N (1UL << 25)    /* 2^25 double = 256 MB */
#define TEKRAR 5

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

int main(void) {
    double *a = malloc(N * sizeof *a);
    double *b = malloc(N * sizeof *b);
    double *c = malloc(N * sizeof *c);
    if (!a || !b || !c) {
        fputs("bellek yetersiz\n", stderr);
        return 1;
    }
    const double q = 3.0;
    /* Ilk dokunus: sayfalar 16 is parcacigi tarafindan eslenir. */
    #pragma omp parallel for num_threads(16) schedule(static)
    for (long i = 0; i < (long)N; i++) {
        a[i] = 0.0;
        b[i] = 1.0;
        c[i] = 2.0;
    }
    printf("# N=%lu (her dizi %.0f MB), tekrar=%d\n",
           N, N * 8.0 / 1e6, TEKRAR);
    printf("p,medyan_gbs,min_gbs,max_gbs\n");
    for (int p = 1; p <= 16; p++) {
        double gb[TEKRAR];
        for (int r = 0; r < TEKRAR; r++) {
            double t0 = omp_get_wtime();
            #pragma omp parallel for num_threads(p) schedule(static)
            for (long i = 0; i < (long)N; i++)
                a[i] = b[i] + q * c[i];
            double dt = omp_get_wtime() - t0;
            gb[r] = 24.0 * (double)N / dt / 1e9;
        }
        qsort(gb, TEKRAR, sizeof gb[0], karsilastir);
        printf("%d,%.2f,%.2f,%.2f\n", p, gb[TEKRAR / 2], gb[0],
               gb[TEKRAR - 1]);
    }
    /* Dogrulama: a[i] = 1 + 3*2 = 7 olmali. */
    printf("dogrulama: a[0]=%.1f a[N-1]=%.1f\n", a[0], a[N - 1]);
    free(a); free(b); free(c);
    return 0;
}
