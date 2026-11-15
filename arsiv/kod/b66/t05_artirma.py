# -*- coding: utf-8 -*-
"""Bölüm 66 - t05: veri artırmanın az veride test doğruluğuna etkisi.

Hedef alan, sınıf başına 50 ve 500 örnek; artırma yok / var. Her koşul
5 tohum. Test seti: 300/sınıf, eğitimden ayrı tohum (99).
Eğitim: Kucuk CNN, Adam lr=1e-3, batch 64, 1500 adım.
"""

import csv
import os
import numpy as np
import torch
from synth import hedef_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk, artir

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
Xs, ys = hedef_veri(300, 99)
Xs_g, ys_g = tensor(Xs, ys)

# Örnek ızgarası: 8 görüntü, her biri için 3 artırılmış kopya (tohum
# 0)
X8, _ = hedef_veri(2, 77)
X8 = torch.tensor(X8[:8], device=DEV)
torch.manual_seed(0)
art = torch.stack([artir(X8) for _ in range(3)])
os.makedirs(VERI, exist_ok=True)
np.savez(
    os.path.join(VERI, "b66_artirma_ornek.npz"),
    orj=X8[:, 0].cpu().numpy(),
    art=art[:, :, 0].cpu().numpy(),
)

sonuc = []
for n in (50, 500):
    for artirma in (False, True):
        for tohum in range(5):
            Xt, yt = hedef_veri(n, 1000 + tohum)
            Xt_g, yt_g = tensor(Xt, yt)
            torch.manual_seed(tohum)
            model = Kucuk().to(DEV)
            egit(
                model,
                Xt_g,
                yt_g,
                adim=1500,
                tohum=tohum,
                aug=artir if artirma else None,
            )
            te = dogruluk(model, Xs_g, ys_g)
            sonuc.append((n, artirma, tohum, te))
        v = [s[3] for s in sonuc if s[0] == n and s[1] == artirma]
        print(
            "sınıf başına %3d, artırma %-5s: test %.4f ± %.4f"
            % (n, artirma, np.mean(v), np.std(v, ddof=1))
        )

with open(
    os.path.join(VERI, "b66_artirma.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["n_sinif", "artirma", "tohum", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], int(s[1]), s[2], "%.4f" % s[3]])
