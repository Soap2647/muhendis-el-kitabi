/* telemetri_cerceve.c: cerceve kodlayici (STM32 tarafi). */
#include "telemetri_cerceve.h"
#include "cobs.h"
#include "crc16.h"

void tel_yuk_yaz(const tel_yuk_t *y, uint8_t b[TEL_YUK_BOYU])
{
    b[0]  = (uint8_t)(y->spd & 0xFF);
    b[1]  = (uint8_t)(y->spd >> 8);
    b[2]  = y->bat;
    b[3]  = (uint8_t)(y->volt_x10 & 0xFF);
    b[4]  = (uint8_t)(y->volt_x10 >> 8);
    b[5]  = (uint8_t)(y->range & 0xFF);
    b[6]  = (uint8_t)(y->range >> 8);
    b[7]  = (uint8_t)y->btemp;        /* int8 -> bit deseni */
    b[8]  = (uint8_t)y->tmp;
    b[9]  = (uint8_t)(y->cell_mv & 0xFF);
    b[10] = (uint8_t)(y->cell_mv >> 8);
    b[11] = y->gear;
    b[12] = y->sigL;
    b[13] = y->sigR;
    b[14] = y->beam;
}

int tel_kodla(const tel_yuk_t *y, uint8_t sira,
              uint8_t *cikis, size_t kapasite)
{
    uint8_t ham[2 + TEL_YUK_BOYU + 2];      /* 19 bayt */
    uint8_t kod[sizeof ham + 2];            /* COBS icin pay */
    uint16_t crc;
    int n;

    ham[0] = TEL_SURUM;
    ham[1] = sira;
    tel_yuk_yaz(y, &ham[2]);
    crc = crc16_ccitt(ham, 2 + TEL_YUK_BOYU);
    ham[17] = (uint8_t)(crc >> 8);          /* CRC: big-endian */
    ham[18] = (uint8_t)(crc & 0xFF);

    n = cobs_kodla(ham, sizeof ham, kod, sizeof kod);
    if (n < 0 || (size_t)n + 1 > kapasite)
        return -1;
    for (int i = 0; i < n; i++)
        cikis[i] = kod[i];
    cikis[n] = 0x00;
    return n + 1;
}
