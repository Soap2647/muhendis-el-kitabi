# -*- coding: utf-8 -*-
"""Cortex-M4 (Thumb) kodunu Unicorn ile calistirir, Python modeliyle
karsilastirir. Kesme cercevesi (NVIC) emule EDILMEZ; yalnizca kesme
govdesi ve ana dongu kodu calisir.
Kullanim: python unicorn_kisa.py emu.bin emu.elf
"""
import random
import subprocess
import sys
from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS,
                     UC_PROT_ALL)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_SP, UC_ARM_REG_LR)

FLASH, RAM = 0x08000000, 0x20000000
SENTINEL = 0x08000F00          # donus adresi: burada durulur
NM = "arm-none-eabi-nm"        # PATH'te olmali

bin_yolu, elf_yolu = sys.argv[1], sys.argv[2]
sembol = {}
for satir in subprocess.run([NM, "-n", elf_yolu], capture_output=True,
                            text=True).stdout.splitlines():
    p = satir.split()
    if len(p) == 3:
        sembol[p[2]] = int(p[0], 16)

uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
uc.mem_map(FLASH, 0x00100000, UC_PROT_ALL)
uc.mem_map(RAM, 0x00020000, UC_PROT_ALL)
uc.mem_write(FLASH, open(bin_yolu, "rb").read())


def cagir(ad, r0=0, r1=0):
    """Thumb fonksiyonunu cagir, R0'daki donus degerini dondur."""
    uc.reg_write(UC_ARM_REG_SP, RAM + 0x1FFF0)
    uc.reg_write(UC_ARM_REG_R0, r0)
    uc.reg_write(UC_ARM_REG_R1, r1)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
    uc.mem_write(SENTINEL, b"\x00\xbf")          # nop
    uc.emu_start(sembol[ad] | 1, SENTINEL, count=20000)
    return uc.reg_read(UC_ARM_REG_R0)


def oku32(adr):
    return int.from_bytes(uc.mem_read(adr, 4), "little")


class Model:
    """Referans: 16 yuvali, 15 elemanli SPSC tampon."""
    def __init__(self):
        self.veri, self.bas, self.kuy, self.dusen = [0] * 16, 0, 0, 0

    def yaz(self, b):
        s = (self.kuy + 1) & 15
        if s == self.bas:
            self.dusen += 1
            return 0
        self.veri[self.kuy], self.kuy = b, s
        return 1

    def oku(self):
        if self.bas == self.kuy:
            return None
        b = self.veri[self.bas]
        self.bas = (self.bas + 1) & 15
        return b


def test_rastgele(tohum, adim=3000):
    rnd = random.Random(tohum)
    m, rb, tmp = Model(), sembol["g_rb"], sembol["g_rb"] + 0x40
    uc.mem_write(rb, b"\x00" * 28)
    hata = 0
    for _ in range(adim):
        if rnd.random() < 0.55:
            b = rnd.randrange(256)
            cagir("adc_isr_govde", b)          # ISR govdesi
            m.yaz(b)
        else:
            r = cagir("rb_oku", rb, tmp)       # ana dongu
            b = m.oku()
            if (b is None) != (r == 0):
                hata += 1
            elif b is not None and uc.mem_read(tmp, 1)[0] != b:
                hata += 1
        if (oku32(rb), oku32(rb + 4), oku32(rb + 24)) != \
           (m.bas, m.kuy, m.dusen):
            hata += 1
    return hata, m.dusen


if __name__ == "__main__":
    rb = sembol["g_rb"]
    uc.mem_write(rb, b"\x00" * 28)
    dizi = [cagir("rb_yaz", rb, k) for k in range(16)]
    print("16 yazma sonucu:", dizi)
    print("bas, kuyruk, dusen =", oku32(rb), oku32(rb + 4),
          oku32(rb + 24))
    for tohum in (1, 2, 3):
        hata, dusen = test_rastgele(tohum)
        print("tohum=%d hata=%d dusen=%d" % (tohum, hata, dusen))
    ps = sembol["g_paylasilan"]
    uc.mem_write(ps, b"\x00" * 4)
    cagir("kritik_artir", 1000)
    print("kritik_artir(1000) -> %d" % oku32(ps))
