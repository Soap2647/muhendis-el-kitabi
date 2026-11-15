# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 2: indirgeme (toplama) cekirdekleri."""

import _cudaenv  # noqa: F401
import csv
import os
import numpy as np
import torch
from numba import cuda, float32
from olcum import medyan_ms_numba, medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
TPB = 256


@cuda.jit
def naif(x, out, n):
    # v1: paylasilan bellek, ama ayrismali adresleme (tid % (2s) == 0)
    sd = cuda.shared.array(TPB, float32)
    tid = cuda.threadIdx.x
    i = cuda.blockIdx.x * TPB + tid
    if i < n:
        sd[tid] = x[i]
    else:
        sd[tid] = float32(0)
    cuda.syncthreads()
    s = 1
    while s < TPB:
        if tid % (2 * s) == 0:
            sd[tid] += sd[tid + s]
        cuda.syncthreads()
        s *= 2
    if tid == 0:
        out[cuda.blockIdx.x] = sd[0]


@cuda.jit
def sirali(x, out, n):
    # v2: sirali adresleme (tid < s): aktif iş parçacıkları bitisik
    sd = cuda.shared.array(TPB, float32)
    tid = cuda.threadIdx.x
    i = cuda.blockIdx.x * TPB + tid
    if i < n:
        sd[tid] = x[i]
    else:
        sd[tid] = float32(0)
    cuda.syncthreads()
    s = TPB // 2
    while s > 0:
        if tid < s:
            sd[tid] += sd[tid + s]
        cuda.syncthreads()
        s //= 2
    if tid == 0:
        out[cuda.blockIdx.x] = sd[0]


@cuda.jit
def warp(x, out, n):
    # v3: son adimlar warp icinde shuffle (senkron yok)
    ws = cuda.shared.array(8, float32)  # TPB // 32 = 8 warp
    tid = cuda.threadIdx.x
    i = cuda.blockIdx.x * TPB + tid
    v = float32(0)
    if i < n:
        v = x[i]
    off = 16
    while off > 0:
        v += cuda.shfl_down_sync(0xFFFFFFFF, v, off)
        off //= 2
    lane = tid & 31
    wid = tid >> 5
    if lane == 0:
        ws[wid] = v
    cuda.syncthreads()
    if wid == 0:
        v = float32(0)
        if lane < 8:
            v = ws[lane]
        off = 16
        while off > 0:
            v += cuda.shfl_down_sync(0xFFFFFFFF, v, off)
            off //= 2
        if lane == 0:
            out[cuda.blockIdx.x] = v


def indirge(cekirdek, x):
    """Bloklar halinde kismi toplam; kalan 1 olana dek tekrarla."""
    n = x.size
    buf = x
    while n > 1:
        blok = (n + TPB - 1) // TPB
        cikis = cuda.device_array(blok, dtype=np.float32)
        cekirdek[blok, TPB](buf, cikis, n)
        buf, n = cikis, blok
    return buf


def main():
    n = 1 << 24  # 16 M eleman, 64 MB
    rng = np.random.default_rng(76)
    host = rng.random(n, dtype=np.float32)
    ref = float(host.astype(np.float64).sum())
    print(f"n = {n}, referans (float64) = {ref:.3f}")
    x = cuda.to_device(host)
    tx = torch.from_numpy(host).cuda()

    rows = []
    print("varyant              ms(medyan)   bagil hata")
    for ad, k in [
        ("naif (ayrismali)", naif),
        ("sirali adresleme", sirali),
        ("warp shuffle", warp),
    ]:
        sonuc = indirge(k, x).copy_to_host()[0]
        bagil = abs(float(sonuc) - ref) / ref
        ms, _, _ = medyan_ms_numba(cuda, lambda: indirge(k, x))
        rows.append((ad, round(ms, 4), f"{bagil:.2e}"))
        print(f"{ad:<20} {ms:10.4f}   {bagil:.2e}")
    ms, _, _ = medyan_ms_torch(lambda: tx.sum())
    bagil = abs(float(tx.sum().item()) - ref) / ref
    rows.append(
        ("torch.sum (kutuphane)", round(ms, 4), f"{bagil:.2e}")
    )
    print(f"{'torch.sum':<20} {ms:10.4f}   {bagil:.2e}")
    # Karsilastirma: sirali float32 toplam (CPU), hata birikimi.
    seq = float(np.cumsum(host, dtype=np.float32)[-1])
    bagil = abs(seq - ref) / ref
    rows.append(("CPU sirali float32", "", f"{bagil:.2e}"))
    print(f"{'CPU sirali float32':<20} {'-':>10}   {bagil:.2e}")

    with open(
        os.path.join(VERI, "b76_indirgeme.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["varyant", "ms", "bagil_hata"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
