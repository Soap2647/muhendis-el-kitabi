# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 1: bellek erisimi, dallanma, bant genisligi."""

import _cudaenv  # noqa: F401
import csv
import os
import numpy as np
import torch
from numba import cuda, float32, int64
from olcum import medyan_ms_numba, medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
TPB = 256  # blok basina is parcacigi


@cuda.jit
def okuma_adimli(x, out, s):
    # i. parcacik x[i*s] okur: s=1 birlesik, s>1 adimli erisim
    i = cuda.grid(1)
    if i < out.size:
        out[i] = x[i * s] * 2.0


@cuda.jit
def dallanma_ayrismali(out, n_it):
    # Ayni warp'ta parcaciklar farkli dallara gider (tek/cift).
    # Dallar dongu icerdigi icin derleyici kosulsuz koda cevirmez.
    i = cuda.grid(1)
    v = float32(i & 7)
    if (cuda.threadIdx.x & 1) == 0:
        for _ in range(n_it):
            v = v * 1.0001 + 0.5
    else:
        for _ in range(n_it):
            v = v * 0.9999 - 0.5
    out[i] = v


@cuda.jit
def dallanma_uniform(out, n_it):
    # Dal warp'a gore sabit: warp'larin yarisi A, yarisi B yapar
    i = cuda.grid(1)
    v = float32(i & 7)
    if ((cuda.threadIdx.x >> 5) & 1) == 0:
        for _ in range(n_it):
            v = v * 1.0001 + 0.5
    else:
        for _ in range(n_it):
            v = v * 0.9999 - 0.5
    out[i] = v


def main():
    props = cuda.get_current_device()
    print("GPU:", props.name.decode())
    print("Compute capability:", props.compute_capability)
    print("SM sayisi:", props.MULTIPROCESSOR_COUNT)
    print("Warp boyutu:", props.WARP_SIZE)
    print(
        "Blok basina en fazla is parcacigi:",
        props.MAX_THREADS_PER_BLOCK,
    )
    print(
        "Bellek veri yolu (genel bilgi): 192 bit, 7001 MHz, ~336 GB/s"
    )
    print()

    # --- 1) Birlesik vs adimli erisim ---
    n = 1 << 22  # 4 M eleman, 16 MB faydali veri
    filo = []
    rows = []
    print("s   ms(medyan)   faydali GB/s   cekilen GB/s")
    for s in [1, 2, 4, 8, 16, 32]:
        x = cuda.to_device(
            np.random.default_rng(76).random(n * s, dtype=np.float32)
        )
        out = cuda.device_array(n, dtype=np.float32)
        blok = (n + TPB - 1) // TPB
        ms, _, _ = medyan_ms_numba(
            cuda, lambda: okuma_adimli[blok, TPB](x, out, s)
        )
        # Faydali: n okuma + n yazma (4 B'lik elemanlar)
        faydali = 8 * n / (ms * 1e-3) / 1e9
        # Cekilen: GPU her okumada en az 32 B'lik sektor getirir; bir
        # sektorde 32/(4s) faydali eleman varsa okumalar birlesir.
        sektor_bayt = n * min(32, 4 * s) + 4 * n
        sektor = sektor_bayt / (ms * 1e-3) / 1e9
        rows.append(
            (s, round(ms, 4), round(faydali, 2), round(sektor, 2))
        )
        print(
            f"{s:<3} {ms:10.4f}   {faydali:10.2f}     {sektor:10.2f}"
        )
        del x, out
    with open(
        os.path.join(VERI, "b76_bellek_adimli.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["adim", "ms", "faydali_gbps", "cekilen_gbps"])
        w.writerows(rows)

    # --- 2) Kopya bant genisligi (cihaz-cihaz) ---
    m = 1 << 25  # 128 MB
    a = torch.rand(m, device="cuda")
    ms, _, _ = medyan_ms_torch(lambda: a.clone())
    # clone: bir okuma + bir yazma = 2 * 4m bayt
    kopya = 2 * 4 * m / (ms * 1e-3) / 1e9
    print(f"\nCihaz-cihaz kopya: {ms:.3f} ms, {kopya:.1f} GB/s")
    with open(
        os.path.join(VERI, "b76_kopya_bant.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["islem", "gbps"])
        w.writerow(["cihaz_kopya", round(kopya, 2)])

    # --- 3) Dallanma ayrismasi ---
    thr = 256
    blok = (1 << 20) // thr
    out = cuda.device_array(blok * thr, dtype=np.float32)
    t_ayris, _, _ = medyan_ms_numba(
        cuda, lambda: dallanma_ayrismali[blok, thr](out, 2000)
    )
    t_uni, _, _ = medyan_ms_numba(
        cuda, lambda: dallanma_uniform[blok, thr](out, 2000)
    )
    print(f"Dallanma ayrismali: {t_ayris:.3f} ms")
    print(f"Warp-uniform dal  : {t_uni:.3f} ms")
    print(f"Oran (ayrismali/uniform): {t_ayris / t_uni:.2f}")
    with open(
        os.path.join(VERI, "b76_dallanma.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["varyant", "ms"])
        w.writerow(["ayrismali", round(t_ayris, 4)])
        w.writerow(["warp_uniform", round(t_uni, 4)])


if __name__ == "__main__":
    main()
