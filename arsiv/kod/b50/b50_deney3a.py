# -*- coding: utf-8 -*-
# SGD gurultusu, Newton karesel yakinsama, LM, cizgi aramasi, BFGS.
import csv
import numpy as np
from scipy.optimize import minimize, least_squares
from b50_core import rosen, rosen_g

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 1) Stokastik gradyan: dogrusal regresyon, n=2000, d=5 ----
rng = np.random.default_rng(0)
n, d = 2000, 5
X = rng.standard_normal((n, d))
wt = np.array([1.0, -2.0, 0.5, 3.0, -1.0])
y = X @ wt + 0.5 * rng.standard_normal(n)
w_star = np.linalg.lstsq(X, y, rcond=None)[0]


def kayip(w):
    return 0.5 * np.mean((X @ w - y) ** 2)


def grad_parti(w, idx):
    Xb = X[idx]
    return Xb.T @ (Xb @ w - y[idx]) / len(idx)


# gurultu: w=0'da parti gradyaninin kovaryans izi, B ile olcekleniyor
w0 = np.zeros(d)
for B in (1, 8, 64, 512):
    gs = np.array([grad_parti(w0, rng.choice(n, B, replace=False))
                   for _ in range(2000)])
    iz = np.trace(np.cov(gs.T))
    print("B=%4d  tr(Cov)=%.4f  B*tr(Cov)=%.2f" % (B, iz, B * iz))

print("\nB  guncelleme  artik kayip (5 tohum ortalamasi)")
for B in (1, 16, 256, 2000):
    artik = []
    for tohum in range(5):
        r = np.random.default_rng(100 + tohum)
        w = np.zeros(d)
        adim = 0
        for _ in range(20):
            p = r.permutation(n)
            for i in range(0, n, B):
                w = w - 0.05 * grad_parti(w, p[i:i + B])
                adim += 1
        artik.append(kayip(w) - kayip(w_star))
    print("%4d  %8d       %.5f" % (B, adim, np.mean(artik)))

