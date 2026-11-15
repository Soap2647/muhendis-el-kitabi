# -*- coding: utf-8 -*-
"""Bolum 74 - Politika gradyani: REINFORCE, taban cizgisi ile
varyans azaltma. CartPole (kendi fizigimiz), 5 tohum, 200 iterasyon.

Her 20 iterasyonda: ayni politika uzerinde M = 10 bagimsiz batch icin
gradyan kestiriminin parametre basina varyansi olculur.
"""

import os
import numpy as np
import torch

torch.set_num_threads(4)
import torch.nn as nn
from torch.distributions import Categorical
from ortam74 import CartPole

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
BASE = "C:/Users/merty/AppData/Local/Temp/b74"
ITER, N, M = 200, 10, 10
TOHUMLAR = [0, 1, 2, 3, 4]


def ag():
    return nn.Sequential(
        nn.Linear(4, 32), nn.Tanh(), nn.Linear(32, 2)
    )


def bolum_topla(pol, env, seed_bol):
    """Bir bolum: (log pi listesi, odul listesi)."""
    s = env.reset(seed=seed_bol)
    logps, odulalr = [], []
    bitti = kes = False
    while not (bitti or kes):
        st = torch.as_tensor(s, dtype=torch.float32)
        d = Categorical(logits=pol(st))
        a = d.sample()
        logps.append(d.log_prob(a))
        s, r, bitti, kes = env.step(int(a))
        odulalr.append(r)
    return logps, odulalr


def getiri_git(odulalr):
    G, geri = 0.0, []
    for r in reversed(odulalr):
        G = r + G  # gamma = 1 (CartPole, sonlu bolum)
        geri.append(G)
    return list(reversed(geri))


def kayip_hesapla(pol, rng, taban):
    """N bolum topla; kayip = -(1/N) sum_t log pi(a_t|s_t) (G_t - b).
    taban=True ise b, bu batch'teki tum getirilerin ortalamasidir."""
    env = CartPole(rng=rng, max_adim=200)
    tum = []
    for _ in range(N):
        lp, od = bolum_topla(pol, env, int(rng.integers(10**9)))
        tum.append((lp, getiri_git(od)))
    b = (
        float(np.mean([x for _, G in tum for x in G]))
        if taban
        else 0.0
    )
    kayip = 0.0
    for lp, G in tum:
        for lpt, Gt in zip(lp, G):
            kayip = kayip + lpt * (Gt - b)
    return -kayip / N


def batch_gradyani(pol, rng, taban):
    pol.zero_grad()
    kayip_hesapla(pol, rng, taban).backward()
    return np.concatenate(
        [p.grad.detach().numpy().ravel() for p in pol.parameters()]
    )


def varyans_olc(pol, seed, taban):
    rng = np.random.default_rng(seed)
    gs = []
    for _ in range(M):
        g = batch_gradyani(pol, rng, taban)
        gs.append(g)
    G = np.array(gs)
    return G.var(axis=0, ddof=1).mean(), np.linalg.norm(
        G.mean(axis=0)
    )


def kos(args):
    tohum, taban = args
    torch.set_num_threads(4)
    torch.manual_seed(tohum)
    pol = ag()
    opt = torch.optim.Adam(pol.parameters(), lr=1e-2)
    rng = np.random.default_rng(tohum + 99)
    kayit = []
    for it in range(ITER + 1):
        if it % 50 == 0:
            print(
                "tohum", tohum, "taban", taban, "iter", it, flush=True
            )
        if it % 20 == 0:
            v, nrm = varyans_olc(pol, 5000 + it, taban)
            kayit.append((it, v, nrm))
        if it == ITER:
            break
        # tek gradyan adimi (N bolum)
        opt.zero_grad()
        kayip_hesapla(pol, rng, taban).backward()
        opt.step()
    return tohum, taban, kayit


if __name__ == "__main__":
    import json
    import sys

    kismi = os.path.join(BASE, "pg_kismi")
    os.makedirs(kismi, exist_ok=True)
    if len(sys.argv) == 3:
        # tek kosu: python pg74.py <tohum> <taban: 0|1>
        t, b = int(sys.argv[1]), bool(int(sys.argv[2]))
        _, _, kayit = kos((t, b))
        ad = "var" if b else "yok"
        with open(
            os.path.join(kismi, "%s_%d.json" % (ad, t)),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                [[int(i), float(v), float(n)] for i, v, n in kayit], f
            )
        print("kayit yazildi:", t, b, flush=True)
    else:
        # birlestirme: 10 kismi kosunun ortalamasi
        sat = ["iter,yontem,var_ort,var_sd,grad_norm_ort"]
        for ad, kok in (("taban_yok", "yok"), ("taban_var", "var")):
            R = []
            for t in TOHUMLAR:
                with open(
                    os.path.join(kismi, "%s_%d.json" % (kok, t)),
                    encoding="utf-8",
                ) as f:
                    R.append(json.load(f))
            for i in range(len(R[0])):
                vals = np.array([r[i][1] for r in R])
                nrm = np.array([r[i][2] for r in R])
                sat.append(
                    "%d,%s,%.4e,%.4e,%.4e"
                    % (
                        R[0][i][0],
                        ad,
                        vals.mean(),
                        vals.std(ddof=1),
                        nrm.mean(),
                    )
                )
            it0 = np.mean([r[0][1] for r in R])
            it200 = np.mean([r[-1][1] for r in R])
            print(
                "%-10s varyans: it0=%.3e it200=%.3e"
                % (ad, it0, it200),
                flush=True,
            )
        os.makedirs(VERI, exist_ok=True)
        with open(
            os.path.join(VERI, "b74_pg_varyans.csv"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write("\n".join(sat) + "\n")
