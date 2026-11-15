# -*- coding: utf-8 -*-
"""Bölüm 68, Örnek 4: sızıntılı bir değerlendirmenin hatalarını
tek tek düzeltiyoruz. Her adımda test MAE'si yeniden ölçülür
(tohum 11)."""
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from ortak import iha_telemetri, pencere, HEDEF, mae

n, W = 24000, 10
ntr, nva = int(0.6 * n), int(0.8 * n)
Z = iha_telemetri(n, seed=11)
X, Y = pencere(Z, W, 1)
y = Y[:, 0]
m = len(X)
hb = np.arange(m) + W                 # hedefin zaman indeksi
F = X.reshape(m, -1)
g = Z[:, HEDEF]
gelecek = (g[hb - 1] + g[hb] + g[np.minimum(hb + 1, n - 1)]) / 3


def degerlendir(bolme, tum_veri_olcek, gelecek_var):
    if bolme == "rastgele":
        rng = np.random.default_rng(3)
        te = np.zeros(m, bool)
        te[rng.permutation(m)[:int(0.2 * m)]] = True
        tr = ~te
    else:
        tr = hb < ntr
        te = hb >= nva
    A = np.column_stack([F, gelecek]) if gelecek_var else F
    kaynak = A if tum_veri_olcek else A[tr]
    mu, sd = kaynak.mean(axis=0), kaynak.std(axis=0) + 1e-8
    A = (A - mu) / sd
    model = KNeighborsRegressor(5).fit(A[tr], y[tr])
    return mae(y[te], model.predict(A[te]))


adimlar = [
    ("0. hatalı: rastgele, tüm veri ölçek, gelecek özelliği",
     "rastgele", True, True),
    ("1. rastgele -> zamana göre bölme", "zaman", True, True),
    ("2. ölçek yalnızca eğitimden", "zaman", False, True),
    ("3. geleceği gören özelliği kaldır", "zaman", False, False),
]
print("%-52s %8s" % ("adım", "test MAE"))
for ad, bolme, tum, gel in adimlar:
    print("%-52s %8.4f" % (ad, degerlendir(bolme, tum, gel)))
