/* blink.c - STM32F407 uzerinde PD12 LED'i yalnizca yazmaclarla
 * surer. Kart: STM32F4 Discovery varsayimi (PD12 yesil LED).
 * Bu program kartta denenmedi; dogrulama emulatorde yapildi. */
#include <stdint.h>
#include "reg.h"

#define LED_PIN 12u   /* PD12 */

/* Baslangic degeri olan global: .data (flash'tan RAM'e kopya) */
uint32_t acilis_degeri = 0xCAFE0001u;
/* Baslangicsiz global: .bss (reset isleyicisi sifirlar).
 * volatile: artirimi derleyici silemez (bkz. Bolum metni). */
volatile uint32_t dongu_sayaci;
/* Yalniz okunur tablo: .rodata'da flash'ta kalir */
const uint8_t kademe[4] = { 25u, 50u, 75u, 100u };
/* Emulator bu degiskeni RAM'den okur */
volatile uint32_t sonuc_menzil;

/* Batarya yuzdesinden menzil: EV Dashboard'daki modelin tam sayi
 * karsiligi (batarya / 100 * 165). Kayan nokta yerine tam sayi. */
uint32_t menzil_hesapla(uint8_t batarya)
{
    return ((uint32_t)batarya * 165u) / 100u;
}

/* Yerel sayac volatile: her azaltma bellege yazilir; derleyici
 * dongunun etkisiz oldugunu dusunup silemez. */
static void gecikme(uint32_t n)
{
    volatile uint32_t sayac = n;
    while (sayac != 0u) {
        sayac--;
    }
}

int main(void)
{
    RCC->AHB1ENR |= (1u << 3);                /* GPIODEN */
    GPIOD->MODER &= ~(3u << (2u * LED_PIN));  /* 2 bit sil */
    GPIOD->MODER |=  (1u << (2u * LED_PIN));  /* 01: cikis */

    sonuc_menzil = menzil_hesapla(kademe[acilis_degeri & 3u]);
    dongu_sayaci = acilis_degeri & 0xFFu;

    while (1) {
        GPIOD->BSRR = (1u << LED_PIN);          /* set: yanar */
        gecikme(100000u);
        GPIOD->BSRR = (1u << (LED_PIN + 16u));  /* reset: soner */
        gecikme(100000u);
        dongu_sayaci++;
    }
}
