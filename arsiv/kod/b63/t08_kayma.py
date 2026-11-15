# -*- coding: utf-8 -*-
"""Bölüm 63.14: sayısal sağlamlık: taşma, log(0), ıraksama."""
import warnings
import numpy as np
from sinir import (ReLU, SoftmaxCE, mlp, ileri_geri, sgd_adim,
                   veri_yukle, mini_batch, log_softmax)

warnings.filterwarnings("ignore")


def naif_softmax(z):
    e = np.exp(z)
    return e / e.sum()


def naif_ce(p, y):
    return -np.sum(y * np.log(p))


if __name__ == "__main__":
    z = np.array([1.0, 2.0, 3.0])
    print("naif softmax (küçük z):", naif_softmax(z))
    z = np.array([1000.0, 1001.0, 999.0])
    print("naif softmax (z=1000):", naif_softmax(z))
    print("kararlı log_softmax (z=1000):",
          np.exp(log_softmax(z[None, :]))[0])
    y = np.array([1.0, 0.0])
    print("naif çapraz entropi, p=0:",
          naif_ce(np.array([0.0, 1.0]), y))
    print("kararlı kayıp, z=[-800, 800]:",
          -np.sum(y * log_softmax(np.array([[-800.0, 800.0]]))))
    (Xt, Yt, yt), _, (Xs, Ys, ys) = veri_yukle()
    print("\nÖğrenme oranı taraması (MLP 64-128-64-10, 3 epoch):")
    for lr in (0.1, 1.0, 5.0, 20.0):
        rng = np.random.default_rng(0)
        ag = mlp([64, 128, 64, 10], ReLU, rng, "he")
        k = SoftmaxCE()
        sonuc = "sorun yok"
        for ep in range(3):
            for idx in mini_batch(len(yt), 32, rng):
                L = ileri_geri(ag, k, Xt[idx], Yt[idx])
                if not np.isfinite(L):
                    sonuc = "kayıp sonlu değil"
                    break
                sgd_adim(ag, lr)
            if sonuc != "sorun yok":
                break
        wmax = max(np.abs(q.W).max() for q in ag.parametreler())
        acc = float(np.mean(ag.ileri(Xs).argmax(1) == ys))
        print("  lr=%5.1f  maks|W|=%9.2e  test acc=%.3f  %s"
              % (lr, wmax, acc, sonuc))
