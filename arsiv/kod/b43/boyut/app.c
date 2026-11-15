/* app.c - boyut olcumu icin ornek uygulama */
#include <stdint.h>

const uint8_t kademe[4] = { 25u, 50u, 75u, 100u };
volatile uint32_t sonuc;

uint32_t menzil_hesapla(uint8_t batarya)
{
    return ((uint32_t)batarya * 165u) / 100u;
}

/* Kullanilmayan yardimci: --gc-sections bunu atabilir */
uint32_t crc_yardimci(const uint8_t *v, uint32_t n)
{
    uint32_t c = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < n; i++) {
        c ^= v[i];
        for (int k = 0; k < 8; k++) {
            c = (c & 1u) ? (c >> 1) ^ 0xEDB88320u : (c >> 1);
        }
    }
    return ~c;
}

/* Kullanilmayan tablo: o da atilabilir */
const uint32_t tablo[8] = {
    0x11111111u, 0x22222222u, 0x33333333u, 0x44444444u,
    0x55555555u, 0x66666666u, 0x77777777u, 0x88888888u,
};

uint32_t tablo_topla(void)
{
    uint32_t t = 0;
    for (uint32_t i = 0; i < 8; i++) {
        t += tablo[i];
    }
    return t;
}

int main(void)
{
    sonuc = menzil_hesapla(kademe[1]);
    return (int)sonuc;
}
