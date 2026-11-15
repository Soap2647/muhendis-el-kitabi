# kararsizlik.py -- alt orneklerde kok bolunmesi ve karar siniri
import csv
import numpy as np
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from agac import KararAgaci

X, y = make_moons(n_samples=400, noise=0.3, random_state=59)
Xa, Xb, ya, yb = train_test_split(X, y, test_size=0.3,
                                  random_state=59)
kokler = []
for sd in range(50):
    r = np.random.default_rng(sd)
    idx = r.choice(len(Xa), size=len(Xa) // 2, replace=False)
    t = DecisionTreeClassifier(max_depth=3, random_state=0)
    t.fit(Xa[idx], ya[idx])
    kokler.append((int(t.tree_.feature[0]),
                   round(float(t.tree_.threshold[0]), 2)))
farkli = sorted(set(kokler), key=lambda k: -kokler.count(k))
print("50 alt ornekte farkli kok bolme sayisi:", len(farkli))
for k in farkli[:3]:
    print("ozellik=%d esik=%.2f : %d / 50"
          % (k[0], k[1], kokler.count(k)))

# Tam veri ile yarim veri agaclari arasindaki karar siniri farki
rng = np.random.default_rng(59)
yarim = rng.choice(len(X), size=len(X) // 2, replace=False)
tam = KararAgaci(max_derinlik=5).fit(X, y)
alt = KararAgaci(max_derinlik=5).fit(X[yarim], y[yarim])
gx, gy = np.meshgrid(np.linspace(-1.5, 2.5, 120),
                     np.linspace(-1.0, 1.5, 90))
G = np.column_stack([gx.ravel(), gy.ravel()])
pa, pb = tam.tahmin(G), alt.tahmin(G)
print("izgarada iki agacin ayristigi oran: %.4f" % np.mean(pa != pb))
with open("D:/Mevcut Projeler/Kitap/engine/veri/"
          "b59_karar_siniri.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["x1", "x2", "tam_agac", "alt_ornek_agac"])
    for i in range(len(G)):
        w.writerow(["%.4f" % G[i, 0], "%.4f" % G[i, 1], int(pa[i]),
                    int(pb[i])])
