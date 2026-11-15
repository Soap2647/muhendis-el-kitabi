# deney3_gbm.py -- ogrenme orani, agac sayisi, erken durdurma, adim izi
import csv, os
import numpy as np
from gbm import GradyanArtirma, sigmoid
from sklearn.datasets import make_friedman1
from sklearn.model_selection import train_test_split
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"

def veri(sd):
    X, y = make_friedman1(n_samples=1000, n_features=10, noise=1.0,
                          random_state=sd)
    return train_test_split(X, y, test_size=0.3, random_state=sd)

print("== 1. Ogrenme orani x agac sayisi (friedman1, 3 tohum)")
etalar = [1.0, 0.3, 0.1, 0.03]
T = 400
egriler = {}
for eta in etalar:
    kayitlar = []
    for sd in range(3):
        Xtr, Xte, ytr, yte = veri(sd)
        m = GradyanArtirma(T=T, eta=eta, derinlik=3, min_yaprak=5)
        m.fit(Xtr, ytr, Xte, yte)
        kayitlar.append([g[1] for g in m.gecmis])
    egriler[eta] = np.array(kayitlar)            # (3, T) test MSE
    son = egriler[eta].mean(axis=0)
    en = int(np.argmin(son))
    print("eta=%.2f  T=50: %.3f  T=100: %.3f  T=400: %.3f  "
          "en iyi T=%d (%.3f)" % (eta, son[49], son[99], son[399],
          en + 1, son[en]))
with open(os.path.join(VERI, "b59_gbm_egri.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["agac_sayisi", "eta", "test_mse_ort", "test_mse_ss"])
    for eta in etalar:
        for t in range(T):
            w.writerow([t + 1, eta, egriler[eta][:, t].mean(),
                        egriler[eta][:, t].std()])

print("\n== 2. Erken durdurma (eta=0.1): dogrulama ile T secimi")
rows = []
for sd in range(3):
    Xtr, Xte, ytr, yte = veri(sd)
    a, v, c, dv = train_test_split(Xtr, ytr, test_size=0.2,
                                   random_state=sd)
    m = GradyanArtirma(T=400, eta=0.1, derinlik=3, min_yaprak=5)
    m.fit(a, c, v, dv)
    val = np.array([g[1] for g in m.gecmis])
    tb = int(np.argmin(val)) + 1
    test_tb = np.mean((yte - m.ham(Xte, tb)) ** 2)
    test_400 = np.mean((yte - m.ham(Xte, 400)) ** 2)
    rows.append((sd, tb, test_tb, test_400))
    print("tohum %d: secilen T=%3d  test MSE(T=secilen)=%.3f  "
          "test MSE(T=400)=%.3f" % rows[-1])

print("\n== 3. Adim izi: 1B oyuncak veri (n=40, derinlik 2, eta=1)")
rng = np.random.default_rng(59)
x = np.sort(rng.uniform(0, 6, 40))
y = np.sin(x) + rng.normal(0, 0.2, 40)
X1 = x.reshape(-1, 1)
m = GradyanArtirma(T=3, eta=1.0, derinlik=2, min_yaprak=3)
m.fit(X1, y)
F = np.full(len(y), m.f0)
kolonlar = {"x": x, "y": y, "F0": F.copy()}
for t in range(3):
    r = y - F
    kolonlar["r%d" % t] = r
    F = F + m.agaclar[t].olasilik(X1)
    kolonlar["F%d" % (t + 1)] = F.copy()
kol = list(kolonlar.keys())
with open(os.path.join(VERI, "b59_gbm_adim.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(kol)
    for i in range(len(x)):
        w.writerow([round(float(kolonlar[k][i]), 5) for k in kol])
for t in range(3):
    print("adim %d: artik ort. kare=%.4f -> sonra=%.4f" % (
        t + 1, np.mean(kolonlar["r%d" % t] ** 2),
        np.mean((y - kolonlar["F%d" % (t + 1)]) ** 2)))
