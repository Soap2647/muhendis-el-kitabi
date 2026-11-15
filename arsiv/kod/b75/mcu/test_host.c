/* test_host.c - konakta bit-tam dogrulama: logit ve etiket Python ile
 * birebir ayni mi? */
#include <stdio.h>
#include <stdint.h>
#include "model_w.h"
#include "test_vektor.h"

int mlp_cikar(const int8_t x[64], int32_t logit[10]);

int main(void)
{
    int bozuk = 0, dogru = 0;
    for (int t = 0; t < N_TEST; ++t) {
        int32_t lg[C_BOYUT];
        int en = mlp_cikar(XT[t], lg);
        for (int k = 0; k < C_BOYUT; ++k)
            if (lg[k] != LT[t][k]) { bozuk++; break; }
        if (en == YT[t]) dogru++;
    }
    printf("logit eslesmesi: %d/%d\n", N_TEST - bozuk, N_TEST);
    printf("dogru etiket: %d/%d\n", dogru, N_TEST);
    return bozuk != 0;
}
