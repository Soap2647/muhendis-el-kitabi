# -*- coding: utf-8 -*-
"""Bolum 75: parametre, MAC ve gecikme karsilastirmasi.
Standart konvolusyon ile derinlemesine ayrilabilir konvolusyon
konvolusyon; torchvision MobileNetV3-Small ve ResNet-18 (224x224).
"""

import csv
import os
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as tvm
from b75_ortak import mlp, zamanla

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def standart_cnn():
    return nn.Sequential(
        nn.Conv2d(1, 32, 3, padding=1),
        nn.ReLU(),
        nn.Conv2d(32, 64, 3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(64 * 4 * 4, 10),
    )


def ayrilabilir_cnn():
    """Ikinci konvolusyon: 32 kanalli DW 3x3 + 1x1 PW (64 kanal)."""
    return nn.Sequential(
        nn.Conv2d(1, 32, 3, padding=1),
        nn.ReLU(),
        nn.Conv2d(32, 32, 3, padding=1, groups=32),
        nn.ReLU(),
        nn.Conv2d(32, 64, 1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(64 * 4 * 4, 10),
    )


def mac_say(model, x):
    """Conv2d ve Linear katmanlarinda MAC: kanca ile cikis boyutundan.
    """
    toplam = [0]

    def kanca(m, g, c):
        # c: cikti tensoru, batch=1 varsayimi (N=1)
        if isinstance(m, nn.Conv2d):
            kh, kw = m.kernel_size
            yer = c.shape[2] * c.shape[3]  # H_cikis * W_cikis
            toplam[0] += (
                m.out_channels
                * yer
                * (m.in_channels // m.groups)
                * kh
                * kw
            )
        elif isinstance(m, nn.Linear):
            konum = int(np.prod(c.shape[1:-1])) if c.dim() > 2 else 1
            toplam[0] += m.in_features * m.out_features * konum

    kancalar = [
        m.register_forward_hook(kanca)
        for m in model.modules()
        if isinstance(m, (nn.Conv2d, nn.Linear))
    ]
    with torch.no_grad():
        model(x)
    for k in kancalar:
        k.remove()
    return toplam[0]


def parametre(model):
    return sum(p.numel() for p in model.parameters())


def olc(ad, model, x, n=300, isinma=30):
    model.eval()
    with torch.no_grad():
        med, p95 = zamanla(lambda: model(x), n=n, isinma=isinma)
    return dict(
        model=ad,
        parametre=parametre(model),
        mac=mac_say(model, x),
        giris=str(tuple(x.shape)[1:]),
        medyan_ms=round(med, 4),
        p95_ms=round(p95, 4),
    )


if __name__ == "__main__":
    torch.set_num_threads(4)
    torch.manual_seed(0)
    satirlar = []
    satirlar.append(
        olc("MLP_64_256_128_10", mlp().eval(), torch.randn(1, 64))
    )
    satirlar.append(
        olc(
            "CNN_standart",
            standart_cnn().eval(),
            torch.randn(1, 1, 8, 8),
        )
    )
    satirlar.append(
        olc(
            "CNN_ayrilabilir",
            ayrilabilir_cnn().eval(),
            torch.randn(1, 1, 8, 8),
        )
    )
    x224 = torch.randn(1, 3, 224, 224)
    satirlar.append(
        olc(
            "MobileNetV3_Small",
            tvm.mobilenet_v3_small(weights=None).eval(),
            x224,
            n=100,
            isinma=10,
        )
    )
    satirlar.append(
        olc(
            "ResNet18",
            tvm.resnet18(weights=None).eval(),
            x224,
            n=60,
            isinma=5,
        )
    )
    for s in satirlar:
        print(s)
    yol = os.path.join(VERI, "b75_mimari.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", yol)
