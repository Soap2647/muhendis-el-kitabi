/* volatile_deney.c - derleyici hangi bellek erisimlerini siler? */
#include <stdint.h>

#define DURUM_REG (*(volatile uint32_t *)0x40020010u)

/* 1: volatile yok, bos dongu */
void gecikme_normal(void)
{
    for (uint32_t i = 0; i < 100000u; i++) {
    }
}

/* 2: sayac volatile */
void gecikme_vol(void)
{
    for (volatile uint32_t i = 0; i < 100000u; i++) {
    }
}

/* 3: parametre volatile */
void gecikme_param(volatile uint32_t n)
{
    while (n != 0u) {
        n--;
    }
}

/* 4: yoklama, volatile yok */
void bekle_normal(void)
{
    while (*(uint32_t *)0x40020010u == 0u) {
    }
}

/* 5: yoklama, volatile erisim */
void bekle_vol(void)
{
    while (DURUM_REG == 0u) {
    }
}

/* 6: sonsuz dongu, global sayac, volatile yok */
uint32_t global_sayac;
void sonsuz_normal(void)
{
    while (1) {
        global_sayac++;
    }
}

/* 7: ayni dongu, global volatile */
volatile uint32_t global_vol;
void sonsuz_vol(void)
{
    while (1) {
        global_vol++;
    }
}

/* 8: inline edilen volatile parametre */
static void gecikme_satir(volatile uint32_t n)
{
    while (n != 0u) {
        n--;
    }
}

void bekle_satir(void)
{
    gecikme_satir(100000u);
}
