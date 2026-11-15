/* dongu_deney2.c - uzunluk bilinmediginde kopyalama dongusu */
#include <stdint.h>

void kopya_n(uint8_t *h, const uint8_t *k, uint32_t n)
{
    for (uint32_t i = 0; i < n; i++) {
        h[i] = k[i];
    }
}

void sifirla_n(uint32_t *p, uint32_t n)
{
    for (uint32_t i = 0; i < n; i++) {
        p[i] = 0u;
    }
}
