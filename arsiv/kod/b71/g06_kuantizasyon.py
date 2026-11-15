# -*- coding: utf-8 -*-
"""Bolum 71 - Agirlik kuantizasyonu: tensor, kanal ve grup bazinda."""

import csv
import math
import os

import torch

from lm71 import CTX, KucukGPT, TEMP, metin_al
from ortak import VERI

torch.set_num_threads(4)
durum = torch.load(TEMP + "/lm71.pt", weights_only=False)
kars = durum["kars"]
si = {c: i for i, c in enumerate(kars)}
metin = metin_al()
n = len(metin)
test = torch.tensor([si[c] for c in metin[int(n * 0.9) :]])


def kuantize(w, bit, kip, grup=32):
    """Simetrik kuantizasyon.

    Dondurur: (dequantize w, bayt)."""
    qmax = 2 ** (bit - 1) - 1
    if kip == "tensor":
        olcek = w.abs().max() / qmax
        q = torch.clamp(torch.round(w / olcek), -qmax - 1, qmax)
        bayt = w.numel() * bit / 8 + 2
        return q * olcek, bayt
    if kip == "kanal":
        olcek = w.abs().amax(dim=1, keepdim=True) / qmax
        q = torch.clamp(torch.round(w / olcek), -qmax - 1, qmax)
        bayt = w.numel() * bit / 8 + 2 * w.shape[0]
        return q * olcek, bayt
    # grup: her satirda girdi boyunca 'grup' uzunlukta parcalar
    satir, sut = w.shape
    g = w.reshape(satir, sut // grup, grup)
    olcek = g.abs().amax(dim=2, keepdim=True) / qmax
    q = torch.clamp(torch.round(g / olcek), -qmax - 1, qmax)
    bayt = w.numel() * bit / 8 + 2 * (w.numel() // grup)
    return (q * olcek).reshape(satir, sut), bayt


HATA = [0.0, 0]


def model_yukle(agirlik_fn=None):
    m = KucukGPT(len(kars))
    m.load_state_dict(durum["durum"])
    m.eval()
    bayt = 0.0
    if agirlik_fn is not None:
        with torch.no_grad():
            for ad, p in m.named_parameters():
                if p.dim() == 2 and ad != "pos.weight":
                    yeni, b = agirlik_fn(p)
                    HATA[0] += float(((yeni - p) ** 2).sum())
                    HATA[1] += p.numel()
                    p.copy_(yeni)
                    bayt += b
                else:
                    bayt += p.numel() * 4
    else:
        bayt = sum(p.numel() for p in m.parameters()) * 4
    return m, bayt


def bpc(m):
    """Test kumesi uzerinde bit/karakter.

    Pencereler CTX uzunlugundadir."""
    toplam, adet = 0.0, 0
    with torch.no_grad():
        for i in range(0, len(test) - CTX - 1, CTX):
            x = test[i : i + CTX].unsqueeze(0)
            y = test[i + 1 : i + CTX + 1].unsqueeze(0)
            logit = m(x)
            kayip = torch.nn.functional.cross_entropy(
                logit.reshape(-1, len(kars)),
                y.reshape(-1),
                reduction="sum",
            )
            toplam += kayip.item()
            adet += CTX
    nll = toplam / adet
    return nll / math.log(2), math.exp(nll)


if __name__ == "__main__":
    deneyler = [
        ("fp32", 32, None),
        ("int8 tensör", 8, lambda w: kuantize(w, 8, "tensor")),
        ("int8 kanal", 8, lambda w: kuantize(w, 8, "kanal")),
        ("int4 tensör", 4, lambda w: kuantize(w, 4, "tensor")),
        ("int4 kanal", 4, lambda w: kuantize(w, 4, "kanal")),
        ("int4 grup-32", 4, lambda w: kuantize(w, 4, "grup", 32)),
    ]
    satirlar = []
    temel = None
    print(
        "%-14s %5s %10s %8s %8s %9s %11s"
        % (
            "yontem",
            "bit",
            "bayt",
            "bpc",
            "ppl",
            "delta",
            "agirlik_mse",
        )
    )
    for ad, bit, fn in deneyler:
        HATA[0], HATA[1] = 0.0, 0
        m, bayt = model_yukle(fn)
        mse = HATA[0] / HATA[1] if HATA[1] else 0.0
        b, ppl = bpc(m)
        if temel is None:
            temel = b
        print(
            "%-14s %5d %10.0f %8.4f %8.3f %+9.4f %11.3e"
            % (ad, bit, bayt, b, ppl, b - temel, mse)
        )
        satirlar.append(
            {
                "yontem": ad,
                "bit": bit,
                "bayt": round(bayt),
                "bpc": round(b, 5),
                "ppl": round(ppl, 4),
                "delta": round(b - temel, 5),
                "agirlik_mse": "%.3e" % mse,
            }
        )
    with open(
        os.path.join(VERI, "b71_kuantizasyon.csv"),
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
