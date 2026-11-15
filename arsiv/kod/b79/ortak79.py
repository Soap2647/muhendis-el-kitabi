# -*- coding: utf-8 -*-
"""Bolum 79 ortak yardimcilari: veri, MLP, egitim, istatistik.

Veri: load_digits, %60 egitim / %20 dogrulama / %20 test (katmanli).
Her koşu bir tohumla belirlenir: agirlik baslangici ve mini-batch
sirasi ayni tohumdan gelir. Test skoru yalnizca raporlama icin okunur.
"""
import os

os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"

import numpy as np
import torch
from torch import nn
from scipy import stats
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

torch.set_num_threads(4)
VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"


def veri():
    X, y = load_digits(return_X_y=True)
    X = (X / 16.0).astype(np.float32)
    Xtr, Xg, ytr, yg = train_test_split(
        X, y, test_size=0.4, stratify=y, random_state=0
    )
    Xva, Xte, yva, yte = train_test_split(
        Xg, yg, test_size=0.5, stratify=yg, random_state=0
    )
    t = torch.tensor
    return (t(Xtr), t(ytr), t(Xva), t(yva), t(Xte), t(yte))


def mlp(bn=False, dropout=0.0):
    """Iki gizli katman, 128 birim, ReLU. BN/dropout istege bagli."""
    kat, d = [], 64
    for _ in range(2):
        kat.append(nn.Linear(d, 128))
        if bn:
            kat.append(nn.BatchNorm1d(128))
        kat.append(nn.ReLU())
        if dropout > 0:
            kat.append(nn.Dropout(dropout))
        d = 128
    kat.append(nn.Linear(d, 10))
    return nn.Sequential(*kat)


def dogruluk(model, X, y):
    model.eval()
    with torch.no_grad():
        return (model(X).argmax(1) == y).float().mean().item()


def egit(seed, opt="adam", lr=3e-3, wd=0.0, bn=False, dropout=0.0,
         cosine=False, epochs=30, batch=32, D=None):
    """Bir koşu. Son epoch modeli değerlendirilir; erken durdurma yok.

    opt: "adam" (torch.optim.Adam, wd=0) ya da "adamw" (AdamW, wd=wd).
    Dönüş: (dogrulama_dogrulugu, test_dogrulugu).
    """
    if D is None:
        D = veri()
    Xtr, ytr, Xva, yva, Xte, yte = D
    torch.manual_seed(seed)
    model = mlp(bn=bn, dropout=dropout)
    if opt == "adam":
        o = torch.optim.Adam(model.parameters(), lr=lr)
    else:
        o = torch.optim.AdamW(model.parameters(), lr=lr,
                              weight_decay=wd)
    sched = None
    if cosine:
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(o, epochs)
    g = torch.Generator().manual_seed(seed)
    loss_fn = nn.CrossEntropyLoss()
    n = len(Xtr)
    for _ in range(epochs):
        model.train()
        perm = torch.randperm(n, generator=g)
        for i in range(0, n, batch):
            idx = perm[i:i + batch]
            o.zero_grad()
            loss_fn(model(Xtr[idx]), ytr[idx]).backward()
            o.step()
        if sched is not None:
            sched.step()
    return dogruluk(model, Xva, yva), dogruluk(model, Xte, yte)


def t_testi(fark):
    """Tek ornek t testi: ortalama, t, iki yonlu p (scipy ile)."""
    fark = np.asarray(fark, dtype=float)
    n = len(fark)
    ort, sd = fark.mean(), fark.std(ddof=1)
    t = ort / (sd / np.sqrt(n))
    p = 2 * stats.t.sf(abs(t), df=n - 1)
    return ort, t, p


def bootstrap_gven(x, B=10000, seed=0, a=0.05):
    """Ortalama icin yuzdelik bootstrap guven araligi (Bolum 49)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    ort = x[idx].mean(axis=1)
    return np.quantile(ort, [a / 2, 1 - a / 2])


def holm(p):
    """Holm duzeltmesi: en kucuk p'den basla, esik alpha/(m-k)."""
    p = np.asarray(p, dtype=float)
    m = len(p)
    sira = np.argsort(p)
    duz = np.empty(m)
    enb = 0.0
    for k, i in enumerate(sira):
        enb = max(enb, (m - k) * p[i])
        duz[i] = min(1.0, enb)
    return duz


def csv_yaz(ad, satirlar, basliklar):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(basliklar) + "\n")
        for s in satirlar:
            f.write(",".join(str(x) for x in s) + "\n")
    return yol
