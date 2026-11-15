#define _POSIX_C_SOURCE 199309L
/* kovalama.c - isaretci kovalama ile onbellek basamaklari.
 * Her dugum bir onbellek satiri (64 bayt) boyutundadir ve bir
 * sonraki dugumun adresini tutar. Dugumler rastgele bir sirada
 * dizilir; her yukleme bir oncekinin sonucuna bagimlidir, bu
 * yuzden islemci yukleri paralel calistiramaz.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 kovalama.c -o kovalama
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

#define SATIR 64                 /* onbellek satir boyu */
#define ADIM (1u << 22)          /* olcum icin yukleme sayisi */
#define DENEME 5                 /* medyan icin deneme sayisi */

static uint64_t tohum = 88172645463325252ULL;   /* sabit tohum */

static uint64_t rastgele(void)                  /* xorshift64 */
{
    tohum ^= tohum << 13;
    tohum ^= tohum >> 7;
    tohum ^= tohum << 17;
    return tohum;
}

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + (double)t.tv_nsec;
}

static void *cikis;              /* derleyici donguyu silmesin diye */

static int karsilastir(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

/* Bir boyut icin ns/erisim degerinin medyanini dondurur. */
static double olc(size_t boyut)
{
    size_t n = boyut / SATIR;
    char *bolge = aligned_alloc(SATIR, n * SATIR);
    size_t *sira = malloc(n * sizeof *sira);
    if (!bolge || !sira) { perror("malloc"); exit(1); }

    for (size_t i = 0; i < n; i++) sira[i] = i;
    /* Sattolo karistirmasi: tek dongu uretir */
    for (size_t i = n - 1; i > 0; i--) {
        size_t j = rastgele() % i;
        size_t t = sira[i]; sira[i] = sira[j]; sira[j] = t;
    }
    for (size_t k = 0; k < n; k++) {             /* tek bir dongu */
        void **d = (void **)(bolge + sira[k] * SATIR);
        *d = bolge + sira[(k + 1) % n] * SATIR;
    }

    double sonuc[DENEME];
    for (int r = 0; r < DENEME; r++) {
        void *q = bolge + sira[0] * SATIR;
        double t0 = simdi_ns();
        for (size_t s = 0; s < ADIM; s++)
            q = *(void *volatile *)q;
        double t1 = simdi_ns();
        cikis = q;
        sonuc[r] = (t1 - t0) / ADIM;
    }
    qsort(sonuc, DENEME, sizeof sonuc[0], karsilastir);
    free(bolge);
    free(sira);
    return sonuc[DENEME / 2];
}

int main(void)
{
    printf("boyut_bayt,ns_erisim\n");
    for (unsigned k = 12; k <= 28; k++) {
        size_t boyutlar[2] = { (size_t)1 << k,
                               3 * ((size_t)1 << (k - 1)) };
        for (int i = 0; i < 2; i++) {
            if (k == 28 && i == 1) continue;      /* 384 MB'a cikma */
            printf("%zu,%.3f\n", boyutlar[i], olc(boyutlar[i]));
            fflush(stdout);
        }
    }
    return 0;
}
