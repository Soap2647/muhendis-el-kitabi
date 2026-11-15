/* q15_fir.h - 5 tap Q15 FIR, dairesel tampon ile */
#ifndef Q15_FIR_H
#define Q15_FIR_H
#include <stdint.h>

#define TAP 5

typedef struct {
    int16_t gecmis[TAP];   /* dairesel tampon: son TAP ornek */
    uint8_t bas;           /* en yeni ornegin indeksi */
} Fir;

void fir_sifirla(Fir *f);
int16_t fir_adim(Fir *f, int16_t x);

#endif
