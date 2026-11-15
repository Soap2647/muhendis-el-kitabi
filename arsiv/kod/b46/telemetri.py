# -*- coding: utf-8 -*-
"""Sentetik EV telemetri pencereleri. GERCEK VERI DEGILDIR.

Dort kanal, her pencerede L = 32 ornek (10 Hz, 3,2 saniye):
  kanal 0: hucre gerilimi  [V]
  kanal 1: hucre sicakligi [derece C]
  kanal 2: akim            [A]
  kanal 3: motor devri     [rpm / 100]

Ozellik vektoru (20 deger): 5 istatistik x 4 kanal.
Sira: [ort(4), std(4), min(4), maks(4), egim(4)].
Indeks = tur*4 + kanal.
"""
import numpy as np

L = 32
KANAL = 4
NOZ = 20
TOHUM = 46


def normal_pencere(rng):
    t = np.arange(L) / 10.0
    v = rng.uniform(3.55, 3.85) + rng.normal(0.0, 0.004, L)
    T0 = rng.uniform(25.0, 40.0)
    drift = 0.01 * rng.uniform(0, 1) * np.arange(L)
    T = T0 + rng.normal(0.0, 0.08, L) + drift
    I0 = rng.uniform(20.0, 80.0)
    frek = rng.uniform(0.8, 2.0)
    faz = rng.uniform(0, 2 * np.pi)
    I = I0 + 0.1 * I0 * np.sin(2 * np.pi * frek * t + faz)
    I = I + rng.normal(0.0, 1.0, L)
    n = rng.uniform(15.0, 40.0) + rng.normal(0.0, 0.2, L)
    return np.stack([v, T, I, n], axis=1)


def anomali_uygula(p, rng):
    p = p.copy()
    tip = rng.integers(0, 4)
    siddet = rng.uniform(0.4, 1.0)  # 0.4 zor, 1.0 belirgin
    if tip == 0:  # gerilim cokmesi (hucre dengesizligi)
        rampa = np.linspace(0, 1, L)
        p[:, 0] -= siddet * rng.uniform(0.10, 0.30) * rampa
    elif tip == 1:  # termal yukselme (sogutma arizasi)
        rampa = np.linspace(0, 1, L) ** 1.5
        p[:, 1] += siddet * rng.uniform(6, 18) * rampa
    elif tip == 2:  # akim sicramasi (kisa sureli)
        for _ in range(rng.integers(1, 4)):
            s = rng.integers(0, L - 2)
            p[s:s + 2, 2] += siddet * rng.uniform(40, 90)
    else:  # devir dusmesi (kismi takilma)
        s = rng.integers(0, L // 2)
        p[s:, 3] -= siddet * rng.uniform(5, 15)
    return p


def ozellik(p):
    """(L, 4) pencereden 20 ozellik. Egim: en kucuk kareler."""
    t = np.arange(L) - (L - 1) / 2.0
    ort = p.mean(axis=0)
    std = p.std(axis=0)
    mn = p.min(axis=0)
    mx = p.max(axis=0)
    egim = (t[:, None] * (p - ort)).sum(axis=0) / (t ** 2).sum()
    return np.concatenate([ort, std, mn, mx, egim])


def veri_uret(n, rng, anomali_orani=0.3):
    X = np.zeros((n, L, KANAL))
    y = (rng.uniform(size=n) < anomali_orani).astype(np.int64)
    for i in range(n):
        p = normal_pencere(rng)
        if y[i] == 1:
            p = anomali_uygula(p, rng)
        X[i] = p
    return X, y


def veri_seti():
    """Egitim (4000) ve test (2000) pencereleri; tohum sabit (46)."""
    rng = np.random.default_rng(TOHUM)
    Xtr, ytr = veri_uret(4000, rng)
    Xte, yte = veri_uret(2000, rng)
    return Xtr, ytr, Xte, yte


if __name__ == "__main__":
    Xtr, ytr, Xte, yte = veri_seti()
    F = np.array([ozellik(p) for p in Xte])
    print("egitim:", Xtr.shape, "anomali:", ytr.mean().round(3))
    print("test  :", Xte.shape, "anomali:", yte.mean().round(3))
    print("ilk ozellik vektoru (test[0]):")
    print(np.round(F[0], 3))
