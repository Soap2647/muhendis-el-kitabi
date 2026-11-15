/* ornek2_oda.c: aralik bolumleme (interval partitioning).
 * Aralik [s, e) yari acik. Baslangica gore sirala; her aralik icin
 * en erken biten odayi kontrol et: bitisi <= s ise o odayi kullan,
 * degilse yeni oda ac. Oda bitisleri bir min-yigindadir.
 * Derleme (WSL): gcc -O2 -Wall -Wextra -std=c11 ornek2_oda.c
 */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int s, e;   /* baslangic ve bitis (e > s) */
    int oda;    /* atanan oda numarasi */
} Aralik;

typedef struct {
    int bitis;  /* odanin mevcut bitis zamani */
    int oda;    /* oda numarasi */
} Oda;

typedef struct {
    Oda *a;
    size_t n;
} Yigin;

static void yukari(Yigin *y, size_t i) {
    while (i > 0) {
        size_t p = (i - 1) / 2;
        if (y->a[p].bitis <= y->a[i].bitis) break;
        Oda t = y->a[p];
        y->a[p] = y->a[i];
        y->a[i] = t;
        i = p;
    }
}

static void asagi(Yigin *y, size_t i) {
    for (;;) {
        size_t sol = 2 * i + 1, sag = sol + 1, en = i;
        if (sol < y->n && y->a[sol].bitis < y->a[en].bitis)
            en = sol;
        if (sag < y->n && y->a[sag].bitis < y->a[en].bitis)
            en = sag;
        if (en == i) break;
        Oda t = y->a[en];
        y->a[en] = y->a[i];
        y->a[i] = t;
        i = en;
    }
}

static int s_karsilastir(const void *x, const void *y) {
    const Aralik *a = x, *b = y;
    return (a->s > b->s) - (a->s < b->s);
}

/* Kullanilan oda sayisini dondurur; bellek hatasinda -1. */
static int oda_ata(Aralik *v, size_t n) {
    Yigin y;
    int oda_say = 0;
    y.a = malloc((n ? n : 1) * sizeof *y.a);
    if (y.a == NULL) return -1;
    y.n = 0;
    qsort(v, n, sizeof *v, s_karsilastir);
    for (size_t i = 0; i < n; i++) {
        if (y.n > 0 && y.a[0].bitis <= v[i].s) {
            v[i].oda = y.a[0].oda;  /* en erken biten odayi devral */
            y.a[0].bitis = v[i].e;  /* bitisi guncelle, asagi suz */
            asagi(&y, 0);
        } else {
            v[i].oda = oda_say++;   /* yeni oda ac */
            y.a[y.n].bitis = v[i].e;
            y.a[y.n].oda = v[i].oda;
            y.n++;
            yukari(&y, y.n - 1);
        }
    }
    free(y.a);
    return oda_say;
}

/* Alt sinir: bir noktada ortusen en fazla aralik sayisi. */
static int derinlik(const Aralik *v, size_t n) {
    int en = 0;
    for (size_t i = 0; i < n; i++) {
        int c = 0;
        for (size_t j = 0; j < n; j++)
            if (v[j].s <= v[i].s && v[i].s < v[j].e) c++;
        if (c > en) en = c;
    }
    return en;
}

/* Ayni odadaki iki aralik cakismiyor mu? */
static int gecerli(const Aralik *v, size_t n) {
    for (size_t i = 0; i < n; i++)
        for (size_t j = i + 1; j < n; j++)
            if (v[i].oda == v[j].oda &&
                !(v[i].e <= v[j].s || v[j].e <= v[i].s))
                return 0;
    return 1;
}

/* Xorshift32, sabit tohum 42: her calistirmada ayni sayilar. */
static uint32_t durum = 42u;

static uint32_t rasgele(void) {
    durum ^= durum << 13;
    durum ^= durum >> 17;
    durum ^= durum << 5;
    return durum;
}

int main(void) {
    Aralik ornek[] = {
        {1, 4, 0}, {2, 6, 0}, {3, 5, 0}, {5, 8, 0},
        {7, 9, 0}, {6, 10, 0}, {9, 12, 0}
    };
    size_t n = sizeof ornek / sizeof ornek[0];
    int k = oda_ata(ornek, n);
    if (k < 0) return 1;
    printf("oda sayisi: %d, derinlik: %d\n", k, derinlik(ornek, n));
    for (size_t i = 0; i < n; i++)
        printf("[%2d,%2d) oda %d\n", ornek[i].s, ornek[i].e,
               ornek[i].oda);
    printf("gecerli: %s\n", gecerli(ornek, n) ? "evet" : "hayir");

    int fark = 0, gecersiz = 0;
    for (int t = 0; t < 300; t++) {
        size_t m = 1 + rasgele() % 12;
        Aralik *v = malloc(m * sizeof *v);
        if (v == NULL) return 1;
        for (size_t i = 0; i < m; i++) {
            v[i].s = (int)(rasgele() % 20);
            v[i].e = v[i].s + 1 + (int)(rasgele() % 6);
            v[i].oda = -1;
        }
        int r = oda_ata(v, m);
        if (r < 0) return 1;
        if (r != derinlik(v, m)) fark++;
        if (!gecerli(v, m)) gecersiz++;
        free(v);
    }
    printf("300 rastgele: derinlik farki %d, gecersiz %d\n",
           fark, gecersiz);
    return 0;
}
