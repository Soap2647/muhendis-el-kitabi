/* hata_opak.c: Opak tipin yapisina erismek derleme hatasidir. */
#include "sensor.h"

double yapiya_bak(sensor_t *s)
{
    return s->son;      /* yapi tanimsiz: derlenmez */
}
