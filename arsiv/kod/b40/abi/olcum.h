/* olcum.h: Paylasimli kutuphanenin baslik dosyasi. */
#ifndef OLCUM_H
#define OLCUM_H

struct olcum {
    int    id;
    double deger;
#ifdef OLCUM_V2
    int    durum;           /* v2'de eklendi: yapinin sonuna */
#endif
};

int  olcum_yapi_boyutu(void);  /* kutuphanenin gordugu sizeof */
void olcum_guncelle(struct olcum *o, double d);

#endif
