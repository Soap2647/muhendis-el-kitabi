/* olcum_lib.c: Kutuphane gerceklemesi. -DOLCUM_V2 ile v2 derlenir. */
#include "olcum.h"

int olcum_yapi_boyutu(void)
{
    return (int)sizeof(struct olcum);
}

void olcum_guncelle(struct olcum *o, double d)
{
    o->deger = d;
#ifdef OLCUM_V2
    o->durum = d > 50.0;        /* v2 davranisi: esik uzerinde 1 */
#endif
}
