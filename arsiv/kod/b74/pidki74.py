# -*- coding: utf-8 -*-
"""Bolum 74 - PID'in integral terimi: alan kaymasi taramasi.

iha74.py'deki nominal ayarli PID (kp=0.4, ki=0, kd=0.1) ile ayni
kp ve kd'de, integral kazancini ki = 0.02 ve 0.05 yapan iki varyant,
ayni 100 degerlendirme bolumu (tohum 3000+) uzerinde olculur.
"""

import numpy as np
from iha74 import PID, alfa_parametre, olc_bolum

KP, KD = 0.4, 0.1
ALFALAR = (0.0, 0.25, 0.5, 0.75, 1.0)

if __name__ == "__main__":
    import csv
    import os

    veri = "D:/Mevcut Projeler/Kitap/engine/veri"
    satirlar = []
    print(
        "alfa  | ki=0.00 basari IAE | ki=0.02 basari IAE"
        " | ki=0.05 basari IAE"
    )
    for alfa in ALFALAR:
        prm = alfa_parametre(alfa)
        satir = "%.2f " % alfa
        for ki in (0.0, 0.02, 0.05):
            kon = PID(KP, ki, KD)
            sonuc = [
                olc_bolum(kon, prm, s) for s in range(3000, 3100)
            ]
            basari = np.mean([r["basari"] for r in sonuc])
            iae = np.nanmean([r["iae"] for r in sonuc])
            satir += "   %.2f  %.3f         " % (basari, iae)
            satirlar.append((alfa, ki, basari, iae))
        print(satir)
    with open(
        os.path.join(veri, "b74_pid_ki.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        yazar = csv.writer(f)
        yazar.writerow(["alfa", "ki", "basari", "iae"])
        for a, k, b, i in satirlar:
            yazar.writerow(
                ["%.2f" % a, "%.2f" % k, "%.3f" % b, "%.4f" % i]
            )
