/* Elle vtable: OOP'nin C'deki atasi (struct + fonksiyon isaretci) */
#include <stdio.h>
#include <stddef.h>

typedef struct Sekil Sekil;

typedef struct {
    double (*alan)(const Sekil *self);
    void   (*yazdir)(const Sekil *self);
} SekilVT;

struct Sekil {
    const SekilVT *vt;      /* her nesne tablo adresini tasir */
};

typedef struct {
    Sekil taban;   /* ilk uye: Sekil* ve Daire* ayni adres */
    double r;
} Daire;

typedef struct {
    Sekil taban;
    double a, b;
} Dikdortgen;

static double daire_alan(const Sekil *s) {
    const Daire *d = (const Daire *)s;
    return 3.14159265358979 * d->r * d->r;
}
static void daire_yazdir(const Sekil *s) {
    const Daire *d = (const Daire *)s;
    printf("Daire r=%.1f\n", d->r);
}
static double dik_alan(const Sekil *s) {
    const Dikdortgen *k = (const Dikdortgen *)s;
    return k->a * k->b;
}
static void dik_yazdir(const Sekil *s) {
    const Dikdortgen *k = (const Dikdortgen *)s;
    printf("Dikdortgen %.1fx%.1f\n", k->a, k->b);
}

static const SekilVT daire_vt = { daire_alan, daire_yazdir };
static const SekilVT dik_vt   = { dik_alan,   dik_yazdir   };

static void daire_kur(Daire *d, double r) {
    d->taban.vt = &daire_vt;
    d->r = r;
}
static void dik_kur(Dikdortgen *k, double a, double b) {
    k->taban.vt = &dik_vt;
    k->a = a; k->b = b;
}

int main(void) {
    Daire d; Dikdortgen k;
    daire_kur(&d, 2.0);
    dik_kur(&k, 3.0, 4.0);

    /* ayni tip (Sekil*), farkli davranis */
    Sekil *liste[2] = { &d.taban, &k.taban };
    double toplam = 0.0;
    for (size_t i = 0; i < 2; i++) {
        liste[i]->vt->yazdir(liste[i]);     /* dolayli cagri */
        toplam += liste[i]->vt->alan(liste[i]);
    }
    printf("toplam alan = %.3f\n", toplam);
    printf("sizeof(Sekil)=%zu sizeof(Daire)=%zu\n",
           sizeof(Sekil), sizeof(Daire));
    printf("offsetof(Daire,r)=%zu\n", offsetof(Daire, r));
    return 0;
}
