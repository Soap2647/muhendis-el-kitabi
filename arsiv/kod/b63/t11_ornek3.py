# -*- coding: utf-8 -*-
"""Bölüm 63, Örnek 3: tek örnekte geri yayılım ve doğrulama."""
import numpy as np
from sinir import Dogrusal, ReLU, SoftmaxCE, Ag, ileri_geri


def kur():
    L1 = Dogrusal(2, 2, np.random.default_rng(0), "he")
    L1.W = np.array([[1.0, -1.0], [0.5, 2.0]])
    L1.b = np.array([0.0, 0.1])
    L2 = Dogrusal(2, 2, np.random.default_rng(0), "he")
    L2.W = np.array([[0.5, -0.3], [0.2, 0.8]])
    L2.b = np.array([0.0, 0.0])
    return Ag([L1, ReLU(), L2]), L1, L2


if __name__ == "__main__":
    ag, L1, L2 = kur()
    X = np.array([[2.0, 1.0]])
    Y = np.array([[1.0, 0.0]])
    kayip = SoftmaxCE()
    L = ileri_geri(ag, kayip, X, Y)
    print("z1 =", L1.X @ L1.W + L1.b)
    print("z2 =", L2.X @ L2.W + L2.b)
    print("p  =", np.round(kayip.P[0], 5))
    print("kayip L = %.5f" % L)
    print("delta2 =", np.round(kayip.geri(), 5))
    print("dW2 =\n", np.round(L2.dW, 5))
    print("dW1 =\n", np.round(L1.dW, 5))
    print("db1 =", np.round(L1.db, 5))
    # sayısal doğrulama: dW1[0,0] ve dW2[1,1]
    eps = 1e-6
    for (L, i, j) in ((L1, 0, 0), (L2, 1, 1)):
        eski = L.W[i, j]
        L.W[i, j] = eski + eps
        lp = kayip.ileri(ag.ileri(X), Y)
        L.W[i, j] = eski - eps
        lm = kayip.ileri(ag.ileri(X), Y)
        L.W[i, j] = eski
        num = (lp - lm) / (2 * eps)
        print("sayısal=%.6f analitik=%.6f" % (num, L.dW[i, j]))
