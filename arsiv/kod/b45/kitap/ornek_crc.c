/* ornek_crc.c: CRC-16/CCITT-FALSE denemesi. */
#include <stdio.h>
#include <string.h>
#include "crc16.h"

int main(void)
{
    const char *girdi[] = {"123456789", "", "A", "MertOS"};
    for (int i = 0; i < 4; i++) {
        size_t n = strlen(girdi[i]);
        uint16_t c = crc16_ccitt((const uint8_t *)girdi[i], n);
        printf("\"%s\" -> 0x%04X\n", girdi[i], c);
    }
    return 0;
}
