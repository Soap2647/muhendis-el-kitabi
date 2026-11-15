#define _POSIX_C_SOURCE 199309L
/* satir.c - adim taramasi ile onbellek satir boyunu bulmak.
 * 64 MB'lik bir dizide her erisim, s bayt ileridedir ve toplam
 * erisim sayisi sabittir. s < 64 iken bir satir birden fazla
 * erisimle paylasilir; s >= 64 iken her erisim yeni bir satir
 * getirir. Egri 64'te duzlesiyorsa satir boyu 64 bayttir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 satir.c -o satir
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define BOYUT (64u << 20)        /* 64 MB, 2'nin kuvveti */
#define ERISIM (1u << 22)
#define DENEME 5

static volatile unsigned char *dizi;
static volatile unsigned char cikis;

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + (double)t.tv_nsec;
}

static int karsilastir(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static double olc(size_t s)
{
    double sonuc[DENEME];
    for (int r = 0; r < DENEME; r++) {
        unsigned toplam = 0;
        size_t idx = 0;
        double t0 = simdi_ns();
        for (size_t i = 0; i < ERISIM; i++) {
            toplam += dizi[idx];
            idx = (idx + s) & (BOYUT - 1);
        }
        double t1 = simdi_ns();
        cikis = (unsigned char)toplam;
        sonuc[r] = (t1 - t0) / ERISIM;
    }
    qsort(sonuc, DENEME, sizeof sonuc[0], karsilastir);
    return sonuc[DENEME / 2];
}

int main(void)
{
    dizi = malloc(BOYUT);
    if (!dizi) { perror("malloc"); return 1; }
    /* sayfa hatalari olcume girmesin diye once dokunulur */
    memset((void *)dizi, 1, BOYUT);

    printf("adim_bayt,ns_erisim\n");
    for (size_t s = 1; s <= 512; s *= 2)
        printf("%zu,%.3f\n", s, olc(s));
    free((void *)dizi);
    return 0;
}
