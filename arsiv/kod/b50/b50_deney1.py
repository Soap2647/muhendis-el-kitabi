# -*- coding: utf-8 -*-
# Sayisal gradyan: ileri/merkezi fark, h taramasi.
import csv, os
import numpy as np
from b50_core import rosen, rosen_g

x0 = np.array([-1.2, 1.0])
analitik = rosen_g(x0)
print("analitik gradyan:", analitik)


def ileri(f, x, h):
    g = np.zeros_like(x)
    fx = f(x)
    for i in range(x.size):
        e = np.zeros_like(x)
        e[i] = h
        g[i] = (f(x + e) - fx) / h
    return g


def merkezi(f, x, h):
    g = np.zeros_like(x)
    for i in range(x.size):
        e = np.zeros_like(x)
        e[i] = h
        g[i] = (f(x + e) - f(x - e)) / (2 * h)
    return g


satirlar = []
for dt in (np.float64, np.float32):
    x = x0.astype(dt)
    for k in range(1, 17):
        h = dt(10.0 ** -k)
        gi = ileri(rosen, x, h)
        gm = merkezi(rosen, x, h)
        ei = np.max(np.abs(gi - analitik))
        em = np.max(np.abs(gm - analitik))
        satirlar.append((dt.__name__, float(h), float(ei), float(em)))

for dt_ad in ("float64", "float32"):
    sec = [s for s in satirlar if s[0] == dt_ad]
    en_iyi_i = min(sec, key=lambda s: s[2])
    en_iyi_m = min(sec, key=lambda s: s[3])
    print(dt_ad, "en iyi ileri h = %.0e hata=%.3e"
          % (en_iyi_i[1], en_iyi_i[2]))
    print(dt_ad, "en iyi merk h = %.0e hata=%.3e"
          % (en_iyi_m[1], en_iyi_m[3]))

for k in (2, 4, 6, 8, 10, 12, 14):
    s = [t for t in satirlar
         if t[0] == "float64" and abs(t[1] - 10.0 ** -k) < 1e-30]
    if s:
        print("h=1e-%02d ileri=%.3e merkezi=%.3e"
              % (k, s[0][2], s[0][3]))

CSV = "D:/Mevcut Projeler/Kitap/engine/veri/b50_sonlu_fark.csv"
with open(CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["tip", "h", "hata_ileri", "hata_merkezi"])
    for s in satirlar:
        w.writerow([s[0], "%.1e" % s[1],
                    "%.6e" % s[2], "%.6e" % s[3]])
