/* ornek_cobs.c: COBS kodla / coz gidis-donusu. */
#include <stdio.h>
#include "cobs.h"

static void yazdir(const char *ad, const uint8_t *v, int n)
{
    printf("%s:", ad);
    for (int i = 0; i < n; i++)
        printf(" %02X", v[i]);
    printf("\n");
}

int main(void)
{
    const uint8_t giris[] = {0x11, 0x22, 0x00, 0x33};
    uint8_t kodlu[16], cozulmus[16];

    int k = cobs_kodla(giris, 4, kodlu, sizeof kodlu);
    yazdir("girdi ", giris, 4);
    yazdir("kodlu ", kodlu, k);
    int c = cobs_coz(kodlu, (size_t)k, cozulmus, sizeof cozulmus);
    yazdir("cozulm", cozulmus, c);
    return 0;
}
