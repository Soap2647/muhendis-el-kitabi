# -*- coding: utf-8 -*-
"""Bölüm 66 - t02: NumPy ile sıfırdan CNN, load_digits üzerinde.

Mimari: Konv(1->8) ReLU Havuz Konv(8->16) ReLU Havuz Düzleştir
Doğrusal(64->10).
Veri ve bölme Bölüm 63 ile aynı: %60 eğitim, %20 doğrulama, %20 test.
"""

import csv
import os
import time
import numpy as np
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from konv_np import (
    konv_im2col,
    konv_geri,
    maxpool_ileri,
    maxpool_geri,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


class Konv:
    def __init__(self, rng, ic, oc, K=3, P=1):
        self.W = rng.normal(
            0, np.sqrt(2 / (ic * K * K)), (oc, ic, K, K)
        )
        self.b = np.zeros(oc)
        self.P = P

    def ileri(self, X):
        self.xs = X.shape
        Y, self.cols = konv_im2col(X, self.W, self.b, 1, self.P)
        return Y

    def geri(self, dY):
        dX, self.dW, self.db = konv_geri(
            dY, self.cols, self.xs, self.W, 1, self.P
        )
        return dX


class ReLU:
    def ileri(self, X):
        self.m = X > 0
        return X * self.m

    def geri(self, dY):
        return dY * self.m


class Havuz:
    def ileri(self, X):
        self.xs = X.shape
        Y, self.idx = maxpool_ileri(X)
        return Y

    def geri(self, dY):
        return maxpool_geri(dY, self.idx, self.xs)


class Duzlestir:
    def ileri(self, X):
        self.xs = X.shape
        return X.reshape(X.shape[0], -1)

    def geri(self, dY):
        return dY.reshape(self.xs)


class Dogrusal:
    def __init__(self, rng, gi, go):
        self.W = rng.normal(0, np.sqrt(2 / gi), (gi, go))
        self.b = np.zeros(go)

    def ileri(self, X):
        self.X = X
        return X @ self.W + self.b

    def geri(self, dY):
        self.dW = self.X.T @ dY
        self.db = dY.sum(axis=0)
        return dY @ self.W.T


def ag_kur(rng):
    return [
        Konv(rng, 1, 8),
        ReLU(),
        Havuz(),
        Konv(rng, 8, 16),
        ReLU(),
        Havuz(),
        Duzlestir(),
        Dogrusal(rng, 64, 10),
    ]


def ileri(ag, X):
    for k in ag:
        X = k.ileri(X)
    return X


def softmax(Z):
    E = np.exp(Z - Z.max(axis=1, keepdims=True))
    return E / E.sum(axis=1, keepdims=True)


def kayip_geri(ag, X, y):
    """Softmax + çapraz entropi; çıkış gradyanı (P - Y)/B."""
    Z = ileri(ag, X)
    P = softmax(Z)
    B = len(y)
    kayip = -np.mean(np.log(P[np.arange(B), y] + 1e-12))
    dZ = P.copy()
    dZ[np.arange(B), y] -= 1
    dZ /= B
    for k in reversed(ag):
        dZ = k.geri(dZ)
    return kayip


def adim(ag, lr):
    for k in ag:
        if hasattr(k, "W"):
            k.W -= lr * k.dW
            k.b -= lr * k.db


def kayip_sayi(ag, X, y):
    """Yalnızca kayıp değeri (geri geçiş yok); sayısal gradyan
    için."""
    P = softmax(ileri(ag, X))
    return -np.mean(np.log(P[np.arange(len(y)), y]))


def dogruluk(ag, X, y):
    return float(np.mean(ileri(ag, X).argmax(axis=1) == y))


def veri():
    X, y = load_digits(return_X_y=True)
    X = (X / 16.0).reshape(-1, 1, 8, 8)
    idx = np.arange(len(y))
    tr, gec = train_test_split(
        idx, test_size=0.4, stratify=y, random_state=0
    )
    va, te = train_test_split(
        gec, test_size=0.5, stratify=y[gec], random_state=0
    )
    return (X[tr], y[tr]), (X[va], y[va]), (X[te], y[te])


if __name__ == "__main__":
    (Xt, yt), (Xv, yv), (Xs, ys) = veri()
    print(
        "Bölme: eğitim %d, doğrulama %d, test %d"
        % (len(yt), len(yv), len(ys))
    )

    # Gradyan kontrolü: ilk konvolüsyon ağırlıkları, küçük batch,
    # float64
    rng = np.random.default_rng(0)
    ag = ag_kur(rng)
    for k in ag:
        for ad in ("W", "b"):
            if hasattr(k, ad):
                setattr(k, ad, getattr(k, ad).astype(np.float64))
    Xk, yk = Xt[:4].astype(np.float64), yt[:4]
    kayip_geri(ag, Xk, yk)  # analitik dW üretir
    k0, h = ag[0], 1e-5
    analitik = k0.dW.copy()
    sayisal = np.zeros_like(k0.W)
    for i in np.ndindex(k0.W.shape):
        w0 = k0.W[i]
        k0.W[i] = w0 + h
        f1 = kayip_sayi(ag, Xk, yk)
        k0.W[i] = w0 - h
        f2 = kayip_sayi(ag, Xk, yk)
        k0.W[i] = w0
        sayisal[i] = (f1 - f2) / (2 * h)
    gr = np.linalg.norm(analitik - sayisal) / (
        np.linalg.norm(analitik) + np.linalg.norm(sayisal)
    )
    print(
        "Gradyan kontrolü (ilk konvolüsyon, tüm ağ): göreli hata %.2e"
        % gr
    )

    # Eğitim: 5 tohum, SGD (lr=0.05, batch 32, 30 epoch)
    sonuc = []
    for tohum in range(5):
        rng = np.random.default_rng(tohum)
        ag = ag_kur(rng)
        t0 = time.perf_counter()
        en_va, en_w = -1, None
        for ep in range(30):
            p = rng.permutation(len(yt))
            for i in range(0, len(yt), 32):
                b_idx = p[i : i + 32]
                kayip_geri(ag, Xt[b_idx], yt[b_idx])
                adim(ag, 0.05)
            va = dogruluk(ag, Xv, yv)
            if va > en_va:
                en_va = va
                en_w = [
                    (k.W.copy(), k.b.copy())
                    for k in ag
                    if hasattr(k, "W")
                ]
        sure = time.perf_counter() - t0
        j = 0
        for k in ag:
            if hasattr(k, "W"):
                k.W, k.b = en_w[j]
                j += 1
        te = dogruluk(ag, Xs, ys)
        sonuc.append((tohum, en_va, te, sure / 30))
        print(
            "tohum %d: doğrulama %.3f  test %.3f  epoch süresi %.2f s"
            % (tohum, en_va, te, sure / 30)
        )
    te_ort = np.mean([s[2] for s in sonuc])
    te_sd = np.std([s[2] for s in sonuc], ddof=1)
    print(
        "CNN (NumPy) test ortalama ± sapma: %.4f ± %.4f"
        % (te_ort, te_sd)
    )

    # Taban çizgisi: lojistik regresyon (aynı veri, aynı bölme, düz 64
    # girdi)
    lr_model = LogisticRegression(max_iter=2000)
    lr_model.fit(Xt.reshape(len(yt), -1), yt)
    lr_te = lr_model.score(Xs.reshape(len(ys), -1), ys)
    print("Lojistik regresyon (taban çizgisi) test: %.4f" % lr_te)

    # Parametre sayısı
    par = 8 * 1 * 9 + 8 + 16 * 8 * 9 + 16 + 64 * 10 + 10
    print("NumPy CNN parametre sayısı: %d" % par)

    os.makedirs(VERI, exist_ok=True)
    with open(
        os.path.join(VERI, "b66_numpy_cnn.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["tohum", "dogrulama", "test", "epoch_sure_s"])
        for s in sonuc:
            w.writerow(
                [s[0], "%.4f" % s[1], "%.4f" % s[2], "%.3f" % s[3]]
            )
        w.writerow(["lojistik", "", "%.4f" % lr_te, ""])
