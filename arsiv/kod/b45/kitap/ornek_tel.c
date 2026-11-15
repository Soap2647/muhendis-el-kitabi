/* ornek_tel.c: telemetri cercevesi (21 bayt) uretir. */
#include <stdio.h>
#include "telemetri_cerceve.h"

int main(void)
{
    tel_yuk_t y = {12, 87, 523, 143, 25, -3, 3300, 'D', 1, 0, 0};
    uint8_t kare[32];
    int n = tel_kodla(&y, 7, kare, sizeof kare);

    printf("uzunluk=%d\n", n);
    for (int i = 0; i < n; i++)
        printf("%02x%c", kare[i], i == n - 1 ? '\n' : ' ');
    return 0;
}
