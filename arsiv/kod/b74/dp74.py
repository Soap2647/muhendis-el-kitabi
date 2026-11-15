# -*- coding: utf-8 -*-
"""Bolum 74 - Dinamik programlama: politika degerlendirme, politika
iterasyonu, deger iterasyonu ve gamma'ya gore yakinsama.

Model bilindiginde (P ve R) Bellman denklemleri dogrudan cozulur.
"""

import os
import numpy as np
from ortam74 import GridWorld

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
np.set_printoptions(precision=3, suppress=True)


def matris(env, pi):
    """Politika icin P_pi (S x S) ve beklenen anlik odul R_pi (S)."""
    S = env.S
    P = np.zeros((S, S))
    R = np.zeros(S)
    for s in range(S):
        for p, s2, r, _ in env.P[(s, pi[s])]:
            P[s, s2] += p
            R[s] += p * r
    return P, R


def degerlendir_dogrusal(env, pi, gamma):
    """V = (I - gamma P_pi)^-1 R_pi  (kapali bicim)."""
    P, R = matris(env, pi)
    return np.linalg.solve(np.eye(env.S) - gamma * P, R)


def degerlendir_yinelemeli(env, pi, gamma, esik=1e-10):
    """V_{k+1} = R_pi + gamma P_pi V_k  (sabit nokta yinelemesi)."""
    P, R = matris(env, pi)
    V = np.zeros(env.S)
    for k in range(100000):
        V_yeni = R + gamma * P @ V
        if np.max(np.abs(V_yeni - V)) < esik:
            return V_yeni, k + 1
        V = V_yeni
    return V, k


def q_hesapla(env, V, gamma):
    """Q(s,a) = sum p (r + gamma V(s'))."""
    Q = np.zeros((env.S, env.nA))
    for s in range(env.S):
        for a in range(env.nA):
            Q[s, a] = sum(
                p * (r + gamma * V[s2])
                for (p, s2, r, _) in env.P[(s, a)]
            )
    return Q


def politika_iterasyonu(env, gamma):
    pi = np.zeros(env.S, dtype=int)  # baslangic: hep yukari
    for it in range(1, 100):
        V = degerlendir_dogrusal(env, pi, gamma)
        Q = q_hesapla(env, V, gamma)
        yeni = np.argmax(Q, axis=1)
        # esitlik kiriciligi: mevcut eylem Q'da en iyiyse koru
        mevcut_iyi = Q[np.arange(env.S), pi] >= Q.max(axis=1) - 1e-12
        yeni = np.where(mevcut_iyi, pi, yeni)
        if np.array_equal(yeni, pi):
            return V, pi, it
        pi = yeni
    return V, pi, it


def deger_iterasyonu(env, gamma, esik=1e-8):
    """V_{k+1}(s) = max_a sum p (r + gamma V_k(s')). Kalinti dizisi
    doner."""
    V = np.zeros(env.S)
    kalintilar = []
    for k in range(100000):
        Q = q_hesapla(env, V, gamma)
        V_yeni = Q.max(axis=1)
        kalinti = float(np.max(np.abs(V_yeni - V)))
        kalintilar.append(kalinti)
        V = V_yeni
        if kalinti < esik:
            break
    pi = np.argmax(q_hesapla(env, V, gamma), axis=1)
    return V, pi, kalintilar


class SabitOdul:
    """Tek durum, tek eylem, odul +1, bitis yok (sonsuz donguyu
    temsil)."""

    def __init__(self):
        self.S, self.nA = 1, 1
        self.P = {(0, 0): [(1.0, 0, 1.0, False)]}


def bellman_optimallik_kalinti(env, V, gamma):
    Q = q_hesapla(env, V, gamma)
    return float(np.max(np.abs(Q.max(axis=1) - V)))


if __name__ == "__main__":
    # 1) 4x4, deterministik: en kisa yol 6 adim (son adim odulsuz),
    # V(0) kapali bicim
    env = GridWorld(4, 4, slip=0.0)
    V44, _, _ = deger_iterasyonu(env, 0.9)
    # 6 adim; son adim hedefte 0 odul verir, yani 5 terim: -1 cezasi
    kapali = -(1 - 0.9**5) / (1 - 0.9)
    print(
        "Deterministik 4x4, V(0) = %.6f, kapali bicim = %.6f"
        % (V44[0], kapali)
    )

    # 2) 5x5, kayganlik 0.1, rastgele politika: dogrusal vs yinelemeli
    env = GridWorld(5, 5, slip=0.1)
    rng = np.random.default_rng(0)
    pi_rast = rng.integers(0, 4, size=env.S)
    V_dog = degerlendir_dogrusal(env, pi_rast, 0.9)
    V_yin, k = degerlendir_yinelemeli(env, pi_rast, 0.9)
    print(
        "Dogrusal ve yinelemeli eslesme farki: %.2e (%d yineleme)"
        % (np.max(np.abs(V_dog - V_yin)), k)
    )

    # 3) Politika ve deger iterasyonu, ayni optimum
    for gamma in (0.9, 0.99):
        Vp, pip, it = politika_iterasyonu(env, gamma)
        Vv, piv, kal = deger_iterasyonu(env, gamma)
        print(
            "gamma=%.2f PI: %d it, VI: %d it"
            % (gamma, it, len(kal))
        )
        print(
            "  max|V_PI-V_VI|=%.2e Bellman=%.2e"
            % (
                np.max(np.abs(Vp - Vv)),
                bellman_optimallik_kalinti(env, Vv, gamma),
            )
        )

    # 4) Yakinsama: gamma'ya gore kalinti dizisi
    # (a) 5x5 izgara, hedef mutlak: oran gamma'dan cok kucuk olabilir
    # (b) tek durumlu, odulu +1 olan dongu: kalinti tam olarak gamma^k
    satirlar = ["senaryo,gamma,iter,kalinti"]
    for gamma in (0.5, 0.9, 0.99):
        _, _, kal = deger_iterasyonu(env, gamma, esik=1e-8)
        for i, k_ in enumerate(kal, 1):
            satirlar.append("izgara,%.2f,%d,%.6e" % (gamma, i, k_))
        w = min(10, len(kal) - 2)
        oran = np.array(kal[-w - 1 : -1]) / np.array(kal[-w - 2 : -2])
        print(
            "izgara gamma=%.2f it=%d son %d oran ort=%.4f"
            % (gamma, len(kal), w, oran.mean())
        )
    dongu = SabitOdul()
    for gamma in (0.5, 0.9, 0.99):
        _, _, kal = deger_iterasyonu(dongu, gamma, esik=1e-8)
        for i, k_ in enumerate(kal, 1):
            satirlar.append("dongu,%.2f,%d,%.6e" % (gamma, i, k_))
        oran = np.array(kal[1:]) / np.array(kal[:-1])
        print(
            "dongu gamma=%.2f it=%d oran=%s"
            % (gamma, len(kal), np.round(oran[:2], 2))
        )
    os.makedirs(VERI, exist_ok=True)
    with open(
        os.path.join(VERI, "b74_vi_gamma.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")

    # 5) Gorsel icin: optimal V ve politika (5x5, gamma=0.9)
    V, pi, _ = deger_iterasyonu(env, 0.9)
    satirlar = ["satir,sutun,V,politika"]
    for s_ in range(env.S):
        r_, c_ = divmod(s_, env.W)
        satirlar.append("%d,%d,%.5f,%d" % (r_, c_, V[s_], pi[s_]))
    with open(
        os.path.join(VERI, "b74_grid_v.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    print("V* (5x5):")
    print(V.reshape(5, 5))
