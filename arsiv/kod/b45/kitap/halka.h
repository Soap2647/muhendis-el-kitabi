/* halka.h: tek uretici (ISR) - tek tuketici (ana dongu) halka tampon.
 * Kapasite 2'nin kuvveti olmali. Dizinler (bas, son) tek yazilir. */
#ifndef HALKA_H
#define HALKA_H
#include <stdint.h>

#define HALKA_KAPASITE 64u          /* 2^n olmali */

typedef struct {
    volatile uint32_t bas;          /* tuketici yazar */
    volatile uint32_t son;          /* uretici yazar */
    uint8_t veri[HALKA_KAPASITE];
} halka_t;

void halka_sifirla(halka_t *h);
int  halka_yaz(halka_t *h, uint8_t b);   /* 0: tamam, -1: dolu */
int  halka_oku(halka_t *h, uint8_t *b);  /* 0: tamam, -1: bos */

#endif
