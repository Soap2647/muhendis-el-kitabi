# -*- coding: utf-8 -*-
"""b53_blas.py - NumPy matmul: OpenBLAS is parcacigi sayisina bagli.

Calistirma: python -I b53_blas.py
Her thread sayisi icin ayri bir surec acilir; OPENBLAS_NUM_THREADS
ortam degiskeni, kutuphane yuklenmeden once ayarlanmalidir.
Cikti: engine\\veri\\b53_blas.csv (p, medyan_s, gflops, hizlanma)
"""
import csv
import os
import statistics
import subprocess
import sys

N = 2048
TEKRAR = 5


def cocuk():
    """Alt surec: matmul'i olcer, sonucun ozetini yazar."""
    import time
    import numpy as np
    rng = np.random.default_rng(53)
    a = rng.standard_normal((N, N))
    b = rng.standard_normal((N, N))
    c = a @ b                              # isinma
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        c = a @ b
        zs.append(time.perf_counter() - t0)
    print(statistics.median(zs), f"{float(np.abs(c).sum()):.12e}")


def ana():
    rows = []
    for p in (1, 2, 4, 8, 16):
        env = dict(os.environ, OPENBLAS_NUM_THREADS=str(p))
        out = subprocess.run(
            [sys.executable, "-I", __file__, "--cocuk"],
                             env=env, capture_output=True, text=True,
                             check=True).stdout.split()
        t, ozet = float(out[0]), out[1]
        rows.append((p, t, ozet))
        print(f"p={p:2d} medyan={t:.4f} s  "
              f"gflops={2*N**3/t/1e9:7.1f}  ozet={ozet}")
    t1 = rows[0][1]
    with open("b53_blas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["p", "medyan_s", "gflops", "hizlanma", "ozet"])
        for p, t, ozet in rows:
            w.writerow([p, f"{t:.6f}", f"{2*N**3/t/1e9:.2f}",
                        f"{t1/t:.3f}", ozet])
    print("CSV: b53_blas.csv")


if __name__ == "__main__":
    if "--cocuk" in sys.argv:
        cocuk()
    else:
        ana()
