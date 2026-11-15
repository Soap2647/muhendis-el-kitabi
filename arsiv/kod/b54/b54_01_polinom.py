import csv
import os
import numpy as np
from numpy.polynomial import Polynomial

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(54)

def veri(n):
    x = rng.uniform(0, 1, n)
    y = np.sin(2 * np.pi * x) + rng.normal(0, 0.2, n)
    return x, y

def rmse(p, x, y):
    return np.sqrt(np.mean((p(x) - y) ** 2))

xe, ye = veri(30)          # egitim: 30 ornek
xv, yv = veri(200)         # dogrulama: 200 ornek, ayni dagilim

print("derece  egitim_RMSE  dogrulama_RMSE")
satirlar = []
for d in range(1, 13):
    p = Polynomial.fit(xe, ye, d)
    e, v = rmse(p, xe, ye), rmse(p, xv, yv)
    satirlar.append((d, e, v))
    print("%5d    %10.4f      %12.4f" % (d, e, v))

en_iyi = min(satirlar, key=lambda t: t[2])
print("dogrulamaya gore en iyi derece:", en_iyi[0])

with open(os.path.join(HERE, "veri", "b54_polinom_hata.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["derece", "egitim_rmse", "dogrulama_rmse"])
    w.writerows(satirlar)

# Cizim icin: egitim noktalari ve secilen derecelerin egrileri
izgara = np.linspace(0, 1, 201)
with open(os.path.join(HERE, "veri", "b54_polinom_uyum.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["derece", "x", "y"])
    for d in (1, 3, 9, 12):
        p = Polynomial.fit(xe, ye, d)
        for x, y in zip(izgara, p(izgara)):
            w.writerow([d, "%.5f" % x, "%.5f" % y])
with open(os.path.join(HERE, "veri", "b54_polinom_nokta.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["x", "y"])
    w.writerows(zip(np.round(xe, 5), np.round(ye, 5)))
