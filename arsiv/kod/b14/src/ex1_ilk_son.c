#include <stddef.h>
#include <stdio.h>

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

/* x'in ilk ve son konumu. Bulunamazsa (-1, -1). */
void ilk_son(const int *a, size_t n, int x, long *ilk, long *son) {
    size_t l = alt_sinir(a, n, x);
    size_t u = ust_sinir(a, n, x);
    if (l == u) {
        *ilk = -1;
        *son = -1;
    } else {
        *ilk = (long)l;
        *son = (long)u - 1;
    }
}

int main(void) {
    int a[] = {5, 7, 7, 8, 8, 10};
    size_t n = sizeof a / sizeof a[0];
    int sorgu[] = {8, 7, 6, 11};
    for (int k = 0; k < 4; k++) {
        long ilk, son;
        ilk_son(a, n, sorgu[k], &ilk, &son);
        printf("x=%2d ilk=%2ld son=%2ld\n", sorgu[k], ilk, son);
    }
    return 0;
}
