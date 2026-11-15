# -*- coding: utf-8 -*-
"""Bölüm 66 - t08: parametre/FLOP, depthwise separable
karşılaştırması,
çıkarım süresi (GPU/CPU, batch'e göre) ve int8 simülasyonu (BN
katlamalı).
"""

import copy
import csv
import os
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.flop_counter import FlopCounterMode
from synth import hedef_veri
from ortak import (
    DEV,
    tensor,
    Kucuk,
    Mlp,
    egit,
    dogruluk,
    parametre_say,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"

# 1) Parametre ve FLOP
m = Kucuk().to(DEV).eval()
with FlopCounterMode(display=False) as fc:
    m(torch.zeros(1, 1, 32, 32, device=DEV))
print(
    "1) Kucuk CNN: parametre %d, FLOP (tek görüntü) %d (%.2f M)"
    % (
        parametre_say(m),
        fc.get_total_flops(),
        fc.get_total_flops() / 1e6,
    )
)
mm = Mlp().to(DEV).eval()
with FlopCounterMode(display=False) as fc2:
    mm(torch.zeros(1, 1, 32, 32, device=DEV))
print(
    "   MLP: parametre %d, FLOP %d (%.2f M)"
    % (
        parametre_say(mm),
        fc2.get_total_flops(),
        fc2.get_total_flops() / 1e6,
    )
)

# 2) Standart konvolüsyon vs depthwise separable (64 -> 128, 3x3,
# 16x16 çıkış)
std = nn.Conv2d(64, 128, 3, padding=1, bias=False)
dws = nn.Sequential(
    nn.Conv2d(64, 64, 3, padding=1, groups=64, bias=False),
    nn.Conv2d(64, 128, 1, bias=False),
)
print("\n2) 64->128, 3x3:")
print("   standart  : parametre %6d" % parametre_say(std))
print(
    "   ayrılabilir: parametre %6d (derinlemesine %d + noktasal %d)"
    % (parametre_say(dws), 64 * 9, 64 * 128)
)
print("   oran: %.2f kat" % (parametre_say(std) / parametre_say(dws)))

# 3) Eğitilmiş model (hedef alan, 500/sınıf, tohum 0)
Xt, yt = hedef_veri(500, 300)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
torch.manual_seed(0)
model = Kucuk().to(DEV)
egit(model, Xt_g, yt_g, adim=1500, tohum=0)
model.eval()
print("\n3) fp32 test doğruluğu: %.4f" % dogruluk(model, Xs_g, ys_g))


# 4) Çıkarım süresi (GPU, batch'e göre; medyan 50 ölçüm)
@torch.no_grad()
def hiz(model, dev, B, n=50):
    x = torch.rand(B, 1, 32, 32, device=dev)
    for _ in range(10):
        model(x)
    if dev.type == "cuda":
        torch.cuda.synchronize()
    zaman = []
    for _ in range(n):
        t0 = time.perf_counter()
        model(x)
        if dev.type == "cuda":
            torch.cuda.synchronize()
        zaman.append(time.perf_counter() - t0)
    return float(np.median(zaman))


kayit = []
print("\n4) Çıkarım süresi (medyan):")
for dev in (DEV, torch.device("cpu")):
    mod = model.to(dev)
    for B in (1, 16, 128, 1024):
        s = hiz(mod, dev, B)
        kayit.append((dev.type, B, s * 1000, B / s))
        print(
            "   %-4s batch %4d: %8.3f ms  (%10.0f görüntü/s)"
            % (dev.type, B, s * 1000, B / s)
        )
model.to(DEV)


# 5) int8 simülasyonu: BN'i konvolüsyona katla, simetrik per-tensor
# int8
def katla(mdl):
    mm = copy.deepcopy(mdl).eval()
    for blok in mm.ozellik:
        conv, bn = blok[0], blok[1]
        s = bn.weight / torch.sqrt(bn.running_var + bn.eps)
        conv.weight.data = conv.weight.data * s.view(-1, 1, 1, 1)
        conv.bias = nn.Parameter(bn.bias - bn.running_mean * s)
        blok[1] = nn.Identity()
    return mm


def fq(x, s):
    return torch.clamp(torch.round(x / s), -127, 127) * s


kat = katla(model).to(DEV)
Xc = Xt_g[:2000]
kayit_a = {}


def kal(mod, name):
    def h(_, inp):
        kayit_a[name] = max(
            kayit_a.get(name, 0.0), inp[0].abs().max().item()
        )

    return h


hook = []
for nm, mod in kat.named_modules():
    if isinstance(mod, (nn.Conv2d, nn.Linear)):
        hook.append(mod.register_forward_pre_hook(kal(mod, nm)))
with torch.no_grad():
    kat(Xc)
for h in hook:
    h.remove()

olcek_a, olcek_w = {}, {}
for nm, mod in kat.named_modules():
    if isinstance(mod, (nn.Conv2d, nn.Linear)):
        olcek_a[nm] = kayit_a[nm] / 127.0
        olcek_w[nm] = mod.weight.data.abs().max().item() / 127.0
        mod.weight.data = fq(mod.weight.data, olcek_w[nm])
        sa = olcek_a[nm]
        mod.register_forward_pre_hook(
            lambda _m, inp, sa=sa: (fq(inp[0], sa),)
        )
with torch.no_grad():
    p8 = kat(Xs_g).argmax(1)
    p32 = model(Xs_g).argmax(1)
acc8 = (p8 == ys_g).float().mean().item()
uyum = (p8 == p32).float().mean().item()
n = parametre_say(model)
print("\n5) int8 simülasyonu (BN katlı, per-tensor simetrik):")
print("   fp32 doğruluk      : %.4f" % dogruluk(model, Xs_g, ys_g))
print("   int8-sim doğruluk  : %.4f" % acc8)
print("   fp32 ile tahmin uyumu: %.4f" % uyum)
print(
    "   ağırlık: fp32 %d bayt, int8 %d bayt "
    "(sapma/ölçek hariç)" % (4 * n, n)
)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_hiz.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["cihaz", "batch", "ms", "goruntu_s"])
    for k in kayit:
        w.writerow([k[0], k[1], "%.4f" % k[2], "%.1f" % k[3]])
