# gbm_adim.py -- 1B oyuncak veride gradyan artirma adim izi (CSV)
import csv
import numpy as np
from gbm import GradyanArtirma

rng = np.random.default_rng(59)
x = np.sort(rng.uniform(0, 6, 40))
y = np.sin(x) + rng.normal(0, 0.2, 40)
X1 = x.reshape(-1, 1)
m = GradyanArtirma(T=3, eta=1.0, derinlik=2, min_yaprak=3)
m.fit(X1, y)
F = np.full(len(y), m.f0)
kol = {"x": x, "y": y, "F0": F.copy()}
for t in range(3):
    kol["r%d" % t] = y - F                 # artik
    F = F + m.agaclar[t].olasilik(X1)      # adim: F += h_t(x)
    kol["F%d" % (t + 1)] = F.copy()
for t in range(3):
    print("adim %d: artik kare ort.=%.4f  adimdan sonra MSE=%.4f"
          % (t + 1, np.mean(kol["r%d" % t] ** 2),
             np.mean((y - kol["F%d" % (t + 1)]) ** 2)))
ad = list(kol.keys())
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_gbm_adim.csv",
          "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(ad)
    for i in range(len(x)):
        w.writerow(["%.5f" % kol[k][i] for k in ad])
