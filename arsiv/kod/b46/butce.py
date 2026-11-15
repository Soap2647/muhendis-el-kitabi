# -*- coding: utf-8 -*-
"""Katman basina parametre, bellek, MAC butcesi (CSV)."""
import os
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
# (katman, parametre, f32 bayt, int8 modeli bayt, MAC, cikti bayt)
SATIR = [
    ("normalizasyon", 40, 160, 160, 0, 80),
    ("katman1_20x8", 168, 672, 256, 160, 8),
    ("katman2_8x2", 18, 72, 24, 16, 8),
]
if __name__ == "__main__":
    yol = os.path.join(VERI, "b46_butce.csv")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("katman,parametre,bayt_f32,bayt_int8,mac,"
                 "cikti_bayt\n")
        for r in SATIR:
            fh.write("%s,%d,%d,%d,%d,%d\n" % r)
        t = [sum(r[i] for r in SATIR) for i in range(1, 6)]
        fh.write("toplam,%d,%d,%d,%d,%d\n" % tuple(t))
    print(open(yol, encoding="utf-8").read(), end="")
