# -*- coding: utf-8 -*-
"""Bolum 74 - Model-serbest tablosal yontemler.

(a) Ucurum yuruyusu: SARSA (on-policy) ve Q-learning (off-policy),
eps=0.1
(b) 4x4 kayganlik 0.1 izgarada Q-learning'in DP cozumune yakinsamasi
(c) MC (ilk ziyaret) ve TD(0) tahmini, V^pi'ye karsi RMSE
5 tohum (0..4) her deneyde.
"""

import os
import numpy as np
from ortam74 import GridWorld, UcurumYuruyusu
from dp74 import deger_iterasyonu, q_hesapla, degerlendir_dogrusal

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TOHUMLAR = [0, 1, 2, 3, 4]


def eps_secim(q, eps, rng):
    if rng.random() < eps:
        return int(rng.integers(len(q)))
    enb = np.flatnonzero(q == q.max())  # esitlikte rastgele
    return int(rng.choice(enb))


def ogren(
    env,
    yontem,
    seed,
    bolum,
    gamma=1.0,
    eps=0.1,
    alfa=0.5,
    adim_siniri=1000,
    Q_yildiz=None,
    kayit_her=None,
):
    """SARSA veya Q-learning. alfa=None ise 1/n(s,a) (Robbins-
    Monro)."""
    rng = np.random.default_rng(seed)
    env.rng = np.random.default_rng(seed + 1000)
    Q = np.zeros((env.S, env.nA))
    n = np.zeros((env.S, env.nA))
    getiri, hatalar = [], []
    for ep in range(1, bolum + 1):
        s = env.reset()
        a = eps_secim(Q[s], eps, rng)
        G, adim = 0.0, 0
        while True:
            s2, r, bitti = env.step(a)
            G += r
            adim += 1
            a2 = eps_secim(Q[s2], eps, rng)
            n[s, a] += 1
            al = alfa if alfa is not None else 1.0 / n[s, a]
            if bitti:
                hedef = r
            elif yontem == "sarsa":
                hedef = r + gamma * Q[s2, a2]
            else:  # q-learning
                hedef = r + gamma * Q[s2].max()
            Q[s, a] += al * (hedef - Q[s, a])
            if bitti or adim >= adim_siniri:
                break
            s, a = s2, a2
        getiri.append(G)
        if Q_yildiz is not None and kayit_her and ep % kayit_her == 0:
            hatalar.append((ep, float(np.max(np.abs(Q - Q_yildiz)))))
    return Q, np.array(getiri), hatalar


def acgozlu_yol(Q, env, adim=40):
    """Acgozlu politikayi takip edip yolu koordinat olarak dondur."""
    s = env.reset()
    yol = [s]
    for _ in range(adim):
        a = int(np.argmax(Q[s]))
        s, _, bitti = env.step(a)
        yol.append(s)
        if bitti:
            break
    return yol


def v_stokastik(env, gamma):
    """Tek tip rastgele politika icin V^pi (kapali bicim)."""
    S = env.S
    P = np.zeros((S, S))
    R = np.zeros(S)
    for s in range(S):
        for a in range(env.nA):
            for p, s2, r, _ in env.P[(s, a)]:
                P[s, s2] += p / env.nA
                R[s] += p * r / env.nA
    return np.linalg.solve(np.eye(S) - gamma * P, R)


def mc_td_tahmin(
    env, V_hedef, seed, bolum, gamma=0.9, alfa=0.1, yontem="td"
):
    """Tek tip rastgele politika; RMSE(V, V^pi) her 'kayit'
    bolumde."""
    rng = np.random.default_rng(seed)
    env.rng = np.random.default_rng(seed + 2000)
    V = np.zeros(env.S)
    sonuc = {}
    for ep in range(1, bolum + 1):
        s = env.reset()
        yol = []
        bitti = False
        adim = 0
        while not bitti and adim < 500:
            a = int(rng.integers(env.nA))
            s2, r, bitti = env.step(a)
            adim += 1
            if yontem == "td":
                hedef = r + (0.0 if bitti else gamma * V[s2])
                V[s] += alfa * (hedef - V[s])
            else:
                yol.append((s, r))
            s = s2
        if yontem == "mc":
            # ilk ziyaret MC: geri donus getirileri, ilk gorulen yerde
            # guncelle
            geri = []
            G = 0.0
            for st, r in reversed(yol):
                G = r + gamma * G
                geri.append((st, G))
            geri.reverse()
            gorulen = set()
            for st, Gt in geri:
                if st not in gorulen:
                    gorulen.add(st)
                    V[st] += alfa * (Gt - V[st])
        if ep in (10, 100, 1000, bolum):
            sonuc[ep] = float(np.sqrt(np.mean((V - V_hedef) ** 2)))
    return sonuc


