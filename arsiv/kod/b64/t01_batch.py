# -*- coding: utf-8 -*-
"""Deney 1: batch boyutu, gradyan gurultusu ve ogrenme orani."""

import numpy as np
import torch
import torch.nn.functional as F
from ortak64 import veri, mlp, egit, csv_yaz, SEEDS, ortalama_sapma

D = veri()
Xtr, ytr = D[0], D[1]

# (a) Gradyan gurultusu: tam gradyana gore sapma, batch boyutuna gore
torch.manual_seed(0)
model = mlp()


def grad_vec(idx):
    model.zero_grad()
    F.cross_entropy(model(Xtr[idx]), ytr[idx]).backward()
    return torch.cat(
        [p.grad.flatten() for p in model.parameters()]
    ).clone()


tam = grad_vec(torch.arange(len(Xtr)))
g = torch.Generator().manual_seed(1)
gur_satir = []
print("Gradyan gurultusu (init, 300 tekrar):")
for b in [8, 32, 128, 512]:
    fark2 = []
    for _ in range(300):
        idx = torch.randperm(len(Xtr), generator=g)[:b]
        fark2.append(((grad_vec(idx) - tam) ** 2).sum().item())
    ort = np.mean(fark2)
    gur_satir.append((b, ort))
    print("  batch=%4d  E||g_b - g||^2 = %.6f" % (b, ort))
base = gur_satir[0][1]
for b, v in gur_satir:
    print("  batch=%4d  oran (8'e gore) = %.3f" % (b, v / base))
csv_yaz(
    "b64_gurultu.csv",
    [(b, "%.6f" % v) for b, v in gur_satir],
    ["batch", "gurultu"],
)

# (b) Sabit epoch, sabit lr vs dogrusal lr olcegi
satirlar = []
print("\nEpoch=30, SGD (momentum yok), 5 tohum:")
for mod, lr_f in [
    ("sabit_lr=0.1", lambda b: 0.1),
    ("dogrusal_olcek", lambda b: 0.1 * b / 32),
]:
    for b in [8, 32, 128, 512]:
        accs, adims = [], []
        for s in SEEDS:
            torch.manual_seed(s)
            m = mlp()
            opt = torch.optim.SGD(m.parameters(), lr=lr_f(b))
            h = egit(m, opt, D, epochs=30, batch=b, seed=s)
            accs.append(h["test_acc"])
            adims.append(h["adim"])
            satirlar.append(
                (mod, b, s, "%.4f" % h["test_acc"], h["adim"])
            )
        mu, sd = ortalama_sapma(accs)
        print(
            "  %-16s batch=%4d adim=%5d  test=%.4f +- %.4f"
            % (mod, b, adims[0], mu, sd)
        )
csv_yaz(
    "b64_batch.csv",
    satirlar,
    ["mod", "batch", "seed", "test_acc", "adim"],
)
