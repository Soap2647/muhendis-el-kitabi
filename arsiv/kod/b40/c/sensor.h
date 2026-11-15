/* sensor.h: Sensor kutuphanesinin genel arayuzu. */
#ifndef SENSOR_H
#define SENSOR_H

/* opak: yapisini yalnizca sensor.c bilir */
typedef struct sensor sensor_t;

typedef enum {
    SENSOR_OK     = 0,   /* basarili */
    SENSOR_EARG   = -1,  /* gecersiz argum (NULL, bos ad) */
    SENSOR_ERANGE = -2   /* deger aralik disi */
} sensor_durum;

/* Sahiplik: donen isaretci cagirana aittir; sensor_yok_et
   ile serbest birakilir. Basarisizlikta NULL doner. */
sensor_t *sensor_olustur(const char *ad);
void sensor_yok_et(sensor_t *s);  /* NULL: hicbir sey yapmaz */

sensor_durum sensor_kaydet(sensor_t *s, double deger);
sensor_durum sensor_oku(const sensor_t *s, double *cikis);

const char *sensor_durum_metni(sensor_durum d);

#endif
