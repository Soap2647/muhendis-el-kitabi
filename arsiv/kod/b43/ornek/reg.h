/* reg.h - STM32F407 yazmac haritasi (RM0090 adresleri).
 * Her yazmac sabit bir adreste duran volatile bir tamsayidir.
 * Ofsetler _Static_assert ile derleme aninda denetlenir. */
#ifndef REG_H
#define REG_H

#include <stdint.h>
#include <stddef.h>

#define RCC_BASE    0x40023800u
#define GPIOD_BASE  0x40020C00u

typedef struct {
    volatile uint32_t MODER;    /* 0x00: pin modu (2 bit/pin) */
    volatile uint32_t OTYPER;   /* 0x04: cikis tipi */
    volatile uint32_t OSPEEDR;  /* 0x08: hiz */
    volatile uint32_t PUPDR;    /* 0x0C: cekme direnci */
    volatile uint32_t IDR;      /* 0x10: giris verisi (okuma) */
    volatile uint32_t ODR;      /* 0x14: cikis verisi */
    volatile uint32_t BSRR;     /* 0x18: set/reset (yalniz yazma) */
    volatile uint32_t LCKR;     /* 0x1C: kilit */
    volatile uint32_t AFR[2];   /* 0x20, 0x24: alternatif islev */
} GPIO_TypeDef;

typedef struct {
    volatile uint32_t CR;         /* 0x00 */
    volatile uint32_t PLLCFGR;    /* 0x04 */
    volatile uint32_t CFGR;       /* 0x08 */
    volatile uint32_t CIR;        /* 0x0C */
    volatile uint32_t AHB1RSTR;   /* 0x10 */
    volatile uint32_t AHB2RSTR;   /* 0x14 */
    volatile uint32_t AHB3RSTR;   /* 0x18 */
    uint32_t          RESERVED0;  /* 0x1C */
    volatile uint32_t APB1RSTR;   /* 0x20 */
    volatile uint32_t APB2RSTR;   /* 0x24 */
    uint32_t          RESERVED1[2]; /* 0x28, 0x2C */
    volatile uint32_t AHB1ENR;    /* 0x30: AHB1 saat kapisi */
} RCC_TypeDef;

_Static_assert(offsetof(GPIO_TypeDef, MODER) == 0x00, "MODER");
_Static_assert(offsetof(GPIO_TypeDef, ODR) == 0x14, "ODR");
_Static_assert(offsetof(GPIO_TypeDef, BSRR) == 0x18, "BSRR");
_Static_assert(offsetof(RCC_TypeDef, AHB1ENR) == 0x30, "AHB1ENR");

#define GPIOD ((GPIO_TypeDef *)GPIOD_BASE)
#define RCC   ((RCC_TypeDef *)RCC_BASE)

#endif /* REG_H */
