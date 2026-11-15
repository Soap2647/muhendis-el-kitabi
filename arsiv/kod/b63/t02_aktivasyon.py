# -*- coding: utf-8 -*-
"""Bölüm 63.3-63.4: doğrusal olmayanlık, aktivasyonlar, ölü ReLU."""
import csv, os
import numpy as np
from sinir import VERI, ReLU, mlp, ileri_geri, SoftmaxCE, sgd_adim
from sinir import veri_yukle, mini_batch, dogruluk


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def d_sigmoid(x):
    s = sigmoid(x)
    return s * (1.0 - s)


def leaky(x, a=0.1):
    return np.where(x > 0, x, a * x)


def d_leaky(x, a=0.1):
    return np.where(x > 0, 1.0, a)


C = np.sqrt(2.0 / np.pi)


def gelu(x):                            # tanh yaklaşımı
    return 0.5 * x * (1.0 + np.tanh(C * (x + 0.044715 * x ** 3)))


def d_gelu(x):                          # yukarıdaki yaklaşımın türevi
    u = C * (x + 0.044715 * x ** 3)
    du = C * (1.0 + 3 * 0.044715 * x ** 2)
    t = np.tanh(u)
    return 0.5 * (1.0 + t) + 0.5 * x * (1.0 - t ** 2) * du


def dogrusal_cokus():
    rng = np.random.default_rng(3)
    W1 = rng.normal(size=(64, 32))
    W2 = rng.normal(size=(32, 16))
    W3 = rng.normal(size=(16, 10))
    X = rng.normal(size=(5, 64))
    cok = X @ W1 @ W2 @ W3
    tek = X @ (W1 @ W2 @ W3)
    lin = np.abs(cok - tek).max()
    relu = np.maximum(0, X @ W1) @ W2
    return lin, 64 * 32 + 32 * 16 + 16 * 10, 64 * 10, relu.shape


def olu_birim_orani(lr, epoch=5):
    (Xt, Yt, yt), (Xv, Yv, yv), (Xs, Ys, ys) = veri_yukle()
    rng = np.random.default_rng(0)
    ag = mlp([64, 64, 10], ReLU, rng, "he")
    kayip = SoftmaxCE()
    for _ in range(epoch):
        for idx in mini_batch(len(yt), 32, rng):
            ileri_geri(ag, kayip, Xt[idx], Yt[idx])
            sgd_adim(ag, lr)
    H = np.maximum(0, Xt @ ag.katmanlar[0].W + ag.katmanlar[0].b)
    olu = np.sum(H.max(axis=0) == 0)
    return olu, dogruluk(ag, Xs, ys)


if __name__ == "__main__":
    x = np.linspace(-4, 4, 401)
    satirlar = []
    for i in range(len(x)):
        satirlar.append([x[i], sigmoid(x[i]), np.tanh(x[i]),
                         max(0.0, x[i]), leaky(x[i]), gelu(x[i]),
                         d_sigmoid(x[i]), 1 - np.tanh(x[i]) ** 2,
                         float(x[i] > 0), d_leaky(x[i]),
                         d_gelu(x[i])])
    with open(os.path.join(VERI, "b63_aktivasyon.csv"), "w",
              newline="", encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(["x", "sigmoid", "tanh", "relu", "leaky", "gelu",
                     "d_sigmoid", "d_tanh", "d_relu", "d_leaky",
                     "d_gelu"])
        yz.writerows(satirlar)
    print("sigmoid'in en büyük türevi =", d_sigmoid(np.array(0.0)))
    print("GELU(1)=%.4f  GELU(-1)=%.4f  GELU(0)=%.4f"
          % (gelu(1.0), gelu(-1.0), gelu(0.0)))
    lin, p3, p1, sekil = dogrusal_cokus()
    print("Doğrusal 3 katman farkı (maks) = %.1e" % lin)
    print("Üç katmanın parametresi = %d, tek katman = %d"
          % (p3, p1))
    print("ReLU'lu iki katmanın çıktı şekli:", sekil)
    print("Ölü ReLU deneyi (64-64-10, 5 epoch, tohum 0):")
    for lr in (0.05, 0.5, 2.0):
        olu, acc = olu_birim_orani(lr)
        print("  lr=%.2f  ölü birim=%2d / 64  test doğruluğu=%.3f"
              % (lr, olu, acc))
