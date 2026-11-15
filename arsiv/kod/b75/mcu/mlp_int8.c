/* mlp_int8.c - 64-32-10 int8 MLP cikarimi (W8A8, tensor olcegi).
 * Python referansi (gen_mcu.py) ile birebir ayni islem sirasi:
 * tamsayi birikim, float32 yeniden olcekleme, yuvarlama. */
#include <stdint.h>
#include "model_w.h"

static int32_t sat8(int32_t v)
{
    if (v > 127) return 127;
    if (v < -127) return -127;
    return v;
}

/* Sifirdan uzaga yuvarlama (round half away from zero). */
static int32_t yuvarla(float v)
{
    if (v >= 0.0f) return (int32_t)(v + 0.5f);
    return -(int32_t)(-v + 0.5f);
}

/* x: 64 int8 girdi. logit: 10 skor. Donus: tahmin edilen sinif. */
int mlp_cikar(const int8_t x[64], int32_t logit[10])
{
    int8_t h[H_BOYUT];
    int en = 0;

    for (int j = 0; j < H_BOYUT; ++j) {
        int32_t acc = B1[j];
        for (int i = 0; i < M1_BOYUT; ++i)
            acc += (int32_t)W1[j][i] * (int32_t)x[i];
        int32_t q = sat8(yuvarla((float)acc * M1));
        h[j] = (int8_t)(q > 0 ? q : 0);          /* ReLU */
    }
    for (int k = 0; k < C_BOYUT; ++k) {
        int32_t acc = B2[k];
        for (int j = 0; j < H_BOYUT; ++j)
            acc += (int32_t)W2[k][j] * (int32_t)h[j];
        logit[k] = acc;
    }
    for (int k = 1; k < C_BOYUT; ++k)
        if (logit[k] > logit[en]) en = k;
    return en;
}
