# -*- coding: utf-8 -*-
"""Bit genisligi taramasi: 8, 7, ... 2 bit (sahte kuantizasyon).

Olcumler (test seti, 2000 pencere):
  yalniz_agirlik : yalniz agirliklar kuantize, aktivasyonlar float
  minmax         : agirlik + girdi + ara aktivasyon, min/maks
                   kalibrasyon
  yuzdelik       : ayni, %0,1 ve %99,9 yuzdelik kalibrasyon
Cikti: engine/veri/b46_bit_dogruluk.csv
"""
import os
import numpy as np
from telemetri import veri_seti
from egit import ozellik_matrisi

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
f32 = np.float32


def qdq_sim(W, bits, eksen=None):
    """Simetrik: Z=0, seviyeler -(2^(b-1)-1) .. 2^(b-1)-1."""
    lv = 2 ** (bits - 1) - 1
    if eksen is None:
        S = np.abs(W).max() / lv
    else:
        S = (np.abs(W).max(axis=eksen) / lv)[:, None]
    q = np.clip(np.round(W / S), -lv, lv)
    return (q * S).astype(f32)


def qdq_asim(x, lo, hi, bits):
    """Asimetrik: [lo, hi] araligi 2^b seviyeye.

    Sifir her zaman temsil edilir."""
    lo = min(lo, 0.0)
    hi = max(hi, 0.0)
    n = 2 ** bits - 1
    S = (hi - lo) / n
    Z = np.round(-lo / S)
    q = np.clip(np.round(x / S) + Z, 0, n)
    return ((q - Z) * S).astype(f32)


def ileri_sim(Xn, p, bits_w, bits_a, lo_x, hi_x, lo_a, hi_a):
    W1 = p["W1"] if bits_w is None else qdq_sim(p["W1"], bits_w, 1)
    W2 = p["W2"] if bits_w is None else qdq_sim(p["W2"], bits_w)
    x = Xn if bits_a is None else qdq_asim(Xn, lo_x, hi_x, bits_a)
    z1 = x @ W1.T + p["b1"]
    a1 = np.maximum(z1, 0.0)
    if bits_a is not None:
        a1 = qdq_asim(a1, lo_a, hi_a, bits_a)
    return a1 @ W2.T + p["b2"]


def main():
    Xtr, ytr, Xte, yte = veri_seti()
    npz = np.load(os.path.join(HERE, "model_f32.npz"))
    p = {k: npz[k] for k in ["W1", "b1", "W2", "b2", "mu", "sd"]}
    Ftr = ozellik_matrisi(Xtr)
    Fte = ozellik_matrisi(Xte)
    Xn_tr = ((Ftr.astype(f32) - p["mu"]) / p["sd"]).astype(f32)
    Xn_te = ((Fte.astype(f32) - p["mu"]) / p["sd"]).astype(f32)
    a1_tr = np.maximum(Xn_tr @ p["W1"].T + p["b1"], 0.0)

    lo_x, hi_x = Xn_tr.min(), Xn_tr.max()
    lo_a, hi_a = a1_tr.min(), a1_tr.max()
    lo_xp, hi_xp = np.percentile(Xn_tr, [0.1, 99.9])
    lo_ap, hi_ap = np.percentile(a1_tr, [0.1, 99.9])

    rows = []
    print("bit  yalniz_agirlik  minmax  yuzdelik")
    for b in [8, 7, 6, 5, 4, 3, 2]:
        z_w = ileri_sim(Xn_te, p, b, None, lo_x, hi_x, lo_a, hi_a)
        z_m = ileri_sim(Xn_te, p, b, b, lo_x, hi_x, lo_a, hi_a)
        z_p = ileri_sim(Xn_te, p, b, b, lo_xp, hi_xp, lo_ap, hi_ap)
        d_w = (z_w.argmax(axis=1) == yte).mean()
        d_m = (z_m.argmax(axis=1) == yte).mean()
        d_p = (z_p.argmax(axis=1) == yte).mean()
        rows.append((b, d_w, d_m, d_p))
        print("%d    %.4f           %.4f  %.4f" % (b, d_w, d_m, d_p))
    yol = os.path.join(VERI, "b46_bit_dogruluk.csv")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("bit,dogruluk_yalniz_agirlik,dogruluk_minmax,"
                 "dogruluk_yuzdelik\n")
        for b, d_w, d_m, d_p in rows:
            fh.write("%d,%.4f,%.4f,%.4f\n" % (b, d_w, d_m, d_p))
    print("CSV yazildi: engine/veri/b46_bit_dogruluk.csv")


if __name__ == "__main__":
    main()
