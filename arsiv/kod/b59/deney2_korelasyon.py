# deney2_korelasyon.py -- rho, B ve ortalamanin varyansi (formul + simulasyon)
import csv, os
import numpy as np
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
sigma2 = 1.0
rng = np.random.default_rng(59)
R = 20000
rows = []
print("rho  B   formul    simulasyon")
for rho in [0.0, 0.3, 0.6, 0.9]:
    for B in [1, 2, 5, 10, 25, 50, 100, 200]:
        Z0 = rng.standard_normal((R, 1))
        E = rng.standard_normal((R, B))
        X = np.sqrt(rho) * Z0 + np.sqrt(1 - rho) * E   # Var=1, corr=rho
        ort = X.mean(axis=1)
        sim = ort.var()
        form = rho * sigma2 + (1 - rho) * sigma2 / B
        rows.append((rho, B, form, sim))
        if B in (1, 10, 100):
            print("%.1f %4d  %.4f   %.4f" % (rho, B, form, sim))
with open(os.path.join(VERI, "b59_korelasyon.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["rho", "B", "formul", "simulasyon"])
    w.writerows(rows)
