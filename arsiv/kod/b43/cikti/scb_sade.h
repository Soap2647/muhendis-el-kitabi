/* SCB_Type: yorum satirlari cikarildi; alan adlari, tipler ve
   dizi boyutlari kaynakla aynidir (core_cm4.h, 445-468). */
typedef struct
{
 __IM uint32_t CPUID;
 __IOM uint32_t ICSR;
 __IOM uint32_t VTOR;
 __IOM uint32_t AIRCR;
 __IOM uint32_t SCR;
 __IOM uint32_t CCR;
 __IOM uint8_t SHP[12U];
 __IOM uint32_t SHCSR;
 __IOM uint32_t CFSR;
 __IOM uint32_t HFSR;
 __IOM uint32_t DFSR;
 __IOM uint32_t MMFAR;
 __IOM uint32_t BFAR;
 __IOM uint32_t AFSR;
 __IM uint32_t PFR[2U];
 __IM uint32_t DFR;
 __IM uint32_t ADR;
 __IM uint32_t MMFR[4U];
 __IM uint32_t ISAR[5U];
 uint32_t RESERVED0[5U];
 __IOM uint32_t CPACR;
} SCB_Type;
