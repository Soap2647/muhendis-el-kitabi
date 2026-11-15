# -*- coding: utf-8 -*-
"""Bölüm 66 - t01: naif / im2col eşleşmesi, gradyan kontrolü, PyTorch
eşleşmesi."""

import time
import numpy as np
import torch
import torch.nn.functional as F
from konv_np import (
    cikis_boyutu,
    konv_naif,
    konv_im2col,
    konv_geri,
    maxpool_ileri,
    maxpool_geri,
)

rng = np.random.default_rng(66)

# 1) Çıktı boyutu formülü örnekleri
print("1) cikis = floor((H + 2P - K)/S) + 1")
for H, K, S, P in [
    (5, 3, 1, 0),
    (5, 3, 1, 1),
    (32, 3, 1, 1),
    (32, 3, 2, 1),
    (32, 5, 2, 2),
    (7, 3, 2, 0),
]:
    print(
        "   H=%2d K=%d S=%d P=%d -> %d"
        % (H, K, S, P, cikis_boyutu(H, K, S, P))
    )

# 2) Naif ve im2col aynı sonucu veriyor mu?
X = rng.normal(size=(4, 3, 9, 9))
W = rng.normal(size=(5, 3, 3, 3))
b = rng.normal(size=5)
Y1 = konv_naif(X, W, b, S=2, P=1)
Y2, _ = konv_im2col(X, W, b, S=2, P=1)
print(
    "\n2) naif ile im2col en büyük fark: %.2e"
    % np.max(np.abs(Y1 - Y2))
)

# 3) Hız: aynı işin iki gerçeklemesi (en iyi üç ölçüm)
X = rng.normal(size=(8, 16, 32, 32))
W = rng.normal(size=(32, 16, 3, 3))
b = np.zeros(32)


def zamanla(f, tekrar=3):
    en = np.inf
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f()
        en = min(en, time.perf_counter() - t0)
    return en


t_naif = zamanla(lambda: konv_naif(X, W, b, 1, 1), tekrar=1)
t_im2c = zamanla(lambda: konv_im2col(X, W, b, 1, 1))
print("\n3) Hız (N=8, C=16, 32x32, OC=32, K=3):")
print("   naif (dört iç içe döngü)                 : %.2f s" % t_naif)
print("   im2col + matris çarpımı                  : %.4f s" % t_im2c)
print("   hızlanma yaklaşık %.0f kat" % (t_naif / t_im2c))

# 4) Geri geçiş: sayısal gradyan kontrolü (float64, merkezi fark)
X = rng.normal(size=(2, 2, 5, 5))
W = rng.normal(size=(3, 2, 3, 3))
b = rng.normal(size=3)
S, P = 1, 1
Y, cols = konv_im2col(X, W, b, S, P)
G = rng.normal(size=Y.shape)  # rastgele kayıp: L = sum(G * Y)
dX, dW, db = konv_geri(G, cols, X.shape, W, S, P)


def kayip_w(Wx):
    return np.sum(G * konv_im2col(X, Wx, b, S, P)[0])


def kayip_x(Xx):
    return np.sum(G * konv_im2col(Xx, W, b, S, P)[0])


def sayisal(f, A, h=1e-6):
    g = np.zeros_like(A)
    it = np.nditer(A, flags=["multi_index"])
    for _ in it:
        i = it.multi_index
        A0 = A[i]
        A[i] = A0 + h
        f1 = f(A)
        A[i] = A0 - h
        f2 = f(A)
        A[i] = A0
        g[i] = (f1 - f2) / (2 * h)
    return g


gW = sayisal(kayip_w, W.copy())
gX = sayisal(kayip_x, X.copy())


def goreli(a, b_):
    """Norm tabanlı göreli hata: ||a-b|| / (||a|| + ||b||)."""
    return np.linalg.norm(a - b_) / (
        np.linalg.norm(a) + np.linalg.norm(b_)
    )


print("\n4) Gradyan kontrolü (norm tabanlı göreli hata):")
print("   dW: %.2e" % goreli(dW, gW))
print("   dX: %.2e" % goreli(dX, gX))
print(
    "   db: %.2e"
    % goreli(db, np.array([np.sum(G[:, c]) for c in range(3)]))
)

# 5) Max pooling geri geçişi
Xp = rng.normal(size=(2, 2, 4, 4))
Yp, idx = maxpool_ileri(Xp)
Gp = rng.normal(size=Yp.shape)
dXp = maxpool_geri(Gp, idx, Xp.shape)
gp = sayisal(lambda A: np.sum(Gp * maxpool_ileri(A)[0]), Xp.copy())
print(
    "\n5) Max pooling geri geçişi, göreli hata: %.2e"
    % goreli(dXp, gp)
)
print(
    "   sıfır olmayan gradyan sayısı (beklenen %d): %d"
    % (Yp.size, np.count_nonzero(dXp))
)

# 6) PyTorch ile aynı ağırlık, aynı girdi -> aynı çıktı ve gradyan
Xt = torch.tensor(X, dtype=torch.float64, requires_grad=True)
Wt = torch.tensor(W, dtype=torch.float64, requires_grad=True)
bt = torch.tensor(b, dtype=torch.float64, requires_grad=True)
Yt = F.conv2d(Xt, Wt, bt, stride=S, padding=P)
(Yt * torch.tensor(G)).sum().backward()
print("\n6) PyTorch eşleşmesi (float64):")
print(
    "   ileri en büyük fark : %.2e"
    % np.max(np.abs(Yt.detach().numpy() - Y))
)
print(
    "   dX farkı            : %.2e"
    % np.max(np.abs(Xt.grad.numpy() - dX))
)
print(
    "   dW farkı            : %.2e"
    % np.max(np.abs(Wt.grad.numpy() - dW))
)
print(
    "   db farkı            : %.2e"
    % np.max(np.abs(bt.grad.numpy() - db))
)
