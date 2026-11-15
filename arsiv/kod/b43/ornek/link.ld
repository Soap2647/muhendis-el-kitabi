/* link.ld - STM32F407VG baglayici betigi (sadelestirilmis).
 * FLASH 1 MB @0x08000000, SRAM 128 KB @0x20000000.
 * Adresler RM0090 bellek haritasina gore. */
ENTRY(Reset_Handler)

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

/* Yigin RAM'in en ustunden asagi dogru buyur */
_estack = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
  .isr_vector :
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector))  /* vektor tablosu basta */
    . = ALIGN(4);
  } > FLASH

  .text :
  {
    . = ALIGN(4);
    *(.text)
    *(.text*)
    . = ALIGN(4);
    _etext = .;
  } > FLASH

  .rodata :
  {
    . = ALIGN(4);
    *(.rodata)
    *(.rodata*)
    . = ALIGN(4);
  } > FLASH

  /* LMA: flash'taki kaynak; VMA: RAM'deki calisma adresi */
  _sidata = LOADADDR(.data);

  .data :
  {
    . = ALIGN(4);
    _sdata = .;
    *(.data)
    *(.data*)
    . = ALIGN(4);
    _edata = .;
  } > RAM AT> FLASH

  .bss (NOLOAD) :
  {
    . = ALIGN(4);
    _sbss = .;
    *(.bss)
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;
  } > RAM

  /* newlib-nano'nun _sbrk'si bu sembolu ister */
  PROVIDE(end = _ebss);

  /* Butce denetimi: veri ile yigin cakismamali */
  ASSERT(_ebss + 1024 <= _estack, "RAM: yigin icin 1 KB yok")
}
