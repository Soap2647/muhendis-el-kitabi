#ifndef KAYIT_H
#define KAYIT_H
#include <stddef.h>

#define SIHIR 0x4B41u /* "KA" dosya basligi */

/* 0: basarili; negatif: hata kodu. Cikista *kayitlar free() edilmeli. */
int kayit_oku(const char *yol, double **kayitlar, size_t *adet);

#endif
