#include <stdio.h>
#include <stdlib.h>
#include "kayit.h"

int kayit_oku(const char *yol, double **kayitlar, size_t *adet)
{
    FILE *f = fopen(yol, "rb");
    unsigned int sihir = 0, n = 0;
    double *tampon;

    if (f == NULL)
        return -1;
    if (fread(&sihir, sizeof sihir, 1, f) != 1 || sihir != SIHIR)
        return -2;                 /* SIZINTI: f kapanmadi */
    if (fread(&n, sizeof n, 1, f) != 1)
        return -3;                 /* SIZINTI: f kapanmadi */
    tampon = malloc(n * sizeof *tampon);
    if (tampon == NULL)
        return -4;                 /* SIZINTI: f kapanmadi */
    if (fread(tampon, sizeof *tampon, n, f) != n)
        return -5;                 /* SIZINTI: f ve tampon */
    fclose(f);
    *kayitlar = tampon;
    *adet = n;
    return 0;
}
