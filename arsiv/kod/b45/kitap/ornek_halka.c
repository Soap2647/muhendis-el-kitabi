/* ornek_halka.c: halka tamponun dolma ve bosalma davranisi. */
#include <stdio.h>
#include "halka.h"

int main(void)
{
    halka_t h;
    uint8_t b;
    int yazilan = 0, reddedilen = 0;

    halka_sifirla(&h);
    for (int i = 0; i < 70; i++) {          /* kapasite 64 */
        if (halka_yaz(&h, (uint8_t)i) == 0)
            yazilan++;
        else
            reddedilen++;
    }
    printf("yazilan=%d reddedilen=%d\n", yazilan, reddedilen);
    if (halka_oku(&h, &b) == 0)
        printf("ilk okunan=%u\n", b);
    while (halka_oku(&h, &b) == 0)
        ;
    printf("bosaltildi, yeni okuma=%d\n", halka_oku(&h, &b));
    return 0;
}
