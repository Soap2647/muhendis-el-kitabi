# -*- coding: utf-8 -*-
"""Bolum 49 - D: Buyuk sayilar, merkezi limit, Monte Carlo.

Cikti CSV'leri engine/veri/ altina yazilir:
  b49_mlt.csv     MLT histogram verisi (Ustel(1) ortalamalari)
  b49_mc_pi.csv   Monte Carlo pi hatasi (n'ye gore, log-log)
"""

import csv
import math
import os

import numpy as np

VERI = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "engine",
    "veri",
)


def buyuk_sayilar(seed=49):
    """Ustel(1) orneklerinin kosan ortalamasi: E[X] = 1."""
    rng = np.random.default_rng(seed)
    x = rng.exponential(1.0, 1_000_000)
    kosan = np.cumsum(x) / np.arange(1, len(x) + 1)
    for n in (10, 100, 1_000, 10_000, 1_000_000):
        print("n=%8d  ort=%.4f" % (n, kosan[n - 1]))


def mlt(seed=49, m=200_000):
    """Ustel(1) icin Z = (Xbar - 1) * sqrt(n) standartlastirmasi.

    Bins: [-4, 4] icinde 40 kutu. Yogunluk, kutu genisligine bolunmus
    oranla verilir; normal yogunluk ile birlikte karsilastirilir.
    """
    rng = np.random.default_rng(seed)
    kenar = np.linspace(-4, 4, 41)
    satirlar = [["n", "merkez", "yogunluk"]]
    for n in (1, 2, 5, 30):
        x = rng.exponential(1.0, (m, n))
        z = (x.mean(axis=1) - 1.0) * math.sqrt(n)
        h, _ = np.histogram(z, bins=kenar)
        yog = h / (m * (kenar[1] - kenar[0]))
        merk = (kenar[:-1] + kenar[1:]) / 2
        for c, y in zip(merk, yog):
            satirlar.append([n, "%.2f" % c, "%.5f" % y])
        # Ozet: ortalama 0 ve varyans 1 hedeflenir.
        print(
            "n=%2d  E[Z]=%.4f  Var(Z)=%.4f  P(|Z|>2)=%.4f"
            % (n, z.mean(), z.var(), np.mean(np.abs(z) > 2))
        )
    return satirlar


def monte_carlo_pi(seed=49, tekrar=20):
    """Birim kare icine rastgele nokta; pi ~ 4 * (iceride / n).

    Her n icin tekrar kosusu yapilir; hata RMS olarak raporlanir.
    """
    rng = np.random.default_rng(seed)
    satirlar = [["n", "rms_hata", "ort_mutlak_hata"]]
    for n in np.logspace(2, 7, 11).astype(int):
        hatalar = []
        for _ in range(tekrar):
            x = rng.random(n)
            y = rng.random(n)
            pi_hat = 4.0 * np.mean(x * x + y * y <= 1.0)
            hatalar.append(pi_hat - math.pi)
        h = np.array(hatalar)
        rms = math.sqrt(np.mean(h * h))
        mab = np.mean(np.abs(h))
        satirlar.append([int(n), "%.6f" % rms, "%.6f" % mab])
    return satirlar


def egim(satirlar):
    """log(rms) - log(n) dogrusunun egimi (en kucuk kareler)."""
    ns = np.array([float(r[0]) for r in satirlar[1:]])
    rms = np.array([float(r[1]) for r in satirlar[1:]])
    a, _ = np.polyfit(np.log(ns), np.log(rms), 1)
    return a


def yaz(ad, satirlar):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(satirlar)
    print("yazildi:", ad)


def main():
    buyuk_sayilar()
    yaz("b49_mlt.csv", mlt())
    pi_satir = monte_carlo_pi()
    yaz("b49_mc_pi.csv", pi_satir)
    for r in pi_satir:
        print(r)
    print("egim (log-log) = %.3f  (beklenen -0.5)" % egim(pi_satir))


if __name__ == "__main__":
    main()
