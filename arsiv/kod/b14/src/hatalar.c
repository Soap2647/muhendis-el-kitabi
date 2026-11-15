#include <stdio.h>

/* Hata 1: hi = n - 1 ve lo < hi. Son aralık hiç denenmez. */
int hatali_son(const int *a, int n, int x) {
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        int orta = (lo + hi) / 2;
        if (a[orta] < x)
            lo = orta + 1;
        else if (a[orta] > x)
            hi = orta - 1;
        else
            return orta;
    }
    return -1;
}

/* Hata 2: lo = orta (orta + 1 yerine). Komşuyken ilerlemez. */
int hatali_dongu(const int *a, int n, int x, int tur_siniri) {
    int lo = 0, hi = n - 1, tur = 0;
    while (lo < hi) {
        if (++tur > tur_siniri)
            return -2;           /* sonsuz döngü, sınırda kestik */
        int orta = (lo + hi) / 2;
        if (a[orta] < x)
            lo = orta;
        else
            hi = orta - 1;
    }
    return lo;
}

int main(void) {
    int a[] = {1, 3, 5};
    int b[] = {1, 3};
    printf("hata 1, x=5: %d (dogru: 2)\n", hatali_son(a, 3, 5));
    int r = hatali_dongu(b, 2, 2, 20);
    if (r == -2)
        printf("hata 2, x=2: 20 turda durduruldu (sonsuz)\n");
    else
        printf("hata 2, x=2: %d\n", r);
    return 0;
}
