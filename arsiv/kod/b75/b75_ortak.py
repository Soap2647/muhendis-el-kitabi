# -*- coding: utf-8 -*-
"""Bolum 75 ortak yardimcilari: veri, MLP, egitim, maske, sahte
kuantizasyon.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

torch.set_num_threads(4)
TOHUMLAR = [0, 1, 2]


def veri(tohum=0):
    X, y = load_digits(return_X_y=True)
    X = (X / 16.0).astype(np.float32)
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.3, random_state=tohum, stratify=y
    )
    return (
        torch.tensor(Xtr),
        torch.tensor(ytr),
        torch.tensor(Xte),
        torch.tensor(yte),
    )


def mlp(gizli=(256, 128)):
    katmanlar, giris = [], 64
    for g in gizli:
        katmanlar += [nn.Linear(giris, g), nn.ReLU()]
        giris = g
    katmanlar.append(nn.Linear(giris, 10))
    return nn.Sequential(*katmanlar)


def mlp_t(tohum, gizli=(256, 128)):
    """Agirliklari tohuma gore kurulan MLP (tekrarlanabilirlik icin).
    """
    torch.manual_seed(tohum)
    return mlp(gizli)


def egit(model, X, y, epoch=60, lr=1e-3, tohum=0, maskeler=None):
    torch.manual_seed(tohum)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    n = len(X)
    for _ in range(epoch):
        perm = torch.randperm(n)
        for i in range(0, n, 64):
            idx = perm[i : i + 64]
            kayip = F.cross_entropy(model(X[idx]), y[idx])
            opt.zero_grad()
            kayip.backward()
            opt.step()
            if maskeler is not None:
                uygula_maske(model, maskeler)
    return model


def dogruluk(model, X, y):
    model.eval()
    with torch.no_grad():
        return (model(X).argmax(1) == y).float().mean().item()


def uygula_maske(model, maskeler):
    """maskeler: {katman_indeksi: 0/1 tensoru}; agirlikta sifirlar."""
    with torch.no_grad():
        for idx, m in maskeler.items():
            model[idx].weight.mul_(m)


def simetrik_olcek(w, bits, kanal=False):
    lv = 2 ** (bits - 1) - 1
    if kanal:
        mx = w.abs().amax(dim=1, keepdim=True)
    else:
        mx = w.abs().max()
    return mx.clamp_min(1e-8) / lv


def qdq(x, s, bits):
    """Simetrik kuantize et ve geri ac: round(x/s) kirp, sonra s ile
    carp.
    """
    lv = 2 ** (bits - 1) - 1
    return torch.clamp(torch.round(x / s), -lv, lv) * s


class SahteKuantFn(torch.autograd.Function):
    """Ileri: qdq. Geri: duz gecis (STE), asiri degerde sifir."""

    @staticmethod
    def forward(ctx, x, s, bits):
        lv = 2 ** (bits - 1) - 1
        ctx.save_for_backward(x)
        ctx.s, ctx.lv = s, lv
        return torch.clamp(torch.round(x / s), -lv, lv) * s

    @staticmethod
    def backward(ctx, g):
        (x,) = ctx.saved_tensors
        maske = (x.abs() <= ctx.s * ctx.lv).to(g.dtype)
        return g * maske, None, None


def zamanla(f, n=300, isinma=30):
    """Olcum disiplini: isinma, n olcum; medyan ve p95 (ms).
    """
    import time

    for _ in range(isinma):
        f()
    t = []
    for _ in range(n):
        t0 = time.perf_counter()
        f()
        t.append((time.perf_counter() - t0) * 1e3)
    t = np.array(t)
    return float(np.median(t)), float(np.percentile(t, 95))
