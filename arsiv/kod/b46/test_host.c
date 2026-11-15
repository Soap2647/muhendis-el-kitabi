/* test_host.c - host (gcc) dogrulama.
 * Kullanim: test_host <veri_dizini>
 * Python referansiyla bit-tam karsilastirma + uctan uca dogruluk.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "tinyml.h"
#include "model_int8.h"

#define N 2000
#define NR 1000

static void *oku(const char *dizin, const char *ad, size_t boyut)
{
    char yol[512];
    snprintf(yol, sizeof yol, "%s/%s", dizin, ad);
    FILE *f = fopen(yol, "rb");
    if (!f) { perror(yol); exit(1); }
    void *b = malloc(boyut);
    if (!b || fread(b, 1, boyut, f) != boyut) {
        fprintf(stderr, "okuma hatasi: %s\n", ad);
        exit(1);
    }
    fclose(f);
    return b;
}

int main(int argc, char **argv)
{
    const char *d = (argc > 1) ? argv[1] : ".";
    float (*pen)[TM_L][TM_K] = oku(d, "test_pencere.bin",
                                   sizeof(float) * N * TM_L * TM_K);
    float (*ozp)[20] = oku(d, "test_ozellik.bin",
                           sizeof(float) * N * 20);
    int8_t (*xqp)[20] = oku(d, "test_xq.bin", N * 20);
    int32_t (*bek)[3] = oku(d, "test_beklenen.bin",
                            sizeof(int32_t) * N * 3);
    int8_t (*rxq)[20] = oku(d, "test_r_xq.bin", NR * 20);
    int32_t (*rbek)[2] = oku(d, "test_r_beklenen.bin",
                             sizeof(int32_t) * NR * 2);

    double ozellik_max = 0.0;
    int girdi_uyus = 0, logit_uyus = 0, dogru = 0, tah_fark = 0;

    for (int i = 0; i < N; i++) {
        /* (a) ozellik: C ile Python arasinda kucuk fark beklenir */
        float oz[20];
        tm_ozellik(pen[i], oz);
        for (int j = 0; j < 20; j++) {
            double dd = (double)oz[j] - (double)ozp[i][j];
            if (dd < 0) dd = -dd;
            if (dd > ozellik_max) ozellik_max = dd;
        }
        /* (b) girdi kuantizasyonu: Python ozellikleriyle bit-tam */
        int8_t xq[20];
        tm_girdi_kuantize(ozp[i], xq);
        for (int j = 0; j < 20; j++) {
            if (xq[j] != xqp[i][j]) { girdi_uyus++; break; }
        }
        /* (c) tam tamsayi cekirdek: Python tamsayi referansi ile */
        int32_t lg[2];
        tm_ileri(xqp[i], lg);
        if (lg[0] != bek[i][1] || lg[1] != bek[i][2]) logit_uyus++;
        /* (d) uctan uca: ham pencere -> sinif */
        int tah = tm_siniflandir(pen[i]);
        if (tah == bek[i][0]) dogru++;
        if (tah != (bek[i][2] > bek[i][1])) tah_fark++;
    }

    /* (e) tam aralikli rastgele girdiler: tasma ve doygunluk */
    int r_uyus = 0;
    for (int i = 0; i < NR; i++) {
        int32_t lg[2];
        tm_ileri(rxq[i], lg);
        if (lg[0] != rbek[i][0] || lg[1] != rbek[i][1]) r_uyus++;
    }

    printf("ozellik en buyuk fark (C - Python): %.3g\n", ozellik_max);
    printf("girdi kuantizasyonu uyusmazlik    : %d / %d\n",
           girdi_uyus, N);
    printf("int8 logit uyusmazlik (bit-tam)   : %d / %d\n",
           logit_uyus, N);
    printf("uctan uca dogruluk (C)            : %.4f\n",
           (double)dogru / N);
    printf("uctan uca ile Python argmax farki : %d\n", tah_fark);
    printf("rastgele tam aralik uyusmazlik    : %d / %d\n",
           r_uyus, NR);
    free(pen);
    free(ozp);
    free(xqp);
    free(bek);
    free(rxq);
    free(rbek);
    if (girdi_uyus || logit_uyus || r_uyus) return 2;
    return 0;
}
