# -*- coding: utf-8 -*-
"""Deney 9b: NaN'in iki yolu. (1) ayrik log(softmax) ile log(0);
(2) kayip degeri sonsuz (inf) olunca gradyan NaN'a donusur."""

import torch
import torch.nn.functional as F
from ortak64 import veri, mlp

D = veri()
Xtr, ytr = D[0], D[1]
torch.manual_seed(0)
m = mlp()
opt = torch.optim.SGD(m.parameters(), lr=1e3)
for k in range(6):
    opt.zero_grad()
    out = m(Xtr[:32])
    p = torch.softmax(out, 1)
    loss = -torch.log(p.gather(1, ytr[:32, None])).mean()  # ayrik log
    loss.backward()
    print(
        "adim %d  kayip=%s  logit_maks=%.3g"
        % (k, loss.item(), out.abs().max().item())
    )
    opt.step()
print("\nKararli: F.cross_entropy ayni veride:")
torch.manual_seed(0)
m = mlp()
opt = torch.optim.SGD(m.parameters(), lr=1e3)
for k in range(6):
    opt.zero_grad()
    loss = F.cross_entropy(m(Xtr[:32]), ytr[:32])
    loss.backward()
    print("adim %d  kayip=%s" % (k, loss.item()))
    opt.step()
