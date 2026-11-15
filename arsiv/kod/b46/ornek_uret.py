# -*- coding: utf-8 -*-
"""MCU ornek penceresi: test setinden 2 normal, 2 anomali."""
import os
import numpy as np
from telemetri import veri_seti

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    _, _, Xte, yte = veri_seti()
    normal = np.where(yte == 0)[0]
    anomali = np.where(yte == 1)[0]
    secim = [int(normal[0]), int(anomali[0]),
             int(normal[1]), int(anomali[1])]
    etiket = ", ".join(str(int(yte[i])) for i in secim)
    L = ["/* ornek.h - otomatik uretildi (ornek_uret.py). */",
         "#ifndef ORNEK_H", "#define ORNEK_H", "",
         "#define ORNEK_SAYI 4",
         "static const int ORNEK_ETIKET[4] = { %s };" % etiket,
         "static const float ORNEK[4][32][4] = {"]
    for i in secim:
        L.append("  {")
        for t in range(32):
            vals = ", ".join("%.4ff" % v for v in Xte[i, t])
            L.append("    {%s}," % vals)
        L.append("  },")
    L += ["};", "", "#endif"]
    yol = os.path.join(HERE, "ornek.h")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("secim:", secim, "etiketler:", [int(yte[i]) for i in secim])
