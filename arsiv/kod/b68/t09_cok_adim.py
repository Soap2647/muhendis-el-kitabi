# -*- coding: utf-8 -*-
"""Bölüm 68.13: çok adımlı tahmin. Özyinelemeli (recursive) ile
doğrudan (direct) yöntemler. Hata ufka göre artar mı? Tohum 11."""
import numpy as np
import torch
from ortak import (iha_telemetri, HEDEF, mae, Tekrarli, egit, tahmin,
                   yaz_csv)

n, W, HMAX, P = 24000, 64, 10, 40
ntr, nva = int(0.6 * n), int(0.8 * n)
s = iha_telemetri(n, seed=11)[:, HEDEF]
mu, sd = s[:ntr].mean(), s[:ntr].std()
u = (s - mu) / sd


def uni(x, W, H):
    """Tek kanallı pencereler: X_i = x[i:i+W], Y_i = x[i+W:i+W+H]."""
    m = len(x) - W - H + 1
    X = x[np.arange(W)[None, :] + np.arange(m)[:, None]]
    Y = x[np.arange(H)[None, :] + np.arange(m)[:, None] + W]
    return X[:, :, None].astype(np.float32), Y.astype(np.float32)


# Test orijinleri: i = nva-W .. n-W-HMAX (son bilinen indeks = i+W-1)
i_te = np.arange(nva - W, n - W - HMAX + 1)
o_te = i_te + W - 1                      # son bilinen indeks
gercek = np.stack([s[o_te + k] for k in range(1, HMAX + 1)], axis=1)

# ---- AR(40) ----
def ar_ozellik(o, p):
    return np.column_stack([np.ones(len(o))]
                           + [s[o - j] for j in range(p)])

ar_rec = np.zeros((len(o_te), HMAX))
kat1 = np.linalg.lstsq(ar_ozellik(np.arange(P - 1, ntr - 1), P),
                       s[P:ntr], rcond=None)[0]
hist = np.column_stack([s[o_te - j] for j in range(P)])   # yeni->eski
for k in range(HMAX):
    A = np.column_stack([np.ones(len(hist))]
                        + [hist[:, j] for j in range(P)])
    pr = A @ kat1
    ar_rec[:, k] = pr
    hist = np.column_stack([pr, hist[:, :-1]])
ar_dir = np.zeros_like(ar_rec)
for k in range(1, HMAX + 1):
    o_tr = np.arange(P - 1, ntr - k)
    A = ar_ozellik(o_tr, P)
    kat = np.linalg.lstsq(A, s[o_tr + k], rcond=None)[0]
    ar_dir[:, k - 1] = ar_ozellik(o_te, P) @ kat

# ---- GRU: özyinelemeli (H=1) ve doğrudan (H=10) ----
def gru_egit(H):
    X, Y = uni(u, W, H)
    tr = np.arange(len(X)) + W < ntr
    hb = np.arange(len(X)) + W
    va = (hb >= ntr) & (hb < nva)
    torch.manual_seed(11)
    m = Tekrarli("gru", 1, 32, cikis=H)
    egit(m, X[tr], Y[tr], X[va], Y[va], seed=11)
    return m

m1 = gru_egit(1)
Xte, _ = uni(u, W, HMAX)
Xte = Xte[i_te]
cur = torch.tensor(Xte.copy())
gru_rec = np.zeros((len(i_te), HMAX))
with torch.no_grad():
    m1.eval()
    for k in range(HMAX):
        p = m1(cur)[:, 0]
        gru_rec[:, k] = p.numpy() * sd + mu
        cur = torch.cat([cur[:, 1:], p.view(-1, 1, 1)], dim=1)

mD = gru_egit(HMAX)
gru_dir = tahmin(mD, Xte) * sd + mu

print("%-3s %-9s %-9s %-9s %-9s" % ("k", "AR-rec", "AR-dir",
                                    "GRU-rec", "GRU-dir"))
satir = []
for k in range(1, HMAX + 1):
    r = [mae(gercek[:, k - 1], v[:, k - 1])
         for v in (ar_rec, ar_dir, gru_rec, gru_dir)]
    print("%-3d %-9.4f %-9.4f %-9.4f %-9.4f" % (k, *r))
    satir.append((k, *[round(x, 5) for x in r]))
yaz_csv("b68_cok_adim.csv", ["k", "ar_rec", "ar_dir", "gru_rec",
                              "gru_dir"], satir)
