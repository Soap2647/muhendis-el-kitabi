# -*- coding: utf-8 -*-
"""Bolum 61 - Boyutun laneti ve k-means iz verisi (sekil icin)."""
import csv
import os

import numpy as np
from sklearn.datasets import make_blobs

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def boyut_laneti():
    print("A) boyutun laneti: [0,1]^d'de 500 nokta, 20 sorgu")
    satirlar = []
    for d in [1, 2, 3, 5, 10, 20, 50, 100, 500, 1000]:
        rng = np.random.default_rng(61 + d)
        X = rng.uniform(size=(500, d))
        oranlar = []
        for _ in range(20):
            q = rng.uniform(size=d)
            D = np.sqrt(((X - q) ** 2).sum(axis=1))
            oranlar.append((D.max() - D.min()) / D.min())
        o = np.mean(oranlar)
        satirlar.append((d, o))
        print("   d=%4d  (Dmaks-Dmin)/Dmin ortalama = %.4f" % (d, o))
    yol = os.path.join(VERI, "b61_boyut_laneti.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["d", "oran"])
        for d, o in satirlar:
            w.writerow([d, "%.6f" % o])
    print("   CSV yazildi")


def kmeans_iz():
    """Lloyd iterasyonlarinin her adimi (2B, 60 nokta, k=3)."""
    X, _ = make_blobs(n_samples=60, centers=3, cluster_std=1.1,
                      random_state=7)
    # kotu baslangic: en soldaki 3 nokta
    C = X[np.argsort(X[:, 0])[:3]].copy()
    yol1 = os.path.join(VERI, "b61_kmeans_iz.csv")
    yol2 = os.path.join(VERI, "b61_kmeans_merkez.csv")
    with open(yol1, "w", newline="", encoding="utf-8") as f1, \
            open(yol2, "w", newline="", encoding="utf-8") as f2:
        w1 = csv.writer(f1)
        w2 = csv.writer(f2)
        w1.writerow(["iter", "x", "y", "kume"])
        w2.writerow(["iter", "cx", "cy", "kume"])
        for it in range(10):
            d = ((X[:, None] - C[None]) ** 2).sum(axis=2)
            y = np.argmin(d, axis=1)
            for p, c in zip(X, y):
                w1.writerow([it, "%.5f" % p[0], "%.5f" % p[1],
                             int(c)])
            for j in range(3):
                w2.writerow([it, "%.5f" % C[j][0],
                             "%.5f" % C[j][1], j])
            Cn = np.array([X[y == j].mean(axis=0) for j in range(3)])
            if np.allclose(Cn, C):
                print("   iz: %d iterasyonda yakinsadi" % it)
                break
            C = Cn
        print("   iz CSV yazildi")


if __name__ == "__main__":
    boyut_laneti()
    kmeans_iz()
