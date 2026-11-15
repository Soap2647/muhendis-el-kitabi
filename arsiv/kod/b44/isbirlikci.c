/* isbirlikci.c - isbirlikci (cooperative) zamanlayici benzetimi.
 * Tick isleyicisi bir sayaci artirir ve vadesi gelen gorevin
 * bayragini kaldirir. Ana dongu bayragi gorurse gorevi bitirene
 * kadar calistirir: hicbir gorev kesilmez.
 * Gecikme = gorevin basladigi tick - vade tick'i. */
#include <stdio.h>

#define GOREV_SAYISI 3
#define TOPLAM_TICK  400

typedef struct {
    const char *ad;
    int periyot;           /* tick */
    int is_suresi;         /* tick: bitene kadar CPU'yu tutar */
    int vade;              /* bir sonraki vade tick'i */
    volatile int bayrak;   /* tick isleyicisi yazar */
    int en_buyuk_gecikme;
    int calisma;
} gorev_t;

static gorev_t g[GOREV_SAYISI] = {
    {"A_hizli",  10,  1, 10, 0, 0, 0},
    {"B_orta",   25,  2, 25, 0, 0, 0},
    {"C_uzun",   50, 30, 50, 0, 0, 0},   /* uzun is */
};

static volatile int tick;

/* Tick "kesmesi": her tick'te vadesi gelen gorevi isaretler */
static void tick_isleyici(void)
{
    tick++;
    for (int i = 0; i < GOREV_SAYISI; i++) {
        if (tick >= g[i].vade) g[i].bayrak = 1;
    }
}

int main(void)
{
    int simdi = 0;

    while (simdi < TOPLAM_TICK) {
        tick_isleyici();
        simdi = tick;
        for (int i = 0; i < GOREV_SAYISI; i++) {
            if (!g[i].bayrak) continue;
            /* baslangic gecikmesi */
            int gecikme = tick - g[i].vade;
            if (gecikme > g[i].en_buyuk_gecikme)
                g[i].en_buyuk_gecikme = gecikme;
            /* isbirlikci: gorev bitene kadar tick'ler sayilir */
            for (int k = 0; k < g[i].is_suresi; k++)
                tick_isleyici();
            g[i].bayrak = 0;
            g[i].calisma++;
            g[i].vade += g[i].periyot;
        }
    }
    printf("gorev      periyot is_suresi calisma max_gecikme\n");
    for (int i = 0; i < GOREV_SAYISI; i++)
        printf("%-10s %6d %9d %7d %11d\n", g[i].ad, g[i].periyot,
               g[i].is_suresi, g[i].calisma, g[i].en_buyuk_gecikme);
    return 0;
}
