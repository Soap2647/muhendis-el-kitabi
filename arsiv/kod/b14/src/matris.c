#include <stddef.h>
#include <stdio.h>

/* Satır ve sütunları artan sıralı matris. Sağ üst köşeden yürünür:
   her adımda bir satır ya da sütun elenir: en fazla sat+sut adım. */
int matris_ara1(const int *m, size_t sat, size_t sut, int x,
                long *adim) {
    if (sat == 0 || sut == 0)
        return 0;
    size_t i = 0, j = sut - 1;
    while (i < sat) {
        (*adim)++;
        int v = m[i * sut + j];
        if (v == x)
            return 1;
        if (v > x) {
            if (j == 0)
                break;
            j--;                 /* bu sütun x'ten büyük: sola */
        } else {
            i++;                 /* bu satır x'ten küçük: aşağı */
        }
    }
    return 0;
}

/* Satırlar birbirini izler: matris düz bir dizi gibi aranır. */
int matris_ara2(const int *m, size_t sat, size_t sut, int x,
                long *adim) {
    (void)sut;                   /* satır-major: indeks doğrudan */
    size_t lo = 0, hi = sat * sut;
    while (lo < hi) {
        (*adim)++;
        size_t orta = lo + (hi - lo) / 2;
        if (m[orta] < x)
            lo = orta + 1;
        else if (m[orta] > x)
            hi = orta;
        else
            return 1;
    }
    return 0;
}

int main(void) {
    int a[4][5] = {
        {1, 4, 7, 11, 15},
        {2, 5, 8, 12, 19},
        {3, 6, 9, 16, 22},
        {10, 13, 14, 17, 24}};
    int sorgu[] = {5, 20, 1, 24, 0};
    for (int k = 0; k < 5; k++) {
        long adim = 0;
        int s = matris_ara1(&a[0][0], 4, 5, sorgu[k], &adim);
        printf("sirali x=%2d bulundu=%d adim=%ld\n",
               sorgu[k], s, adim);
    }
    int b[3][4] = {
        {1, 3, 5, 7},
        {10, 11, 16, 20},
        {23, 30, 34, 60}};
    int sorgu2[] = {34, 3, 35};
    for (int k = 0; k < 3; k++) {
        long adim = 0;
        int s = matris_ara2(&b[0][0], 3, 4, sorgu2[k], &adim);
        printf("duz    x=%2d bulundu=%d adim=%ld\n",
               sorgu2[k], s, adim);
    }
    return 0;
}
