# -*- coding: utf-8 -*-
"""Deney 4: guc analizi (sentetik Monte Carlo, sigma olculmus).

Sigma, Deney 1'in 200 tohumlu havuzundan alinir (test dogrulugu sd).
Iki yontem, bagimsiz tohum kumeleriyle (n tohum her biri), Welch
t testi, alfa=0,05. Her (n, delta) icin 4000 simulasyon: gercek
fark delta iken testin kac kez "fark var" dedigi = guc.
Analitik n icin: n = 2 (z_a/2 + z_b)^2 sigma^2 / delta^2
(z_b icin 0,84 alinir).
"""
import numpy as np
from scipy import stats
from ortak79 import csv_yaz, VERI
import os

pool = np.genfromtxt(os.path.join(VERI, "b79_tohum_havuz.csv"),
                     delimiter=",", skip_header=1, usecols=2)
sigma = pool.std(ddof=1)
print("sigma (test sd, n=200) = %.4f" % sigma)

NS = [2, 3, 5, 10, 20]
DELTAS = [0.005, 0.010, 0.020]
SIM = 4000
rng = np.random.default_rng(79)
satir = []
for d in DELTAS:
    z = stats.norm.ppf(0.975) + stats.norm.ppf(0.80)
    nana = 2 * z ** 2 * sigma ** 2 / d ** 2
    print("delta=%.3f  analitik n/grup = %.1f" % (d, nana))
    for n in NS:
        a = rng.normal(0.0, sigma, size=(SIM, n))
        b = rng.normal(d, sigma, size=(SIM, n))
        p = stats.ttest_ind(b, a, axis=1, equal_var=False).pvalue
        guc = np.mean(p < 0.05)
        print("  n=%2d  guc=%.3f" % (n, guc))
        satir.append((d, n, "%.3f" % guc, "%.1f" % nana))
csv_yaz("b79_guc.csv", satir, ["delta", "n", "guc", "n_analitik"])
