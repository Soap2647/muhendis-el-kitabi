/* tinyml.h - sabit noktali (int8) MLP cikarim kutuphanesi.
 * Dinamik bellek yok (malloc yok). Tum tamponlar cagiran tarafta
 * veya yigida (cok kucuk) tutulur.
 */
#ifndef TINYML_H
#define TINYML_H

#include <stdint.h>

#define TM_L 32 /* pencere uzunlugu (ornek) */
#define TM_K 4  /* kanal sayisi */

/* Ham pencere (TM_L x TM_K float) -> 20 ozellik (float).
 * Sira: [ort(4), std(4), min(4), maks(4), egim(4)].         */
void tm_ozellik(const float p[TM_L][TM_K], float oz[20]);

/* Ozellik (float) -> int8 girdi. Normalizasyon ve kuantizasyon. */
void tm_girdi_kuantize(const float oz[20], int8_t xq[20]);

/* int8 girdi -> int32 logit'ler (tam tamsayi cekirdek). */
void tm_ileri(const int8_t xq[20], int32_t logit[2]);

/* Ham pencere -> 0 (normal) veya 1 (anomali). */
int tm_siniflandir(const float p[TM_L][TM_K]);

#endif
