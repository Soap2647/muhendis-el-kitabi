# -*- coding: utf-8 -*-
"""20 -> 8 (ReLU) -> 2 (logit) MLP, numpy ile sifirdan egitim.

Gradyan inisi: softmax capraz entropi kaybi.
Geri yayilim elle yazildi.
Tohum sabit (46). Cikti: model_f32.npz (float32 parametreler).
"""
import numpy as np
from telemetri import veri_seti, ozellik

TOHUM = 46
NIN, NH, NOUT = 20, 8, 2


def ozellik_matrisi(X):
    return np.array([ozellik(p) for p in X])


def ileri(x, W1, b1, W2, b2):
    """x: (B, 20). Doner: z1, a1, z2."""
    z1 = x @ W1.T + b1
    a1 = np.maximum(z1, 0.0)
    z2 = a1 @ W2.T + b2
    return z1, a1, z2


def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def egit(xtr, ytr, epoch=80, lr=0.1, bs=64):
    rng = np.random.default_rng(TOHUM)
    W1 = rng.normal(0, np.sqrt(2.0 / NIN), (NH, NIN))
    b1 = np.zeros(NH)
    W2 = rng.normal(0, np.sqrt(1.0 / NH), (NOUT, NH))
    b2 = np.zeros(NOUT)
    n = len(xtr)
    for ep in range(epoch):
        sira = rng.permutation(n)
        for k in range(0, n, bs):
            idx = sira[k:k + bs]
            x, y = xtr[idx], ytr[idx]
            z1, a1, z2 = ileri(x, W1, b1, W2, b2)
            p = softmax(z2)
            p[np.arange(len(y)), y] -= 1.0      # dKayip/dz2
            dz2 = p / len(y)
            dW2 = dz2.T @ a1
            db2 = dz2.sum(axis=0)
            da1 = dz2 @ W2
            dz1 = da1 * (z1 > 0)
            dW1 = dz1.T @ x
            db1 = dz1.sum(axis=0)
            W1 -= lr * dW1
            b1 -= lr * db1
            W2 -= lr * dW2
            b2 -= lr * db2
        if ep % 20 == 19 or ep == 0:
            _, _, z2 = ileri(xtr, W1, b1, W2, b2)
            olas = softmax(z2)[np.arange(n), ytr]
            kayip = -np.log(olas + 1e-12).mean()
            dog = (z2.argmax(axis=1) == ytr).mean()
            print("epoch %3d  kayip %.4f  egitim dogrulugu %.4f"
                  % (ep + 1, kayip, dog))
    return W1, b1, W2, b2


if __name__ == "__main__":
    Xtr, ytr, Xte, yte = veri_seti()
    Ftr = ozellik_matrisi(Xtr)
    Fte = ozellik_matrisi(Xte)
    mu = Ftr.mean(axis=0)
    sd = Ftr.std(axis=0) + 1e-8          # sifira bolunmeyi onler
    xtr = (Ftr - mu) / sd
    xte = (Fte - mu) / sd
    W1, b1, W2, b2 = egit(xtr, ytr)
    _, _, z2 = ileri(xte, W1, b1, W2, b2)
    dog = (z2.argmax(axis=1) == yte).mean()
    print("test dogrulugu (float64): %.4f" % dog)
    f32 = lambda a: a.astype(np.float32)
    np.savez("model_f32.npz", W1=f32(W1), b1=f32(b1), W2=f32(W2),
             b2=f32(b2), mu=f32(mu), sd=f32(sd))
    print("model_f32.npz yazildi")
