# -*- coding: utf-8 -*-
"""Bolum 72 ortak yardimcilari: digits verisi, sinif-landirici,
2B halka verisi ve mod olcutu."""
import os
import numpy as np
import torch
import torch.nn as nn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
os.makedirs(OUT, exist_ok=True)


def digits_bol(seed=0):
    """8x8 el yazisi rakamlari, [0,1] araliginda; %80 egitim,
    %20 test (siniflara gore tabakali)."""
    d = load_digits()
    x = (d.data / 16.0).astype(np.float32)
    y = d.target.astype(np.int64)
    xtr, xte, ytr, yte = train_test_split(
        x, y, test_size=0.2, random_state=seed, stratify=y)
    return xtr, ytr, xte, yte


class Siniflandirici(nn.Module):
    """64 -> 128 -> 32 (ozellik) -> 10 (sinif)."""

    def __init__(self):
        super().__init__()
        self.ozellik = nn.Sequential(
            nn.Linear(64, 128), nn.ReLU(),
            nn.Linear(128, 32), nn.ReLU())
        self.cikis = nn.Linear(32, 10)

    def forward(self, x):
        return self.cikis(self.ozellik(x))


def sinif_egit(x, y, seed=0, epoch=60):
    torch.manual_seed(seed)
    m = Siniflandirici()
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    X = torch.as_tensor(x)
    Y = torch.as_tensor(y)
    for _ in range(epoch):
        p = torch.randperm(len(X))
        for i in range(0, len(X), 64):
            b = p[i:i + 64]
            kayip = nn.functional.cross_entropy(m(X[b]), Y[b])
            opt.zero_grad()
            kayip.backward()
            opt.step()
    m.eval()
    return m


def clf_yukle(xtr, ytr):
    """Olcum sinifiricisi: bir kez egitilir, out/clf.pt'ye yazilir."""
    yol = os.path.join(OUT, "clf.pt")
    m = Siniflandirici()
    if os.path.exists(yol):
        m.load_state_dict(torch.load(yol, weights_only=True))
    else:
        m = sinif_egit(xtr, ytr, seed=0)
        torch.save(m.state_dict(), yol)
    m.eval()
    return m


@torch.no_grad()
def tahmin(m, x):
    t = torch.as_tensor(x, dtype=torch.float32)
    return m(t).argmax(1).numpy()


# ---- 2B halka verisi: 8 Gauss, yaricap 2, sigma 0.02 ----
MERKEZ = 2.0 * np.stack(
    [np.cos(2 * np.pi * np.arange(8) / 8),
     np.sin(2 * np.pi * np.arange(8) / 8)], 1)


def halka_veri(n, rng, sigma=0.02):
    k = rng.integers(0, 8, n)
    x = MERKEZ[k] + sigma * rng.standard_normal((n, 2))
    return x.astype(np.float32), k


def mod_olcutu(x, yaricap=0.2, esik=0.01):
    """Kapsanan mod sayisi ve yuksek kaliteli oran.
    Bir mod 'kapsandi' sayilir: en az esik*n ornek merkezine
    yaricap icinde duser. Kalite: herhangi bir merkeze yaricap
    icinde dusen orani."""
    d = np.linalg.norm(x[:, None, :] - MERKEZ[None], axis=2)
    en = d.argmin(1)
    yakin = d.min(1) <= yaricap
    kapsanan = 0
    for j in range(8):
        if ((en == j) & yakin).sum() >= esik * len(x):
            kapsanan += 1
    return kapsanan, float(yakin.mean())
