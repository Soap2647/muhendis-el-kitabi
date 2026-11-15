#define _POSIX_C_SOURCE 199309L
/* catisma.c - ayni kumeye dusen satirlarin catisma kaybi.
 * K dugum, adim kadar aralikla dizilir ve bir halka olusturur:
 * her dugum sonrakini gosterir. Adim 4096 bayt ise tum dugumler
 * ayni L1 kumesine duser; L1 8 yol oldugu icin K > 8 olunca
 * halkanin her turu L1'den kacar. Adim 4160 (4096 + 64) dugumleri
 * kumelere dagitir ve catisma olusmaz.
 * Erisimler birbirine bagimli oldugu icin olculen sure gecikmedir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 catisma.c -o catisma
 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define ADIM_SAYI (1u << 22)     /* her olcumde toplam yukleme */
#define DENEME 5

static void *cikis;

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + (double)t.tv_nsec;
}

static int karsilastir(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static double olc(char *bolge, size_t adim, size_t k)
{
    for (size_t j = 0; j < k; j++) {        /* halka kur */
        void **d = (void **)(bolge + j * adim);
        *d = bolge + ((j + 1) % k) * adim;
    }
    double sonuc[DENEME];
    for (int r = 0; r < DENEME; r++) {
        void *q = bolge;
        double t0 = simdi_ns();
        for (unsigned s = 0; s < ADIM_SAYI; s++)
            q = *(void *volatile *)q;
        double t1 = simdi_ns();
        cikis = q;
        sonuc[r] = (t1 - t0) / ADIM_SAYI;
    }
    qsort(sonuc, DENEME, sizeof sonuc[0], karsilastir);
    return sonuc[DENEME / 2];
}

int main(void)
{
    char *bolge = aligned_alloc(4096, 1u << 20);
    if (!bolge) { perror("malloc"); return 1; }
    size_t adimler[3] = { 64, 4096, 4160 };
    size_t kler[3] = { 8, 9, 16 };
    printf("adim_bayt,satir_sayisi,ns_erisim\n");
    for (int a = 0; a < 3; a++)
        for (int b = 0; b < 3; b++)
            printf("%zu,%zu,%.3f\n", adimler[a], kler[b],
                   olc(bolge, adimler[a], kler[b]));
    free(bolge);
    return 0;
}
