#include <stdio.h>
#include "tarih.h"

/* Tanimsiz davranis gosterimi: sinirsiz fonksiyona ay = 13. */
int main(void) {
    volatile int s = gun_sayisi_ham(2024, 13);
    printf("sonuc (tanimsiz): %d\n", s);
    return 0;
}
