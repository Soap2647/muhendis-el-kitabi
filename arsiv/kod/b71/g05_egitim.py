# -*- coding: utf-8 -*-
"""Bolum 71 - Kucuk GPT egitimi (CPU, sabit tohum)."""

import time

import torch
import torch.nn.functional as F

from lm71 import CTX, KucukGPT, TEMP, metin_al, parametre_sayisi

torch.manual_seed(71)
torch.set_num_threads(4)
metin = metin_al()
kars = sorted(set(metin))
si = {c: i for i, c in enumerate(kars)}
veri = torch.tensor([si[c] for c in metin], dtype=torch.long)
n = len(veri)
bol = int(n * 0.9)
egitim, test = veri[:bol], veri[bol:]
print(
    "karakter=%d sozluk=%d egitim=%d test=%d"
    % (n, len(kars), bol, n - bol)
)
model = KucukGPT(len(kars))
print("parametre sayisi:", parametre_sayisi(model))
opt = torch.optim.AdamW(
    model.parameters(), lr=3e-3, weight_decay=0.01
)
ADIM, BATCH = 1500, 32
t0 = time.time()
gen = torch.Generator().manual_seed(71)
for adim in range(1, ADIM + 1):
    i = torch.randint(
        0, len(egitim) - CTX - 1, (BATCH,), generator=gen
    )
    x = torch.stack([egitim[j : j + CTX] for j in i])
    y = torch.stack([egitim[j + 1 : j + CTX + 1] for j in i])
    lr = 3e-3 * min(1.0, adim / 100) * (1 - adim / ADIM) + 3e-4
    for g in opt.param_groups:
        g["lr"] = lr
    logit = model(x)
    loss = F.cross_entropy(
        logit.reshape(-1, len(kars)), y.reshape(-1)
    )
    opt.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    if adim % 250 == 0 or adim == 1:
        print(
            "adim %4d kayip %.4f sure %.0f sn"
            % (adim, loss.item(), time.time() - t0)
        )
torch.save(
    {"durum": model.state_dict(), "kars": kars}, TEMP + "/lm71.pt"
)
print("kaydedildi:", TEMP + "/lm71.pt")
