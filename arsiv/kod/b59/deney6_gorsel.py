# deney6_gorsel.py -- 2B bolme kutulari ve karar siniri izgarasi (CSV)
import csv, os
import numpy as np
from agac import KararAgaci
from sklearn.datasets import make_moons
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"

X, y = make_moons(n_samples=300, noise=0.25, random_state=59)
ag = KararAgaci(max_derinlik=3).fit(X, y)
kutular = []

def gez(d, sinir, g):
    if d.sol is None:
        kutular.append((sinir, d.derinlik, int(np.argmax(d.deger))))
        return
    x0, x1, y0, y1 = sinir
    if d.ozellik == 0:
        gez(d.sol, (x0, d.esik, y0, y1), g)
        gez(d.sag, (d.esik, x1, y0, y1), g)
    else:
        gez(d.sol, (x0, x1, y0, d.esik), g)
        gez(d.sag, (x0, x1, d.esik, y1), g)

SIN = (-1.5, 2.5, -1.0, 1.5)
gez(ag.kok, SIN, None)
with open(os.path.join(VERI, "b59_bolme_2b.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["tur", "x1", "x2", "x3", "x4", "etiket", "derinlik"])
    for i in range(len(X)):
        w.writerow(["nokta", "%.5f" % X[i, 0], "%.5f" % X[i, 1], "",
                    "", int(y[i]), ""])
    for (a, b, c, d), dd, lab in kutular:
        w.writerow(["kutu", "%.5f" % a, "%.5f" % b, "%.5f" % c,
                    "%.5f" % d, lab, dd])
print("kutu sayisi:", len(kutular))

# Karar siniri: tam veri ile agac vs %50 alt ornekle agac
rng = np.random.default_rng(59)
yarim = rng.choice(len(X), size=len(X) // 2, replace=False)
ag_t = KararAgaci(max_derinlik=5).fit(X, y)
ag_y = KararAgaci(max_derinlik=5).fit(X[yarim], y[yarim])
gx, gy = np.meshgrid(np.linspace(-1.5, 2.5, 120),
                     np.linspace(-1.0, 1.5, 90))
G = np.column_stack([gx.ravel(), gy.ravel()])
pa = ag_t.tahmin(G)
pb = ag_y.tahmin(G)
with open(os.path.join(VERI, "b59_karar_siniri.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["x1", "x2", "tam_agac", "alt_ornek_agac"])
    for i in range(len(G)):
        w.writerow(["%.4f" % G[i, 0], "%.4f" % G[i, 1], int(pa[i]),
                    int(pb[i])])
print("izgara:", len(G), "tam-alt ayrisma orani: %.4f"
      % np.mean(pa != pb))
print("tam agac derinlik:", ag_t.derinlik(), "alt agac derinlik:",
      ag_y.derinlik())
