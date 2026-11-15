# -*- coding: utf-8 -*-
"""Deney 3: 2x2x2 faktoriyel ablation.

Uc bilesen: BN (BatchNorm), DO (dropout 0,2), COS (kosinus takvimi).
Sekiz kosul x bes tohum (0..4). Tohum basina ana etki:
  etki_A(s) = ortalama(A acik kosullar) - ortalama(A kapali kosullar)
Ana etkinin %95 guven araligi, bes tohumluk t dagilimi ile.
Ablation burada secim icin degil, bilesenin katkisini gormek icin.
"""
import itertools
import numpy as np
from scipy import stats
from ortak79 import veri, egit, csv_yaz

D = veri()
TOHUM = [0, 1, 2, 3, 4]
KOSUL = list(itertools.product([0, 1], repeat=3))  # (BN, DO, COS)
AD = ["BN", "DO", "COS"]

# sonuc[k][s] = test dogrulugu
sonuc = {}
for k in KOSUL:
    sonuc[k] = []
    for s in TOHUM:
        _, te = egit(s, lr=3e-3, bn=bool(k[0]), dropout=0.2 * k[1],
                     cosine=bool(k[2]), D=D)
        sonuc[k].append(te)
    x = np.array(sonuc[k])
    h = stats.t.ppf(0.975, df=len(x) - 1)
    h = h * x.std(ddof=1) / np.sqrt(len(x))
    tag = "+".join(a for a, v in zip(AD, k) if v) or "temel"
    print("%-12s test=%.4f  +-GA %.4f  (sd %.4f)" % (
        tag, x.mean(), h, x.std(ddof=1)))

print("Ana etkiler (tohum basina, 5 tohum):")
satir = []
for k in KOSUL:
    satir.append(("+".join(a for a, v in zip(AD, k) if v) or "temel",
                  k[0], k[1], k[2],
                  "%.4f" % np.mean(sonuc[k])))
csv_yaz("b79_ablation.csv", satir,
        ["kosul", "BN", "DO", "COS", "test_ort"])

for j, a in enumerate(AD):
    ac = [k for k in KOSUL if k[j] == 1]
    kap = [k for k in KOSUL if k[j] == 0]
    etki = np.array([
        np.mean([sonuc[k][s] for k in ac]) -
        np.mean([sonuc[k][s] for k in kap])
        for s in range(len(TOHUM))])
    ort = etki.mean()
    h = stats.t.ppf(0.975, df=4) * etki.std(ddof=1) / np.sqrt(5)
    print("%-4s etki=%+.4f  %%95 GA [%+.4f, %+.4f]" % (
        a, ort, ort - h, ort + h))
