#include <stddef.h>
#include <stdio.h>

typedef struct {
    size_t ilk;
    size_t son;
} aralik;

/* Alt sınır: a[i] >= x olan ilk i (yoksa n). */
size_t alt_sinir(const int *a, size_t n, int x) {
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        if (a[orta] < x)
            lo = orta + 1;
        else
            hi = orta;
    }
    return lo;
}

/* Üst sınır: a[i] > x olan ilk i (yoksa n). */
size_t ust_sinir(const int *a, size_t n, int x) {
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        if (a[orta] <= x)
            lo = orta + 1;
        else
            hi = orta;
    }
    return lo;
}

/* x'in eşit aralığı [ilk, son): x yoksa ilk == son. */
aralik esit_aralik(const int *a, size_t n, int x) {
    aralik r = {alt_sinir(a, n, x), ust_sinir(a, n, x)};
    return r;
}

int main(void) {
    int a[] = {1, 2, 2, 2, 3, 5, 5, 8};
    size_t n = sizeof a / sizeof a[0];
    int sorgu[] = {2, 4, 9, 0};
    printf("%3s %4s %4s %5s\n", "x", "alt", "ust", "sayi");
    for (int k = 0; k < 4; k++) {
        aralik r = esit_aralik(a, n, sorgu[k]);
        printf("%3d %4zu %4zu %5zu\n", sorgu[k], r.ilk, r.son,
               r.son - r.ilk);
    }
    return 0;
}
