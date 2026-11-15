# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 4: cekirdek birlestirme (fusion), bellek."""

import _cudaenv  # noqa: F401
import csv
import os
import torch
from numba import cuda, float32
from olcum import medyan_ms_numba, medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
A, B, C, D = 1.5, -0.25, 0.75, 0.1


@cuda.jit
def fused(x, y, n):
    # y = relu(x*A + B) * C + D tek cekirdekte: bellek trafigi 8N bayt
    i = cuda.grid(1)
    if i < n:
        v = x[i] * float32(A) + float32(B)
        if v < 0.0:
            v = float32(0.0)
        y[i] = v * float32(C) + float32(D)


def eager(x):
    # Bes ayri cekirdek; her biri bellekten okur ve bellege yazar
    t1 = x * A
    t2 = t1 + B
    t3 = torch.relu(t2)
    t4 = t3 * C
    return t4 + D


def main():
    print(
        "n            eager ms   fused ms   hizlanma   eager GB/s  "
        "fused GB/s"
    )
    rows = []
    for k in [14, 18, 22, 25]:
        n = 1 << k
        x = torch.randn(
            n,
            device="cuda",
            generator=torch.Generator(device="cuda").manual_seed(76),
        )
        y = torch.empty_like(x)
        dx = cuda.as_cuda_array(x)
        dy = cuda.as_cuda_array(y)
        blok = (n + 255) // 256
        me, _, _ = medyan_ms_torch(lambda: eager(x))
        mf, _, _ = medyan_ms_numba(
            cuda, lambda: fused[blok, 256](dx, dy, n)
        )
        # Dogruluk: eager ile fused ayni sonucu vermeli
        fused[blok, 256](dx, dy, n)
        cuda.synchronize()
        fark = (eager(x) - y).abs().max().item()
        # Bayt trafigi: eager = 5 islem x (4N okuma + 4N yazma) = 40N
        ge = 40 * n / (me * 1e-3) / 1e9
        gf = 8 * n / (mf * 1e-3) / 1e9
        rows.append(
            (
                n,
                round(me, 4),
                round(mf, 4),
                round(me / mf, 2),
                round(ge, 1),
                round(gf, 1),
                f"{fark:.1e}",
            )
        )
        print(
            f"2^{k:<3} {me:10.4f} {mf:10.4f}   {me / mf:6.2f}x   "
            f"{ge:8.1f}   {gf:8.1f}"
        )
    maks = max(float(r[6]) for r in rows)
    print(f"max fark (tum boyutlar): {maks:.1e}")
    with open(
        os.path.join(VERI, "b76_fuzyon.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(
            [
                "n",
                "eager_ms",
                "fused_ms",
                "hizlanma",
                "eager_gbps",
                "fused_gbps",
                "max_fark",
            ]
        )
        w.writerows(rows)


if __name__ == "__main__":
    main()
