# -*- coding: utf-8 -*-
"""Bölüm 68.8: İHA telemetrisinde 1 adım ileri akım tahmini.
Baz modeller ve RNN/LSTM/GRU/TCN; tohum 11, 12, 13; CPU; zamana
göre bölme; ölçekleme yalnızca eğitimden; test yalnızca bir kez."""
import time
import numpy as np
import torch
from ortak import (iha_telemetri, olcek, veri_bol, HEDEF, mae, rmse,
                   naif_tahmin, hareketli_ort, ar_sec, ar_1adim,
                   Tekrarli, TCN, egit, tahmin, yaz_csv)

n, W = 24000, 64
ntr, nva = int(0.6 * n), int(0.8 * n)
te_idx = np.arange(nva, n)
satir, ornek = [], None
ozet = {}


def kaydet(tohum, ad, pred, params, sure, s_te):
    a, r = mae(s_te, pred), rmse(s_te, pred)
    satir.append((tohum, ad, round(a, 5), round(r, 5), params,
                  round(sure, 1)))
    ozet.setdefault(ad, []).append((a, r, sure))


for tohum in (11, 12, 13):
    Z = iha_telemetri(n, seed=tohum)
    s = Z[:, HEDEF]
    s_te = s[te_idx]
    # baz modeller (ham ölçekte)
    kaydet(tohum, "naif", naif_tahmin(s, te_idx), 0, 0, s_te)
    kaydet(tohum, "hareketli ort. (10)", hareketli_ort(s, te_idx),
           0, 0, s_te)
    p, kat = ar_sec(s, ntr, nva)
    kaydet(tohum, "AR(%d)" % p, ar_1adim(s, kat, te_idx), p + 1, 0,
           s_te)
    # sinir ağları (ölçekli)
    Zs, mu, sd = olcek(Z.astype(np.float32), ntr)
    (Xtr, ytr), (Xva, yva), (Xte, yte) = veri_bol(Zs, W, 1, ntr, nva)
    for ad, mk in [
        ("RNN", lambda: Tekrarli("rnn", 4, 32)),
        ("LSTM", lambda: Tekrarli("lstm", 4, 32)),
        ("GRU", lambda: Tekrarli("gru", 4, 32)),
        ("TCN", lambda: TCN(4, 32, 3, (1, 2, 4, 8)))]:
        torch.manual_seed(tohum)
        m = mk()
        t0 = time.time()
        en, ep = egit(m, Xtr, ytr, Xva, yva, seed=tohum)
        sure = time.time() - t0
        pr = tahmin(m, Xte)[:, 0] * sd[HEDEF] + mu[HEDEF]
        npar = sum(q.numel() for q in m.parameters())
        kaydet(tohum, ad, pr, npar, sure, s_te)
        print("tohum %d %-5s en iyi epoch=%2d  sure=%5.1f s  param=%d"
              % (tohum, ad, ep, sure, npar))
        if tohum == 11 and ad == "GRU":
            ornek = {"gercek": s_te[:400], "GRU": pr[:400]}
        if tohum == 11 and ad == "TCN":
            ornek["TCN"] = pr[:400]
    if tohum == 11:
        ornek["AR"] = ar_1adim(s, kat, te_idx)[:400]

print()
print("%-22s %-18s %-18s" % ("Model", "MAE ort+-sd", "RMSE ort+-sd"))
for ad, v in ozet.items():
    a = np.array([x[0] for x in v])
    r = np.array([x[1] for x in v])
    print("%-22s %6.4f+-%.4f  %6.4f+-%.4f" % (
        ad, a.mean(), a.std(ddof=1), r.mean(), r.std(ddof=1)))
yaz_csv("b68_tahmin.csv",
        ["tohum", "model", "mae", "rmse", "param", "egitim_s"], satir)
yaz_csv("b68_tahmin_ornek.csv",
        ["adim", "gercek", "GRU", "TCN", "AR"],
        [(i, round(float(ornek["gercek"][i]), 4),
          round(float(ornek["GRU"][i]), 4),
          round(float(ornek["TCN"][i]), 4),
          round(float(ornek["AR"][i]), 4)) for i in range(400)])
