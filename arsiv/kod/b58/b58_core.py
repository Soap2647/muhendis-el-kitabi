# -*- coding: utf-8 -*-
# b58_core.py: Bolum 58 icin sifirdan dogrusal model cekirdegi.
import numpy as np


def sigmoid(z):
    # Sayisal kararli sigmoid: ustel hep negatif bir ustle hesaplanir.
    e = np.exp(-np.abs(z))
    return np.where(z >= 0, 1.0 / (1.0 + e), e / (1.0 + e))


def ridge_fit(Z, y, alpha):
    # min ||y - Zw - b||^2 + alpha ||w||^2 ; sapma (b) cezalanmaz.
    zm, ym = Z.mean(axis=0), y.mean()
    Zc, yc = Z - zm, y - ym
    d = Z.shape[1]
    w = np.linalg.solve(Zc.T @ Zc + alpha * np.eye(d), Zc.T @ yc)
    return w, ym - zm @ w


def soft(z, g):
    # Yumusak esik (soft-thresholding): L1 proksimal operatoru
    return np.sign(z) * np.maximum(np.abs(z) - g, 0.0)


def enet_cd(Z, y, lam, rho=1.0, tol=1e-10, maks=10000):
    # Elastic net, koordinat inisi. Amac (sklearn ile ayni):
    # (1/2n)||y - Zw||^2 + lam*rho*||w||_1 + (1/2) lam (1-rho) ||w||^2
    # Z ortalanmis; her sutun (1/n)||z_j||^2 = 1 olacak sekilde.
    n, d = Z.shape
    w = np.zeros(d)
    r = y.copy()  # w = 0 iken artik = y
    for _ in range(maks):
        en_buyuk = 0.0
        for j in range(d):
            r += Z[:, j] * w[j]  # j'nin katkisini artiktan cikar
            rho_j = Z[:, j] @ r / n
            yeni = soft(rho_j, lam * rho) / (1.0 + lam * (1.0 - rho))
            r -= Z[:, j] * yeni
            en_buyuk = max(en_buyuk, abs(yeni - w[j]))
            w[j] = yeni
        if en_buyuk < tol:
            break
    return w


def lse_satir(Z):
    # log-sum-exp, satir bazinda (Bolum 51.10)
    m = Z.max(axis=1, keepdims=True)
    return m[:, 0] + np.log(np.exp(Z - m).sum(axis=1))


def softmax_kayip(theta, X, Y, lam, K):
    # theta = [W (d*K), b (K)]; L = ortalama kayip + (lam/2)||W||^2
    d = X.shape[1]
    W = theta[: d * K].reshape(d, K)
    b = theta[d * K :]
    n = X.shape[0]
    Z = X @ W + b
    lse = lse_satir(Z)
    kayip = np.mean(lse - np.sum(Y * Z, axis=1)) + 0.5 * lam * np.sum(
        W * W
    )
    P = np.exp(Z - lse[:, None])
    G = (P - Y) / n
    gW = X.T @ G + lam * W
    gb = G.sum(axis=0)
    return kayip, np.concatenate([gW.ravel(), gb])


def logistik_newton(X, y, lam=0.0, sw=None, adim=50, tol=1e-12):
    # Newton / IRLS. Kayip: ortalama (agirlikli) ikili cross-entropy
    # + (lam/2)||w||^2. Sapma cezalanmaz. Dondurulen: (w, adim_sayisi)
    n, d = X.shape
    A = np.hstack([np.ones((n, 1)), X])
    if sw is None:
        sw = np.ones(n)
    w = np.zeros(d + 1)
    R = lam * np.eye(d + 1)
    R[0, 0] = 0.0
    for k in range(adim):
        p = sigmoid(A @ w)
        g = A.T @ (sw * (p - y)) / n + R @ w
        S = sw * p * (1.0 - p)
        H = (A.T * S) @ A / n + R
        dw = np.linalg.solve(H, g)
        w = w - dw
        if np.max(np.abs(dw)) < tol:
            return w, k + 1
    return w, adim


def poisson_irls(A, y, adim=50, tol=1e-10):
    # Poisson, log baglanti, ceza yok. A'nin ilk sutunu 1.
    w = np.zeros(A.shape[1])
    w[0] = np.log(y.mean())
    for k in range(adim):
        mu = np.exp(A @ w)
        g = A.T @ (y - mu)
        H = (A.T * mu) @ A
        dw = np.linalg.solve(H, g)
        w = w + dw
        if np.max(np.abs(dw)) < tol:
            return w, k + 1
    return w, adim


def huber_kayip(w, X, y, delta):
    # Huber kaybi ve gradyani (ortalama degil, toplam)
    r = y - X @ w
    a = np.abs(r)
    rho = np.where(a <= delta, 0.5 * r * r, delta * (a - 0.5 * delta))
    psi = np.clip(r, -delta, delta)
    return rho.sum(), -(X.T @ psi)
