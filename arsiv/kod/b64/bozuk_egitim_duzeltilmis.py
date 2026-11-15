# -*- coding: utf-8 -*-
"""Bolum 64 - Cozumlu Ornek 4: duzeltilmis egitim betigi."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri

Xtr, ytr, Xva, yva, Xte, yte = veri()
torch.manual_seed(0)
model = nn.Sequential(
    nn.Linear(64, 128),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(128, 128),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(128, 10),
)
opt = torch.optim.Adam(model.parameters(), lr=1e-2)


def dogruluk(X, y):
    model.eval()
    with torch.no_grad():
        return (model(X).argmax(1) == y).float().mean().item()


for ep in range(15):
    model.train()
    perm = torch.randperm(len(Xtr))
    kayip = 0.0
    for i in range(0, len(Xtr), 32):
        idx = perm[i : i + 32]
        opt.zero_grad()
        loss = F.cross_entropy(model(Xtr[idx]), ytr[idx])
        loss.backward()
        opt.step()
        kayip += loss.item()
    print(
        "ep %2d  kayip=%.4f  dogrulama=%.4f"
        % (ep + 1, kayip / (len(Xtr) / 32), dogruluk(Xva, yva))
    )
print("son test dogrulugu = %.4f" % dogruluk(Xte, yte))
