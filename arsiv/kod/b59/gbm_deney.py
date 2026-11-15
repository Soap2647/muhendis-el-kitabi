# gbm_deney.py -- ogrenme orani, agac sayisi, erken durdurma
import csv
import numpy as np
from sklearn.datasets import make_friedman1
from sklearn.model_selection import train_test_split
from gbm import GradyanArtirma


def veri(sd):
    X, y = make_friedman1(n_samples=1000, n_features=10, noise=1.0,
                          random_state=sd)
    return train_test_split(X, y, test_size=0.3, random_state=sd)


print("== Ogrenme orani x agac sayisi (3 tohum, test MSE)")
T = 400
egri = {}
for eta in [1.0, 0.3, 0.1, 0.03]:
    kayit = []
    for sd in range(3):
        Xtr, Xte, ytr, yte = veri(sd)
        m = GradyanArtirma(T=T, eta=eta, derinlik=3, min_yaprak=5)
        m.fit(Xtr, ytr, Xte, yte)
        kayit.append([g[1] for g in m.gecmis])
    egri[eta] = np.array(kayit).mean(axis=0)
    e = egri[eta]
    print("eta=%.2f  T=50: %.3f  T=100: %.3f  T=400: %.3f  "
          "en iyi T=%d (%.3f)" % (eta, e[49], e[99], e[399],
          int(np.argmin(e)) + 1, e.min()))
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_gbm_egri.csv",
          "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["agac_sayisi", "eta", "test_mse_ort"])
    for eta in egri:
        for t in range(T):
            w.writerow([t + 1, eta, "%.5f" % egri[eta][t]])

print("\n== Erken durdurma (eta=0.1): T dogrulamayla secilir")
for sd in range(3):
    Xtr, Xte, ytr, yte = veri(sd)
    a, v, c, dv = train_test_split(Xtr, ytr, test_size=0.2,
                                   random_state=sd)
    m = GradyanArtirma(T=400, eta=0.1, derinlik=3, min_yaprak=5)
    m.fit(a, c, v, dv)
    tb = int(np.argmin([g[1] for g in m.gecmis])) + 1
    print("tohum %d: secilen T=%3d  test(T secilen)=%.3f  "
          "test(T=400)=%.3f"
          % (sd, tb, np.mean((yte - m.ham(Xte, tb)) ** 2),
             np.mean((yte - m.ham(Xte, 400)) ** 2)))
