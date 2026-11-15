# -*- coding: utf-8 -*-
"""Deney 3a: kayip yuzeyinde optimizer yorungeleri.

f(x, y) = 0.5 (x^2 + 10 y^2) kotu kosullu bir ikinci dereceden
fonksiyondur. SGD, momentum ve Adam ayni baslangic noktasindan
baslar; her adimin konumu ve kaybi CSV'ye yazilir."""

import numpy as np
from egitim_np import sgd_momentum, adam_adim
from ortak64 import csv_yaz


def grad(p):
    return np.array([p[0], 10.0 * p[1]])


p0 = np.array([-4.0, 1.0])
ADIM = 60
yol = {}
yol["SGD"] = [p0.copy()]
p = p0.copy()
for _ in range(ADIM):
    p = p - 0.09 * grad(p)
    yol["SGD"].append(p.copy())
yol["Momentum"] = [p0.copy()]
p, v = p0.copy(), np.zeros(2)
for _ in range(ADIM):
    p, v = sgd_momentum(p, grad(p), v, lr=0.09, mu=0.9)
    yol["Momentum"].append(p.copy())
yol["Adam"] = [p0.copy()]
p, m, vv, t = p0.copy(), np.zeros(2), np.zeros(2), 0
for _ in range(ADIM):
    p, m, vv, t = adam_adim(p, grad(p), m, vv, t, lr=0.3)
    yol["Adam"].append(p.copy())

satir = []
for ad, pts in yol.items():
    for k, q in enumerate(pts):
        f = 0.5 * (q[0] ** 2 + 10 * q[1] ** 2)
        satir.append(
            (ad, k, "%.6f" % q[0], "%.6f" % q[1], "%.6f" % f)
        )
    print(
        "%-9s son nokta=(%.4f, %.4f)  f=%.2e"
        % (
            ad,
            pts[-1][0],
            pts[-1][1],
            0.5 * (pts[-1][0] ** 2 + 10 * pts[-1][1] ** 2),
        )
    )
csv_yaz(
    "b64_yorunge.csv", satir, ["optimizer", "adim", "x", "y", "f"]
)
