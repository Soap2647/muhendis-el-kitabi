# -*- coding: utf-8 -*-
"""Deney 3: (a) kayip yuzeyinde optimizer yorungeleri (NumPy),
(b) LR aralik testi (Smith genel bilgi) ile ogrenme orani taramasi."""

import math
import numpy as np
import torch
import torch.nn.functional as F
from egitim_np import sgd_momentum, adam_adim
from ortak64 import veri, mlp, csv_yaz


# ---- (a) f(x, y) = 0.5 (x^2 + 10 y^2): kotu koşullu ikinci dereceden
def grad(p):
    return np.array([p[0], 10.0 * p[1]])


p0 = np.array([-4.0, 1.0])
ADIM = 60
yol = {}
yol["SGD"] = [p0.copy()]
p = p0.copy()
for _ in range(ADIM):
    p = p - 0.09 * grad(p)
    yol["SGD"].append(p.copy())
yol["Momentum"] = [p0.copy()]
p, v = p0.copy(), np.zeros(2)
for _ in range(ADIM):
    p, v = sgd_momentum(p, grad(p), v, lr=0.09, mu=0.9)
    yol["Momentum"].append(p.copy())
yol["Adam"] = [p0.copy()]
p, m, vv, t = p0.copy(), np.zeros(2), np.zeros(2), 0
for _ in range(ADIM):
    p, m, vv, t = adam_adim(p, grad(p), m, vv, t, lr=0.3)
    yol["Adam"].append(p.copy())

satir = []
for ad, pts in yol.items():
    for k, q in enumerate(pts):
        f = 0.5 * (q[0] ** 2 + 10 * q[1] ** 2)
        satir.append(
            (ad, k, "%.6f" % q[0], "%.6f" % q[1], "%.6f" % f)
        )
    print(
        "%-9s son nokta=(%.4f, %.4f)  f=%.2e"
        % (
            ad,
            pts[-1][0],
            pts[-1][1],
            0.5 * (pts[-1][0] ** 2 + 10 * pts[-1][1] ** 2),
        )
    )
csv_yaz(
    "b64_yorunge.csv", satir, ["optimizer", "adim", "x", "y", "f"]
)

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
