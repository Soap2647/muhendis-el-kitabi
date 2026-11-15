# -*- coding: utf-8 -*-
"""Deney 4: ogrenme orani takvimleri ve isinmanin (warmup) etkisi."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from egitim_np import (
    lr_adim_kurali,
    lr_ustel,
    lr_kosinus,
    lr_isinma_kosinus,
)
from ortak64 import veri, mlp, egit, csv_yaz, SEEDS, ortalama_sapma

T = 300
# (a) Takvim sekilleri (2x2 sekil icin)
satir = []
for t in range(T):
    satir.append(
        (
            t,
            "%.6f" % 0.01,
            "%.6f" % lr_adim_kurali(t, 0.01, 0.5, 100),
            "%.6f" % lr_ustel(t, 0.01, 0.993),
            "%.6f" % lr_kosinus(t, T, 0.01, 0.0),
            "%.6f" % lr_isinma_kosinus(t, 30, T, 0.01, 0.0),
        )
    )
csv_yaz(
    "b64_takvim.csv",
    satir,
    [
        "adim",
        "sabit",
        "basamak",
        "ustel",
        "kosinus",
        "isinma_kosinus",
    ],
)

# Torch karsilastirmasi (kosinus): sayisal farki yazdir
w = nn.Parameter(torch.zeros(1))
opt = torch.optim.SGD([w], lr=0.01)
sch = torch.optim.lr_scheduler.CosineAnnealingLR(
    opt, T_max=T, eta_min=0.0
)
tor = []
for t in range(T):
    tor.append(opt.param_groups[0]["lr"])
    opt.step()
    sch.step()
mine = [lr_kosinus(t, T, 0.01, 0.0) for t in range(T)]
print(
    "Kosinus: torch ile max fark = %.2e"
    % np.max(np.abs(np.array(tor) - mine))
)
print(
    "Isinma adim 0,29,30: %.6f %.6f %.6f"
    % (
        lr_isinma_kosinus(0, 30, T, 0.01),
        lr_isinma_kosinus(29, 30, T, 0.01),
        lr_isinma_kosinus(30, 30, T, 0.01),
    )
)

# (b) Sig MLP, Adam, 30 epoch, 5 tohum: takvim karsilastirmasi
D = veri()
ADIM_TOP = 30 * int(np.ceil(len(D[0]) / 32))
TAKVIM = {
    "sabit": lambda t: 1e-3,
    "kosinus": lambda t: lr_kosinus(t, ADIM_TOP, 3e-3, 0.0),
    "isinma+kosinus": lambda t: lr_isinma_kosinus(
        t, 100, ADIM_TOP, 3e-3, 0.0
    ),
}
satir = []
for ad, fn in TAKVIM.items():
    tes = []
    for s in SEEDS:
        torch.manual_seed(s)
        m = mlp()
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        h = egit(m, opt, D, epochs=30, batch=32, seed=s, lr_fn=fn)
        tes.append(h["test_acc"])
    mu, sd = ortalama_sapma(tes)
    print("MLP %-15s test = %.4f +- %.4f" % (ad, mu, sd))
    satir.append((ad, "%.4f" % mu, "%.4f" % sd))
csv_yaz(
    "b64_takvim_test.csv", satir, ["takvim", "test_ort", "test_sd"]
)


# (c) Derin ag (12 katman, BN yok), Adam lr=1e-2: isinmanin kararlilik
def derin_ag():
    kat, d = [], 64
    for _ in range(12):
        kat += [nn.Linear(d, 128), nn.ReLU()]
        d = 128
    kat.append(nn.Linear(d, 10))
    return nn.Sequential(*kat)


satir = []
print("\nDerin ag (12 katman), Adam lr=1e-2, 10 epoch (~340 adim):")
for ad, W in [("isinmasiz", 0), ("isinma 200 adim", 200)]:
    kayiplar = []
    for s in SEEDS:
        torch.manual_seed(s)
        m = derin_ag()
        opt = torch.optim.Adam(m.parameters(), lr=1e-2)
        if W == 0:
            fn = lambda t: 1e-2
        else:
            fn = lambda t, W=W: lr_isinma_kosinus(
                t, W, 2000, 1e-2, 1e-4
            )
        h = egit(m, opt, D, epochs=10, batch=32, seed=s, lr_fn=fn)
        kayiplar.append(
            (max(h["tr"][:3]), h["tr"][-1], h["test_acc"])
        )
    arr = np.array(kayiplar)
    print(
        "  %-16s tepe=%.3f son=%.3f test=%.3f"
        % (ad, arr[:, 0].mean(), arr[:, 1].mean(), arr[:, 2].mean())
    )
    satir.append(
        (
            ad,
            "%.4f" % arr[:, 0].mean(),
            "%.4f" % arr[:, 1].mean(),
            "%.4f" % arr[:, 2].mean(),
        )
    )
csv_yaz(
    "b64_isinma_derin.csv",
    satir,
    ["mod", "ilk3_tepe", "son_egitim_kayip", "test"],
)
