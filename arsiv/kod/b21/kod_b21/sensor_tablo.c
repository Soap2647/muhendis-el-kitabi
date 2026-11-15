/* sensor_tablo.c: fonksiyon isaretci tablosu ile genisletilebilir
 * surucu. Cekirdek (raporla) somut surucu fonksiyonlarini bilmez. */
#include <stddef.h>
#include <stdio.h>

typedef struct {
    const char *ad;
    const char *birim;
    double (*oku)(int ham);        /* zorunlu */
    double (*kalibre)(double v);   /* istege bagli: NULL olabilir */
} sensor_ops;

static double termistor_oku(int ham) { return ham * 0.1 - 40.0; }
static double gerilim_oku(int ham) { return ham * 3.3 / 4095.0; }
static double basinc_oku(int ham) { return ham * 0.05; }
static double basinc_duzelt(double v) { return v + 1.5; }

static const sensor_ops tablo[] = {
    {"termistor", "C", termistor_oku, NULL},
    {"gerilim", "V", gerilim_oku, NULL},
    {"basinc", "kPa", basinc_oku, basinc_duzelt},
};

static void raporla(const sensor_ops *t, size_t n, const int *ham)
{
    for (size_t i = 0; i < n; i++) {
        double v = t[i].oku(ham[i]);
        if (t[i].kalibre != NULL)     /* NULL ise adim atlanir */
            v = t[i].kalibre(v);
        printf("%-10s %8.3f %s\n", t[i].ad, v, t[i].birim);
    }
}

/* Test icin sahte surucu: cekirdek bunu da ayni sekilde isler */
static double sahte_oku(int ham) { return (double)ham; }
static const sensor_ops sahte[] = {{"sahte", "u", sahte_oku, NULL}};

int main(void)
{
    int ham[3] = {1500, 1100, 1200};
    size_t n = sizeof tablo / sizeof tablo[0];
    raporla(tablo, n, ham);
    printf("-- sahte surucu --\n");
    int ham2[1] = {7};
    raporla(sahte, sizeof sahte / sizeof sahte[0], ham2);
    return 0;
}
