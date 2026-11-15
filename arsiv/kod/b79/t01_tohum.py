# -*- coding: utf-8 -*-
"""Deney 1: tohum gurultusu. Ayni yontem, 200 tohum (0..199).

Hic degisiklik yok: her kosu ayni ayarlarla (Adam, lr=0,003,
30 epoch, batch 32). Tek fark tohum. Iki tohumlu kosularin farki
"sifir" olmali; degil. Bu fark, bir yontemin "daha iyi" sayilmasi
icin gereken esigi belirler.
"""
import numpy as np
from ortak79 import veri, egit, csv_yaz

D = veri()
satir = []
for s in range(200):
    va, te = egit(s, D=D)
    satir.append((s, "%.4f" % va, "%.4f" % te))
csv_yaz("b79_tohum_havuz.csv", satir, ["tohum", "dogrulama", "test"])

te = np.array([float(r[2]) for r in satir])
va = np.array([float(r[1]) for r in satir])
print("havuz n=200  test ort=%.4f  sd=%.4f"
      % (te.mean(), te.std(ddof=1)))
print("havuz n=200  dogr ort=%.4f  sd=%.4f"
      % (va.mean(), va.std(ddof=1)))
print("min=%.4f  max=%.4f  aralik=%.4f"
      % (te.min(), te.max(), te.max() - te.min()))

# Ayni yontemin iki kosusu: (0,1), (2,3), ... 100 cift
fark = te[0::2][:100] - te[1::2][:100]
print("100 cift farki: ort=%+.4f  sd=%.4f"
      % (fark.mean(), fark.std(ddof=1)))
print("|fark| >= 0.01 : %d / 100" % np.sum(np.abs(fark) >= 0.01))
print("|fark| >= 0.02 : %d / 100" % np.sum(np.abs(fark) >= 0.02))
print("en buyuk |fark| = %.4f" % np.abs(fark).max())
csv_yaz("b79_tohum_fark.csv",
        [(i, "%.4f" % f) for i, f in enumerate(fark)],
        ["cift", "fark"])
