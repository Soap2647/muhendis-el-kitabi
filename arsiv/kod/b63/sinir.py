# -*- coding: utf-8 -*-
"""Bölüm 63: NumPy ile sıfırdan çok katmanlı algılayıcı (MLP)."""
import os
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"


class Dogrusal:
    """Z = X W + b.  Şekiller: X (B, d_in), W (d_in, d_out)."""

    def __init__(self, d_in, d_out, rng, yontem="he"):
        sd = {"he": np.sqrt(2.0 / d_in),
              "xavier": np.sqrt(2.0 / (d_in + d_out)),
              "kucuk": 0.01, "buyuk": 1.0, "sifir": 0.0}[yontem]
        self.W = rng.normal(0.0, sd, (d_in, d_out))
        self.b = np.zeros(d_out)

    def ileri(self, X):
        self.X = X
        return X @ self.W + self.b

    def geri(self, d):                  # d = dL/dZ, şekil (B, d_out)
        self.dW = self.X.T @ d          # şekil (d_in, d_out)
        self.db = d.sum(axis=0)         # şekil (d_out,)
        return d @ self.W.T             # dL/dX, şekil (B, d_in)


class ReLU:
    def ileri(self, Z):
        self.Z = Z
        return np.maximum(0.0, Z)

    def geri(self, d):                  # türev: z>0 ise 1, değilse 0
        return d * (self.Z > 0)


class Tanh:
    def ileri(self, Z):
        self.A = np.tanh(Z)
        return self.A

    def geri(self, d):                  # tanh' = 1 - tanh^2
        return d * (1.0 - self.A ** 2)


def log_softmax(Z):
    m = Z.max(axis=1, keepdims=True)    # log-sum-exp hilesi (63.14)
    return Z - m - np.log(np.exp(Z - m).sum(axis=1, keepdims=True))


class SoftmaxCE:
    """Çıkış kaybı: ileri = ortalama çapraz entropi,
    geri = dL/dZ = (P - Y) / B."""

    def ileri(self, Z, Y):              # Y: one-hot, şekil (B, K)
        lp = log_softmax(Z)
        self.P, self.Y = np.exp(lp), Y
        return -np.mean(np.sum(Y * lp, axis=1))

    def geri(self):
        return (self.P - self.Y) / self.Y.shape[0]


class Mse:
    """Regresyon kaybı: L = (1/2B) Σ ||z - y||^2."""

    def ileri(self, Z, Y):
        self.Z, self.Y = Z, Y
        return 0.5 * np.mean(np.sum((Z - Y) ** 2, axis=1))

    def geri(self):
        return (self.Z - self.Y) / self.Z.shape[0]


class Ag:
    """Katmanları sırayla bağlar. Geri geçiş ters sırada çalışır."""

    def __init__(self, katmanlar):
        self.katmanlar = katmanlar

    def ileri(self, X):
        for k in self.katmanlar:
            X = k.ileri(X)
        return X

    def geri(self, d):
        for k in reversed(self.katmanlar):
            d = k.geri(d)
        return d

    def parametreler(self):
        return [k for k in self.katmanlar if isinstance(k, Dogrusal)]


def mlp(boyutlar, aktivasyon, rng, yontem="he"):
    """boyutlar=[64,128,64,10]: Dogrusal, act, Dogrusal, act, ..."""
    L = []
    for i in range(len(boyutlar) - 1):
        L.append(Dogrusal(boyutlar[i], boyutlar[i + 1], rng, yontem))
        if i < len(boyutlar) - 2:
            L.append(aktivasyon())
    return Ag(L)


def ileri_geri(ag, kayip, X, Y):
    """Bir kayıp değeri hesaplar ve tüm gradyanları doldurur."""
    L = kayip.ileri(ag.ileri(X), Y)
    ag.geri(kayip.geri())
    return L


def sgd_adim(ag, lr, lam=0.0):
    """W <- W - lr (dW + lam W). Sapmaya (b) ceza uygulanmaz."""
    for k in ag.parametreler():
        k.W -= lr * (k.dW + lam * k.W)
        k.b -= lr * k.db


def tahmin(ag, X):
    return ag.ileri(X).argmax(axis=1)


def dogruluk(ag, X, y):
    return float(np.mean(tahmin(ag, X) == y))


def veri_yukle():
    """load_digits: 1797 örnek, 8x8. Bölme sabit: 60/20/20."""
    X, y = load_digits(return_X_y=True)
    X = X / 16.0                        # piksel 0..16 -> 0..1
    idx = np.arange(len(y))
    tr, gec = train_test_split(idx, test_size=0.4,
                               stratify=y, random_state=0)
    va, te = train_test_split(gec, test_size=0.5,
                              stratify=y[gec], random_state=0)
    Y = np.eye(10)[y]
    return ((X[tr], Y[tr], y[tr]), (X[va], Y[va], y[va]),
            (X[te], Y[te], y[te]))


def mini_batch(n, B, rng):
    """Her epoch başında karıştırılmış indeks grupları."""
    p = rng.permutation(n)
    return [p[i:i + B] for i in range(0, n, B)]
