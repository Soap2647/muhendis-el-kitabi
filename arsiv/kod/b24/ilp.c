#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#define N 1024                /* 8 KB: tamamen L1 önbelleğinde */
#define TEKRAR 200000
#define OLCUM 7

static uint64_t durum = 42;

static uint32_t rnd(void)
{
    durum ^= durum << 13;
    durum ^= durum >> 7;
    durum ^= durum << 17;
    return (uint32_t)(durum >> 32);
}

static volatile double sink;

/* tek zincir: her toplama bir öncekinin sonucunu bekler */
__attribute__((noinline))
double topla1(const double *a, int n)
{
    double s0 = 0.0;
    for (int i = 0; i < n; i++)
        s0 += a[i];
    return s0;
}

__attribute__((noinline))
double topla2(const double *a, int n)
{
    double s0 = 0.0, s1 = 0.0;
    for (int i = 0; i < n; i += 2) {
        s0 += a[i];
        s1 += a[i + 1];
    }
    return s0 + s1;
}

__attribute__((noinline))
double topla4(const double *a, int n)
{
    double s0 = 0.0, s1 = 0.0, s2 = 0.0, s3 = 0.0;
    for (int i = 0; i < n; i += 4) {
        s0 += a[i];
        s1 += a[i + 1];
        s2 += a[i + 2];
        s3 += a[i + 3];
    }
    return (s0 + s1) + (s2 + s3);
}

__attribute__((noinline))
double topla8(const double *a, int n)
{
    double s0 = 0.0, s1 = 0.0, s2 = 0.0, s3 = 0.0;
    double s4 = 0.0, s5 = 0.0, s6 = 0.0, s7 = 0.0;
    for (int i = 0; i < n; i += 8) {
        s0 += a[i];
        s1 += a[i + 1];
        s2 += a[i + 2];
        s3 += a[i + 3];
        s4 += a[i + 4];
        s5 += a[i + 5];
        s6 += a[i + 6];
        s7 += a[i + 7];
    }
    return ((s0 + s1) + (s2 + s3)) + ((s4 + s5) + (s6 + s7));
}

static double simdi_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

static int cmp_dbl(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

typedef double (*fn_t)(const double *, int);

static void olc(const char *derleme, const char *ad, int akum,
                fn_t f, const double *a, double *bek)
{
    double t[OLCUM], sonuc = 0.0;
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_ms();
        for (int r = 0; r < TEKRAR; r++)
            sonuc = f(a, N);
        t[k] = simdi_ms() - b;
        sink = sonuc;
    }
    if (*bek < 0.0)
        *bek = sonuc;
    if (sonuc != *bek) {
        fprintf(stderr, "HATA: %s toplam uyusmuyor\n", ad);
        exit(1);
    }
    qsort(t, OLCUM, sizeof t[0], cmp_dbl);
    double eleman = (double)TEKRAR * N;
    printf("%s,%s,%d,%.2f,%.2f,%.4f\n", derleme, ad, akum,
           t[0], t[OLCUM / 2], t[0] * 1e6 / eleman);
}

int main(int argc, char **argv)
{
    const char *derleme = argc > 1 ? argv[1] : "bilinmiyor";
    static double a[N];
    for (int i = 0; i < N; i++)
        a[i] = (double)(rnd() % 1000);   /* tam sayı: toplam kesin */

    double bek = -1.0;
    printf("derleme,fonksiyon,akumulator,en_az_ms,"
           "medyan_ms,ns_per_eleman\n");
    olc(derleme, "topla1", 1, topla1, a, &bek);
    olc(derleme, "topla2", 2, topla2, a, &bek);
    olc(derleme, "topla4", 4, topla4, a, &bek);
    olc(derleme, "topla8", 8, topla8, a, &bek);
    return 0;
}
