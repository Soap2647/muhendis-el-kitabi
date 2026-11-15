/* isr_vec.c - vektor tablosunda adi gecen kesme isleyicileri */
#include <stdint.h>
#include "ringbuf.h"

extern volatile uint32_t g_tick;
extern rb_t g_rb;
volatile uint32_t g_usart_rx;

/* Periyodik zamanlayici kesmesi: tick ve tampon */
void TIM2_IRQHandler(void)
{
    g_tick++;
    rb_yaz(&g_rb, (uint8_t)g_tick);
}

/* UART alim kesmesi (ayrinti Bolum 45) */
void USART1_IRQHandler(void)
{
    g_usart_rx++;
}
