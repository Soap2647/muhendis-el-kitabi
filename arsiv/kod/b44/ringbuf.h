/* ringbuf.h - tek uretici / tek tuketici (SPSC) halka tamponu */
#ifndef RINGBUF_H
#define RINGBUF_H
#include <stdint.h>

/* Kapasite 2'nin kuvveti olmali: indeksler maskeyle sarar */
#define RB_KAPASITE 16u
#define RB_MASKE    (RB_KAPASITE - 1u)

typedef struct {
    volatile uint32_t bas;       /* tuketici yazar */
    volatile uint32_t kuyruk;    /* uretici yazar */
    volatile uint8_t  veri[RB_KAPASITE];
    volatile uint32_t dusen;     /* dolu iken atilan olay sayisi */
} rb_t;

/* Uretici (ISR): dolu ise olayi dusurur ve sayar. 1 = basarili */
int rb_yaz(rb_t *rb, uint8_t b);

/* Tuketici (ana dongu): bos ise 0 doner */
int rb_oku(rb_t *rb, uint8_t *b);

/* Tuketici icin: su an kac eleman var */
uint32_t rb_dolu(const rb_t *rb);

#endif
