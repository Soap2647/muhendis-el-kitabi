/* fpu_isr.c - kayan noktali kesme isleyicisi */
#include <stdint.h>

volatile float g_girdi[4];
volatile float g_cikti;

/* Baska birimde tanimli, yavas bir hesap */
extern float yavas_hesap(float x);

void SysTick_Handler(void)
{
    float a = g_girdi[0];
    float b = g_girdi[1];
    float c = g_girdi[2];
    float d = g_girdi[3];
    float s = a * b + c * d;

    /* Cagri: s16-s31 cagri boyunca korunur */
    float t = yavas_hesap(s);
    g_cikti = t * a - b;
}
