/* ringbuf.c - SPSC halka tamponu: kesme ile ana dongu arasinda */
#include "ringbuf.h"

int rb_yaz(rb_t *rb, uint8_t b)
{
    uint32_t kuyruk = rb->kuyruk;             /* kendi indeksimiz */
    uint32_t sonraki = (kuyruk + 1u) & RB_MASKE;

    if (sonraki == rb->bas) {                 /* tuketici bekliyor */
        rb->dusen++;                          /* dolu: olayi at */
        return 0;
    }
    rb->veri[kuyruk] = b;                     /* once veri yazilir */
    rb->kuyruk = sonraki;                     /* indeks yayinlanir */
    return 1;
}

int rb_oku(rb_t *rb, uint8_t *b)
{
    uint32_t bas = rb->bas;

    if (bas == rb->kuyruk) return 0;          /* bos */
    *b = rb->veri[bas];
    rb->bas = (bas + 1u) & RB_MASKE;
    return 1;
}

uint32_t rb_dolu(const rb_t *rb)
{
    return (rb->kuyruk - rb->bas) & RB_MASKE;
}
