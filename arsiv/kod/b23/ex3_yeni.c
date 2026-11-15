#include <stdio.h>
#include <stdlib.h>
#include "kayit.h"

int kayit_oku(const char *yol, double **kayitlar, size_t *adet)
{
    int durum;
    FILE *f;
    unsigned int sihir = 0, n = 0;
    double *tampon = NULL;

    f = fopen(yol, "rb");
    if (f == NULL)
        return -1;

    durum = -2;
    if (fread(&sihir, sizeof sihir, 1, f) != 1 || sihir != SIHIR)
        goto cik_dosya;

    durum = -3;
    if (fread(&n, sizeof n, 1, f) != 1)
        goto cik_dosya;

    durum = -4;
    tampon = malloc(n * sizeof *tampon);
    if (tampon == NULL)
        goto cik_dosya;

    durum = -5;
    if (fread(tampon, sizeof *tampon, n, f) != n)
        goto cik_tampon;

    fclose(f);
    *kayitlar = tampon;
    *adet = n;
    return 0;

cik_tampon:
    free(tampon);
cik_dosya:
    fclose(f);
    return durum;
}
