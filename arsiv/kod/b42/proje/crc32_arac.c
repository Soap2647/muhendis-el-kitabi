/* crc32_arac.c: girdi baytlarının CRC-32 özeti (IEEE 802.3).
 * Bölüm 31'deki telemetri çerçevesinin CRC alanıyla aynı polinom.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 crc32_arac.c
 * Kullanım: ./crc32_arac < dosya */
#include <stdint.h>
#include <stdio.h>

static uint32_t tablo[256];

static void tablo_kur(void)
{
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t c = i;
        for (int k = 0; k < 8; k++)
            c = (c & 1u) ? 0xEDB88320u ^ (c >> 1) : c >> 1;
        tablo[i] = c;
    }
}

int main(void)
{
    tablo_kur();
    uint32_t crc = 0xFFFFFFFFu;
    int c;
    while ((c = getchar()) != EOF)
        crc = tablo[(crc ^ (uint32_t)c) & 0xFFu] ^ (crc >> 8);
    printf("%08x\n", crc ^ 0xFFFFFFFFu);
    return 0;
}
