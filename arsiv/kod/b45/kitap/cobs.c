/* cobs.c: Consistent Overhead Byte Stuffing. */
#include "cobs.h"

int cobs_kodla(const uint8_t *giris, size_t n,
               uint8_t *cikis, size_t kapasite)
{
    size_t w = 0;          /* yazma konumu */
    size_t kod_yeri = 0;   /* kod baytinin konumu */
    uint8_t kod = 1;
    if (kapasite < 1)
        return -1;
    w = 1;
    for (size_t i = 0; i < n; i++) {
        if (giris[i] == 0) {
            cikis[kod_yeri] = kod;
            kod_yeri = w;
            kod = 1;
        } else {
            if (w >= kapasite)
                return -1;
            cikis[w++] = giris[i];
            kod++;
            if (kod == 0xFF) {       /* 254 veri baytı: blok biter */
                cikis[kod_yeri] = kod;
                kod_yeri = w;
                kod = 1;
                if (w >= kapasite)
                    return -1;
                w++;
            }
            continue;
        }
        /* sifirda: kod yeri icin yer ayir */
        if (w >= kapasite)
            return -1;
        w++;
    }
    if (kod_yeri >= kapasite)
        return -1;
    cikis[kod_yeri] = kod;
    return (int)w;
}

int cobs_coz(const uint8_t *kodlu, size_t n,
             uint8_t *cikis, size_t kapasite)
{
    size_t i = 0, w = 0;
    while (i < n) {
        uint8_t kod = kodlu[i++];
        if (kod == 0)
            return -1;
        if (i + (size_t)kod - 1 > n)
            return -1;
        for (uint8_t k = 1; k < kod; k++) {
            if (w >= kapasite)
                return -1;
            cikis[w++] = kodlu[i++];
        }
        if (kod != 0xFF && i < n) {
            if (w >= kapasite)
                return -1;
            cikis[w++] = 0;
        }
    }
    return (int)w;
}
