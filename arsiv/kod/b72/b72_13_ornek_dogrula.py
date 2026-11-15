# -*- coding: utf-8 -*-
"""Bolum 72 Cozumlu Ornekler: (2) iki adimli beta takvimi icin abar
ve ileri surecin ortalama/varyansi; (4) gizil kodun 2, 4, 8 bitle
kuantizasyonu ve bit butcesi."""
import math
import numpy as np

# ---------- Ornek 2: beta_1 = 0,1, beta_2 = 0,2 ----------
b1, b2 = 0.1, 0.2
a1, a2 = 1 - b1, 1 - b2
ab1, ab2 = a1, a1 * a2
print("== Ornek 2: abar_1, abar_2 ==")
print(f"abar_1 = {ab1:.4f}   abar_2 = {ab2:.4f}")
x0 = 2.0
for t, ab in [(1, ab1), (2, ab2)]:
    mu = math.sqrt(ab) * x0
    var = 1 - ab
    rng = np.random.default_rng(0)
    e = rng.standard_normal(400000)
    xt = math.sqrt(ab) * x0 + math.sqrt(var) * e
    print(f"t={t}: kapali ort={mu:.4f} var={var:.4f} | "
          f"MC ort={xt.mean():.4f} var={xt.var():.4f}")

# ---------- Ornek 4: tekduzgun gizil kod, b bit ----------
print()
print("== Ornek 4: U[-1,1] kuantizasyonu, bit basina MSE ==")
rng = np.random.default_rng(1)
z = rng.uniform(-1, 1, 1_000_000)
for b in [2, 4, 8]:
    L = 2 ** b
    delta = 2.0 / L
    idx = np.clip(np.floor((z + 1) / delta), 0, L - 1)
    zq = -1 + (idx + 0.5) * delta
    mse_mc = float(((z - zq) ** 2).mean())
    print(f"b={b}: delta={delta:.5f} teorik={delta**2 / 12:.3e} "
          f"MC={mse_mc:.3e}")
d = 16
print()
print("== Bit butcesi: d = 16 boyut ==")
for b in [2, 4, 8]:
    print(f"b={b}: R = d*b = {d * b} bit / ornek")
