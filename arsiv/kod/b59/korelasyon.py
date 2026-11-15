# korelasyon.py -- rho ve B ile ortalamanin varyansi
import csv
import numpy as np

rng = np.random.default_rng(59)
R = 20000                                # tekrar sayisi
satirlar = []
print("rho    B   formul   simulasyon")
for rho in [0.0, 0.3, 0.6, 0.9]:
    for B in [1, 2, 5, 10, 25, 50, 100, 200]:
        Z0 = rng.standard_normal((R, 1))  # ortak faktor
        E = rng.standard_normal((R, B))   # ozgul hatalar
        X = np.sqrt(rho) * Z0 + np.sqrt(1 - rho) * E
        sim = X.mean(axis=1).var()
        form = rho + (1 - rho) / B        # sigma^2 = 1
        satirlar.append((rho, B, form, sim))
        if B in (1, 10, 100):
            print("%.1f %4d   %.4f   %.4f" % (rho, B, form, sim))
with open("D:/Mevcut Projeler/Kitap/engine/veri/"
          "b59_korelasyon.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["rho", "B", "formul", "simulasyon"])
    w.writerows(satirlar)
