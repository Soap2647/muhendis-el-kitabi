# -*- coding: utf-8 -*-
"""Bolum 60 - SVM ve cekirdek yontemleri: sifirdan (NumPy).

Iceriik:
  pegasos_dogrusal : birincil problem, alt-gradyan (Pegasos benzeri)
  smo_basit        : basitlestirilmis SMO (dual problem, cekirdekli)
  rff_olustur, rff_donustur : rastgele Fourier oznitelikleri (RBF)
  krr_fit, krr_tahmin       : kernel ridge regresyonu (kapali form)
"""
import numpy as np


def pegasos_dogrusal(X, y, C, epoch=50, seed=0):
    """min (lam/2)|w|^2 + ortalama menteşe kaybi ; lam = 1/(C n).
    Bias (b) cezalandirilmaz. y in {-1, +1}."""
    n, d = X.shape
    lam = 1.0 / (C * n)
    R = 1.0 / np.sqrt(lam)              # Pegasos izdusum yaricapi
    rng = np.random.default_rng(seed)
    w = np.zeros(d)
    b = 0.0
    t = 0
    for _ in range(epoch):
        for i in rng.permutation(n):
            t += 1
            eta = 1.0 / (lam * t)
            aktif = y[i] * (X[i] @ w + b) < 1.0
            w = (1.0 - eta * lam) * w
            if aktif:
                w += eta * y[i] * X[i]
                b += eta * y[i]
            nrm = np.linalg.norm(w)
            if nrm > R:
                w *= R / nrm
    return w, b


def smo_basit(K, y, C, tol=1e-3, max_pas=10, seed=0):
    """Basitlestirilmis SMO (Platt 1998'in sadelestirilmis hali).
    K: n x n cekirdek (Gram) matrisi, y in {-1,+1}.
    Dondurur: alpha (n,), b."""
    n = len(y)
    alpha = np.zeros(n)
    b = 0.0
    rng = np.random.default_rng(seed)
    pas = 0
    while pas < max_pas:
        degisen = 0
        for i in range(n):
            Ei = (alpha * y) @ K[:, i] + b - y[i]
            if not ((y[i] * Ei < -tol and alpha[i] < C) or
                    (y[i] * Ei > tol and alpha[i] > 0)):
                continue
            j = i
            while j == i:
                j = rng.integers(n)
            Ej = (alpha * y) @ K[:, j] + b - y[j]
            ai, aj = alpha[i], alpha[j]
            if y[i] != y[j]:
                L, H = max(0.0, aj - ai), min(C, C + aj - ai)
            else:
                L, H = max(0.0, ai + aj - C), min(C, ai + aj)
            if L == H:
                continue
            eta = 2 * K[i, j] - K[i, i] - K[j, j]
            if eta >= 0:
                continue
            aj_yeni = np.clip(aj - y[j] * (Ei - Ej) / eta, L, H)
            if abs(aj_yeni - aj) < 1e-5:
                continue
            ai_yeni = ai + y[i] * y[j] * (aj - aj_yeni)
            b1 = (b - Ei - y[i] * (ai_yeni - ai) * K[i, i]
                  - y[j] * (aj_yeni - aj) * K[i, j])
            b2 = (b - Ej - y[i] * (ai_yeni - ai) * K[i, j]
                  - y[j] * (aj_yeni - aj) * K[j, j])
            if 0 < ai_yeni < C:
                b = b1
            elif 0 < aj_yeni < C:
                b = b2
            else:
                b = 0.5 * (b1 + b2)
            alpha[i], alpha[j] = ai_yeni, aj_yeni
            degisen += 1
        pas = pas + 1 if degisen == 0 else 0
    return alpha, b


def rff_olustur(d, D, gamma, seed=0):
    """RBF cekirdegi icin D rastgele Fourier ozniteligi."""
    rng = np.random.default_rng(seed)
    W = np.sqrt(2.0 * gamma) * rng.normal(size=(d, D))
    b = rng.uniform(0.0, 2.0 * np.pi, size=D)
    return W, b


def rff_donustur(X, W, b):
    D = W.shape[1]
    return np.sqrt(2.0 / D) * np.cos(X @ W + b)


def krr_fit(K, y, lam):
    """Kernel ridge: alpha = (K + lam I)^-1 y (kapali form)."""
    n = K.shape[0]
    return np.linalg.solve(K + lam * np.eye(n), y)


def krr_tahmin(K_test, alpha):
    """K_test: (m x n) test-egitim cekirdek matrisi."""
    return K_test @ alpha
