# -*- coding: utf-8 -*-
"""Ornek 3: kanarya icin gereken ornek ve gun sayisi."""
import math

from b77_ab import gerekli_n, guc_sim

GUNLUK = 100000       # gunluk toplam istek
KOL_PAYI = 0.02       # her kola gunun yuzde 2'si

for p0, p1 in [(0.05, 0.06), (0.05, 0.055)]:
    n = gerekli_n(p0, p1)
    gun = math.ceil(n / (GUNLUK * KOL_PAYI))
    print("p0=%.3f p1=%.3f: n=%d, gun=%d, sim guc=%.3f" %
          (p0, p1, n, gun, guc_sim(p0, p1, n)))
