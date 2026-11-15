/* startup.c - Cortex-M4 icin C ile yazilmis baslangic kodu.
 * Assembly yok: vektor tablosu, reset ve varsayilan isleyici.
 * Derleme bayraklari: -ffreestanding (libc varsayimi yok) ve
 * -fno-tree-loop-distribute-patterns (kopyalama dongusunun
 * memcpy'ye donusmesini onleyen onlem; bu kodda gozlemlenmedi). */
#include <stdint.h>

/* Baglayici betiginin tanimladigi semboller (adres) */
extern uint32_t _estack;                 /* RAM sonu: yigin tepesi */
extern uint32_t _sidata, _sdata, _edata; /* .data: kaynak ve hedef */
extern uint32_t _sbss, _ebss;            /* .bss: sifirlanacak */

extern int main(void);
void Reset_Handler(void);
void Varsayilan_Isleyici(void);

/* Vektor tablosu: ilk kelime baslangic MSP, ikincisi reset.
 * Fonksiyon adreslerinin bit 0'i derleyici tarafindan 1 yapilir
 * (Thumb biti). Kesme girisleri Bolum 44'te anlatilir. */
__attribute__((used, section(".isr_vector")))
void *const vektor_tablosu[16] = {
    (void *)&_estack,            /* 0  baslangic MSP */
    (void *)Reset_Handler,       /* 1  reset */
    (void *)Varsayilan_Isleyici, /* 2  NMI */
    (void *)Varsayilan_Isleyici, /* 3  HardFault */
    (void *)Varsayilan_Isleyici, /* 4  MemManage */
    (void *)Varsayilan_Isleyici, /* 5  BusFault */
    (void *)Varsayilan_Isleyici, /* 6  UsageFault */
    (void *)0, (void *)0, (void *)0, (void *)0, /* 7-10 */
    (void *)Varsayilan_Isleyici, /* 11 SVCall */
    (void *)Varsayilan_Isleyici, /* 12 DebugMonitor */
    (void *)0,                   /* 13 ayrilmis */
    (void *)Varsayilan_Isleyici, /* 14 PendSV */
    (void *)Varsayilan_Isleyici, /* 15 SysTick */
};

/* Reset: .data'yi flash'tan RAM'e kopyala, .bss'yi sifirla,
 * FPU'yu ac, sonra main'e gec. */
void Reset_Handler(void)
{
    uint32_t *kaynak = &_sidata;
    uint32_t *hedef = &_sdata;
    while (hedef < &_edata) {
        *hedef++ = *kaynak++;
    }

    for (uint32_t *p = &_sbss; p < &_ebss; p++) {
        *p = 0u;
    }

    /* CPACR (0xE000ED88) bit 20-23: CP10, CP11 tam erisim.
     * Bu acilmadan ilk kayan nokta komutu usage fault uretir. */
    *(volatile uint32_t *)0xE000ED88u |= (0xFu << 20);

    main();
    while (1) {
    }
}

void Varsayilan_Isleyici(void)
{
    while (1) {
    }
}
