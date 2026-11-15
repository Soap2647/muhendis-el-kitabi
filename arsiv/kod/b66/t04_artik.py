# -*- coding: utf-8 -*-
"""Bölüm 66 - t04: düz derin ağ vs artık (residual) ağ, BN ile ve
BN'siz.

Her iki model da 25 konvolüsyon katmanlı (1 stem + 12 blok x 2).
Eğitim: hedef alan, 1500 örnek/sınıf, 20 epoch, Adam lr=1e-3, batch
64.
3 tohum. Eğitim kaybı her epoch'un ortalaması olarak kaydedilir.
"""

import csv
import os
import time
import numpy as np
import torch
from synth import hedef_veri
from ortak import (
    DEV,
    tensor,
    DerinAg,
    egit,
    dogruluk,
    parametre_say,
    sure_olc,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
BLOK, EPOCH, BS = 12, 20, 64
Xt, yt = hedef_veri(1500, 2)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
ADIM_EP = int(np.ceil(len(yt) / BS))  # 94 adım/epoch
print(
    "Konvolüsyon sayısı: %d, parametre: %d"
    % (1 + 2 * BLOK, parametre_say(DerinAg(BLOK)))
)
print(
    "Eğitim %d, test %d, adım/epoch %d" % (len(yt), len(ys), ADIM_EP)
)

VARYANTLAR = [
    ("duz_BN", True, False),
    ("artik_BN", True, True),
    ("duz_BNsiz", False, False),
    ("artik_BNsiz", False, True),
]
kayip_satir, son_satir = [], []
for ad, bn, artik in VARYANTLAR:
    for tohum in range(3):
        torch.manual_seed(tohum)
        model = DerinAg(BLOK, bn=bn, artik=artik).to(DEV)
        t0 = time.perf_counter()
        kay = egit(
            model, Xt_g, yt_g, adim=EPOCH * ADIM_EP, tohum=tohum
        )
        torch.cuda.synchronize()
        sure = time.perf_counter() - t0
        epoch_kay = kay.reshape(EPOCH, ADIM_EP).mean(axis=1)
        for e, v in enumerate(epoch_kay, 1):
            kayip_satir.append((ad, tohum, e, v))
        tr = dogruluk(model, Xt_g[:1500], yt_g[:1500])
        te = dogruluk(model, Xs_g, ys_g)
        son_satir.append((ad, tohum, tr, te, sure))
        print(
            "%-12s tohum %d  kayıp %.4f  eğitim %.3f  test %.3f"
            % (ad, tohum, epoch_kay[-1], tr, te)
        )

print("\nEpoch 1 / 5 / 20 ortalama eğitim kaybı (3 tohum):")
for ad, _, _ in VARYANTLAR:
    v = {
        e: np.mean(
            [s[3] for s in kayip_satir if s[0] == ad and s[2] == e]
        )
        for e in (1, 5, EPOCH)
    }
    print("%-12s %.4f  %.4f  %.4f" % (ad, v[1], v[5], v[EPOCH]))

print("\nTest doğruluğu (ortalama ± sapma):")
for ad, _, _ in VARYANTLAR:
    v = [s[3] for s in son_satir if s[0] == ad]
    print("%-12s %.4f ± %.4f" % (ad, np.mean(v), np.std(v, ddof=1)))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_artik_kayip.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["varyant", "tohum", "epoch", "egitim_kaybi"])
    for s in kayip_satir:
        w.writerow([s[0], s[1], s[2], "%.5f" % s[3]])
with open(
    os.path.join(VERI, "b66_artik_son.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(
        [
            "varyant",
            "tohum",
            "egitim_dogruluk",
            "test_dogruluk",
            "sure_s",
        ]
    )
    for s in son_satir:
        w.writerow(
            [s[0], s[1], "%.4f" % s[2], "%.4f" % s[3], "%.1f" % s[4]]
        )
