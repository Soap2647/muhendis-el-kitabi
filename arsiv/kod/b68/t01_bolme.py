# -*- coding: utf-8 -*-
"""Bölüm 68.4: rastgele ve zamana göre bölme, sızıntı ölçümü."""
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from ortak import iha_telemetri, pencere, mae, rmse, yaz_csv, HEDEF

n, W = 24000, 10
Z = iha_telemetri(n, seed=11)
X, Y = pencere(Z, W, 1)
m = len(X)
y = Y[:, 0]
F = X.reshape(m, -1)
hb = np.arange(m) + W                     # hedefin zaman indeksi
ntr, nva = int(0.6 * n), int(0.8 * n)
zt_tr, zt_te = hb < ntr, hb >= nva        # zamana göre bölme

rng = np.random.default_rng(3)
perm = rng.permutation(m)
rt_te = np.zeros(m, bool)
rt_te[perm[:int(0.2 * m)]] = True         # rastgele: %20 test
rt_tr = ~rt_te


def olcekle(Fx, tr, mu=None, sd=None):
    if mu is None:
        mu, sd = Fx[tr].mean(0), Fx[tr].std(0) + 1e-8
    return (Fx - mu) / sd, mu, sd


def deney(tr, te, model, Fx):
    A, _, _ = olcekle(Fx, tr)
    model.fit(A[tr], y[tr])
    p = model.predict(A[te])
    return mae(y[te], p), rmse(y[te], p)


sonuc = []
for ad, mdl in [("kNN (k=5)", lambda: KNeighborsRegressor(5)),
                ("Doğrusal", lambda: LinearRegression())]:
    for bolme, tr, te in [("zaman", zt_tr, zt_te),
                          ("rastgele", rt_tr, rt_te)]:
        a, r = deney(tr, te, mdl(), F)
        sonuc.append((ad, bolme, a, r))

# Geleceği gören özellik: merkezli pencere ortalaması
# (merkezli kayan ortalama: rolling(center=True) hatası)
g = Z[:, HEDEF]
gelecek = (g[hb - 1] + g[hb] + g[np.minimum(hb + 1, n - 1)]) / 3
F2 = np.column_stack([F, gelecek])
a, r = deney(zt_tr, zt_te, LinearRegression(), F2)
sonuc.append(("Doğrusal+gelecek", "zaman", a, r))

# Ölçekleme sızıntısı: ortalama ve sapma tüm veriden
A_all, _, _ = olcekle(F, np.ones(m, bool))
lr = LinearRegression().fit(A_all[zt_tr], y[zt_tr])
p = lr.predict(A_all[zt_te])
sonuc.append(("Doğrusal (tüm veriyle ölçek)", "zaman",
              mae(y[zt_te], p), rmse(y[zt_te], p)))

print("%-28s %-9s %8s %8s" % ("Yöntem", "bölme", "MAE", "RMSE"))
for ad, b, a, r in sonuc:
    print("%-28s %-9s %8.4f %8.4f" % (ad, b, a, r))
print("test boyutu zaman=%d rastgele=%d" % (zt_te.sum(), rt_te.sum()))

yaz_csv("b68_bolme_sonuc.csv", ["yontem", "bolme", "mae", "rmse"],
        [(a, b, round(c, 5), round(d, 5)) for a, b, c, d in sonuc])
yaz_csv("b68_bolme_maske.csv", ["hb", "rastgele_test", "zaman_test"],
        [(i, int(rt_te[i]), int(zt_te[i]))
         for i in range(14000, 20000)])
