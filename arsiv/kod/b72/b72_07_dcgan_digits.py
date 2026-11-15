# -*- coding: utf-8 -*-
"""Bolum 72.8: kucuk DCGAN, load_digits (8x8). Evrisimli uretici ve
ayirt edici, BatchNorm, dogal (doymayan) uretici kaybi."""
import time
import numpy as np
import torch
import torch.nn as nn
from b72_veri import digits_bol, OUT

ZD = 32
EPOCH = 60
B = 64
torch.manual_seed(0)


class Uretici(nn.Module):
    """z(32) -> 128x2x2 -> 64x4x4 -> 1x8x8 (sigmoid, [0,1])."""

    def __init__(self):
        super().__init__()
        self.lin = nn.Sequential(nn.Linear(ZD, 128 * 2 * 2),
                                 nn.BatchNorm1d(128 * 2 * 2),
                                 nn.ReLU())
        self.net = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 4, 2, 1), nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 1, 4, 2, 1), nn.Sigmoid())

    def forward(self, z):
        h = self.lin(z).view(-1, 128, 2, 2)
        return self.net(h)


class Ayirt(nn.Module):
    """1x8x8 -> 64x4x4 -> 128x2x2 -> logit."""

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 64, 4, 2, 1), nn.LeakyReLU(0.2),
            nn.Conv2d(64, 128, 4, 2, 1), nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2), nn.Flatten(), nn.Linear(512, 1))

    def forward(self, x):
        return self.net(x)


if __name__ == "__main__":
    xtr, ytr, xte, yte = digits_bol(seed=0)
    X = torch.tensor(xtr).view(-1, 1, 8, 8)
    G, D = Uretici(), Ayirt()
    oG = torch.optim.Adam(G.parameters(), 2e-4, betas=(0.5, 0.999))
    oD = torch.optim.Adam(D.parameters(), 2e-4, betas=(0.5, 0.999))
    bce = nn.BCEWithLogitsLoss()
    t0 = time.perf_counter()
    print("== DCGAN (digits, 8x8), 60 epoch ==")
    print("epoch  D_kayip  G_kayip  D(gercek)  D(sahte)")
    for ep in range(1, EPOCH + 1):
        p = torch.randperm(len(X))
        dk, gk, dr, df = [], [], [], []
        for i in range(0, len(X) - B + 1, B):
            xr = X[p[i:i + B]]
            z = torch.randn(B, ZD)
            xf = G(z).detach()
            lr_ = D(xr)
            lf = D(xf)
            kd = bce(lr_, torch.ones(B, 1)) + \
                bce(lf, torch.zeros(B, 1))
            oD.zero_grad()
            kd.backward()
            oD.step()
            lo = D(G(torch.randn(B, ZD)))
            kg = bce(lo, torch.ones(B, 1))   # doymayan kayip
            oG.zero_grad()
            kg.backward()
            oG.step()
            dk.append(kd.item())
            gk.append(kg.item())
            dr.append(torch.sigmoid(lr_).mean().item())
            df.append(torch.sigmoid(lf).mean().item())
        if ep % 10 == 0 or ep == 1:
            print(f"{ep:>5}  {np.mean(dk):7.4f}  {np.mean(gk):7.4f}"
                  f"  {np.mean(dr):9.3f}  {np.mean(df):8.3f}")
    G.eval()
    with torch.no_grad():
        ornek = G(torch.randn(1000, ZD)).view(-1, 64).numpy()
    np.save(OUT + "/dcgan_ornek.npy", ornek)
    torch.save(G.state_dict(), OUT + "/dcgan_g.pt")
    t1 = time.perf_counter()
    for _ in range(5):
        with torch.no_grad():
            _ = G(torch.randn(1000, ZD))
    ms = (time.perf_counter() - t1) / 5 / 1000 * 1e3
    with open(OUT + "/zaman_dcgan.txt", "w") as f:
        f.write(f"{ms:.6f}")
    print(f"Egitim suresi: {time.perf_counter() - t0:.1f} s")
    print(f"Ornekleme suresi (CPU, ornek basina): {ms:.4f} ms")
    print(f"Uretilen ornek: {ornek.shape}, aralik "
          f"[{ornek.min():.3f}, {ornek.max():.3f}]")
