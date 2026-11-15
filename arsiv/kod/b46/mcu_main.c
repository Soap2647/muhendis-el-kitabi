/* mcu_main.c - Cortex-M4 olcum programu.
 * DWT cycle sayaci ile cikarim suresini olcer.
 * Bu kod DONANIMDA CALISTIRILMADI; yalniz derlendi. */
#include <stdint.h>
#include "tinyml.h"
#include "ornek.h"

#define DEMCR      (*(volatile uint32_t *)0xE000EDFCu)
#define DWT_CTRL   (*(volatile uint32_t *)0xE0001000u)
#define DWT_CYCCNT (*(volatile uint32_t *)0xE0001004u)

volatile int sonuc[ORNEK_SAYI];
volatile uint32_t dongu[ORNEK_SAYI];
volatile uint32_t cekirdek_dongu;
volatile int32_t lg_son[2];

int main(void)
{
    DEMCR |= (1u << 24);   /* TRCENA: DWT'yi etkinlestir */
    DWT_CYCCNT = 0;
    DWT_CTRL |= 1u;        /* CYCCNTENA */

    for (int i = 0; i < ORNEK_SAYI; i++) {
        uint32_t t0 = DWT_CYCCNT;
        sonuc[i] = tm_siniflandir(ORNEK[i]);
        dongu[i] = DWT_CYCCNT - t0;
    }

    /* Yalniz tamsayi cekirdek: ozellik ve kuantizasyon haric */
    float oz[20];
    int8_t xq[20];
    int32_t lg[2];
    tm_ozellik(ORNEK[0], oz);
    tm_girdi_kuantize(oz, xq);
    uint32_t t1 = DWT_CYCCNT;
    tm_ileri(xq, lg);
    cekirdek_dongu = DWT_CYCCNT - t1;
    lg_son[0] = lg[0];
    lg_son[1] = lg[1];
    return 0;
}
