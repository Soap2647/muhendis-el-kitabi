#define _POSIX_C_SOURCE 199309L
/* ayirici.c - sabit boyutlu blok havuzu (pool) ayirici.
 * Serbest bloklar, bloklarin ICINDE tutulan bir bagli listede durur:
 * bos bir blogun ilk 8 bayti bir sonraki bos blogun adresidir.
 * Derleme : gcc -O2 -Wall -Wextra -std=c11 ayirici.c -o ayirici
 * ASan ile: gcc -O1 -g -fsanitize=address,undefined ayirici.c
 * Kullanim: ./ayirici test  |  ./ayirici olc
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define BLOK 64              /* blok boyu; en az sizeof(void *) */
#define ADET 4096            /* havuzdaki blok sayisi */

typedef struct {
    unsigned char *bellek;   /* ADET * BLOK bayt, tek parca */
    void *bos;               /* serbest listenin basi */
    size_t kullanilan;
} Havuz;

static int havuz_kur(Havuz *h)
{
    h->bellek = malloc((size_t)ADET * BLOK);
    if (!h->bellek) return 0;
    h->bos = NULL;
    h->kullanilan = 0;
    /* tersten doldur: 0. blok listenin basinda olsun */
    for (size_t i = ADET; i-- > 0; ) {
        void *b = h->bellek + i * BLOK;
        *(void **)b = h->bos;
        h->bos = b;
    }
    return 1;
}

static void *havuz_ayir(Havuz *h)
{
    void *b = h->bos;
    if (!b) return NULL;                 /* havuz dolu */
    h->bos = *(void **)b;
    h->kullanilan++;
    return b;
}

static int havuz_birak(Havuz *h, void *p)
{
    uintptr_t adr = (uintptr_t)p;
    uintptr_t taban = (uintptr_t)h->bellek;
    if (adr < taban || adr >= taban + (uintptr_t)ADET * BLOK)
        return 0;                        /* bu havuza ait degil */
    if ((adr - taban) % BLOK != 0)
        return 0;                        /* blok sinirinda degil */
    *(void **)p = h->bos;
    h->bos = p;
    h->kullanilan--;
    return 1;
}

static uint32_t tohum = 2463534242u;     /* xorshift32, sabit tohum */

static uint32_t rastgele(void)
{
    tohum ^= tohum << 13;
    tohum ^= tohum >> 17;
    tohum ^= tohum << 5;
    return tohum;
}

static int test(void)
{
    Havuz h;
    if (!havuz_kur(&h)) return 1;
    static void *canli[ADET];
    static unsigned char desen[ADET];
    size_t n = 0, en_fazla = 0;
    const long ADIM = 2000000;

    for (long adim = 0; adim < ADIM; adim++) {
        if (n < ADET && (n == 0 || rastgele() % 2 == 0)) {
            void *p = havuz_ayir(&h);
            if (!p) {
                printf("HATA: bos blok yok, n=%zu\n", n);
                return 1;
            }
            unsigned char d = (unsigned char)rastgele();
            memset(p, d, BLOK);
            canli[n] = p;
            desen[n] = d;
            n++;
            if (n > en_fazla) en_fazla = n;
        } else {
            size_t k = rastgele() % n;
            unsigned char *c = canli[k];
            for (size_t i = sizeof(void *); i < BLOK; i++)
                if (c[i] != desen[k]) {
                    printf("HATA: blok bozuldu, adim=%ld\n", adim);
                    return 1;
                }
            if (!havuz_birak(&h, c)) {
                printf("HATA: birakma reddedildi, adim=%ld\n", adim);
                return 1;
            }
            canli[k] = canli[n - 1];
            desen[k] = desen[n - 1];
            n--;
        }
        if (h.kullanilan != n) {
            printf("HATA: sayim uyusmuyor, adim=%ld\n", adim);
            return 1;
        }
    }
    /* listeyi say: serbest blok sayisi ADET - n olmali */
    size_t bos = 0;
    for (void *b = h.bos; b; b = *(void **)b) bos++;
    if (bos != ADET - n) { printf("HATA: liste bozuk\n"); return 1; }
    printf("test gecti: %ld adim, en fazla dolu blok = %zu\n",
           ADIM, en_fazla);
    free(h.bellek);
    return 0;
}

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + (double)t.tv_nsec;
}

/* Ayni is yukunu havuzla ve malloc ile yapip ns/islem dondurur. */
static double olc(int havuz_mi)
{
    static void *canli[ADET];
    const long ISLEM = 10000000;
    Havuz h;
    if (havuz_mi && !havuz_kur(&h)) return -1;
    tohum = 2463534242u;
    size_t n = 0;
    double t0 = simdi_ns();
    for (long i = 0; i < ISLEM; i++) {
        if (n < ADET && (n == 0 || rastgele() % 2 == 0)) {
            canli[n++] = havuz_mi ? havuz_ayir(&h) : malloc(BLOK);
        } else {
            size_t k = rastgele() % n;
            if (havuz_mi) havuz_birak(&h, canli[k]);
            else free(canli[k]);
            canli[k] = canli[--n];
        }
    }
    double t1 = simdi_ns();
    for (size_t k = 0; k < n; k++) {     /* temizlik */
        if (havuz_mi) havuz_birak(&h, canli[k]);
        else free(canli[k]);
    }
    if (havuz_mi) free(h.bellek);
    return (t1 - t0) / ISLEM;
}

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "test") == 0)
        return test();
    if (argc == 2 && strcmp(argv[1], "olc") == 0) {
        printf("havuz : %6.2f ns/islem\n", olc(1));
        printf("malloc: %6.2f ns/islem\n", olc(0));
        return 0;
    }
    fprintf(stderr, "kullanim: %s test | olc\n", argv[0]);
    return 1;
}
