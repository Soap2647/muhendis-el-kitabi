# -*- coding: utf-8 -*-
"""Bölüm 66 - t07: dağılım kayması altında sağlamlık (bozulma
şiddeti).

Model: Kucuk CNN, hedef alan 500/sınıf, temiz (kendi dağılımında)
eğitim.
Test: aynı dağılımın test kümesi, dört bozulma türünde beş şiddet
düzeyi:
  gurultu   : Gauss gürültüsü, sigma = 0, 0.1, 0.2, 0.3, 0.4
  bulaniklik: 3x3 kutu bulanıklığı, 0-4 kez uygulanır
  karanlik  : parlaklık çarpanı 1.0, 0.7, 0.5, 0.3, 0.15 (düşük ışık)
  kontrast  : 0.5 + c (x - 0.5), c = 1, 0.7, 0.5, 0.3, 0.15
5 tohum. Bu bir sensör bozulması modelidir; saldırı değildir.
"""

import csv
import os
import numpy as np
import torch
import torch.nn.functional as F
from synth import hedef_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
Xs, ys = hedef_veri(300, 99)
Xs_g, ys_g = tensor(Xs, ys)
g = torch.Generator(device=DEV).manual_seed(5)


def boz(x, tur, sev):
    if tur == "gurultu":
        s = [0, 0.1, 0.2, 0.3, 0.4][sev]
        n = torch.randn(x.shape, generator=g, device=DEV) * s
        return (x + n).clamp(0, 1)
    if tur == "bulaniklik":
        for _ in range(sev):
            x = F.avg_pool2d(x, 3, 1, 1, count_include_pad=False)
        return x
    if tur == "karanlik":
        return x * [1.0, 0.7, 0.5, 0.3, 0.15][sev]
    if tur == "kontrast":
        c = [1.0, 0.7, 0.5, 0.3, 0.15][sev]
        return (0.5 + c * (x - 0.5)).clamp(0, 1)
    raise ValueError(tur)


TURLER = ["gurultu", "bulaniklik", "karanlik", "kontrast"]
sonuc = []
for tohum in range(5):
    Xt, yt = hedef_veri(500, 300 + tohum)
    Xt_g, yt_g = tensor(Xt, yt)
    torch.manual_seed(tohum)
    model = Kucuk().to(DEV)
    egit(model, Xt_g, yt_g, adim=1500, tohum=tohum)
    for tur in TURLER:
        for sev in range(5):
            x = boz(Xs_g, tur, sev)
            sonuc.append((tur, sev, tohum, dogruluk(model, x, ys_g)))
    print(
        "tohum %d bitti (temiz test %.3f)"
        % (
            tohum,
            [
                s[3]
                for s in sonuc
                if s[0] == "gurultu" and s[1] == 0 and s[2] == tohum
            ][0],
        )
    )

print("\nOrtalama doğruluk (5 tohum), şiddet 0..4:")
for tur in TURLER:
    satir = []
    for sev in range(5):
        v = [s[3] for s in sonuc if s[0] == tur and s[1] == sev]
        satir.append("%.3f" % np.mean(v))
    print("%-11s " % tur + "  ".join(satir))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_bozulma.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["tur", "siddet", "tohum", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], s[1], s[2], "%.4f" % s[3]])
