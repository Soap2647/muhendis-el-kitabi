/* q15_test.c - host testi: Q15 cekirdegi ve float referans */
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include "q15_fir.h"

static const float BF[TAP] = {0.010087f, 0.220341f, 0.539144f,
                              0.220341f, 0.010087f};
static const float BQ[TAP] = {331/32768.f, 7220/32768.f,
                              17667/32768.f,
                              7220/32768.f, 331/32768.f};

int main(void)
{
    enum { N = 2000 };
    static int16_t x[N];
    static int16_t y[N];
    uint32_t s = 52;                    /* sabit tohum (LCG) */
    for (int n = 0; n < N; n++) {
        s = s * 1664525u + 1013904223u;
        x[n] = (int16_t)((int32_t)(s >> 16) - 32768);
    }

    Fir f;
    fir_sifirla(&f);
    for (int n = 0; n < N; n++)
        y[n] = fir_adim(&f, x[n]);

    double e_q = 0.0, e_f = 0.0;
    for (int n = TAP - 1; n < N; n++) {
        float r_q = 0.f, r_f = 0.f;
        for (int k = 0; k < TAP; k++) {
            r_q += BQ[k] * x[n - k];    /* Q15 katsayili referans */
            r_f += BF[k] * x[n - k];    /* kesin katsayili referans */
        }
        double dq = fabs(y[n] - r_q), df = fabs(y[n] - r_f);
        if (dq > e_q) e_q = dq;
        if (df > e_f) e_f = df;
    }
    printf("ilk 6 cikti: ");
    for (int n = 0; n < 6; n++) printf("%d ", y[n]);
    printf("\nmax |Q15 - (Q15 katsayi float)| = %.2f LSB\n", e_q);
    printf("max |Q15 - (kesin float)|       = %.2f LSB\n", e_f);

    /* sinir: tam olcekli DC giris */
    fir_sifirla(&f);
    int16_t son = 0;
    for (int n = 0; n < 10; n++)
        son = fir_adim(&f, 32767);
    printf("DC 32767 girisi, cikis = %d\n", son);
    return 0;
}
