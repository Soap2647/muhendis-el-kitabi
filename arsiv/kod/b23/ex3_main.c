#include <stdio.h>
#include <stdlib.h>
#include "kayit.h"

static void dosya_yaz(const char *ad, unsigned int sihir,
                      unsigned int n, int adet_gercek)
{
    FILE *f = fopen(ad, "wb");
    double v = 1.5;
    fwrite(&sihir, sizeof sihir, 1, f);
    fwrite(&n, sizeof n, 1, f);
    for (int i = 0; i < adet_gercek; i++)
        fwrite(&v, sizeof v, 1, f);
    fclose(f);
}

int main(void)
{
    double *k = NULL;
    size_t adet = 0;
    int r;

    setvbuf(stdout, NULL, _IONBF, 0);
    dosya_yaz("iyi.bin", SIHIR, 3, 3);
    dosya_yaz("sihir.bin", 0x1234u, 3, 3);
    dosya_yaz("kesik.bin", SIHIR, 1000, 3);

    r = kayit_oku("iyi.bin", &k, &adet);
    printf("iyi.bin    -> %d, adet=%zu\n", r, adet);
    free(k);
    r = kayit_oku("sihir.bin", &k, &adet);
    printf("sihir.bin  -> %d\n", r);
    r = kayit_oku("kesik.bin", &k, &adet);
    printf("kesik.bin  -> %d\n", r);
    r = kayit_oku("yok.bin", &k, &adet);
    printf("yok.bin    -> %d\n", r);
    return 0;
}
