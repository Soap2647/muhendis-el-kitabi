# -*- coding: utf-8 -*-
"""Bolum 72.8: GAN. (A) doymayan kayip gradyani, (B) optimal
ayirt edici ve JS, (C) 8 Gauss halkasinda minimaks, doymayan ve
WGAN-GP egitimi; mod cokmesi olcumu (3 tohum)."""
import csv
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from b72_veri import halka_veri, mod_olcutu, VERI

ZD = 8
ITER = 4000
TOHUMLAR = [0, 1, 2]
LOG = 250

# ---------- (A) doymayan kayip: gradyan karsilastirmasi ----------
print("== A. Uretici kaybi: dL/dl (l = ayirt edicinin logit'i) ==")
l = torch.tensor([-6.0, -4.0, -2.0, 0.0, 2.0], requires_grad=True)
doyan = -F.softplus(l)           # log(1 - sigmoid(l))
doymayan = F.softplus(-l)        # -log(sigmoid(l))
g1, = torch.autograd.grad(doyan.sum(), l)
g2, = torch.autograd.grad(doymayan.sum(), l)
print("   l     D(G(z))   |dL_doyan|  |dL_doymayan|")
for i in range(5):
    d = torch.sigmoid(l[i]).item()
    print(f"{l[i].item():+5.1f}  {d:9.5f}  {abs(g1[i].item()):10.5f}"
          f"  {abs(g2[i].item()):12.5f}")

# ---------- (B) optimal ayirt edici ve JS (1B, ayrik) ----------
print()
print("== B. Optimal ayirt edici D*(x) = p/(p+q) ve JS ==")
p = np.array([0.5, 0.3, 0.2])
q = np.array([0.1, 0.4, 0.5])
Dst = p / (p + q)
V = np.sum(p * np.log(Dst)) + np.sum(q * np.log(1 - Dst))
m = (p + q) / 2
kl = lambda a, b: np.sum(a * np.log(a / b))
JS = 0.5 * kl(p, m) + 0.5 * kl(q, m)
rng0 = np.random.default_rng(0)
Dr = rng0.uniform(1e-6, 1 - 1e-6, (20000, 3))
vals = (p * np.log(Dr)).sum(1) + (q * np.log(1 - Dr)).sum(1)
print("D* =", np.round(Dst, 4))
print(f"V(D*)          = {V:.6f}")
print(f"-log4 + 2JS    = {-np.log(4) + 2 * JS:.6f}  (JS = {JS:.6f})")
print(f"Rastgele 20000 D icinde en buyuk V = "
      f"{vals.max():.6f} <= V(D*)")

# ---------- (C) egitim: minimaks, doymayan, WGAN-GP ----------
Xall, _ = halka_veri(200000, np.random.default_rng(1))
Xall = torch.tensor(Xall)


def ureteci():
    return nn.Sequential(nn.Linear(ZD, 128), nn.ReLU(),
                         nn.Linear(128, 128), nn.ReLU(),
                         nn.Linear(128, 2))


def ayirt_edici(giris=2):
    return nn.Sequential(nn.Linear(giris, 128), nn.LeakyReLU(0.2),
                         nn.Linear(128, 128), nn.LeakyReLU(0.2),
                         nn.Linear(128, 1))


def egit(varyant, seed, B=256):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    G, D = ureteci(), ayirt_edici()
    if varyant == "wgan":
        oG = torch.optim.Adam(G.parameters(), 1e-4, betas=(0.5, 0.9))
        oD = torch.optim.Adam(D.parameters(), 1e-4, betas=(0.5, 0.9))
    else:
        lrG = 1e-3 if varyant == "dogal_yl" else 2e-4
        oG = torch.optim.Adam(G.parameters(), lrG, betas=(0.5, 0.999))
        oD = torch.optim.Adam(D.parameters(), 2e-4,
                              betas=(0.5, 0.999))
    bce = nn.BCEWithLogitsLoss()
    one = torch.ones(B, 1)
    zero = torch.zeros(B, 1)
    gecmis = []
    for it in range(1, ITER + 1):
        if varyant == "wgan":
            for _ in range(5):
                xr = Xall[torch.randint(0, len(Xall), (B,))]
                with torch.no_grad():
                    xf = G(torch.randn(B, ZD))
                e = torch.rand(B, 1)
                xh = (e * xr + (1 - e) * xf).requires_grad_(True)
                gr = torch.autograd.grad(D(xh).sum(), xh,
                                         create_graph=True)[0]
                gp = ((gr.norm(2, dim=1) - 1) ** 2).mean()
                kd = D(xf).mean() - D(xr).mean() + 10 * gp
                oD.zero_grad()
                kd.backward()
                oD.step()
            kg = -D(G(torch.randn(B, ZD))).mean()
            oG.zero_grad()
            kg.backward()
            oG.step()
        else:
            xr = Xall[torch.randint(0, len(Xall), (B,))]
            with torch.no_grad():
                xf = G(torch.randn(B, ZD))
            kd = bce(D(xr), one) + bce(D(xf), zero)
            oD.zero_grad()
            kd.backward()
            oD.step()
            lo = D(G(torch.randn(B, ZD)))
            if varyant == "doyan":
                kg = -F.softplus(lo).mean()   # minimaks: log(1-D)
            else:
                kg = bce(lo, one)             # doymayan: -log D
            oG.zero_grad()
            kg.backward()
            oG.step()
        if it % LOG == 0:
            with torch.no_grad():
                x = G(torch.randn(2000, ZD)).numpy()
            mo, hq = mod_olcutu(x)
            gecmis.append((it, mo, hq))
    with torch.no_grad():
        son = G(torch.randn(2000, ZD)).numpy()
    return son, gecmis


VARYANTLAR = ["doyan", "dogal", "dogal_yl", "wgan"]
ad = {"doyan": "minimaks (doyan)", "dogal": "doymayan",
      "dogal_yl": "doymayan, G lr=1e-3", "wgan": "WGAN-GP"}
tum = {}
satirlar = []
ornekler = {}
for v in VARYANTLAR:
    for s in TOHUMLAR:
        son, gec = egit(v, s)
        tum[(v, s)] = gec
        for it, mo, hq in gec:
            satirlar.append([v, s, it, mo, f"{hq:.4f}"])
        if s == 0:
            ornekler[v] = son
        print(f"[{ad[v]} tohum {s}] son: modes={gec[-1][1]} "
              f"hq={gec[-1][2]:.3f}", flush=True)

print()
print("== Son durum (4000 iterasyon, 3 tohum) ==")
print("varyant                  modes(ort+-sd)  min   hq(ort+-sd)")
for v in VARYANTLAR:
    mo = np.array([tum[(v, s)][-1][1] for s in TOHUMLAR])
    hq = np.array([tum[(v, s)][-1][2] for s in TOHUMLAR])
    print(f"{ad[v]:<24} {mo.mean():4.2f} +- {mo.std():4.2f}   "
          f"{mo.min():d}     {hq.mean():.3f} +- {hq.std():.3f}")

with open(VERI + "/b72_gan_mod.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["varyant", "tohum", "iterasyon", "modes", "hq"])
    w.writerows(satirlar)
np.savez(VERI + "/b72_gan_ornek.npz", **ornekler)
print("CSV ve ornekler yazildi.")
