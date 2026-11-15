# -*- coding: utf-8 -*-
"""Bölüm 66 - kontrol: gürültü şiddetine duyarlılık ve BN katlama
doğruluğu."""

import copy
import torch
import torch.nn as nn
from synth import hedef_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk

Xt, yt = hedef_veri(500, 300)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
torch.manual_seed(0)
model = Kucuk().to(DEV)
egit(model, Xt_g, yt_g, adim=1500, tohum=0)
model.eval()
print("Temiz test doğruluğu: %.4f" % dogruluk(model, Xs_g, ys_g))

g = torch.Generator(device=DEV).manual_seed(5)
for s in [0.02, 0.05, 0.10]:
    n = torch.randn(Xs_g.shape, generator=g, device=DEV) * s
    x = (Xs_g + n).clamp(0, 1)
    print(
        "gürültü sigma=%.2f: doğruluk %.4f"
        % (s, dogruluk(model, x, ys_g))
    )

mm = copy.deepcopy(model).eval()
for blok in mm.ozellik:
    conv, bn = blok[0], blok[1]
    s = bn.weight / torch.sqrt(bn.running_var + bn.eps)
    conv.weight.data = conv.weight.data * s.view(-1, 1, 1, 1)
    conv.bias = nn.Parameter(bn.bias - bn.running_mean * s)
    blok[1] = nn.Identity()
with torch.no_grad():
    fark = (model(Xs_g) - mm(Xs_g)).abs().max().item()
print("BN katlı model, en büyük logit farkı: %.2e" % fark)
print("BN katlı model doğruluğu: %.4f" % dogruluk(mm, Xs_g, ys_g))
