# -*- coding: utf-8 -*-
"""Bölüm 68.1: zaman serisi bileşenleri, durağanlık sezgisi, ACF."""
import numpy as np
from ortak import yaz_csv

rng = np.random.default_rng(7)
n = 600
t = np.arange(n)
trend = 0.02 * t
mevsim = 3.0 * np.sin(2 * np.pi * t / 50)
gurultu = np.zeros(n)
e = rng.normal(0, 1.0, n)
for i in range(1, n):                      # AR(1), phi = 0,6
    gurultu[i] = 0.6 * gurultu[i - 1] + e[i]
seri = trend + mevsim + gurultu


def acf(x, K):
    """Örneklem ACF: r_k = sum (x_t-m)(x_{t+k}-m) / sum (x_t-m)^2."""
    m = x.mean()
    d = x - m
    payda = np.sum(d * d)
    return np.array([np.sum(d[:len(x) - k] * d[k:]) / payda
                     for k in range(K + 1)])


r = acf(seri, 60)
beyaz = acf(e, 60)
band = 1.96 / np.sqrt(n)
print("ACF (seri), gecikme 1,5,10,25,50:")
print(" ", [round(float(r[k]), 3) for k in (1, 5, 10, 25, 50)])
print("ACF (beyaz gürültü), gecikme 1,5,10:")
print(" ", [round(float(beyaz[k]), 3) for k in (1, 5, 10)])
print("Yaklaşık %%95 bant: +-%.3f" % band)

# Durağanlık sezgisi: iki yarının ortalaması ve sapması
for ad, x in [("trend", seri),
              ("AR(1)", gurultu)]:
    a, b = x[:n // 2], x[n // 2:]
    print("%-8s ilk: ort=%6.2f sd=%5.2f | ikinci: ort=%6.2f sd=%5.2f"
          % (ad, a.mean(), a.std(), b.mean(), b.std()))

yaz_csv("b68_bilesen.csv",
         ["t", "seri", "trend", "mevsim", "gurultu"],
         [(i, round(seri[i], 4), round(trend[i], 4),
           round(mevsim[i], 4), round(gurultu[i], 4))
          for i in range(n)])
yaz_csv("b68_acf.csv", ["gecikme", "acf_seri", "acf_beyaz", "bant"],
        [(k, round(r[k], 4), round(beyaz[k], 4), round(band, 4))
         for k in range(61)])
