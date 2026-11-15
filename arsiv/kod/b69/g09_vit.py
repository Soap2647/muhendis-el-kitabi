# -*- coding: utf-8 -*-
"""Bölüm 69 - Küçük ViT ve küçük CNN: veri miktarı."""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tr69 import Blok, tohum

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
BOY = 32
ADIM = 1500
BATCH = 64
TOHUMLAR = [0, 1, 2]


def uret(rng, n):
    """4 sınıf: yatay, dikey çubuk, daire, köşegen."""
    X = np.zeros((n, 1, BOY, BOY), np.float32)
    y = rng.integers(0, 4, size=n)
    yy, xx = np.mgrid[0:BOY, 0:BOY]
    for i in range(n):
        cx, cy = rng.integers(10, 22, size=2)
        r = int(rng.integers(4, 8))
        if y[i] == 0:
            m = (np.abs(yy - cy) <= 1) & (np.abs(xx - cx) <= r)
        elif y[i] == 1:
            m = (np.abs(xx - cx) <= 1) & (np.abs(yy - cy) <= r)
        elif y[i] == 2:
            d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
            m = np.abs(d - r) <= 1
        else:
            m = (np.abs((xx - cx) - (yy - cy)) <= 1) & (
                np.abs(xx - cx) <= r
            )
        parlaklik = 0.6 + 0.4 * rng.random()
        X[i, 0] = m * parlaklik + rng.normal(0, 0.25, (BOY, BOY))
    return torch.tensor(X), torch.tensor(y, dtype=torch.long)


class VitK(nn.Module):
    """Yama gömmesi + konum gömmesi + kodlayıcı blokları."""

    def __init__(self, d=64, h=4, L=2, yama=8):
        super().__init__()
        n = (BOY // yama) ** 2
        self.proj = nn.Conv2d(1, d, yama, stride=yama)
        self.pos = nn.Parameter(torch.randn(1, n, d) * 0.02)
        self.blocks = nn.ModuleList(
            [Blok(d, h, "pre", 0.0, False) for _ in range(L)]
        )
        self.son = nn.LayerNorm(d)
        self.cikis = nn.Linear(d, 4)

    def forward(self, x):
        h = self.proj(x).flatten(2).transpose(1, 2) + self.pos
        for b in self.blocks:  # maske yok: çift yönlü
            h = b(h)
        return self.cikis(self.son(h).mean(dim=1))


class Cnn(nn.Module):
    """Üç konvolüsyon bloğu (yerel, öteleme-eşdeğişken)."""

    def __init__(self):
        super().__init__()
        self.ag = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(64, 4),
        )

    def forward(self, x):
        return self.ag(x)


def egit(model, X, y, seed):
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    for _ in range(ADIM):
        i = torch.tensor(rng.integers(0, len(X), size=BATCH))
        loss = F.cross_entropy(model(X[i]), y[i])
        opt.zero_grad()
        loss.backward()
        opt.step()


@torch.no_grad()
def dogruluk(model, X, y):
    model.eval()
    tahmin = torch.cat(
        [
            model(X[b : b + 500]).argmax(-1)
            for b in range(0, len(X), 500)
        ]
    )
    return float((tahmin == y).float().mean())


def main():
    Xt, yt = uret(np.random.default_rng(999), 1000)
    print("test kümesi: 1000 görüntü, 4 sınıf, tohum 999")
    sonuc = {}
    satirlar = []
    for N in [300, 5000]:
        for ad, kur in [("ViT (yama 8)", VitK), ("CNN", Cnn)]:
            sonuc[(ad, N)] = []
            for s in TOHUMLAR:
                tohum(s)
                X, y = uret(np.random.default_rng(100 + s), N)
                model = kur()
                t0 = time.time()
                egit(model, X, y, s)
                te = dogruluk(model, Xt, yt)
                tr = dogruluk(model, X[:1000], y[:1000])
                sonuc[(ad, N)].append(te)
                print(
                    "%-13s N=%5d tohum=%d test=%.3f egitim=%.3f "
                    "sure=%.0fs"
                    % (ad, N, s, te, tr, time.time() - t0)
                )
            v = np.array(sonuc[(ad, N)])
            satirlar.append(
                [ad, N, "%.4f" % v.mean(), "%.4f" % v.std(ddof=1)]
            )
    print()
    print(
        "Parametre sayısı: ViT %d, CNN %d"
        % (
            sum(p.numel() for p in VitK().parameters()),
            sum(p.numel() for p in Cnn().parameters()),
        )
    )
    print("Test doğruluğu (ortalama ± örnek sapması):")
    for N in [300, 5000]:
        for ad in ["ViT (yama 8)", "CNN"]:
            v = np.array(sonuc[(ad, N)])
            print(
                "N=%5d %-13s %.3f ± %.3f"
                % (N, ad, v.mean(), v.std(ddof=1))
            )
    with open(
        os.path.join(VERI, "b69_vit.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["model", "N", "ortalama", "sapma"])
        w.writerows(satirlar)


if __name__ == "__main__":
    main()
