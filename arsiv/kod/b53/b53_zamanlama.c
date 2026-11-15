/* b53_zamanlama.c - statik, dinamik, guided (dengesiz is).
 * Derleme: gcc -O2 -std=c11 -fopenmp b53_zamanlama.c -o zamanlama
 * Kullanim: ./zamanlama <thread>      (ornek: ./zamanlama 8)
 * Is i, (i+1) * BIRIM adimlik bir karma dongusudur: is maliyeti
 * dogrusal artar. Statik bolme son iş parçacigini yukler.
 * Ilk kosunun zaman cizelgesi: engine\veri\b53_gantt.csv
 */
#define _POSIX_C_SOURCE 200809L
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M 512            /* is (iterasyon) sayisi */
#define BIRIM 2000       /* i. is: (i+1)*BIRIM adim */
#define TEKRAR 5
#define GANTT "b53_gantt.csv"

static volatile unsigned long sink;
static int th[M];
static double ts[M], te[M];

static void yuk(long n) {
    unsigned long s = 1;
    for (long k = 0; k < n; k++)
        s = s * 31UL + (unsigned long)k;
    sink += s;
}

/* Calisma suresini dondurur; th/ts/te zaman cizelgesini doldurur. */
static double kos(omp_sched_t tur, int p) {
    omp_set_schedule(tur, tur == omp_sched_dynamic ? 8 : 0);
    double t0 = omp_get_wtime();
    #pragma omp parallel for num_threads(p) schedule(runtime)
    for (int i = 0; i < M; i++) {
        ts[i] = omp_get_wtime() - t0;
        yuk((long)(i + 1) * BIRIM);
        te[i] = omp_get_wtime() - t0;
        th[i] = omp_get_thread_num();
    }
    return omp_get_wtime() - t0;
}

static int karsilastir(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    int p = argc > 1 ? atoi(argv[1]) : 8;
    omp_sched_t turler[3] = {omp_sched_static, omp_sched_dynamic,
                             omp_sched_guided};
    const char *ad[3] = {"statik", "dinamik8", "guided"};
    FILE *g = fopen(GANTT, "w");
    if (!g) { perror("gantt"); return 1; }
    fprintf(g, "zamanlama,is,thread,baslangic_ms,bitis_ms\n");
    double t1 = kos(omp_sched_static, 1);   /* tek is referansi */
    printf("# M=%d BIRIM=%d thread=%d tekrar=%d\n", M, BIRIM, p,
           TEKRAR);
    printf("# tek_is_parcacigi_s=%.4f ideal_s=%.4f\n", t1, t1 / p);
    printf("zamanlama,medyan_s,hizlanma\n");
    for (int k = 0; k < 3; k++) {
        double t[TEKRAR];
        for (int r = 0; r < TEKRAR; r++) {
            t[r] = kos(turler[k], p);
            if (r == 0)
                for (int i = 0; i < M; i++)
                    fprintf(g, "%s,%d,%d,%.3f,%.3f\n",
                            ad[k], i, th[i],
                            ts[i] * 1e3, te[i] * 1e3);
        }
        qsort(t, TEKRAR, sizeof t[0], karsilastir);
        printf("%s,%.4f,%.2f\n", ad[k], t[TEKRAR / 2],
               t1 / t[TEKRAR / 2]);
    }
    fclose(g);
    return 0;
}
