# -*- coding: utf-8 -*-
"""Bolum 56: el yapimi SMOTE (imbalanced-learn kurulu degil)."""
import numpy as np


def smote(X, y, rng, oran=0.5, k=5):
    """Azinlik orneklerinin k en yakin komsusu arasina yeni ornek koy.
    oran: hedef (azinlik / cogunluk) orani."""
    poz = X[y == 1]
    n_neg = int((y == 0).sum())
    n_yeni = int(oran * n_neg) - len(poz)
    if n_yeni <= 0:
        return X, y
    d = ((poz[:, None, :] - poz[None, :, :]) ** 2).sum(axis=2)
    komsu = np.argsort(d, axis=1)[:, 1:k + 1]    # 0. kendisi
    i = rng.integers(0, len(poz), n_yeni)
    j = komsu[i, rng.integers(0, k, n_yeni)]
    lam = rng.random((n_yeni, 1))
    yeni = poz[i] + lam * (poz[j] - poz[i])
    return (np.vstack([X, yeni]),
            np.concatenate([y, np.ones(n_yeni, dtype=int)]))
