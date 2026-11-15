#include <stddef.h>
#include <stdio.h>

/* Döndürülmüş sıralı dizinin minimum konumu (n >= 1).
   adim: döngü turu sayacı. Eşitlik dalı (hi--) tekrarlarda
   her turda bir eleman eler; bu en kötü durumu O(n) yapar. */
size_t min_konum(const int *a, size_t n, long *adim) {
    size_t lo = 0, hi = n - 1;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        (*adim)++;
        if (a[orta] > a[hi])
            lo = orta + 1;       /* minimum orta'nın sağında */
        else if (a[orta] < a[hi])
            hi = orta;           /* minimum orta dahil solda */
        else
            hi--;                /* a[orta] == a[hi]: karar yok */
    }
    return lo;
}

/* Farklı elemanlı döndürülmüş dizide x'in konumu, yoksa -1. */
long dondurulmus_ara(const int *a, size_t n, int x) {
    long adim = 0;
    size_t k = min_konum(a, n, &adim);
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        size_t gercek = (orta + k) % n;
        if (a[gercek] < x)
            lo = orta + 1;
        else if (a[gercek] > x)
            hi = orta;
        else
            return (long)gercek;
    }
    return -1;
}

int main(void) {
    int a[] = {4, 5, 6, 7, 0, 1, 2};
    size_t n = sizeof a / sizeof a[0];
    long adim = 0;
    size_t k = min_konum(a, n, &adim);
    printf("min konumu=%zu adim=%ld\n", k, adim);
    int sorgu[] = {0, 3, 6, 9};
    for (int i = 0; i < 4; i++)
        printf("x=%d -> %ld\n", sorgu[i],
               dondurulmus_ara(a, n, sorgu[i]));
    printf("tekrarli en kotu durum (min en solda, geri kalan 1):\n");
    for (size_t m = 8; m <= 64; m *= 2) {
        int b[64];
        b[0] = 0;
        for (size_t i = 1; i < m; i++)
            b[i] = 1;
        long t = 0;
        min_konum(b, m, &t);
        printf("  n=%2zu adim=%2ld\n", m, t);
    }
    return 0;
}
