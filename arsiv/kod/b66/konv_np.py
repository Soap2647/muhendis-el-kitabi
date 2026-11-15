# -*- coding: utf-8 -*-
"""Bölüm 66: sıfırdan konvolüsyon katmanı (yalnızca NumPy).

Şekiller: X (N, C, H, W), ağırlık W (OC, C, K, K), sapma b (OC,).
Tüm fonksiyonlar çapraz korelasyon yapar (derin öğrenmedeki
"konvolüsyon").
"""

import numpy as np


def cikis_boyutu(H, K, S, P):
    return (H + 2 * P - K) // S + 1


def dolgu(X, P):
    return np.pad(X, ((0, 0), (0, 0), (P, P), (P, P)))


def konv_naif(X, W, b, S=1, P=1):
    """Dört iç içe döngü: en açık, en yavaş gerçekleme."""
    N, C, H, Wd = X.shape
    OC, _, K, _ = W.shape
    Xp = dolgu(X, P)
    OH, OW = cikis_boyutu(H, K, S, P), cikis_boyutu(Wd, K, S, P)
    Y = np.zeros((N, OC, OH, OW))
    for n in range(N):
        for oc in range(OC):
            for i in range(OH):
                for j in range(OW):
                    yama = Xp[
                        n, :, i * S : i * S + K, j * S : j * S + K
                    ]
                    Y[n, oc, i, j] = np.sum(yama * W[oc]) + b[oc]
    return Y


def im2col(X, K, S, P):
    """Her çıkış konumunun alıcı alanını bir satıra aç: (N*OH*OW,
    C*K*K)."""
    N, C, H, Wd = X.shape
    Xp = dolgu(X, P)
    OH, OW = cikis_boyutu(H, K, S, P), cikis_boyutu(Wd, K, S, P)
    cols = np.empty((N, C, K, K, OH, OW))
    for ki in range(K):
        for kj in range(K):
            cols[:, :, ki, kj] = Xp[
                :, :, ki : ki + S * OH : S, kj : kj + S * OW : S
            ]
    cols = cols.transpose(0, 4, 5, 1, 2, 3).reshape(
        N * OH * OW, C * K * K
    )
    return cols, OH, OW


def konv_im2col(X, W, b, S=1, P=1):
    """im2col + tek bir matris çarpımı. Dönüş: Y ve geri geçiş için
    cols."""
    N = X.shape[0]
    OC, C, K, _ = W.shape
    cols, OH, OW = im2col(X, K, S, P)
    Y = cols @ W.reshape(OC, C * K * K).T + b
    Y = Y.reshape(N, OH, OW, OC).transpose(0, 3, 1, 2)
    return Y, cols


def col2im(dcols, X_sekil, K, S, P):
    """im2col'in transpozu: örtüşen konumların gradyanlarını
    toplar."""
    N, C, H, Wd = X_sekil
    OH, OW = cikis_boyutu(H, K, S, P), cikis_boyutu(Wd, K, S, P)
    dXp = np.zeros((N, C, H + 2 * P, Wd + 2 * P))
    d = dcols.reshape(N, OH, OW, C, K, K).transpose(0, 3, 4, 5, 1, 2)
    for ki in range(K):
        for kj in range(K):
            dXp[
                :, :, ki : ki + S * OH : S, kj : kj + S * OW : S
            ] += d[:, :, ki, kj]
    return dXp[:, :, P : P + H, P : P + Wd]


def konv_geri(dY, cols, X_sekil, W, S=1, P=1):
    """dW = girdi ⋆ dY (cols üzerinden), dX = col2im(dY · W), db = Σ
    dY."""
    OC = W.shape[0]
    dYf = dY.transpose(0, 2, 3, 1).reshape(-1, OC)
    dW = (dYf.T @ cols).reshape(W.shape)
    db = dYf.sum(axis=0)
    dcols = dYf @ W.reshape(OC, -1)
    dX = col2im(dcols, X_sekil, W.shape[2], S, P)
    return dX, dW, db


def maxpool_ileri(X, K=2, S=2):
    N, C, H, Wd = X.shape
    OH, OW = (H - K) // S + 1, (Wd - K) // S + 1
    Y = np.empty((N, C, OH, OW))
    idx = np.empty((N, C, OH, OW), dtype=np.int64)
    for i in range(OH):
        for j in range(OW):
            pen = X[
                :, :, i * S : i * S + K, j * S : j * S + K
            ].reshape(N, C, K * K)
            idx[:, :, i, j] = pen.argmax(axis=2)
            Y[:, :, i, j] = pen.max(axis=2)
    return Y, idx


def maxpool_geri(dY, idx, X_sekil, K=2, S=2):
    """Gradyan yalnızca maksimumu veren konuma gider; diğerleri
    sıfır."""
    N, C = X_sekil[0], X_sekil[1]
    dX = np.zeros(X_sekil)
    nn, cc = np.meshgrid(np.arange(N), np.arange(C), indexing="ij")
    for i in range(dY.shape[2]):
        for j in range(dY.shape[3]):
            a = idx[:, :, i, j]
            dX[nn, cc, i * S + a // K, j * S + a % K] += dY[
                :, :, i, j
            ]
    return dX
