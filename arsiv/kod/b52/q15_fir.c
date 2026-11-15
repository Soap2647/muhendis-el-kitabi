/* q15_fir.c - Q15 FIR cekirdegi (libc gerektirmez) */
#include "q15_fir.h"

/* Q15 katsayilari: round(b * 2^15), katsayi_q15.py ile uretildi */
static const int16_t B[TAP] = {331, 7220, 17667, 7220, 331};

void fir_sifirla(Fir *f)
{
    for (int i = 0; i < TAP; i++)
        f->gecmis[i] = 0;
    f->bas = 0;
}

int16_t fir_adim(Fir *f, int16_t x)
{
    /* yeni ornek: baslangic indeksini bir geri al (sarmali), yaz */
    f->bas = (f->bas == 0) ? (uint8_t)(TAP - 1)
                           : (uint8_t)(f->bas - 1);
    f->gecmis[f->bas] = x;

    /* y = sum B[k] * x[n-k]; x[n-k] konumu (bas + k) mod TAP */
    int64_t acc = 0;
    uint8_t i = f->bas;
    for (int k = 0; k < TAP; k++) {
        acc += (int64_t)B[k] * f->gecmis[i];   /* Q30 birikim */
        i = (uint8_t)(i + 1);
        if (i == TAP) i = 0;                   /* mod yerine dal */
    }
    /* Q30 -> Q15: 15 bit saga kaydir, yuvarla, doyur */
    int64_t y = (acc + (1 << 14)) >> 15;
    if (y > 32767) return 32767;
    if (y < -32768) return -32768;
    return (int16_t)y;
}
