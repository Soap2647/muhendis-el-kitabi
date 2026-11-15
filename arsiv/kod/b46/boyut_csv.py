# -*- coding: utf-8 -*-
"""Firmware boyut dokumu: arm-none-eabi-size ve nm ciktilari."""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TB = ("C:/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins/"
      "com.st.stm32cube.ide.mcu.externaltools."
      "gnu-tools-for-stm32.13.3.rel1.win32_1.0.0.202411081344"
      "/tools/bin")
MODEL = ["TM_W1", "TM_W2", "TM_B1", "TM_B2", "TM_M1", "TM_RS1",
         "TM_MU", "TM_SD"]


def sayilar(elf):
    out = subprocess.run([TB + "/arm-none-eabi-size.exe", "-A", elf],
                         capture_output=True, text=True).stdout
    text = int(re.search(r"\.text\s+(\d+)", out).group(1))
    bss = int(re.search(r"\.bss\s+(\d+)", out).group(1))
    nmexe = TB + "/arm-none-eabi-nm.exe"
    nm = subprocess.run([nmexe, "-S", "-t", "d", elf],
                        capture_output=True, text=True).stdout
    sembol = {}
    for sat in nm.splitlines():
        p = sat.split()
        if len(p) == 4:
            sembol[p[3]] = int(p[1])
    model = sum(sembol.get(s, 0) for s in MODEL)
    ornek = sembol.get("ORNEK", 0)
    return dict(model=model, ornek=ornek,
                kod=text - model - ornek, ram=bss)


if __name__ == "__main__":
    a = sayilar(os.path.join(HERE, "fw_dsp0.elf"))
    b = sayilar(os.path.join(HERE, "fw_dsp1.elf"))
    yol = os.path.join(VERI, "b46_boyut.csv")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("bilesen,hedef,duz_c_bayt,dsp_bayt\n")
        fh.write("model_parametreleri,flash,%d,%d\n"
                 % (a["model"], b["model"]))
        fh.write("kod_ve_sabitler,flash,%d,%d\n"
                 % (a["kod"], b["kod"]))
        fh.write("ornek_pencereler,flash,%d,%d\n"
                 % (a["ornek"], b["ornek"]))
        fh.write("durum_ve_tamponlar,ram,%d,%d\n"
                 % (a["ram"], b["ram"]))
    print(open(yol, encoding="utf-8").read(), end="")
