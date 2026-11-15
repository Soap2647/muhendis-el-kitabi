/* izdogrula.c - 4 bloklu bir havuzda serbest liste izi.
 * Derleme: gcc -O1 -Wall -Wextra -std=c11 izdogrula.c -o izdogrula
 */
#include <stdio.h>
#include <stdlib.h>

#define BLOK 64
#define ADET 4

typedef struct {
    unsigned char *bellek;
    void *bos;                  /* serbest listenin basi */
    size_t kullanilan;
} Havuz;

static void havuz_kur(Havuz *h)
{
    h->bellek = malloc((size_t)ADET * BLOK);
    h->bos = NULL;
    h->kullanilan = 0;
    for (size_t i = ADET; i-- > 0; ) {
        void *b = h->bellek + i * BLOK;
        *(void **)b = h->bos;
        h->bos = b;
    }
}

static void *havuz_ayir(Havuz *h)
{
    void *b = h->bos;
    if (!b) return NULL;
    h->bos = *(void **)b;
    h->kullanilan++;
    return b;
}

static int havuz_birak(Havuz *h, void *p)
{
    *(void **)p = h->bos;       /* sinir/cift birakma kontrolu yok */
    h->bos = p;
    h->kullanilan--;
    return 1;
}

static int blok_no(Havuz *h, void *p)
{
    if (!p) return -1;
    return (int)(((unsigned char *)p - h->bellek) / BLOK);
}

static void yaz(Havuz *h, const char *ad, void *p)
{
    printf("%-14s blok=%2d  bos_bas=%2d\n",
           ad, blok_no(h, p), blok_no(h, h->bos));
}

int main(void)
{
    Havuz h;
    havuz_kur(&h);
    void *b0 = havuz_ayir(&h); yaz(&h, "ayir", b0);
    void *b1 = havuz_ayir(&h); yaz(&h, "ayir", b1);
    havuz_birak(&h, b0); yaz(&h, "birak(B0)", b0);
    void *c = havuz_ayir(&h); yaz(&h, "ayir", c);
    havuz_birak(&h, b1); yaz(&h, "birak(B1)", b1);
    void *d = havuz_ayir(&h); yaz(&h, "ayir", d);
    void *e = havuz_ayir(&h); yaz(&h, "ayir", e);
    void *f = havuz_ayir(&h); yaz(&h, "ayir", f);
    void *g = havuz_ayir(&h); yaz(&h, "ayir (bos)", g);
    havuz_birak(&h, e); yaz(&h, "birak(B2)", e);
    havuz_birak(&h, e); yaz(&h, "birak(B2) 2.", e);
    void *x = havuz_ayir(&h); yaz(&h, "ayir", x);
    void *y = havuz_ayir(&h); yaz(&h, "ayir", y);
    printf("ayni blok iki kez verildi mi? %s\n",
           x == y ? "EVET" : "hayir");
    free(h.bellek);
    return 0;
}
