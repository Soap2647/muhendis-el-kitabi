# -*- coding: utf-8 -*-
"""Cortex-M4 ikilisini Unicorn ile calistirir (simulasyon).

Kullanim: python -I harness.py <elf> <bin> <cikti_klasoru>
  <bin> : objcopy -O binary ile uretilmis flash goruntusu
Ciktilar: ekrana dokum; ayrica <cikti_klasoru> altina
  startup_iz.csv (startup komutlari, r1-r3 durumu) ve
  led_trafik.csv (GPIOD BSRR yazmalari).
Not: Unicorn islevsel bir emulatordur; zamanlama ve cevre
birimi davranisi modellenmez. BSRR yazmasi ODR'yi degistirmez
(donanimda degistirir); bu bir model farkidir.
"""
import os
import struct
import subprocess
import sys

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS
from unicorn import UC_PROT_ALL, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_R1
from unicorn.arm_const import UC_ARM_REG_R2, UC_ARM_REG_R3

# Windows'ta Python'dan tam yol: ortam PATH'ine bagli olmasin
NM = ("C:/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins/"
      "com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32."
      "13.3.rel1.win32_1.0.0.202411081344/tools/bin/"
      "arm-none-eabi-nm.exe")
FLASH = (0x08000000, 0x00100000)
RAM = (0x20000000, 0x00020000)
PERIF = (0x40020000, 0x00004000)
SCB = (0xE000E000, 0x00001000)
BSRR = 0x40020C18


def simgeler(elf):
    out = subprocess.run([NM, "-n", elf], capture_output=True,
                         text=True, check=True).stdout
    tablo = {}
    for satir in out.splitlines():
        p = satir.split()
        if len(p) == 3:
            tablo[p[2]] = int(p[0], 16)
    return tablo


def main():
    elf, binf, cikti = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(cikti, exist_ok=True)
    sym = simgeler(elf)
    flash = open(binf, "rb").read()

    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    for taban, boy in (FLASH, RAM, PERIF, SCB):
        uc.mem_map(taban, boy, UC_PROT_ALL)
    uc.mem_write(FLASH[0], flash)
    uc.mem_write(RAM[0], b"\xAA" * 0x100)   # bilinen desen

    sp0, reset = struct.unpack("<II", flash[0:8])
    uc.reg_write(UC_ARM_REG_SP, sp0)
    print("Vektor[0] (SP)    = 0x%08X" % sp0)
    print("Vektor[1] (reset) = 0x%08X  (Thumb biti=%d)"
          % (reset, reset & 1))

    say = [0]
    iz = []
    yaz = []
    faz = [1]

    def komut(uc_, adr, boy, _u):
        say[0] += 1
        if faz[0] == 1:
            iz.append((adr,
                       uc_.reg_read(UC_ARM_REG_R1),
                       uc_.reg_read(UC_ARM_REG_R2),
                       uc_.reg_read(UC_ARM_REG_R3)))

    def bellek(uc_, tur, adr, boy, deger, _u):
        if PERIF[0] <= adr < PERIF[0] + PERIF[1]:
            yaz.append((say[0], adr, deger & 0xFFFFFFFF))

    uc.hook_add(UC_HOOK_CODE, komut)
    uc.hook_add(UC_HOOK_MEM_WRITE, bellek)

    def oku32(adr):
        return struct.unpack("<I", bytes(uc.mem_read(adr, 4)))[0]

    main_adr = sym["main"] & ~1
    # 1. faz: reset -> main (startup)
    uc.emu_start(reset, main_adr, 0, 0)
    print("\n[1] Startup: main'e varis, komut = %d" % say[0])
    print("  .data kaynagi (flash)  : 0x%08X"
          % oku32(sym["_sidata"]))
    print("  acilis_degeri (RAM)    : 0x%08X"
          % oku32(sym["acilis_degeri"]))
    print("  .bss ilk kelime        : 0x%08X" % oku32(sym["_sbss"]))
    print("  .bss ikinci kelime     : 0x%08X"
          % oku32(sym["_sbss"] + 4))
    print("  CPACR (0xE000ED88)     : 0x%08X" % oku32(0xE000ED88))
    with open(os.path.join(cikti, "startup_iz.csv"), "w") as f:
        f.write("sira,adres,r1,r2,r3\n")
        for k, (a, r1, r2, r3) in enumerate(iz, 1):
            f.write("%d,0x%08X,0x%08X,0x%08X,0x%08X\n"
                    % (k, a, r1, r2, r3))

    # 2. faz: main dongusu
    faz[0] = 2
    say[0] = 0
    yaz.clear()
    uc.emu_start(main_adr | 1, 0, 0, 2500000)
    print("\n[2] main calisti, komut = %d" % say[0])
    print("  RCC AHB1ENR (0x40023830): 0x%08X" % oku32(0x40023830))
    print("  GPIOD MODER (0x40020C00): 0x%08X" % oku32(0x40020C00))
    print("  sonuc_menzil (RAM)      : %d"
          % oku32(sym["sonuc_menzil"]))
    print("  dongu_sayaci (RAM)      : %d"
          % oku32(sym["dongu_sayaci"]))
    bsrr_list = [y for y in yaz if y[1] == BSRR]
    print("  GPIOD ODR (0x40020C14)  : 0x%08X" % oku32(0x40020C14))
    print("  BSRR yazma sayisi       : %d" % len(bsrr_list))
    print("\nBSRR yazmalari (komut sayisi, deger):")
    for n, adr, deger in bsrr_list:
        print("  komut=%-8d 0x%08X  <- 0x%08X" % (n, adr, deger))
    with open(os.path.join(cikti, "led_trafik.csv"), "w") as f:
        f.write("komut,deger\n")
        for n, adr, deger in bsrr_list:
            f.write("%d,0x%08X\n" % (n, deger))


if __name__ == "__main__":
    main()
