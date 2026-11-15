# -*- coding: utf-8 -*-
"""Bölüm 69 - Konumsal kodlama: permütasyon, sinüzoidal, RoPE."""

import csv
import os
import torch
from tr69 import Dikkat, rotasyon, sinuzoidal, tohum

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
torch.set_default_dtype(torch.float64)


def permutasyon_testi(T=6, d=8):
    print("--- Permütasyon eşdeğişkenliği ---")
    tohum(0)
    m = Dikkat(d, 2)
    x = torch.randn(1, T, d)
    p = torch.tensor([3, 0, 5, 1, 4, 2])
    y, _ = m(x, x)
    yp, _ = m(x[:, p], x[:, p])
    print(
        "cikti(x[p]) - cikti(x)[p] :",
        float((yp - y[:, p]).abs().max()),
    )
    pe = sinuzoidal(T, d).double()
    y2, _ = m(x + pe, x + pe)  # konum eklendi
    # belirteçler karıştı, konum kodu yerinde kaldı
    yp2, _ = m(x[:, p] + pe, x[:, p] + pe)
    print(
        "konumlu, fark             :",
        float((yp2 - y2[:, p]).abs().max()),
    )


def sinuzoidal_tablo(T=32, d=32):
    print("--- Sinüzoidal kodlama: komşu konum benzerliği ---")
    pe = sinuzoidal(T, d).double()
    for k in [0, 1, 2, 4, 8]:
        benz = float((pe[0] @ pe[k]) / (pe[0].norm() * pe[k].norm()))
        print("konum 0 ile %2d arasinda kosinus: %.4f" % (k, benz))
    with open(
        os.path.join(VERI, "b69_pe.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerows(
            [["%.6f" % v for v in satir] for satir in pe.tolist()]
        )


def rope_testi(T=12, dh=8):
    print("--- RoPE: skor yalnızca göreli konuma mı bağlı? ---")
    tohum(1)
    qv = torch.randn(dh)
    kv = torch.randn(dh)
    q = rotasyon(qv.expand(1, 1, T, dh).clone())
    k = rotasyon(kv.expand(1, 1, T, dh).clone())
    for m, n in [(5, 2), (9, 6), (11, 8), (3, 0), (11, 0)]:
        print(
            "m=%2d n=%2d  m-n=%2d  skor=%.6f"
            % (m, n, m - n, float(q[0, 0, m] @ k[0, 0, n]))
        )
    ham = float(qv @ kv)
    print("dönmemiş q.k =", round(ham, 6))


if __name__ == "__main__":
    permutasyon_testi()
    sinuzoidal_tablo()
    rope_testi()
