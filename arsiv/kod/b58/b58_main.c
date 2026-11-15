/* b58_main.c: test kumesinde float ve int8 modelleri calistirir. */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include "b58_model.h"
#include "b58_test.h"

float lojistik_olasilik(const float *x, const float *w,
                        float b, size_t d);
float lojistik_olasilik_q8(const float *x, const int8_t *wq,
                           float olcek, float b, size_t d);

int main(void)
{
    for (int i = 0; i < NT; i++) {
        float pf = lojistik_olasilik(XT[i], W, B, D);
        float pq = lojistik_olasilik_q8(XT[i], WQ, OLCEK, B, D);
        printf("%d %.9g %.9g\n", i, pf, pq);
    }
    return 0;
}
