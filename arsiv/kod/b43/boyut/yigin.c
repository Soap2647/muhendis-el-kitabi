/* yigin.c - -fstack-usage ciktisini gormek icin */
#include <stdint.h>

volatile uint32_t cikti;

/* 64 baytlik yerel tampon: yiginda ayrilir */
uint32_t ic_fonk(uint32_t x)
{
    volatile uint8_t tampon[64];
    for (uint32_t i = 0; i < 64u; i++) {
        tampon[i] = (uint8_t)(x + i);
    }
    return tampon[x & 63u];
}

uint32_t orta(uint32_t x)
{
    return ic_fonk(x) + ic_fonk(x + 1u);
}

uint32_t dis(uint32_t x)
{
    return orta(x) ^ 0xA5u;
}

int main(void)
{
    cikti = dis(7u);
    return 0;
}
