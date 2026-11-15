# -*- coding: utf-8 -*-
"""Bolum 64 - egitim tekniklerinin NumPy ile sifirdan gerceklemesi.

Her fonksiyon kendi basina test edilebilir. PyTorch karsiliklari
test_np64.py icinde gradyan denetimi ve esleme testleriyle kontrol
edilir.
"""

import math
import numpy as np

# ---------- 1. Optimizasyon algoritmalari ----------


def sgd_momentum(theta, g, v, lr=0.01, mu=0.9):
    """Momentum: hiz v birikir, theta hizla guncellenir."""
    v = mu * v + g
    return theta - lr * v, v


def sgd_nesterov(theta, g, v, lr=0.01, mu=0.9):
    """Nesterov: once hizla ileri bak, sonra gradyan hesapla.
    Burada PyTorch'un nesterov=True bicimi kullanilir."""
    v = mu * v + g
    return theta - lr * (g + mu * v), v


def adam_adim(theta, g, m, v, t, lr=1e-3, b1=0.9, b2=0.999, eps=1e-8):
    """Bir Adam adimi. t, bu noktaya kadar yapilan adim sayisi."""
    t = t + 1
    m = b1 * m + (1 - b1) * g
    v = b2 * v + (1 - b2) * g * g
    mh = m / (1 - b1**t)  # sapma duzeltmesi
    vh = v / (1 - b2**t)
    theta = theta - lr * mh / (np.sqrt(vh) + eps)
    return theta, m, v, t


def adamw_adim(
    theta, g, m, v, t, lr=1e-3, wd=1e-2, b1=0.9, b2=0.999, eps=1e-8
):
    """AdamW: azaltma gradyana karismaz, dogrudan uygulanir."""
    theta = theta * (1 - lr * wd)
    return adam_adim(theta, g, m, v, t, lr, b1, b2, eps)


def adam_l2_adim(
    theta, g, m, v, t, lr=1e-3, wd=1e-2, b1=0.9, b2=0.999, eps=1e-8
):
    """Adam + L2: azaltma gradyana eklenir (Adam'in eski bicimi)."""
    g = g + wd * theta
    return adam_adim(theta, g, m, v, t, lr, b1, b2, eps)


# ---------- 2. Normalizasyon: BatchNorm ----------


def bn_ileri(x, gamma, beta, eps=1e-5):
    """Egitim modu: mini-batch istatistikleri kullanilir.
    x: (N, D). Doner: y, onbellek (geri gecis icin), mu, var."""
    mu = x.mean(axis=0)
    var = x.var(axis=0)  # bolen N (yanli tahmin)
    xh = (x - mu) / np.sqrt(var + eps)
    y = gamma * xh + beta
    return y, (xh, var, eps, gamma), mu, var


def bn_geri(dy, onbellek):
    """BatchNorm geri gecisi: dx, dgamma, dbeta."""
    xh, var, eps, gamma = onbellek
    n = dy.shape[0]
    dgamma = (dy * xh).sum(axis=0)
    dbeta = dy.sum(axis=0)
    dxh = dy * gamma
    inv = 1.0 / np.sqrt(var + eps)
    dx = (inv / n) * (
        n * dxh - dxh.sum(axis=0) - xh * (dxh * xh).sum(axis=0)
    )
    return dx, dgamma, dbeta


def bn_cikarim(x, gamma, beta, run_mu, run_var, eps=1e-5):
    """Degerlendirme modu: egitimde biriken hareketli ortalamalar."""
    return gamma * (x - run_mu) / np.sqrt(run_var + eps) + beta


# ---------- 3. Dropout (ters olcekli) ----------


def dropout_ileri(x, p, egitim, rng):
    """Egitimde her ogeyi 1-p olasilikla tutar, 1/(1-p) ile olceklar.
    Cikarimda hicbir sey yapmaz."""
    if not egitim or p == 0.0:
        return x, None
    maske = (rng.random(x.shape) >= p) / (1.0 - p)
    return x * maske, maske


# ---------- 4. Ogrenme orani takvimleri ----------


def lr_adim_kurali(t, lr0, gamma=0.5, adim=100):
    """Her 'adim' adimda lr'yi gamma ile carpar (basamakli)."""
    return lr0 * gamma ** (t // adim)


def lr_ustel(t, lr0, gamma=0.99):
    return lr0 * gamma**t


def lr_kosinus(t, T, lr_max, lr_min=0.0):
    """Kosinus: t=0'da lr_max, t=T'de lr_min."""
    return lr_min + 0.5 * (lr_max - lr_min) * (
        1 + math.cos(math.pi * min(t, T) / T)
    )


def lr_isinma_kosinus(t, W, T, lr_max, lr_min=0.0):
    """Once W adim dogrusal artis, sonra kosinus azalma."""
    if t < W:
        return lr_max * (t + 1) / W
    return lr_kosinus(t - W, T - W, lr_max, lr_min)


# ---------- 5. Gradyan normu kirpma ----------


def norm_kirp(gradlar, max_norm):
    """Tum gradyanlarin birlesik L2 normunu max_norm'a indirir.
    Yonu degistirmez; yalnizca boyu kisar."""
    toplam = math.sqrt(sum(float((g * g).sum()) for g in gradlar))
    if toplam > max_norm:
        s = max_norm / (toplam + 1e-6)
        gradlar = [g * s for g in gradlar]
    return gradlar, toplam
