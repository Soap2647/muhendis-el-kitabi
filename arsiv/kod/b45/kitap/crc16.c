/* crc16.c: bit bit (tablosuz) CRC-16/CCITT-FALSE. */
#include "crc16.h"

uint16_t crc16_ccitt(const uint8_t *veri, size_t n)
{
    uint16_t crc = 0xFFFFu;
    for (size_t i = 0; i < n; i++) {
        crc ^= (uint16_t)((uint16_t)veri[i] << 8);
        for (int k = 0; k < 8; k++) {
            if (crc & 0x8000u)
                crc = (uint16_t)((crc << 1) ^ 0x1021u);
            else
                crc = (uint16_t)(crc << 1);
        }
    }
    return crc;
}
