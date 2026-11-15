/* tlb.c - TLB etkisini, onbellek yukunu sabit tutarak olcmek.
 * Uc duzen, ayni sayida dugum (16384) ve ayni rastgele dongu:
 *   sikli  : dugumler 1 MB'lik bolgede (256 sayfa)
 *   seyrek : her dugum ayri sayfada (16384 sayfa, 64 MB)
 *   buyuk  : seyrek ile ayni, ama 2 MB huge page uzerinde
 * Uc duzende de 16384 onbellek satiri kullanilir; fark TLB'den gelir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 tlb.c -o tlb
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/resource.h>

#define DUGUM 16384
#define ADIM (1u << 21)
#define DENEME 5
#define SAYFA 4096
#define IKI_MB (2u << 20)
#define BOYUT (64u << 20)

static uint64_t tohum = 88172645463325252ULL;

static uint64_t rastgele(void)
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

static long kucuk_hata(void)
{
    struct rusage u;
    getrusage(RUSAGE_SELF, &u);
    return u.ru_minflt;
}

static void *cikis;

/* Dugum p'nin bolge icindeki ofseti. */
static size_t yer(size_t p, int sayfali)
{
    if (!sayfali) return p * 64;                     /* sikli */
    return p * SAYFA + ((p >> 8) & 63) * 64;        /* seyrek */
}

static int karsilastir(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static double olc(char *bolge, int sayfali, long *hata)
{
    size_t *ord = malloc(DUGUM * sizeof *ord);
    for (size_t i = 0; i < DUGUM; i++) ord[i] = i;
    for (size_t i = DUGUM - 1; i > 0; i--) {         /* Sattolo */
        size_t j = rastgele() % i;
        size_t t = ord[i]; ord[i] = ord[j]; ord[j] = t;
    }
    long h0 = kucuk_hata();
    for (size_t k = 0; k < DUGUM; k++) {
        void **d = (void **)(bolge + yer(ord[k], sayfali));
        *d = bolge + yer(ord[(k + 1) % DUGUM], sayfali);
    }
    *hata = kucuk_hata() - h0;

    double sonuc[DENEME];
    for (int r = 0; r < DENEME; r++) {
        void *q = bolge + yer(ord[0], sayfali);
        double t0 = simdi_ns();
        for (size_t s = 0; s < ADIM; s++)
            q = *(void *volatile *)q;
        double t1 = simdi_ns();
        cikis = q;
        sonuc[r] = (t1 - t0) / ADIM;
    }
    qsort(sonuc, DENEME, sizeof sonuc[0], karsilastir);
    free(ord);
    return sonuc[DENEME / 2];
}

static void huge_bilgi(void)
{
    FILE *f = fopen("/proc/self/smaps_rollup", "r");
    char satir[256];
    if (!f) return;
    while (fgets(satir, sizeof satir, f))
        if (strncmp(satir, "AnonHugePages", 13) == 0)
            printf("  %s", satir);
    fclose(f);
}

int main(void)
{
    char *sikli = aligned_alloc(SAYFA, 1u << 20);
    char *seyrek = aligned_alloc(SAYFA, BOYUT);
    char *buyuk = aligned_alloc(IKI_MB, BOYUT);
    if (!sikli || !seyrek || !buyuk) { perror("alloc"); return 1; }
    madvise(buyuk, BOYUT, MADV_HUGEPAGE);   /* THP: 2 MB sayfa iste */

    long h1, h2, h3;
    double n1 = olc(sikli, 0, &h1);
    double n2 = olc(seyrek, 1, &h2);
    double n3 = olc(buyuk, 1, &h3);

    printf("duzen    sayfa  ns/erisim  kucuk_hata\n");
    printf("sikli      256 %9.2f %10ld\n", n1, h1);
    printf("seyrek   16384 %9.2f %10ld\n", n2, h2);
    printf("buyuk       32 %9.2f %10ld\n", n3, h3);
    printf("buyuk icin /proc/self/smaps_rollup:\n");
    huge_bilgi();
    free(sikli); free(seyrek); free(buyuk);
    return 0;
}
