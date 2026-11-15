/* sensor_main.c: API'yi kullanan istemci. Yapiyi goremez. */
#include <stdio.h>
#include "sensor.h"

int main(void)
{
    sensor_t *s = sensor_olustur("EV-batarya");
    double v = -1.0;
    sensor_durum d;

    if (s == NULL) {
        puts("olusturulamadi");
        return 1;
    }
    d = sensor_kaydet(s, 23.5);
    printf("kaydet 23.5 -> %s\n", sensor_durum_metni(d));
    d = sensor_kaydet(s, 500.0);
    printf("kaydet 500  -> %s\n", sensor_durum_metni(d));
    d = sensor_oku(s, &v);
    printf("oku         -> %s, v=%.1f\n", sensor_durum_metni(d), v);
    d = sensor_oku(NULL, &v);
    printf("NULL oku    -> %s\n", sensor_durum_metni(d));

    sensor_yok_et(s);
    sensor_yok_et(NULL);
    s = NULL;               /* serbest birakilan isaretciyi sifirla */
    return 0;
}
