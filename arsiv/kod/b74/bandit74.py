# -*- coding: utf-8 -*-
"""Bolum 74 - Cok kollu haydut: eps-acgozlu, UCB1, Thompson ornekleme.

Ortam: K=5 Bernoulli kolu, p = [0.30, 0.45, 0.55, 0.40, 0.25].
Pismanlik (pseudo-regret): R_T = sum_t (p* - p[a_t]).
5 tohum (0..4), her tohum icin T = 2000 adim.
"""

import os
import numpy as np
from ortam74 import Haydut

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
P = [0.30, 0.45, 0.55, 0.40, 0.25]
T = 2000
TOHUMLAR = [0, 1, 2, 3, 4]


def eps_acgozlu(rng, K, T, eps=0.1):
    n = np.zeros(K)
    q = np.zeros(K)
    secim = []
    env = Haydut(P, rng)
    for t in range(T):
        if rng.random() < eps:
            a = int(rng.integers(K))
        else:
            a = int(
                np.argmax(q + 1e-12 * rng.random(K))
            )  # bagli kiriklari
        r = env.cek(a)
        n[a] += 1
        q[a] += (r - q[a]) / n[a]  # ortalama guncellemesi
        secim.append(a)
    return secim


def ucb1(rng, K, T):
    n = np.zeros(K)
    q = np.zeros(K)
    secim = []
    env = Haydut(P, rng)
    for t in range(T):
        if t < K:
            a = t  # her kolu bir kez dene
        else:
            guven = np.sqrt(2 * np.log(t + 1) / n)
            a = int(np.argmax(q + guven))
        r = env.cek(a)
        n[a] += 1
        q[a] += (r - q[a]) / n[a]
        secim.append(a)
    return secim


def thompson(rng, K, T):
    """Beta(1,1) onsel; her kol icin Beta(alfa, beta) sonsal, orneklem
    al."""
    alfa = np.ones(K)
    beta = np.ones(K)
    secim = []
    env = Haydut(P, rng)
    for t in range(T):
        ornek = rng.beta(alfa, beta)
        a = int(np.argmax(ornek))
        r = env.cek(a)
        alfa[a] += r
        beta[a] += 1 - r
        secim.append(a)
    return secim


def pismanlik(secim):
    p = np.asarray(P)
    gap = p.max() - p[np.asarray(secim)]
    return np.cumsum(gap)


if __name__ == "__main__":
    yontemler = {
        "eps-acgozlu (0,1)": eps_acgozlu,
        "UCB1": ucb1,
        "Thompson": thompson,
    }
    satirlar = ["algoritma,t,ort,sd"]
    son = {}
    for ad, fn in yontemler.items():
        egriler = []
        for tohum in TOHUMLAR:
            rng = np.random.default_rng(tohum)
            egriler.append(pismanlik(fn(rng, len(P), T)))
        E = np.array(egriler)
        son[ad] = E[:, -1]
        for t in range(T):
            satirlar.append(
                "%s,%d,%.4f,%.4f"
                % (ad, t + 1, E[:, t].mean(), E[:, t].std(ddof=1))
            )
        print(
            "%-18s R_T ort=%.2f sd=%.2f"
            % (
                ad,
                E[:, -1].mean(),
                E[:, -1].std(ddof=1),
            )
        )
    os.makedirs(VERI, exist_ok=True)
    with open(
        os.path.join(VERI, "b74_bandit.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
