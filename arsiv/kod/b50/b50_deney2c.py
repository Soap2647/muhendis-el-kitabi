# -*- coding: utf-8 -*-
# Ogrenme orani takvimleri: Adam ile sabit, adim, kosinus.
import numpy as np
from b50_core import rosen, rosen_g

np.seterr(all="ignore")


def kalici(fk, esik=1e-6):
    kotu = np.where(np.asarray(fk) >= esik)[0]
    if len(kotu) == 0:
        return 0
    if kotu[-1] == len(fk) - 1:
        return None
    return int(kotu[-1]) + 1


def adam_takvim(g, x0, takvim, n, b1=0.9, b2=0.999, eps=1e-8):
    x = np.asarray(x0, float).copy()
    m = np.zeros_like(x)
    v = np.zeros_like(x)
    yol = [x.copy()]
    for t in range(1, n + 1):
        gr = g(x)
        m = b1 * m + (1 - b1) * gr
        v = b2 * v + (1 - b2) * gr * gr
        mh = m / (1 - b1 ** t)
        vh = v / (1 - b2 ** t)
        x = x - takvim(t) * mh / (np.sqrt(vh) + eps)
        yol.append(x.copy())
    return np.array(yol)


N = 20000
ETA = 3e-3
ETA_MIN = 1e-5
ISINMA = 500


def kosinus(t):
    ilerleme = np.pi * (t - 1) / N
    return ETA_MIN + 0.5 * (ETA - ETA_MIN) * (1 + np.cos(ilerleme))


def isinma_kosinus(t):
    if t <= ISINMA:
        return ETA * t / ISINMA
    ilerleme = np.pi * (t - ISINMA) / (N - ISINMA)
    return ETA_MIN + 0.5 * (ETA - ETA_MIN) * (1 + np.cos(ilerleme))


def adim(t):
    return ETA * 0.3 ** ((t - 1) // 5000)


takvimler = {
    "sabit 3e-4": lambda t: 3e-4,
    "sabit 3e-3": lambda t: ETA,
    "adim (x0.3 / 5000)": adim,
    "kosinus": kosinus,
    "isinma + kosinus": isinma_kosinus,
}
print("Rosenbrock, Adam, N = %d, x0 = (-1.2, 1.0)" % N)
print("takvim              adim(f<1e-6)   son f         en iyi f")
for ad, tk in takvimler.items():
    y = adam_takvim(rosen_g, [-1.2, 1.0], tk, N)
    fk = np.array([rosen(x) for x in y])
    print("%-19s %-14s %-13.3e %.3e"
          % (ad, kalici(fk), fk[-1], fk.min()))
