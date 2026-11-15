/* crc16.h: CRC-16/CCITT-FALSE (poli 0x1021, ilk 0xFFFF). */
#ifndef CRC16_H
#define CRC16_H
#include <stddef.h>
#include <stdint.h>

uint16_t crc16_ccitt(const uint8_t *veri, size_t n);

#endif
