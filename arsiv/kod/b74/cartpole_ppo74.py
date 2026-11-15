# -*- coding: utf-8 -*-
"""Bolum 74 - CartPole'da PPO (kendi fizigimiz). 5 tohum, 100000 adim.
Degerlendirme: ayri tohumlu 10 bolum, greedy (argmax) politika."""

import os
import numpy as np
import torch

torch.set_num_threads(2)  # en fazla 2 is parcacigi
from concurrent.futures import ProcessPoolExecutor
from ortam74 import CartPole
from ppo74 import ppo_egit, acgozlu_eylem

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TOHUMLAR = [0, 1, 2, 3, 4]
TOPLAM = 100000


class KartWrap:
    def __init__(self, seed):
        self.env = CartPole(
            rng=np.random.default_rng(seed), max_adim=500
        )
        self.seed = seed
        self.sayac = 0

    def reset(self):
        self.sayac += 1
        return self.env.reset(seed=self.seed * 100000 + self.sayac)

    def step_ppo(self, a):
        s2, r, bitti, kesildi = self.env.step(int(a))
        return s2, r, bitti, kesildi and not bitti


def degerlendir(pol, adet=10):
    G = []
    for ep in range(adet):
        env = CartPole(rng=np.random.default_rng(0), max_adim=500)
        s = env.reset(seed=700000 + ep)
        g, bitti, kes = 0.0, False, False
        while not (bitti or kes):
            a = acgozlu_eylem(pol, s, True)
            s, r, bitti, kes = env.step(a)
            g += r
        G.append(g)
    return float(np.mean(G))


def kos(tohum):
    torch.set_num_threads(2)
    pol, egri = ppo_egit(
        lambda sd: KartWrap(sd),
        4,
        2,
        True,
        TOPLAM,
        tohum,
        eval_fn=degerlendir,
        eval_her=10000,
    )
    return tohum, egri


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as ex:
        sonuc = list(ex.map(kos, TOHUMLAR))
    os.makedirs(VERI, exist_ok=True)
    satirlar = ["adim,ort,sd"]
    adimlar = [a for a, _ in sonuc[0][1]]
    M = np.array([[g for _, g in e] for _, e in sonuc])
    for i, a in enumerate(adimlar):
        satirlar.append(
            "%d,%.2f,%.2f" % (a, M[:, i].mean(), M[:, i].std(ddof=1))
        )
    with open(
        os.path.join(VERI, "b74_cartpole_ppo.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    son = M[:, -1]
    print("PPO CartPole son (%d adim):" % TOPLAM)
    print(
        "  ort=%.1f sd=%.1f tohumlar=%s"
        % (son.mean(), son.std(ddof=1), son.round().tolist())
    )
    print(
        "egri (ort):", np.round(M.mean(axis=0)).astype(int).tolist()
    )
