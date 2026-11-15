# -*- coding: utf-8 -*-
"""Deney 6: BatchNorm - el ornegi, batch boyutu,
egitim/cikarim farki."""

import numpy as np
import torch
import torch.nn as nn
from egitim_np import bn_ileri
from ortak64 import veri, egit, csv_yaz, SEEDS, ortalama_sapma

# (a) El ornegi: N=4, D=1, gamma=2, beta=1
x = np.array([[1.0], [3.0], [5.0], [7.0]])
y, _, mu, var = bn_ileri(x, np.array([2.0]), np.array([1.0]))
print("mu =", mu, " var (N'e bolunmus) =", var)
print("xhat =", np.round((x - mu) / np.sqrt(var + 1e-5), 4).ravel())
print("y    =", np.round(y, 4).ravel())

# (b) Kucuk batch: BN'li MLP, egitim batch boyutu
D = veri()
satir = []
print("\nBN'li MLP (2 gizli katman), 20 epoch, 5 tohum:")
for b in [2, 8, 32, 128]:
    tes = []
    for s in SEEDS:
        torch.manual_seed(s)
        from ortak64 import mlp

        m = mlp(bn=True)
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        h = egit(m, opt, D, epochs=20, batch=b, seed=s)
        tes.append(h["test_acc"])
    mu_, sd = ortalama_sapma(tes)
    print("  batch=%4d  test = %.4f +- %.4f" % (b, mu_, sd))
    satir.append((b, "%.4f" % mu_, "%.4f" % sd))
csv_yaz("b64_bn_batch.csv", satir, ["batch", "test_ort", "test_sd"])

# (c) Egitim ve cikarim modu: BN istatistiklerinin farki
torch.manual_seed(0)
from ortak64 import mlp

m = mlp(bn=True)
opt = torch.optim.Adam(m.parameters(), lr=1e-3)
egit(m, opt, D, epochs=10, batch=32, seed=0)
Xva = D[2][:64]
m.eval()
with torch.no_grad():
    cik = m(Xva).argmax(1)
m.train()
with torch.no_grad():
    egt = m(Xva).argmax(1)  # yanlis: batch istatistikleri kullanilir
print(
    "\nAyni 64 dogrulama orneginde tahmin farki "
    "(eval vs train modu): "
    "%d / 64" % (cik != egt).sum().item()
)
