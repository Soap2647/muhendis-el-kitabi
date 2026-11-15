/* bit_testleri.c - bit islemleri, bit-band adresi, tamsayi
 * yukseltme. WSL derleme:
 * gcc -O2 -Wall -Wextra -std=c11 -fsanitize=address,undefined */
#include <stdint.h>
#include <stdio.h>

#define BIT(n)         (1u << (n))
#define BIT_SET(r, n)  ((r) |= BIT(n))
#define BIT_CLR(r, n)  ((r) &= ~BIT(n))
#define BIT_TOG(r, n)  ((r) ^= BIT(n))
#define BIT_TEST(r, n) (((r) >> (n)) & 1u)

/* Bit-band takma adresi (ARMv7-M), cevre birimi bolgesi:
 *   alias = 0x42000000 + (adres - 0x40000000) * 32 + bit * 4 */
static uint32_t bitband_adres(uint32_t adres, unsigned bit)
{
    return 0x42000000u + (adres - 0x40000000u) * 32u + bit * 4u;
}

/* Model: once bayt ofsetinden toplam bit sayisi, sonra adres */
static uint32_t bitband_model(uint32_t adres, unsigned bit)
{
    uint32_t bayt_ofseti = adres - 0x40000000u;
    uint32_t bit_toplam = bayt_ofseti * 8u + bit;
    return 0x42000000u + bit_toplam * 4u;
}

/* Sabit tohumlu xorshift: her calistirmada ayni sayilar */
static uint32_t xorshift(uint32_t *s)
{
    uint32_t x = *s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *s = x;
    return x;
}

int main(void)
{
    /* 1. Bit islemleri: rastgele islemleri modelle karsilastir */
    uint32_t seed = 43u;
    uint32_t r = 0, model = 0;
    uint32_t hata = 0;
    for (int i = 0; i < 100000; i++) {
        uint32_t x = xorshift(&seed);
        unsigned n = x % 32u;
        switch ((x >> 8) % 3u) {
        case 0:
            BIT_SET(r, n);
            model |= (uint32_t)1 << n;
            break;
        case 1:
            BIT_CLR(r, n);
            model &= ~((uint32_t)1 << n);
            break;
        default:
            BIT_TOG(r, n);
            model ^= (uint32_t)1 << n;
            break;
        }
        if (r != model || BIT_TEST(r, n) != ((model >> n) & 1u)) {
            hata++;
        }
    }
    printf("bit islemleri: 100000 islem, hata = %u\n", hata);
    printf("son r = 0x%08X\n", r);

    /* 2. Bit-band: formul ve model ayni mi? */
    uint32_t adresler[3] = { 0x40020C14u, 0x40020000u, 0x40023830u };
    uint32_t uyusmazlik = 0;
    for (int k = 0; k < 3; k++) {
        for (unsigned b = 0; b < 32; b++) {
            if (bitband_adres(adresler[k], b) !=
                bitband_model(adresler[k], b)) {
                uyusmazlik++;
            }
        }
    }
    printf("bit-band: 96 kontrol, uyusmazlik = %u\n", uyusmazlik);
    printf("ODR bit 12 -> 0x%08X\n", bitband_adres(0x40020C14u, 12));
    printf("ODR bit 0  -> 0x%08X\n", bitband_adres(0x40020C14u, 0));

    /* 3. Tamsayi yukseltme: uint8_t toplamasi int'e yukselir */
    uint8_t a = 200, b = 100;
    int toplam = a + b;
    uint8_t sarmali = (uint8_t)(a + b);
    printf("uint8: a+b = %d, (uint8_t)(a+b) = %u\n", toplam, sarmali);
    if (a + b > 255) {
        printf("a+b > 255 DOGRU (int karsilastirmasi)\n");
    }
    return (hata != 0 || uyusmazlik != 0) ? 1 : 0;
}
