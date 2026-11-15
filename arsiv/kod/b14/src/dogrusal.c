#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

/* Klasik doğrusal arama. cmp: karşılaştırma sayacı. */
long dogrusal(const int *a, size_t n, int x, long *cmp) {
    for (size_t i = 0; i < n; i++) {
        *cmp += 2;               /* i < n ve a[i] == x */
        if (a[i] == x)
            return (long)i;
    }
    *cmp += 1;                   /* son, başarısız i < n kontrolü */
    return -1;
}

/* Nöbetçili arama: a[n] hücresi x'i tutar; döngüde sınır
   denetimi yok. */
long nobetci(int *a, size_t n, int x, long *cmp) {
    int eski = a[n];
    size_t i = 0;
    a[n] = x;
    while (a[i] != x) {
        *cmp += 1;               /* doğru olan her tur için */
        i++;
    }
    *cmp += 1;                   /* son, yanlış kontrol */
    a[n] = eski;
    return (i < n) ? (long)i : -1;
}

int main(void) {
    size_t n = 1000;
    int *a = malloc((n + 1) * sizeof *a);
    if (a == NULL)
        return 1;
    for (size_t i = 0; i < n; i++)
        a[i] = 2 * (int)i;
    a[n] = 0;                    /* nöbetçi hücresinin ilk değeri */
    int hedef[] = {1000, 1001, 0};
    for (int k = 0; k < 3; k++) {
        long c1 = 0, c2 = 0;
        long r1 = dogrusal(a, n, hedef[k], &c1);
        long r2 = nobetci(a, n, hedef[k], &c2);
        printf("x=%5d klasik: konum=%4ld cmp=%5ld\n",
               hedef[k], r1, c1);
        printf("        nobetci: konum=%4ld cmp=%5ld\n", r2, c2);
    }
    free(a);
    return 0;
}
