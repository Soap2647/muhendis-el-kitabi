/* istemci.c: v1 basligiyla derlenmis eski istemci. */
#include <stdio.h>
#include "olcum.h"

int main(void)
{
    struct olcum o = {7, 0.0};
    int kutuphane = olcum_yapi_boyutu();
    int yerel = (int)sizeof o;
    printf("istemci sizeof=%d kutuphane=%d\n", yerel, kutuphane);
    if (kutuphane != yerel) {
        puts("uyumsuz: calistirma durduruldu");
        return 2;
    }
    olcum_guncelle(&o, 42.0);
    printf("id=%d deger=%.1f\n", o.id, o.deger);
    return 0;
}
