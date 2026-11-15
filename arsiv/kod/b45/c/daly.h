/* daly.h: Daly BMS 13 bayt cerceve surucusu (donanimdan bagimsiz).
 * G/O fonksiyonlari disaridan verilir: test icin sahte, STM32 icin
 * HAL sarmalayicisi. Donus: 0 tamam, -1 zaman asimi, -2 bozuk. */
#ifndef DALY_H
#define DALY_H
#include <stdint.h>

typedef struct {
    void *ctx;
    int  (*gonder)(void *ctx, const uint8_t *v, uint32_t n);
    int  (*al_bayt)(void *ctx, uint8_t *b, uint32_t zaman_asimi_ms);
    void (*tampon_temizle)(void *ctx);
} daly_io_t;

int daly_sorgu(const daly_io_t *io, uint8_t komut, uint8_t cevap[13]);

#endif
