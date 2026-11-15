/* sensor.c: sensor.h arayuzunun gerceklemesi. */
#include <stdlib.h>
#include <string.h>
#include "sensor.h"

/* Yapi disariya kapali: kullanici bunu goremez. */
struct sensor {
    char   ad[32];
    double son;
    int    kayit_sayisi;
};

sensor_t *sensor_olustur(const char *ad)
{
    sensor_t *s;

    if (ad == NULL || ad[0] == '\0')
        return NULL;
    s = malloc(sizeof *s);
    if (s == NULL)
        return NULL;
    strncpy(s->ad, ad, sizeof s->ad - 1);
    s->ad[sizeof s->ad - 1] = '\0';
    s->son = 0.0;
    s->kayit_sayisi = 0;
    return s;
}

void sensor_yok_et(sensor_t *s)
{
    free(s);                /* free(NULL) tanimli, guvenli */
}

sensor_durum sensor_kaydet(sensor_t *s, double deger)
{
    if (s == NULL)
        return SENSOR_EARG;
    if (deger < -100.0 || deger > 100.0)
        return SENSOR_ERANGE;
    s->son = deger;
    s->kayit_sayisi++;
    return SENSOR_OK;
}

sensor_durum sensor_oku(const sensor_t *s, double *cikis)
{
    if (s == NULL || cikis == NULL)
        return SENSOR_EARG;
    *cikis = s->son;
    return SENSOR_OK;
}

const char *sensor_durum_metni(sensor_durum d)
{
    switch (d) {
    case SENSOR_OK:     return "tamam";
    case SENSOR_EARG:   return "gecersiz argum";
    case SENSOR_ERANGE: return "aralik disi";
    }
    return "bilinmeyen";
}
