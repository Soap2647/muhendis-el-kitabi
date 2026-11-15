# -*- coding: utf-8 -*-
"""Bölüm 69 - Dolgu ve nedensel maskeleme: gizlilik testleri."""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # bu bölümde yalnızca CPU
import numpy as np

np.set_printoptions(precision=3, suppress=True)


def softmax(z):
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def attention(Q, K, V, maske=None):
    S = Q @ K.T / np.sqrt(Q.shape[-1])
    if maske is not None:
        S = np.where(maske, S, -np.inf)
    A = softmax(S)
    return A @ V, A


def nedensel_maske(T):
    return np.tril(np.ones((T, T), dtype=bool))


def gizlilik_testi():
    print(
        "--- Nedensel maske: gelecek degisince gecmis? ---"
    )
    rng = np.random.default_rng(0)
    T, d = 6, 4
    Q, K, V = (rng.normal(size=(T, d)) for _ in range(3))
    m = nedensel_maske(T)
    print("maske (1 = gorulebilir):")
    print(m.astype(int))
    out1, A = attention(Q, K, V, m)
    K2, V2 = K.copy(), V.copy()
    K2[4:], V2[4:] = rng.normal(size=(2, d)), rng.normal(size=(2, d))
    out2, _ = attention(Q, K2, V2, m)
    print("t<4 satirlarinda fark:", np.abs(out1[:4] - out2[:4]).max())
    print(
        "t>=4 satirlarinda fark:", np.abs(out1[4:] - out2[4:]).max()
    )
    print("3. satirin agirliklari:", A[3])
    out3, _ = attention(Q, K2, V2)  # maskesiz karsilastirma
    out4, _ = attention(Q, K, V)
    print("maskesiz: t<4 fark:", np.abs(out3[:4] - out4[:4]).max())


def dolgu_testi():
    print("--- Dolgu maskesi: 2 ornek, uzunluklar 5 ve 3 ---")
    rng = np.random.default_rng(1)
    T, d = 5, 4
    uzunluk = [5, 3]
    Q = rng.normal(size=(2, T, d))
    K = rng.normal(size=(2, T, d))
    V = rng.normal(size=(2, T, d))
    for b, L in enumerate(uzunluk):
        m = np.zeros((T, T), dtype=bool)
        m[:, :L] = True  # anahtar tarafında dolguyu kapat
        K2, V2 = K.copy(), V.copy()
        K2[b, L:] = rng.normal(size=(T - L, d))
        V2[b, L:] = rng.normal(size=(T - L, d))
        o1, _ = attention(Q[b], K[b], V[b], m)
        o2, _ = attention(Q[b], K2[b], V2[b], m)
        print(
            "ornek %d: dolgu degisince cikti farki = %.1e"
            % (b, np.abs(o1 - o2).max())
        )


def nan_tuzagi():
    print("--- Tuzak: bir satirin tamamen maskelenmesi ---")
    rng = np.random.default_rng(2)
    T, d = 3, 2
    Q, K, V = (rng.normal(size=(T, d)) for _ in range(3))
    m = nedensel_maske(T)
    m[0, :] = False  # ilk sorgu hicbir anahtari gormez
    out, A = attention(Q, K, V, m)
    print("ilk satir:", A[0])
    print("NaN sayisi:", int(np.isnan(out).sum()))
    m2 = nedensel_maske(T)
    m2[0, :] = False
    S = Q @ K.T / np.sqrt(d)
    S2 = np.where(m2, S, -1e9)  # -inf yerine buyuk negatif
    print("-1e9 ile satir:", softmax(S2)[0])


if __name__ == "__main__":
    gizlilik_testi()
    dolgu_testi()
    nan_tuzagi()
