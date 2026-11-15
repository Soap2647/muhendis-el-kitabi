#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#define N 32768
#define TEKRAR 4000
#define OLCUM 7

static uint64_t durum = 42;   /* sabit tohum: tekrarlanabilir */

static uint32_t rnd(void)
{
    durum ^= durum << 13;
    durum ^= durum >> 7;
    durum ^= durum << 17;
    return (uint32_t)(durum >> 32);
}

static int karsilastir(const void *a, const void *b)
{
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

static volatile long sink;    /* sonucu kullan: derleyici silmesin */

__attribute__((noinline))
long dalli(const int *v, int n)
{
    long s = 0;
    for (int i = 0; i < n; i++) {
        if (v[i] >= 128)      /* veriye bağlı dal */
            s += v[i];
    }
    return s;
}

__attribute__((noinline))
long dalsiz(const int *v, int n)
{
    long s = 0;
    for (int i = 0; i < n; i++) {
        int m = -(v[i] >= 128);   /* 0 ya da -1 (bütün bitler 1) */
        s += v[i] & m;
    }
    return s;
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

typedef long (*fn_t)(const int *, int);

static void olc(const char *derleme, const char *ad, fn_t f,
                const int *v, const char *dizi, long *bek)
{
    double t[OLCUM];
    long sonuc = 0;
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_ms();
        for (int r = 0; r < TEKRAR; r++)
            sonuc = f(v, N);
        t[k] = simdi_ms() - b;
        sink = sonuc;
    }
    if (*bek < 0)
        *bek = sonuc;
    if (sonuc != *bek) {
        fprintf(stderr, "HATA: toplam uyusmuyor\n");
        exit(1);
    }
    qsort(t, OLCUM, sizeof t[0], cmp_dbl);
    double en = t[0], med = t[OLCUM / 2];
    printf("%s,%s,%s,%.2f,%.2f,%.3f,%ld\n", derleme, ad, dizi,
           en, med, en * 1e6 / ((double)TEKRAR * N), sonuc);
}

int main(int argc, char **argv)
{
    const char *derleme = argc > 1 ? argv[1] : "bilinmiyor";
    static int v[N], s[N];
    for (int i = 0; i < N; i++)
        v[i] = (int)(rnd() % 256);  /* yaklaşık yarısı >= 128 */
    for (int i = 0; i < N; i++)
        s[i] = v[i];
    qsort(s, N, sizeof s[0], karsilastir);

    long bek = -1;
    printf("derleme,fonksiyon,dizi,en_az_ms,medyan_ms,"
           "ns_per_eleman,toplam\n");
    olc(derleme, "dalli", dalli, v, "sirasiz", &bek);
    olc(derleme, "dalli", dalli, s, "sirali", &bek);
    bek = -1;
    olc(derleme, "dalsiz", dalsiz, v, "sirasiz", &bek);
    olc(derleme, "dalsiz", dalsiz, s, "sirali", &bek);
    return 0;
}
