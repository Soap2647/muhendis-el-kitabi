# -*- coding: utf-8 -*-
"""Bölüm 68.4: baz modeller (naif, mevsimsel naif, hareketli
ortalama, AR(p)). Tohum 11, 12, 13: her biri ayrı bir telemetri
gerçekleşmesi."""
import numpy as np
from ortak import (iha_telemetri, HEDEF, PERIYOT, mae, rmse,
                   naif_tahmin, mevsimsel_naif, hareketli_ort,
                   ar_sec, ar_egit, ar_1adim, yaz_csv)

n = 24000
ntr, nva = int(0.6 * n), int(0.8 * n)
satir, ozet = [], {}
for seed in (11, 12, 13):
    Z = iha_telemetri(n, seed=seed)
    s = Z[:, HEDEF]
    te = np.arange(nva, n)
    p, kat = ar_sec(s, ntr, nva)
    tahminler = {
        "naif": naif_tahmin(s, te),
        "mevsimsel naif": mevsimsel_naif(s, te),
        "hareketli ort. (10)": hareketli_ort(s, te, 10),
        "AR(%d)" % p: ar_1adim(s, kat, te),
    }
    for ad, pr in tahminler.items():
        a, r = mae(s[te], pr), rmse(s[te], pr)
        satir.append((seed, ad, round(a, 5), round(r, 5)))
        ozet.setdefault(ad, []).append((a, r))

print("Test (son %%20), H=1, hedef: akım (A). Periyot=%d" % PERIYOT)
print("%-22s %16s %16s" % ("Model", "MAE ort+-sd", "RMSE ort+-sd"))
for ad, v in ozet.items():
    a = np.array([x[0] for x in v])
    r = np.array([x[1] for x in v])
    print("%-22s %8.4f+-%.4f %8.4f+-%.4f"
          % (ad, a.mean(), a.std(ddof=1), r.mean(), r.std(ddof=1)))
print("AR derece seçimi (tohum 11, doğrulama MAE):")
Z = iha_telemetri(n, seed=11)
for q in (1, 2, 5, 10, 20, 40):
    k2 = ar_egit(Z[:, HEDEF], ntr, q)
    va = np.arange(ntr, nva)
    pr = ar_1adim(Z[:, HEDEF], k2, va)
    print("  p=%2d  MAE=%.4f" % (q, mae(Z[va, HEDEF], pr)))
yaz_csv("b68_baz.csv", ["tohum", "model", "mae", "rmse"], satir)
