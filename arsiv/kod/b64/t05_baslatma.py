# -*- coding: utf-8 -*-
"""Deney 5: derin agda baslatma (init) ve BatchNorm'un etkisi.

20 gizli katman (256 birim, ReLU). Her katman icin ileri geçişte
aktivasyon standart sapmasi ve geri geçişte agirlik gradyani normu
olculur. Olcum tek bir 512 orneklik batch uzerinde (tohum 0)."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri, egit, csv_yaz, SEEDS, ortalama_sapma

D = veri()
Xtr, ytr = D[0], D[1]
X = Xtr[:512]
Y = ytr[:512]
DERIN = 20


def ag(init, bn):
    kat, d = [], 64
    lin_list = []
    for k in range(DERIN):
        L = nn.Linear(d, 256)
        lin_list.append(L)
        kat.append(L)
        if bn:
            kat.append(nn.BatchNorm1d(256))
        kat.append(nn.ReLU())
        d = 256
    L = nn.Linear(d, 10)
    lin_list.append(L)
    kat.append(L)
    model = nn.Sequential(*kat)
    for L in lin_list:
        if init == "kucuk":
            nn.init.normal_(L.weight, std=0.01)
        elif init == "xavier":
            nn.init.xavier_normal_(L.weight)
        elif init == "he":
            nn.init.kaiming_normal_(L.weight, nonlinearity="relu")
        nn.init.zeros_(L.bias)
    return model, lin_list


def olc(init, bn, seed=0):
    torch.manual_seed(seed)
    model, lins = ag(init, bn)
    model.train()
    act = []
    h = X
    for mod in model:
        h = mod(h)
        if isinstance(mod, nn.ReLU):
            act.append(h.std().item())
    model.zero_grad()
    F.cross_entropy(model(X), Y).backward()
    gn = [L.weight.grad.norm().item() for L in lins]
    return act, gn


satir = []
print("Katman 1 / 10 / 20 icin aktivasyon std ve gradyan normu:")
for init in ["kucuk", "xavier", "he"]:
    for bn in [False, True]:
        act, gn = olc(init, bn)
        ad = "%s%s" % (init, "+BN" if bn else "")
        for k in range(DERIN):
            a = act[k] if k < len(act) else float("nan")
            satir.append((ad, k + 1, "%.6e" % a, "%.6e" % gn[k]))
        print(
            "  %-10s act: %.2e %.2e %.2e"
            % (ad, act[0], act[9], act[19])
        )
        print(
            "  %-10s grad W1=%.2e W10=%.2e W20=%.2e cikis=%.2e"
            % (ad, gn[0], gn[9], gn[19], gn[-1])
        )
csv_yaz(
    "b64_baslatma.csv",
    satir,
    ["init", "katman", "aktivasyon_std", "gradyan_norm"],
)

# Egitim: 20 katman, SGD lr=0.05, 20 epoch, 3 tohum, test dogrulugu
print("\nEgitim (20 katman, SGD lr=0.05, 20 epoch, 3 tohum):")
satir = []
for init, bn in [
    ("kucuk", False),
    ("xavier", False),
    ("he", False),
    ("he", True),
]:
    tes = []
    for s in SEEDS[:3]:
        torch.manual_seed(s)
        model, _ = ag(init, bn)
        opt = torch.optim.SGD(model.parameters(), lr=0.05)
        h = egit(model, opt, D, epochs=20, batch=32, seed=s)
        tes.append(h["test_acc"])
    mu, sd = ortalama_sapma(tes)
    ad = "%s%s" % (init, "+BN" if bn else "")
    print("  %-10s test = %.4f +- %.4f" % (ad, mu, sd))
    satir.append((ad, "%.4f" % mu, "%.4f" % sd))
csv_yaz(
    "b64_baslatma_egitim.csv", satir, ["init", "test_ort", "test_sd"]
)
