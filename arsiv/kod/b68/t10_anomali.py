# -*- coding: utf-8 -*-
"""Bölüm 68.10: tahmin artığına dayalı anomali tespiti.
Eşikler YALNIZCA anomalisiz eğitim/doğrulama artıklarından; test'te
arızalar (5 sıçrama + kayma) enjekte edilmiş; tohum 11; CPU."""
import numpy as np
from ortak import (iha_telemetri, ariza_ekle, HEDEF, ar_egit,
                   ar_1adim, yaz_csv)

n = 24000
ntr, nva = int(0.6 * n), int(0.8 * n)
Z = iha_telemetri(n, seed=11)
Zf, etiket = ariza_ekle(Z, nva, n, seed=5)
s = Zf[:, HEDEF]                          # gözlenen (arızalı) akım
rng = np.random.default_rng(5)          # ariza_ekle ile aynı çekiliş
sicrama = rng.choice(np.arange(nva, n - 10), size=5, replace=False)
sm = np.zeros(n, bool)
sm[sicrama] = True
km = (etiket == 1) & ~sm                  # kayma örnekleri
va, te = np.arange(ntr, nva), np.arange(nva, n)
Q, K = 0.9995, 20


def hareketli(r, k=K):
    cs = np.concatenate([[0.0], np.cumsum(r)])
    out = np.full(len(r), np.nan)
    out[k - 1:] = (cs[k:] - cs[:-k]) / k
    return out


# Zamansal artık: AR(p), tahmin geçmiş GÖZLENEN akımdan
def zamansal(p):
    kat = ar_egit(Z[:, HEDEF], ntr, p)
    r = np.full(n, np.nan)
    idx = np.arange(p, n)
    r[idx] = s[idx] - ar_1adim(s, kat, idx)
    return r

# Bağlamsal artık: akım, aynı andaki hız ve |yuvarlanma| ile tahmin
def baglamsal():
    A = np.column_stack([np.ones(n), Z[:, 1], np.abs(Z[:, 2])])
    kat, *_ = np.linalg.lstsq(A[:ntr], Z[:ntr, HEDEF], rcond=None)
    return s - A @ kat, kat


def degerlendir(ad, r):
    nan = np.isnan(r)
    e = np.quantile(np.abs(r[va][~np.isnan(r[va])]), Q)
    al = (np.abs(r) > e)[te] & ~nan[te]
    y = etiket[te].astype(bool)
    tp, fp = np.sum(al & y), np.sum(al & ~y)
    rs = np.sum(al & sm[te]) / sm[te].sum()
    rk = np.sum(al & km[te]) / km[te].sum()
    print("%-26s %6.3f %6.3f %7.3f %8.2f %6.2f %8.1f"
          % (ad, e, tp / max(al.sum(), 1), tp / y.sum(), rs, rk,
             fp / (~y).sum() * 36000))
    return np.abs(r), e


print("%-26s %6s %6s %7s %8s %6s %8s" % (
    "Detektör", "esik", "prec", "recall", "sicrama", "kayma",
    "FAR/s"))
kayit = {}
for ad, r in [("zamansal AR(5)", zamansal(5)),
              ("zamansal AR(40)", zamansal(40))]:
    kayit[ad] = degerlendir(ad, r)
rb, kat = baglamsal()
kayit["bağlamsal"] = degerlendir("bağlamsal (v, |yuv|)", rb)
mb = hareketli(np.nan_to_num(rb))
kayit["bağlamsal MA20"] = degerlendir("bağlamsal + MA20", mb)
print("bağlamsal katsayılar (sabit, v, |yuv|):", np.round(kat, 4))

yaz_csv("b68_anomali.csv",
        ["t", "etiket", "zaman_ar40", "baglam", "baglam_ma20"],
        [(t, int(etiket[t]),
          round(float(kayit["zamansal AR(40)"][0][t]), 4),
          round(float(kayit["bağlamsal"][0][t]), 4),
          round(float(kayit["bağlamsal MA20"][0][t]), 4))
         for t in te])
yaz_csv("b68_anomali_esik.csv", ["detektor", "esik"],
        [(ad, round(float(kayit[ad][1]), 4))
         for ad in ("zamansal AR(40)", "bağlamsal",
                    "bağlamsal MA20")])
