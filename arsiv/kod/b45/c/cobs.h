/* cobs.h: COBS kodlayici / cozucu. Hata: -1 dondurur. */
#ifndef COBS_H
#define COBS_H
#include <stddef.h>
#include <stdint.h>

/* Girisi kodlar; cikis kapasitesi yetmezse -1. Donus: kod uzunlugu. */
int cobs_kodla(const uint8_t *giris, size_t n,
               uint8_t *cikis, size_t kapasite);

/* Kodlu veriyi cozer (sonlandirici 0x00 icermemeli). */
int cobs_coz(const uint8_t *kodlu, size_t n,
             uint8_t *cikis, size_t kapasite);

#endif
