# -*- coding: utf-8 -*-
"""Deney 2: optimizer karsilastirmasi.

Her optimizer icin ogrenme orani YALNIZCA dogrulama
kumesinde secilir (secim tohumlari 10,11,12). Secilen lr ile
test kumesi 5 tohumda olculur (tohumlar 0-4). Test kumesi
secimde kullanilmaz.
"""

import numpy as np
import torch
from ortak64 import veri, mlp, egit, csv_yaz, SEEDS, ortalama_sapma

D = veri()
SECIM = [10, 11, 12]
LRS = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]

OPT = {
    "SGD": lambda p, lr: torch.optim.SGD(p, lr=lr),
    "Momentum": lambda p, lr: torch.optim.SGD(p, lr=lr, momentum=0.9),
    "Nesterov": lambda p, lr: torch.optim.SGD(
        p, lr=lr, momentum=0.9, nesterov=True
    ),
    "AdaGrad": lambda p, lr: torch.optim.Adagrad(p, lr=lr),
    "RMSProp": lambda p, lr: torch.optim.RMSprop(p, lr=lr),
    "Adam": lambda p, lr: torch.optim.Adam(p, lr=lr),
    "AdamW": lambda p, lr: torch.optim.AdamW(
        p, lr=lr, weight_decay=0.01
    ),
}


def kos(ad, lr, seed):
    torch.manual_seed(seed)
    m = mlp()
    opt = OPT[ad](m.parameters(), lr)
    return egit(m, opt, D, epochs=30, batch=32, seed=seed)


print("Adim 1: lr secimi (yalnizca dogrulama, tohum 10-12)")
secilen = {}
grid_satir = []
for ad in OPT:
    skor = {}
    for lr in LRS:
        vals = [kos(ad, lr, s)["val_acc"] for s in SECIM]
        skor[lr] = np.mean(vals)
        grid_satir.append((ad, lr, "%.4f" % skor[lr]))
    en = max(skor, key=skor.get)
    secilen[ad] = en
    print(
        "  %-9s en iyi lr = %-7g dogrulama = %.4f"
        % (ad, en, skor[en])
    )
csv_yaz(
    "b64_lr_izgara.csv", grid_satir, ["optimizer", "lr", "val_acc"]
)

print("\nAdim 2: secilen lr ile test (tohum 0-4)")
satir = []
for ad in OPT:
    testler, egriler, vlosses = [], [], []
    for s in SEEDS:
        h = kos(ad, secilen[ad], s)
        testler.append(h["test_acc"])
        egriler.append(h["vacc"])
        vlosses.append(h["va"])
    mu, sd = ortalama_sapma(testler)
    print(
        "  %-9s lr=%-7g test=%.4f +- %.4f" % (ad, secilen[ad], mu, sd)
    )
    E = np.array(egriler)
    L = np.array(vlosses)
    for ep in range(E.shape[1]):
        satir.append(
            (
                ad,
                ep + 1,
                "%.5f" % E[:, ep].mean(),
                "%.5f" % E[:, ep].std(ddof=1),
                "%.5f" % L[:, ep].mean(),
                "%.5f" % L[:, ep].std(ddof=1),
            )
        )
csv_yaz(
    "b64_optim_egri.csv",
    satir,
    [
        "optimizer",
        "epoch",
        "vacc_ort",
        "vacc_sd",
        "vloss_ort",
        "vloss_sd",
    ],
)
for k, v in secilen.items():
    print("secim %-9s lr=%g" % (k, v))
