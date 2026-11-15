/* daly.c: Daly BMS sorgusu; baslik, adres, komut, sagalama dogrular. */
#include "daly.h"

#define DALY_BASLIK   0xA5u
#define DALY_ADRES    0x01u     /* BMS yaniti (ESPHome'a gore) */
#define DALY_ZAMAN_MS 200u

static uint8_t topla8(const uint8_t *v, uint32_t n)
{
    uint8_t s = 0;
    for (uint32_t i = 0; i < n; i++)
        s = (uint8_t)(s + v[i]);
    return s;
}

int daly_sorgu(const daly_io_t *io, uint8_t komut, uint8_t cevap[13])
{
    uint8_t istek[13] = {DALY_BASLIK, 0x40, komut, 0x08};
    uint8_t b = 0;
    int bulundu = 0;

    istek[12] = topla8(istek, 12);
    io->tampon_temizle(io->ctx);            /* eski bayt kalmasin */
    if (io->gonder(io->ctx, istek, 13) != 0)
        return -1;

    /* Baslik baytini ara: gurultu/yarim cerceve bayt kaymasi yapabilir */
    for (int k = 0; k < 64 && !bulundu; k++) {
        if (io->al_bayt(io->ctx, &b, DALY_ZAMAN_MS) != 0)
            return -1;
        if (b == DALY_BASLIK)
            bulundu = 1;
    }
    if (!bulundu)
        return -2;
    cevap[0] = b;
    for (int i = 1; i < 13; i++)
        if (io->al_bayt(io->ctx, &cevap[i], DALY_ZAMAN_MS) != 0)
            return -1;

    if (cevap[1] != DALY_ADRES || cevap[2] != komut)
        return -2;
    if (topla8(cevap, 12) != cevap[12])
        return -2;
    return 0;
}
