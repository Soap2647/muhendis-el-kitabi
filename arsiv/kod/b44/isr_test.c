/* isr_test.c - kesme isleyicisi ve ana dongu benzeri fonksiyonlar.
 * Gercek kesme girisi yok: bu fonksiyonlar dogrudan cagrilir. */
#include <stdint.h>
#include "ringbuf.h"

volatile uint32_t g_tick;
rb_t g_rb;
volatile uint32_t g_paylasilan;

/* "ISR" govdesi: sayaci artir, ornegi tampona yaz */
void adc_isr_govde(uint8_t ornek)
{
    g_tick++;
    rb_yaz(&g_rb, ornek);
}

/* Ana dongu: tampondan n bayt alip toplar */
uint32_t ana_dongu_topla(uint32_t n)
{
    uint32_t toplam = 0;
    uint8_t b;

    for (uint32_t i = 0; i < n; i++) {
        if (rb_oku(&g_rb, &b)) toplam += b;
    }
    return toplam;
}

/* Kritik bolge: PRIMASK ile paylasilan sayaci guvenli artir */
static inline uint32_t primask_kaydet(void)
{
    uint32_t p;
    __asm volatile("mrs %0, primask\n\t"
                   "cpsid i" : "=r"(p) :: "memory");
    return p;
}

static inline void primask_geri(uint32_t p)
{
    __asm volatile("msr primask, %0" :: "r"(p) : "memory");
}

void kritik_artir(uint32_t n)
{
    for (uint32_t i = 0; i < n; i++) {
        uint32_t p = primask_kaydet();
        g_paylasilan = g_paylasilan + 1u;
        primask_geri(p);
    }
}
