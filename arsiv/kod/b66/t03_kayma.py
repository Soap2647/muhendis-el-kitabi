# -*- coding: utf-8 -*-
"""Bölüm 66 - t03: MLP vs CNN, öteleme (kayma) duyarlılığı ve
eşdeğişkenlik.

Eğitim: hedef alan, 800 örnek/sınıf (konum jitter ±3 px). Test:
300/sınıf,
test görüntüleri (dx, 0) kadar kaydırılarak ölçülür. 5 tohum.
"""

import csv
import os
import numpy as np
import torch
import torch.nn.functional as F
from synth import hedef_veri, kaydir
from ortak import (
    DEV,
    tensor,
    Mlp,
    Kucuk,
    egit,
    dogruluk,
    parametre_say,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
KAYMALAR = [0, 1, 2, 4, 6, 8]

# 1) Eşdeğişkenlik: konvolüsyonu 1 px kaydır, çıktı da kayar mı?
torch.manual_seed(0)
conv = torch.nn.Conv2d(1, 4, 3, padding=1, bias=False).to(DEV)
x = torch.rand(1, 1, 32, 32, device=DEV)
x_k = torch.roll(
    x, shifts=(0, 1), dims=(2, 3)
)  # sağa 1 px (dairesel)
y1 = conv(x)
y2 = conv(x_k)
ic = slice(2, 30)  # kenar etkisi yok
fark = (
    (
        torch.roll(y1, shifts=(0, 1), dims=(2, 3))[..., ic, ic]
        - y2[..., ic, ic]
    )
    .abs()
    .max()
    .item()
)
print(
    "1) Konvolüsyon eşdeğişkenliği: iç bölgede en büyük fark = %.2e"
    % fark
)

# 2) Veri ve parametre sayıları
Xt, yt = hedef_veri(800, 1)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
print(
    "2) Parametre sayısı: MLP %d, CNN %d"
    % (parametre_say(Mlp()), parametre_say(Kucuk()))
)

# 3) Eğitim ve kayma testi
sonuc = []
for tohum in range(5):
    for ad, kur in (("MLP", Mlp), ("CNN", Kucuk)):
        torch.manual_seed(tohum)
        model = kur().to(DEV)
        egit(model, Xt_g, yt_g, adim=1500, tohum=tohum)
        satir = []
        for dx in KAYMALAR:
            Xk = tensor(kaydir(Xs, dx, 0), ys)[0]
            acc = dogruluk(model, Xk, ys_g)
            satir.append(acc)
            sonuc.append((ad, tohum, dx, acc))
        print(
            "tohum %d %-3s  " % (tohum, ad)
            + "  ".join(
                "%d:%.3f" % (dx, a) for dx, a in zip(KAYMALAR, satir)
            )
        )

print("\nOrtalama doğruluk (5 tohum) — kayma (px) başına:")
for ad in ("MLP", "CNN"):
    ort = []
    for dx in KAYMALAR:
        v = [s[3] for s in sonuc if s[0] == ad and s[2] == dx]
        ort.append("%.3f" % np.mean(v))
    print("%-3s  " % ad + "  ".join(ort))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_kayma.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["model", "tohum", "kayma", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], s[1], s[2], "%.4f" % s[3]])
