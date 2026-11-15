/* dongu_deney.c - kopyalama/sifirlama dongusu hangi formda memcpy olur? */
#include <stdint.h>
extern uint8_t _sidata_b[], _sdata_b[], _edata_b[];
extern uint8_t _sbss_b[], _ebss_b[];

/* A: indeks tabanli kopyalama dongusu */
void kopya_indeks(void)
{
    for (uint32_t i = 0; i < 256u; i++) {
        _sdata_b[i] = _sidata_b[i];
    }
}

/* B: bu programdaki gibi isaretci dongusu, sinir sembolden */
void kopya_isaretci(void)
{
    uint8_t *k = _sidata_b, *h = _sdata_b;
    while (h < _edata_b) {
        *h++ = *k++;
    }
}

/* C: bss sifirlama, indeks tabanli */
void sifirla_indeks(void)
{
    for (uint32_t i = 0; i < 256u; i++) {
        _sbss_b[i] = 0u;
    }
}
