# -*- coding: utf-8 -*-
"""Bolum 75: roofline olcumu (tepe, bant, katman
aritmetik yogunlugu) ve dinamik int8 ile fp32 gecikme karsilastirmasi.
"""

import copy
import csv
import os
import time
import numpy as np
import torch
import torch.nn as nn
from b75_ortak import mlp, zamanla

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def tepe_flops():
    """Buyuk matris carpimiyla ulasilan en yuksek GFLOP/s (yaklasik
    tepe).
    """
    a = torch.randn(1024, 1024)
    b = torch.randn(1024, 1024)
    med, _ = zamanla(lambda: a @ b, n=20, isinma=5)
    return 2 * 1024**3 / (med * 1e-3) / 1e9


def bellek_bandi():
    """Buyuk bir kopyalama: okuma + yazma baytlari / sure (GB/s)."""
    x = torch.randn(64 * 1024 * 1024 // 4)  # 64 MB float32
    med, _ = zamanla(lambda: x.clone(), n=20, isinma=5)
    return 2 * x.numel() * 4 / (med * 1e-3) / 1e9


def roofline(tepe, bant):
    """Her girdi boyu icin 2048x2048 Linear katmani; AI ve olculen
    GFLOP/s.
    """
    n = 2048
    W = torch.randn(n, n)
    satir = []
    for B in [1, 4, 16, 64, 256, 1024]:
        x = torch.randn(B, n)
        flops = 2.0 * B * n * n
        bayt = 4.0 * (
            n * n + 2 * B * n
        )  # agirlik + girdi + cikti (fp32)
        ai = flops / bayt
        med, _ = zamanla(lambda: x @ W.T, n=60, isinma=10)
        gf = flops / (med * 1e-3) / 1e9
        sinir = min(tepe, bant * ai)
        satir.append(
            dict(
                B=B,
                ai=round(ai, 3),
                gflops=round(gf, 2),
                sinir=round(sinir, 2),
                sure_ms=round(med, 4),
                sinir_turu="bellek" if bant * ai < tepe else "hesap",
            )
        )
        print(
            "B=%-5d AI=%7.3f FLOP/bayt  olculen=%8.2f GFLOP/s  "
            "tavan=%8.2f (%s)"
            % (B, ai, gf, sinir, satir[-1]["sinir_turu"])
        )
    return satir


def dinamik_gecikme():
    """2048x2048 MLP: fp32 ve PyTorch dinamik int8 (Linear icin)."""
    torch.manual_seed(0)
    fp = mlp(gizli=(2048, 2048)).eval()
    q = torch.ao.quantization.quantize_dynamic(
        copy.deepcopy(fp), {nn.Linear}, dtype=torch.qint8
    ).eval()
    satir = []
    for B in [1, 32]:
        x = torch.randn(B, 64)
        for ad, m in [("fp32", fp), ("dinamik_int8", q)]:
            with torch.no_grad():
                med, p95 = zamanla(lambda: m(x), n=300, isinma=30)
            satir.append(
                dict(
                    model=ad,
                    B=B,
                    medyan_ms=round(med, 4),
                    p95_ms=round(p95, 4),
                )
            )
            print(
                "%-13s B=%-3d medyan=%.4f ms  p95=%.4f ms"
                % (ad, B, med, p95)
            )
    return satir


def yaz(ad, satirlar):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", yol)


if __name__ == "__main__":
    torch.set_num_threads(4)
    tepe = tepe_flops()
    bant = bellek_bandi()
    print("tepe (olculen, yaklasik): %.1f GFLOP/s" % tepe)
    print("bellek bant genisligi (olculen, kopya): %.1f GB/s" % bant)
    yaz("b75_roofline.csv", roofline(tepe, bant))
    yaz("b75_dinamik_gecikme.csv", dinamik_gecikme())
