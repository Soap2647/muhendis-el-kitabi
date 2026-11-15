# -*- coding: utf-8 -*-
# Tavlama (TSP) ve rastgele arama.
import csv
import itertools
import numpy as np
from scipy.optimize import minimize, minimize_scalar

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 1) Tavlama: gezgin satici ----
def mesafe_matrisi(P):
    return np.sqrt(((P[:, None, :] - P[None, :, :]) ** 2).sum(-1))


def tur_maliyeti(D, tur):
    n = len(tur)
    return sum(D[tur[i], tur[(i + 1) % n]] for i in range(n))


def tavlama(D, T0=50.0, alfa=0.9995, adim=60000, seed=0):
    r = np.random.default_rng(seed)
    n = D.shape[0]
    tur = list(r.permutation(n))
    c = tur_maliyeti(D, tur)
    en_iyi, en_c = list(tur), c
    T = T0
    gecmis = []
    for k in range(adim):
        i, j = sorted(r.choice(n, 2, replace=False))
        yeni = tur[:i] + tur[i:j + 1][::-1] + tur[j + 1:]   # 2-opt
        cy = tur_maliyeti(D, yeni)
        if cy < c or r.random() < np.exp(-(cy - c) / T):
            tur, c = yeni, cy
            if c < en_c:
                en_iyi, en_c = list(tur), c
        T *= alfa
        if k % 500 == 0:
            gecmis.append((k, T, c))
    return en_iyi, en_c, gecmis


def kesin(D):
    n = D.shape[0]
    en = min(tur_maliyeti(D, (0,) + p)
             for p in itertools.permutations(range(1, n)))
    return en


ok = 0
for tohum in range(5):
    P = np.random.default_rng(10 + tohum).uniform(0, 100, (9, 2))
    D = mesafe_matrisi(P)
    _, sa_c, _ = tavlama(D, adim=20000, seed=tohum)
    kes = kesin(D)
    ok += int(abs(sa_c - kes) < 1e-9)
    print("tohum %d: SA=%.4f  kesin=%.4f" % (tohum, sa_c, kes))
print("9 sehir, 5 tohum: kesin optimumu bulan SA sayisi =", ok)

P = np.random.default_rng(3).uniform(0, 100, (30, 2))
D = mesafe_matrisi(P)
tur, c_sa, gec = tavlama(D, T0=50.0, alfa=0.9997, adim=120000, seed=1)
print("30 sehir: SA maliyeti=%.3f" % c_sa)
with open(VERI + "b50_tavlama.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["adim", "T", "maliyet"])
    for k, T, cc in gec:
        w.writerow([k, "%.6f" % T, "%.4f" % cc])

# ---- 2) Rastgele arama vs izgara (Rastrigin, 2B, 100 eval) ----
def rastrigin(x, y):
    return 20 + x * x + y * y - 10 * np.cos(2 * np.pi * x) \
        - 10 * np.cos(2 * np.pi * y)


izgara = np.linspace(-5.12, 5.12, 10)
en_izg = min(rastrigin(a, b) for a in izgara for b in izgara)
rs = []
for tohum in range(20):
    r = np.random.default_rng(tohum)
    p = r.uniform(-5.12, 5.12, (100, 2))
    rs.append(min(rastrigin(a, b) for a, b in p))
print("\nizgara (10x10) en iyi f=%.4f" % en_izg)
print("rastgele (100) en iyi f: ort=%.4f  en kotu=%.4f  en iyi=%.4f"
      % (np.mean(rs), np.max(rs), np.min(rs)))

