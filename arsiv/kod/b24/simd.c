#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <immintrin.h>

#define N 2048                /* 2 x 8 KB: L1 önbelleğinde kalır */
#define TEKRAR 50000
#define OLCUM 5

void axpy_skaler(float *y, const float *x, float a, int n);

/* Otomatik vektörleşme adayı: -O3 ile SSE kodu üretebilir */
__attribute__((noinline))
void axpy_oto(float *y, const float *x, float a, int n)
{
    for (int i = 0; i < n; i++)
        y[i] = a * x[i] + y[i];
}

/* Elle yazılmış AVX2 + FMA: 8 float tek yazmaçta (256 bit) */
__attribute__((noinline, target("avx2,fma")))
void axpy_avx2(float *y, const float *x, float a, int n)
{
    __m256 va = _mm256_set1_ps(a);
    int i = 0;
    for (; i + 8 <= n; i += 8) {
        __m256 vx = _mm256_loadu_ps(x + i);
        __m256 vy = _mm256_loadu_ps(y + i);
        vy = _mm256_fmadd_ps(va, vx, vy);
        _mm256_storeu_ps(y + i, vy);
    }
    for (; i < n; i++)        /* kalan elemanlar */
        y[i] = a * x[i] + y[i];
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

static float x[N], y0[N], y[N];

typedef void (*fn_t)(float *, const float *, float, int);

static void olc(const char *derleme, const char *ad, fn_t f)
{
    double t[OLCUM];
    /* doğruluk: tek geçiş, tam sayı değerler (kesin toplanır) */
    for (int i = 0; i < N; i++)
        y[i] = y0[i];
    f(y, x, 0.5f, N);
    for (int i = 0; i < N; i++) {
        float bek = 0.5f * x[i] + y0[i];
        if (y[i] != bek) {
            fprintf(stderr, "HATA: %s i=%d\n", ad, i);
            exit(1);
        }
    }
    for (int k = 0; k < OLCUM; k++) {
        for (int i = 0; i < N; i++)
            y[i] = y0[i];
        double b = simdi_ms();
        for (int r = 0; r < TEKRAR; r++)
            f(y, x, 0.5f, N);
        t[k] = simdi_ms() - b;
    }
    qsort(t, OLCUM, sizeof t[0], cmp_dbl);
    double eleman = (double)TEKRAR * N;
    printf("%s,%s,%.2f,%.4f\n", derleme, ad, t[0],
           t[0] * 1e6 / eleman);
}

int main(int argc, char **argv)
{
    const char *derleme = argc > 1 ? argv[1] : "bilinmiyor";
    for (int i = 0; i < N; i++) {
        x[i] = (float)(i % 37);
        y0[i] = (float)(i % 11);
    }
    printf("derleme,surum,en_az_ms,ns_per_eleman\n");
    olc(derleme, "skaler", axpy_skaler);
    olc(derleme, "oto_vektor", axpy_oto);
    if (__builtin_cpu_supports("avx2") &&
        __builtin_cpu_supports("fma"))
        olc(derleme, "avx2_fma", axpy_avx2);
    else
        printf("%s,avx2_fma,atlandi,0\n", derleme);
    return 0;
}
