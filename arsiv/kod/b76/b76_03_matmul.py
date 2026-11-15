# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 3: matris carpimi (naif, tiled, cuBLAS)."""

import _cudaenv  # noqa: F401
import csv
import os
import numpy as np
import torch
from numba import cuda, float32
from olcum import medyan_ms_numba, medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
T = 16  # dongu (tile) boyutu


@cuda.jit
def matmul_naif(A, B, C):
    # Her iş parçacığı C[row,col] için tüm k'yı global bellekten okur
    col, row = cuda.grid(2)
    if row < C.shape[0] and col < C.shape[1]:
        acc = float32(0)
        for k in range(A.shape[1]):
            acc += A[row, k] * B[k, col]
        C[row, col] = acc


@cuda.jit
def matmul_tiled(A, B, C):
    # Her blok T x T döşemeleri paylaşımlı belleğe kopyalar; her
    # global okuma T çarpım için yeniden kullanılır.
    sA = cuda.shared.array((16, 16), float32)
    sB = cuda.shared.array((16, 16), float32)
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    row = cuda.blockIdx.y * 16 + ty
    col = cuda.blockIdx.x * 16 + tx
    acc = float32(0)
    for t in range(A.shape[1] // 16):
        sA[ty, tx] = A[row, t * 16 + tx]
        sB[ty, tx] = B[t * 16 + ty, col]
        cuda.syncthreads()
        for k in range(16):
            acc += sA[ty, k] * sB[k, tx]
        cuda.syncthreads()
    C[row, col] = acc


def main():
    torch.backends.cuda.matmul.allow_tf32 = False  # saf FP32
    n = 2048
    rng = np.random.default_rng(76)
    a = rng.standard_normal((n, n)).astype(np.float32)
    b = rng.standard_normal((n, n)).astype(np.float32)
    ref = a.astype(np.float64) @ b.astype(np.float64)
    ref_norm = np.abs(ref).max()
    flop = 2.0 * n**3
    da, db = cuda.to_device(a), cuda.to_device(b)
    dc = cuda.device_array((n, n), dtype=np.float32)
    ta, tb = torch.from_numpy(a).cuda(), torch.from_numpy(b).cuda()
    blok = (T, T)
    izgara = (n // T, n // T)

    def hata(c):
        return float(np.abs(c - ref).max() / ref_norm)

    rows = []
    print(f"N = {n}, FLOP = {flop / 1e9:.2f} GFLOP")
    print(
        "varyant          ms(medyan)   GFLOP/s   bagil max hata  AI"
    )
    for ad, k, ai in [
        ("naif", matmul_naif, 0.25),
        ("tiled (T=16)", matmul_tiled, T / 4),
    ]:
        matmul_run = lambda kk=k: kk[izgara, blok](da, db, dc)
        matmul_run()
        cuda.synchronize()
        c = dc.copy_to_host()
        ms, _, _ = medyan_ms_numba(cuda, matmul_run, tekrar=7)
        gf = flop / (ms * 1e-3) / 1e9
        e = hata(c)
        rows.append((ad, round(ms, 3), round(gf, 1), f"{e:.2e}", ai))
        print(f"{ad:<16} {ms:10.3f}   {gf:8.1f}   {e:.2e}      {ai}")
    ms, _, _ = medyan_ms_torch(
        lambda: torch.matmul(ta, tb), tekrar=10
    )
    gf = flop / (ms * 1e-3) / 1e9
    e = hata(torch.matmul(ta, tb).cpu().numpy())
    rows.append(
        (
            "torch.matmul (cuBLAS)",
            round(ms, 3),
            round(gf, 1),
            f"{e:.2e}",
            "-",
        )
    )
    print(f"{'torch.matmul':<16} {ms:10.3f}   {gf:8.1f}   {e:.2e}")

    with open(
        os.path.join(VERI, "b76_matmul.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["varyant", "ms", "gflops", "bagil_hata", "ai"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
