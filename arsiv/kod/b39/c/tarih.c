#include "tarih.h"

static const int AY_GUN[12] = {31, 28, 31, 30, 31, 30,
                               31, 31, 30, 31, 30, 31};

int artik_yil_mi(int yil) {
    return yil % 4 == 0 && (yil % 100 != 0 || yil % 400 == 0);
}

/* Sinir kontrolu YOK: ay 1..12 disinda okuma tanimsiz davranis. */
int gun_sayisi_ham(int yil, int ay) {
    if (ay == 2 && artik_yil_mi(yil)) return 29;
    return AY_GUN[ay - 1];
}

int gun_sayisi(int yil, int ay) {
    if (ay < 1 || ay > 12) return -1;
    return gun_sayisi_ham(yil, ay);
}

int gecerli_tarih(int yil, int ay, int gun) {
    int n = gun_sayisi(yil, ay);
    return n > 0 && gun >= 1 && gun <= n;
}
