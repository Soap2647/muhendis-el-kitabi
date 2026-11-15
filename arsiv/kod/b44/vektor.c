/* vektor.c - Cortex-M4 vektor tablosu (STM32F407 IRQ numaralari) */
#include <stdint.h>

extern uint32_t _estack;            /* baglayiciden: RAM sonu */
extern uint32_t _sbss, _ebss;       /* .bss sinirlari */
void Reset_Handler(void);
void Default_Handler(void);
void TIM2_IRQHandler(void);
void USART1_IRQHandler(void);
int main(void);

/* Tablo: [0] MSP, [1] Reset, [2..15] istisnalar, [16+n] IRQn */
__attribute__((section(".isr_vector"), used))
const void *g_vektor[16 + 60] = {
    [0]  = &_estack,
    [1]  = Reset_Handler,
    [2]  = Default_Handler,         /* NMI */
    [3]  = Default_Handler,         /* HardFault */
    [14] = Default_Handler,         /* PendSV */
    [15] = Default_Handler,         /* SysTick */
    [16 + 28] = TIM2_IRQHandler,    /* IRQ28: TIM2 */
    [16 + 37] = USART1_IRQHandler,  /* IRQ37: USART1 */
};

void Reset_Handler(void)
{
    uint32_t *p;

    for (p = &_sbss; p < &_ebss; p++) *p = 0;
    main();
    for (;;) { }
}

void Default_Handler(void)
{
    for (;;) { }
}
