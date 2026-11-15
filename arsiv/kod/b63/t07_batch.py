# -*- coding: utf-8 -*-
"""Bölüm 63.13: batch boyutuna göre süre ve verim (CPU, NumPy)."""
import csv, os, time
import numpy as np
from sinir import (VERI, ReLU, SoftmaxCE, mlp, ileri_geri, sgd_adim,
                   veri_yukle, mini_batch)

(Xt, Yt, yt), _, _ = veri_yukle()
n = len(yt)
parametre = 64 * 128 + 128 + 128 * 64 + 64 + 64 * 10 + 10
ileri_flop = 2 * (64 * 128 + 128 * 64 + 64 * 10)   # örnek başına
print("Parametre sayısı:", parametre)
print("İleri geçiş FLOP (örnek başına, çarpma+toplama):", ileri_flop)
print("Geri geçiş yaklaşık 2x ileri: toplam ~ %d" % (3 * ileri_flop))


def epoch_suresi(B, tekrar=5):
    ss = []
    for t in range(tekrar):
        rng = np.random.default_rng(t)
        ag = mlp([64, 128, 64, 10], ReLU, rng, "he")
        k = SoftmaxCE()
        t0 = time.perf_counter()
        for idx in mini_batch(n, B, rng):
            ileri_geri(ag, k, Xt[idx], Yt[idx])
            sgd_adim(ag, 0.1)
        ss.append(time.perf_counter() - t0)
    return float(np.median(ss))


if __name__ == "__main__":
    satir = []
    print("%6s %12s %14s" % ("batch", "epoch (ms)", "örnek/saniye"))
    for B in (1, 4, 16, 32, 64, 128, 256, 1078):
        s = epoch_suresi(B, tekrar=3 if B < 16 else 5)
        print("%6d %12.1f %14.0f" % (B, 1000 * s, n / s))
        satir.append([B, 1000 * s, n / s])
    with open(os.path.join(VERI, "b63_batch.csv"), "w", newline="",
              encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(["batch", "epoch_ms", "ornek_s"])
        yz.writerows(satir)
