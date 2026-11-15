# -*- coding: utf-8 -*-
"""Deney 5: coklu karsilastirma. Gercek fark YOK (H0 dogru).

20 model, her biri baz modelle (n=5 tohum) karsilastiriliyor: 20 test.
Sigma Deney 1'den. 3000 deney; her deneyde 20 p degeri uretilir.
Ucu olculen sey: en az bir "anlamli" sonuc cikma olasiligi (FWER).
Holm ve Bonferroni duzeltmesi ile karsilastirma.
"""
import os
import numpy as np
from scipy import stats
from ortak79 import csv_yaz, VERI, holm

pool = np.genfromtxt(os.path.join(VERI, "b79_tohum_havuz.csv"),
                     delimiter=",", skip_header=1, usecols=2)
sigma = pool.std(ddof=1)
M, N, R = 20, 5, 3000
rng = np.random.default_rng(790)

ham = bon = hol = 0
toplam = {"ham": 0, "bon": 0, "holm": 0}
for _ in range(R):
    base = rng.normal(0.0, sigma, N)
    p = np.array([
        stats.ttest_ind(rng.normal(0.0, sigma, N), base,
                        equal_var=False).pvalue for _ in range(M)])
    ham += np.any(p < 0.05)
    bon += np.any(p * M < 0.05)
    hol += np.any(holm(p) < 0.05)
    toplam["ham"] += np.sum(p < 0.05)
    toplam["bon"] += np.sum(p * M < 0.05)
    toplam["holm"] += np.sum(holm(p) < 0.05)

print("sigma=%.4f  M=%d  n=%d  R=%d" % (sigma, M, N, R))
print("FWER ham     = %.3f" % (ham / R))
print("FWER Bonf.   = %.3f" % (bon / R))
print("FWER Holm    = %.3f" % (hol / R))
print("ort. yanlis alarm (ham) = %.2f" % (toplam["ham"] / R))
csv_yaz("b79_coklu.csv",
        [("ham", "%.4f" % (ham / R), "%.3f" % (toplam["ham"] / R)),
         ("bonferroni", "%.4f" % (bon / R),
          "%.3f" % (toplam["bon"] / R)),
         ("holm", "%.4f" % (hol / R), "%.3f" % (toplam["holm"] / R))],
        ["duzeltme", "fwer", "ort_yanlis_alarm"])
