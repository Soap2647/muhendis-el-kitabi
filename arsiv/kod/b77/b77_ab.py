# -*- coding: utf-8 -*-
"""Kanarya / A-B: gereken ornek sayisi, formul ve simulasyon.

Iki esit kol (taban ve aday), her koldan n istek. Hata oranlari
p0 ve p1. Iki oranli z-testi, iki yonlu alfa = 0,05.
"""
import math

import numpy as np
from scipy.stats import norm


def gerekli_n(p0, p1, alfa=0.05, guc=0.8):
    """Her kol icin ornek sayisi (iki oranli z-testi formulu)."""
    za = norm.ppf(1 - alfa / 2)
    zb = norm.ppf(guc)
    pb = (p0 + p1) / 2
    pay = (za * math.sqrt(2 * pb * (1 - pb))
           + zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1)))
    return math.ceil(pay ** 2 / (p1 - p0) ** 2)


def guc_sim(p0, p1, n, alfa=0.05, deneme=20000, seed=0):
    """Ayni testi simule ederek tespit olasiligini olcer."""
    rng = np.random.default_rng(seed)
    x0 = rng.binomial(n, p0, deneme) / n
    x1 = rng.binomial(n, p1, deneme) / n
    pb = (x0 + x1) / 2
    se = np.sqrt(pb * (1 - pb) * 2 / n)
    z = np.abs(x1 - x0) / np.where(se > 0, se, np.inf)
    return float(np.mean(z > norm.ppf(1 - alfa / 2)))


if __name__ == "__main__":
    print("senaryo               n (formul)  guc (formul)  guc (sim)")
    for p0, p1 in [(0.05, 0.06), (0.05, 0.055), (0.05, 0.07)]:
        n = gerekli_n(p0, p1)
        print("p0=%.3f p1=%.3f   %-11d 0.800         %.3f" %
              (p0, p1, n, guc_sim(p0, p1, n)))
    n = gerekli_n(0.05, 0.06)
    print("--- n yarisina inerse (p0=0.05, p1=0.06)")
    yari = n // 2
    print("n=%d guc(sim)=%.3f" % (yari, guc_sim(0.05, 0.06, yari)))
    print("--- sahte alarm: p0=p1=0.05 (fark yok)")
    print("alfa(sim)=%.3f" % guc_sim(0.05, 0.05, n))
