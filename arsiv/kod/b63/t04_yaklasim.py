# -*- coding: utf-8 -*-
"""Bölüm 63.5: tek gizli katmanla 1B yaklaşım (birim sayısı)."""
import csv, os
import numpy as np
from sinir import VERI, ReLU, Mse, mlp, ileri_geri, sgd_adim
from sinir import mini_batch


def hedef(x):
    return np.sin(3 * x) + 0.3 * x ** 2


def egit(h, seed, kayma, epoch=1500, lr=0.05, B=32):
    rng = np.random.default_rng(seed)
    X = rng.uniform(-2, 2, size=(400, 1))
    Y = hedef(X)
    ag = mlp([1, h, 1], ReLU, rng, "he")
    if kayma:                       # kıvrımları [-2, 2] üzerine yay
        L1 = ag.katmanlar[0]
        c = rng.uniform(-2, 2, size=h)
        L1.b = -L1.W[0] * c
    kayip = Mse()
    for _ in range(epoch):
        for idx in mini_batch(len(X), B, rng):
            ileri_geri(ag, kayip, X[idx], Y[idx])
            sgd_adim(ag, lr)
    return ag, X, Y


if __name__ == "__main__":
    xt = np.linspace(-2, 2, 1000).reshape(-1, 1)
    yt = hedef(xt)                       # gürültüsüz: kapasite ölçümü
    egri = {"x": xt[:, 0], "hedef": yt[:, 0]}
    csv_satir = []
    for kayma, ad in ((False, "sifir_sapma"), (True, "yayilmis")):
        for h in (2, 8, 32):
            rt, re, rts = [], [], []
            for seed in range(5):
                ag, X, Y = egit(h, seed, kayma)
                re.append(np.sqrt(np.mean((ag.ileri(X) - Y) ** 2)))
                tah = ag.ileri(xt)
                rt.append(np.sqrt(np.mean((tah - yt) ** 2)))
                rts.append(rt[-1])
                if seed == 0 and kayma:
                    egri["h%d" % h] = tah[:, 0]
            print("%-11s h=%2d  eğitim RMSE=%.4f  dizi RMSE=%.4f"
                  % (ad, h, np.mean(re), np.mean(rt)),
                  "+- %.4f" % np.std(rt))
            csv_satir.append([ad, h, np.mean(re), np.mean(rt),
                              np.std(rt)])
            if kayma:
                print("   tohum bazında dizi RMSE:",
                      " ".join("%.3f" % v for v in rts))
    with open(os.path.join(VERI, "b63_yaklasim_egri.csv"), "w",
              newline="", encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(list(egri.keys()))
        for i in range(len(xt)):
            yz.writerow([egri[k][i] for k in egri])
    with open(os.path.join(VERI, "b63_yaklasim_rmse.csv"), "w",
              newline="", encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(["baslatma", "gizli_birim", "egitim_rmse",
                     "test_rmse", "test_sapma"])
        yz.writerows(csv_satir)
