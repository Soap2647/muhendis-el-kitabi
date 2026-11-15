/* tinyml.c - sabit noktali MLP cikarimi (20 -> 8 -> 2).
 * TM_KULLAN_DSP=1 ve ARM hedefinde iç dongu SMLAD ile yazilir.
 */
#include <stdint.h>
#include <math.h>
#include "tinyml.h"
#include "model_int8.h"

#ifndef TM_KULLAN_DSP
#define TM_KULLAN_DSP 0
#endif

#if TM_KULLAN_DSP && defined(__ARM_FEATURE_DSP)
#define TM_DSP_AKTIF 1
#else
#define TM_DSP_AKTIF 0
#endif

/* ---- Ozellikler (float; Cortex-M4F'te tek duyarlik FPU) ---- */
void tm_ozellik(const float p[TM_L][TM_K], float oz[20])
{
    const float n = (float)TM_L;
    const float tden = 2728.0f; /* sum (t - 15.5)^2, L = 32 */
    for (int k = 0; k < TM_K; k++) {
        float s = 0.0f, mn = p[0][k], mx = p[0][k];
        for (int t = 0; t < TM_L; t++) {
            float v = p[t][k];
            s += v;
            if (v < mn) mn = v;
            if (v > mx) mx = v;
        }
        float ort = s / n, var = 0.0f, eg = 0.0f;
        for (int t = 0; t < TM_L; t++) {
            float d = p[t][k] - ort;
            var += d * d;
            eg += ((float)t - 15.5f) * d;
        }
        oz[0 * TM_K + k] = ort;
        oz[1 * TM_K + k] = sqrtf(var / n);
        oz[2 * TM_K + k] = mn;
        oz[3 * TM_K + k] = mx;
        oz[4 * TM_K + k] = eg / tden;
    }
}

/* ---- Girdi kuantizasyonu: q = floor((x-mu)/sd / S) + Z ---- */
void tm_girdi_kuantize(const float oz[20], int8_t xq[20])
{
    for (int i = 0; i < TM_NIN; i++) {
        float v = (oz[i] - TM_MU[i]) / TM_SD[i];
        float w = v / TM_SIN;
        float wr = w + 0.5f;
        int32_t q = (int32_t)wr;       /* sifira dogru kirpma */
        if ((float)q > wr) q--;        /* floor (negatif icin) */
        q += TM_ZIN;
        if (q < -128) q = -128;
        if (q > 127) q = 127;
        xq[i] = (int8_t)q;
    }
}

/* ---- Nokta carpimi: sum w[j]*x[j], n, 4'un kati ---- */
#if !TM_DSP_AKTIF
static int32_t dot_c(const int8_t *w, const int8_t *x, int n)
{
    int32_t acc = 0;
    for (int j = 0; j < n; j++) {
        acc += (int32_t)w[j] * (int32_t)x[j];
    }
    return acc;
}
#endif

#if TM_DSP_AKTIF
static inline uint32_t sxtb16_0(uint32_t v)   /* bayt 0 ve 2 */
{
    uint32_t r;
    __asm__ ("sxtb16 %0, %1" : "=r"(r) : "r"(v));
    return r;
}

static inline uint32_t sxtb16_1(uint32_t v)   /* bayt 1 ve 3 */
{
    uint32_t r;
    __asm__ ("sxtb16 %0, %1, ror #8" : "=r"(r) : "r"(v));
    return r;
}

static inline int32_t smlad(uint32_t a, uint32_t b, int32_t c)
{
    int32_t r;
    __asm__ ("smlad %0, %1, %2, %3"
             : "=r"(r) : "r"(a), "r"(b), "r"(c));
    return r;
}

static int32_t dot_dsp(const int8_t *w, const int8_t *x, int n)
{
    int32_t acc = 0;
    for (int j = 0; j < n; j += 4) {
        uint32_t wv, xv;
        __builtin_memcpy(&wv, w + j, 4);
        __builtin_memcpy(&xv, x + j, 4);
        acc = smlad(sxtb16_0(wv), sxtb16_0(xv), acc);
        acc = smlad(sxtb16_1(wv), sxtb16_1(xv), acc);
    }
    return acc;
}
#define DOT(w, x, n) dot_dsp((w), (x), (n))
#else
#define DOT(w, x, n) dot_c((w), (x), (n))
#endif

/* ---- Katman 1: 20 -> 8, yeniden olcekleme + ReLU ---- */
static void katman1(const int8_t x[20], int8_t a1[TM_NH])
{
    for (int i = 0; i < TM_NH; i++) {
        int32_t acc = TM_B1[i] + DOT(&TM_W1[i * TM_NIN], x, TM_NIN);
        int32_t rs = TM_RS1[i];
        int64_t p = (int64_t)acc * TM_M1[i];
        p += (int64_t)1 << (rs - 1);   /* yuvarlama */
        int32_t y = (int32_t)(p >> rs) + TM_ZA1;
        if (y < TM_ZA1) y = TM_ZA1;    /* ReLU: sifir = ZA1 */
        if (y > 127) y = 127;          /* doygunluk */
        a1[i] = (int8_t)y;
    }
}

/* ---- Katman 2: 8 -> 2, yeniden olcekleme yok (argmax yeter) ---- */
static void katman2(const int8_t a1[TM_NH], int32_t logit[TM_NOUT])
{
    for (int o = 0; o < TM_NOUT; o++) {
        logit[o] = TM_B2[o] + DOT(&TM_W2[o * TM_NH], a1, TM_NH);
    }
}

void tm_ileri(const int8_t xq[20], int32_t logit[2])
{
    int8_t a1[TM_NH];
    katman1(xq, a1);
    katman2(a1, logit);
}

int tm_siniflandir(const float p[TM_L][TM_K])
{
    float oz[20];
    int8_t xq[20];
    int32_t lg[2];
    tm_ozellik(p, oz);
    tm_girdi_kuantize(oz, xq);
    tm_ileri(xq, lg);
    return lg[1] > lg[0];
}
