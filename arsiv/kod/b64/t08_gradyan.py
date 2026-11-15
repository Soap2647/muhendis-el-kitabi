# -*- coding: utf-8 -*-
"""Deney 8: gradyan sorunlari.
(a) Patlayan gradyan ve norm kirpma (20 katman, BN yok, SGD lr=0.5).
(b) Kaybolan gradyan: 30 katman, varsayilan init vs He vs artik
    (residual) baglanti; ilk katmanin gradyan normu (init'te)."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri, csv_yaz

D = veri()
Xtr, ytr = D[0], D[1]


def derin(katman, he=True):
    kat, d = [], 64
    for _ in range(katman):
        L = nn.Linear(d, 128)
        if he:
            nn.init.kaiming_normal_(L.weight, nonlinearity="relu")
            nn.init.zeros_(L.bias)
        kat += [L, nn.ReLU()]
        d = 128
    kat.append(nn.Linear(d, 10))
    return nn.Sequential(*kat)


# (a) patlayan gradyan
def patlat(klip, lr=0.5, adim=200, seed=0):
    torch.manual_seed(seed)
    m = derin(20)
    opt = torch.optim.SGD(m.parameters(), lr=lr)
    g = torch.Generator().manual_seed(seed)
    gn_l, loss_l, nan_ilk = [], [], None
    for k in range(adim):
        idx = torch.randperm(len(Xtr), generator=g)[:32]
        opt.zero_grad()
        loss = F.cross_entropy(m(Xtr[idx]), ytr[idx])
        loss.backward()
        gn = torch.sqrt(
            sum((p.grad**2).sum() for p in m.parameters())
        ).item()
        if klip is not None:
            torch.nn.utils.clip_grad_norm_(m.parameters(), klip)
        opt.step()
        gn_l.append(gn)
        loss_l.append(loss.item())
        if nan_ilk is None and not np.isfinite(loss.item()):
            nan_ilk = k
            break
    return gn_l, loss_l, nan_ilk


gn0, l0, n0 = patlat(None)
gn1, l1, n1 = patlat(1.0)
print("Kirpmasiz: NaN adimi=%s, son kayip=%.3f" % (n0, l0[-1]))
print("  en buyuk norm=%.3g" % max(gn0))
print("Kirpmali (max_norm=1): NaN adimi=%s" % n1)
print("  son kayip=%.3f, en buyuk norm=%.3g" % (l1[-1], max(gn1)))
satir = []
for k in range(len(l0)):
    satir.append(("kirpmasiz", k, "%.5g" % gn0[k], "%.5g" % l0[k]))
for k in range(len(l1)):
    satir.append(("kirpmali", k, "%.5g" % gn1[k], "%.5g" % l1[k]))
csv_yaz(
    "b64_klip.csv", satir, ["mod", "adim", "gradyan_norm", "kayip"]
)

# (b) kaybolan gradyan: ilk katman gradyani (init'te, tek batch)
torch.manual_seed(0)
X = Xtr[:256]
Y = ytr[:256]
sat2 = []
print("\nIlk katman agirlik gradyan normu (init, 256 ornek):")
for ad, model in [
    ("varsayilan 30 katman", None),
    ("He 30 katman", derin(30, he=True)),
]:
    if model is None:
        torch.manual_seed(0)
        model = derin(30, he=False)
    model.zero_grad()
    F.cross_entropy(model(X), Y).backward()
    g1 = model[0].weight.grad.norm().item()
    gson = model[-1].weight.grad.norm().item()
    print(
        "  %-22s ilk katman=%.3e   son katman=%.3e" % (ad, g1, gson)
    )
    sat2.append((ad, "%.6e" % g1, "%.6e" % gson))


# artik (residual) blok: h = h + W2 relu(W1 h), He init
class Artik(nn.Module):
    def __init__(self, n, katman, zero_son=False):
        super().__init__()
        self.giris = nn.Linear(64, n)
        self.bloklar = nn.ModuleList()
        for _ in range(katman):
            a = nn.Linear(n, n)
            b = nn.Linear(n, n)
            for L in (a, b):
                nn.init.kaiming_normal_(L.weight, nonlinearity="relu")
                nn.init.zeros_(L.bias)
            if zero_son:
                nn.init.zeros_(b.weight)  # dal sifirdan baslar
            self.bloklar.append(nn.ModuleList([a, b]))
        self.cikis = nn.Linear(n, 10)

    def forward(self, x):
        h = self.giris(x)
        for a, b in self.bloklar:
            h = h + b(F.relu(a(h)))
        return self.cikis(h)


for ad, zs in [
    ("artik He (30 katman)", False),
    ("artik, dal son=0 (30)", True),
]:
    torch.manual_seed(0)
    art = Artik(128, 15, zero_son=zs)  # 30 dogrusal katman
    art.zero_grad()
    F.cross_entropy(art(X), Y).backward()
    g1 = art.giris.weight.grad.norm().item()
    gs = art.cikis.weight.grad.norm().item()
    print("  %-22s ilk katman=%.3e   son katman=%.3e" % (ad, g1, gs))
    sat2.append((ad, "%.6e" % g1, "%.6e" % gs))
csv_yaz(
    "b64_residual.csv",
    sat2,
    ["model", "ilk_katman_grad", "son_katman_grad"],
)
