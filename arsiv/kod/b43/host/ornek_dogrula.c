/* ornek_dogrula.c - bolum orneklerindeki sayilari dogrular */
#include <stdint.h>
#include <stdio.h>

static void yaz_modeller(uint32_t m)
{
    for (int p = 15; p >= 12; p--) {
        printf("pin%d=%u%u ", p, (m >> (2 * p + 1)) & 1u,
               (m >> (2 * p)) & 1u);
    }
    printf("| 0x%08X\n", m);
}

static uint32_t bitband(uint32_t taban, uint32_t bolge, unsigned b)
{
    return taban + (bolge - 0x40000000u) * 32u + b * 4u;
}

int main(void)
{
    /* Ornek 1: MODER pin 12'yi 10 -> 01 yap, digerlerine dokunma */
    uint32_t m = 0x26000000u;
    printf("ilk:  "); yaz_modeller(m);
    m &= ~(3u << 24);
    printf("temizle:  "); yaz_modeller(m);
    m |= (1u << 24);
    printf("set:  "); yaz_modeller(m);

    /* Ornek 2: bit-band takma adresleri */
    printf("SRAM 0x20000004 bit3 -> 0x%08X\n",
           0x22000000u + (0x20000004u - 0x20000000u) * 32u + 3u * 4u);
    printf("ODR bit 31 -> 0x%08X\n",
           bitband(0x42000000u, 0x40020C14u, 31u));
    printf("ODR bit 0  -> 0x%08X\n",
           bitband(0x42000000u, 0x40020C14u, 0u));
    return 0;
}
