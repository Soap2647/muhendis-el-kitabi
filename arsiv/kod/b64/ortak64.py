# -*- coding: utf-8 -*-
"""Bolum 64 deneyleri icin ortak veri, model ve egitim dongusu.

Veri: sklearn load_digits (1797 ornek, 8x8 = 64 ozellik, 10 sinif).
Bolme sabit: %60 egitim, %20 dogrulama, %20 test (stratified,
random_state=0). Tohum (seed) yalnizca baslangic agirliklarini ve
mini-batch sirasini degistirir; veri bolmesi her kosuda aynidir.
"""

import csv
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
SEEDS = [0, 1, 2, 3, 4]
torch.set_num_threads(1)


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


def mlp(gizli=128, derinlik=2, bn=False, dropout=0.0, giris=64):
    kat, d = [], giris
    for _ in range(derinlik):
        kat.append(nn.Linear(d, gizli))
        if bn:
            kat.append(nn.BatchNorm1d(gizli))
        kat.append(nn.ReLU())
        if dropout > 0:
            kat.append(nn.Dropout(dropout))
        d = gizli
    kat.append(nn.Linear(d, 10))
    return nn.Sequential(*kat)


@torch.no_grad()
def olc(model, X, y):
    model.eval()
    out = model(X)
    return (
        F.cross_entropy(out, y).item(),
        (out.argmax(1) == y).float().mean().item(),
    )


def egit(
    model,
    opt,
    veri_,
    epochs=30,
    batch=32,
    seed=0,
    lr_fn=None,
    klip=None,
    erken=None,
    ls=0.0,
):
    """Egitim dongusu. lr_fn(adim) verilirse her adimda lr ayarlanir.
    Doner: gecmis sozlugu; son adimda dogrulama ve test metrikleri."""
    Xtr, ytr, Xva, yva, Xte, yte = veri_
    g = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    n, adim = len(Xtr), 0
    h = {"tr": [], "va": [], "vacc": [], "lr": [], "gnorm": []}
    en_iyi, en_iyi_ep = 1e9, -1
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(n, generator=g)
        top, cnt = 0.0, 0
        for i in range(0, n, batch):
            idx = perm[i : i + batch]
            if lr_fn is not None:
                for pg in opt.param_groups:
                    pg["lr"] = lr_fn(adim)
            opt.zero_grad()
            loss = F.cross_entropy(
                model(Xtr[idx]), ytr[idx], label_smoothing=ls
            )
            loss.backward()
            gn = torch.sqrt(
                sum((p.grad**2).sum() for p in model.parameters())
            ).item()
            if klip is not None:
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), klip
                )
            opt.step()
            adim += 1
            top += loss.item() * len(idx)
            cnt += len(idx)
            h["gnorm"].append(gn)
            h["lr"].append(opt.param_groups[0]["lr"])
        vl, va = olc(model, Xva, yva)
        h["tr"].append(top / cnt)
        h["va"].append(vl)
        h["vacc"].append(va)
        if vl < en_iyi:
            en_iyi, en_iyi_ep = vl, ep
        if erken is not None and ep - en_iyi_ep >= erken:
            break
    _, h["test_acc"] = olc(model, Xte, yte)
    _, h["val_acc"] = olc(model, Xva, yva)
    h["adim"] = adim
    h["en_iyi_ep"] = en_iyi_ep
    return h


def csv_yaz(ad, satirlar, basliklar):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)
    return yol


def ortalama_sapma(xs):
    a = np.array(xs, dtype=float)
    return a.mean(), a.std(ddof=1) if len(a) > 1 else 0.0
