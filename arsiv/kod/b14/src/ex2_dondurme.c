#include <stddef.h>
#include <stdio.h>

/* Farklı elemanlı, döndürülmüş sıralı dizi. Kaç kez döndürüldüğünü,
   yani minimumun konumunu döndürür. n >= 1 olmalı. */
size_t dondurme_sayisi(const int *a, size_t n) {
    size_t lo = 0, hi = n - 1;
    while (lo < hi) {
        size_t orta = lo + (hi - lo) / 2;
        if (a[orta] > a[hi])
            lo = orta + 1;
        else
            hi = orta;
    }
    return lo;
}

int main(void) {
    int a[] = {9, 12, 15, 18, 22, 3, 5, 7};
    size_t n = sizeof a / sizeof a[0];
    printf("dondurme sayisi: %zu\n", dondurme_sayisi(a, n));
    int b[] = {1, 2, 3, 4, 5};
    printf("dondurme sayisi: %zu\n", dondurme_sayisi(b, 5));
    return 0;
}
