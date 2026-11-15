/* b58_tahmin.c: egitilmis lojistik modelin cikarim (inference) kodu.
 * Kayan noktali ve int8 agirlikli iki surum. */
#include <math.h>
#include <stddef.h>
#include <stdint.h>

/* Olasilik = sigmoid(w . x + b) */
float lojistik_olasilik(const float *x, const float *w,
                        float b, size_t d)
{
    float z = b;
    for (size_t i = 0; i < d; i++) {
        z += w[i] * x[i];
    }
    return 1.0f / (1.0f + expf(-z));
}

/* Agirliklar simetrik int8 (olcek ile) saklanir. Birikim ve girdi
 * float kalir; yalniz w kuantize edilir. */
float lojistik_olasilik_q8(const float *x, const int8_t *wq,
                           float olcek, float b, size_t d)
{
    float z = b;
    for (size_t i = 0; i < d; i++) {
        z += ((float)wq[i] * olcek) * x[i];
    }
    return 1.0f / (1.0f + expf(-z));
}
