# -*- coding: utf-8 -*-
"""Deney 3b: LR aralik testi (Smith, genel bilgi).

Ogrenme orani 1e-7'den 10'a kadar ustel olarak artirilir; her
adimda tek bir mini-batch (64 ornek) ile SGD (momentum 0,9)
guncellemesi yapilir. Kayip, 0,98 ustel ortalama ile yumusatilir
ve sapma duzeltmesi uygulanir. Tohum 0."""

import numpy as np
import torch
import torch.nn.functional as F
from ortak64 import veri, mlp, csv_yaz

# ---- (b) LR aralik testi: lr ustel artar, kayip izlenir
D = veri()
Xtr, ytr = D[0], D[1]
torch.manual_seed(0)
m = mlp()
opt = torch.optim.SGD(m.parameters(), lr=1e-7, momentum=0.9)
ADIM_LR = 300
lr_min, lr_max = 1e-7, 10.0
g = torch.Generator().manual_seed(0)
ema, en_iyi = None, 1e9
satir = []
for k in range(ADIM_LR):
    lr = lr_min * (lr_max / lr_min) ** (k / (ADIM_LR - 1))
    for pg in opt.param_groups:
        pg["lr"] = lr
    idx = torch.randperm(len(Xtr), generator=g)[:64]
    opt.zero_grad()
    loss = F.cross_entropy(m(Xtr[idx]), ytr[idx])
    loss.backward()
    opt.step()
    L = loss.item()
    ema = L if ema is None else 0.98 * ema + 0.02 * L
    ema_duz = ema / (1 - 0.98 ** (k + 1))  # sapma duzeltmesi
    en_iyi = min(en_iyi, ema_duz)
    satir.append((k, "%.4e" % lr, "%.5f" % L, "%.5f" % ema_duz))
    if ema_duz > 4 * en_iyi and k > 10:
        break
csv_yaz(
    "b64_lr_aralik.csv", satir, ["adim", "lr", "kayip", "kayip_ema"]
)
kayit = np.array([float(r[3]) for r in satir])
lrs = np.array([float(r[1]) for r in satir])
kmin = int(np.argmin(kayit))
print("LR aralik testi: adim sayisi=%d" % len(satir))
print(
    "  en dusuk EMA kayip: lr=%.3e  kayip=%.4f"
    % (lrs[kmin], kayit[kmin])
)
print("  onerilen (en dusuk / 10): lr=%.3e" % (lrs[kmin] / 10))
print("  son adimlarda lr=%.3e kayip=%.4f" % (lrs[-1], kayit[-1]))
