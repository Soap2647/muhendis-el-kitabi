#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N (1u << 24)

static volatile long long sink;

int main(void) {
    int *a = malloc(N * sizeof *a);
    unsigned int *p = malloc(N * sizeof *p);
    if (a == NULL || p == NULL) return 1;
    srand(42);
    for (unsigned int i = 0; i < N; i++) {
        a[i] = (int)(i % 1000);
        p[i] = i;
    }
    for (unsigned int i = N - 1; i > 0; i--) {
        unsigned int j = (unsigned int)rand() % (i + 1);
        unsigned int t = p[i];
        p[i] = p[j];
        p[j] = t;
    }
    double en_sirali = 1e9, en_rastgele = 1e9;
    for (int tekrar = 0; tekrar < 4; tekrar++) {
        long long s = 0;
        clock_t t0 = clock();
        for (unsigned int i = 0; i < N; i++)
            s += a[i];
        clock_t t1 = clock();
        sink = s;
        double d = (double)(t1 - t0) / CLOCKS_PER_SEC;
        if (d < en_sirali) en_sirali = d;

        s = 0;
        t0 = clock();
        for (unsigned int i = 0; i < N; i++)
            s += a[p[i]];
        t1 = clock();
        sink = s;
        d = (double)(t1 - t0) / CLOCKS_PER_SEC;
        if (d < en_rastgele) en_rastgele = d;
    }
    printf("N = %u (%.0f MB dizi)\n", N, N * sizeof *a / 1048576.0);
    printf("sirali erisim   : %8.2f ms\n", en_sirali * 1e3);
    printf("rastgele erisim : %8.2f ms\n", en_rastgele * 1e3);
    printf("oran            : %8.2f\n", en_rastgele / en_sirali);
    free(a);
    free(p);
    return 0;
}