if __name__ == "__main__":
    os.makedirs(VERI, exist_ok=True)

    # (a) Ucurum yuruyusu
    satirlar = ["yontem,bolum,ort,sd"]
    yol_satir = ["yontem,r,c"]
    son_ort = {}
    for yontem in ("sarsa", "qlearn"):
        E = []
        for tohum in TOHUMLAR:
            env = UcurumYuruyusu()
            Q, G, _ = ogren(env, yontem, tohum, 500)
            E.append(G)
            if tohum == 0:
                yol = acgozlu_yol(Q, env)
                for s in yol:
                    r, c = divmod(s, env.W)
                    yol_satir.append("%s,%d,%d" % (yontem, r, c))
        E = np.array(E)
        # 10'luk kayan ortalama (her tohum icin), sonra tohum
        # ortalamasi
        kay = np.array(
            [
                np.convolve(e, np.ones(10) / 10, mode="valid")
                for e in E
            ]
        )
        for i in range(kay.shape[1]):
            satirlar.append(
                "%s,%d,%.3f,%.3f"
                % (
                    yontem,
                    i + 10,
                    kay[:, i].mean(),
                    kay[:, i].std(ddof=1),
                )
            )
        son = E[:, -100:].mean(axis=1)
        son_ort[yontem] = son
        print(
            "%-7s son100 ort=%.2f sd=%.2f"
            % (yontem, son.mean(), son.std(ddof=1))
        )
    with open(
        os.path.join(VERI, "b74_cliff_egri.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    with open(
        os.path.join(VERI, "b74_cliff_yol.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(yol_satir) + "\n")

    # (b) 4x4 kaygan izgara: Q-learning, Q* ile maksimum sapma
    env = GridWorld(4, 4, slip=0.1)
    V_star, _, _ = deger_iterasyonu(env, 0.9)
    Q_star = q_hesapla(env, V_star, 0.9)
    eg = []
    greedy_hata = []
    for tohum in TOHUMLAR:
        env = GridWorld(4, 4, slip=0.1)
        Q, _, h = ogren(
            env,
            "qlearn",
            tohum,
            20000,
            gamma=0.9,
            eps=0.2,
            alfa=None,
            Q_yildiz=Q_star,
            kayit_her=1000,
        )
        eg.append([x[1] for x in h])
        pi_g = np.argmax(Q, axis=1)
        Vg = degerlendir_dogrusal(env, pi_g, 0.9)
        greedy_hata.append(float(np.max(np.abs(Vg - V_star))))
    eg = np.array(eg)
    satirlar = ["bolum,ort,sd"]
    for i in range(eg.shape[1]):
        satirlar.append(
            "%d,%.5f,%.5f"
            % ((i + 1) * 1000, eg[:, i].mean(), eg[:, i].std(ddof=1))
        )
    with open(
        os.path.join(VERI, "b74_q_dp.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    print(
        "Q-learning max|Q-Q*|: 1000. bolum %.3f, 20000. bolum %.4f"
        % (eg[:, 0].mean(), eg[:, -1].mean())
    )
    print(
        "Greedy V - V* (max, 5 tohum):",
        np.round(greedy_hata, 4),
    )

    # (c) MC ve TD(0) tahmini (rastgele politika, gamma=0.9)
    env = GridWorld(4, 4, slip=0.1)
    V_pi = v_stokastik(env, 0.9)
    tablo = {}
    for yontem in ("mc", "td"):
        kayitlar = [
            mc_td_tahmin(
                GridWorld(4, 4, slip=0.1),
                V_pi,
                t,
                1000,
                yontem=yontem,
            )
            for t in TOHUMLAR
        ]
        for ep in (10, 100, 1000):
            vals = np.array([k[ep] for k in kayitlar])
            tablo[(yontem, ep)] = (vals.mean(), vals.std(ddof=1))
    print("RMSE(V, V^pi), 5 tohum ort (sd):")
    for ep in (10, 100, 1000):
        print(
            "  %5d bolum  MC %.3f (%.3f)   TD(0) %.3f (%.3f)"
            % (ep, *tablo[("mc", ep)], *tablo[("td", ep)])
        )
