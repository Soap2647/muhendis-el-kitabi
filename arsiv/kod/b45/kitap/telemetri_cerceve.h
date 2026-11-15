/* telemetri_cerceve.h: EV telemetri cercevesi (surum+sira+yuk+CRC16).
 * Cerceve: COBS kodlu, sonunda 0x00. Toplam 21 bayt. */
#ifndef TELEMETRI_CERCEVE_H
#define TELEMETRI_CERCEVE_H
#include <stddef.h>
#include <stdint.h>

#define TEL_SURUM      1u
#define TEL_YUK_BOYU  15u

typedef struct {
    uint16_t spd;       /* km/h */
    uint8_t  bat;       /* % */
    uint16_t volt_x10;  /* 0.1 V birimi */
    uint16_t range;     /* km */
    int8_t   btemp;     /* C */
    int8_t   tmp;       /* C */
    uint16_t cell_mv;   /* mV */
    uint8_t  gear;      /* 'P' 'R' 'N' 'D' */
    uint8_t  sigL;
    uint8_t  sigR;
    uint8_t  beam;
} tel_yuk_t;

/* Yuku 15 bayt little-endian yazar (struct dolgusundan bagimsiz). */
void tel_yuk_yaz(const tel_yuk_t *y, uint8_t cikis[TEL_YUK_BOYU]);

/* Cerceveyi uretir. Donus: uzunluk (0x00 dahil) ya da -1. */
int tel_kodla(const tel_yuk_t *y, uint8_t sira,
              uint8_t *cikis, size_t kapasite);

#endif
