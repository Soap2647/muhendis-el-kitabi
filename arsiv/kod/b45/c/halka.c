/* halka.c: SPSC halka tampon (Bolum 27 ve 44 ile ayni fikir). */
#include "halka.h"

void halka_sifirla(halka_t *h)
{
    h->bas = 0;
    h->son = 0;
}

int halka_yaz(halka_t *h, uint8_t b)
{
    uint32_t son = h->son;
    if (son - h->bas >= HALKA_KAPASITE)     /* dolu */
        return -1;
    h->veri[son & (HALKA_KAPASITE - 1u)] = b;
    h->son = son + 1u;                      /* veriden sonra yayin */
    return 0;
}

int halka_oku(halka_t *h, uint8_t *b)
{
    uint32_t bas = h->bas;
    if (h->son == bas)                      /* bos */
        return -1;
    *b = h->veri[bas & (HALKA_KAPASITE - 1u)];
    h->bas = bas + 1u;
    return 0;
}
