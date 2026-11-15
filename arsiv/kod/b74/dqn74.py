# -*- coding: utf-8 -*-
"""Bolum 74 - DQN, sifirdan (PyTorch 2.6.0, CPU).

Bilesenler: dairesel deneyim tamponu (replay), hedef ag (hard update),
Huber kaybi, epsilon takvimi, gradyan kirpma. Double DQN bayragi var.
Ablasyon: hedef ag yok, replay yok (tampon = batch boyutu), Double
DQN.
Ortam: kendi CartPole'umuz (ortam74.py). 5 tohum, 40000 adim.
"""

import os
import sys
import time
import numpy as np
import torch

torch.set_num_threads(4)
import torch.nn as nn
import torch.nn.functional as F
from ortam74 import CartPole

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
BASE = "C:/Users/merty/AppData/Local/Temp/b74"
ADIM = 40000
BATCH = 64
GAMMA = 0.99
LR = 5e-4
HEDEF_GUNCELLE = 250  # hedef agin guncelleme araligi (adim)
EPS_BASLA, EPS_BIT, EPS_SURE = 1.0, 0.05, 5000
BASLAMA = 500  # bu kadar gecis birikince egitime basla
DEGERLENDIR_HER = 2000
TOHUMLAR = [0, 1, 2, 3, 4]


def ag_kur():
    return nn.Sequential(
        nn.Linear(4, 128),
        nn.ReLU(),
        nn.Linear(128, 128),
        nn.ReLU(),
        nn.Linear(128, 2),
    )


class Tampon:
    """Dairesel tampon: kapasite dolunca en eski gecis uzerine
    yazilir."""

    def __init__(self, kapasite, rng):
        self.k, self.rng = kapasite, rng
        self.i, self.dolu = 0, 0
        self.s = np.zeros((kapasite, 4), np.float32)
        self.a = np.zeros(kapasite, np.int64)
        self.r = np.zeros(kapasite, np.float32)
        self.s2 = np.zeros((kapasite, 4), np.float32)
        self.d = np.zeros(kapasite, np.float32)

    def ekle(self, s, a, r, s2, d):
        j = self.i
        self.s[j], self.a[j], self.r[j] = s, a, r
        self.s2[j], self.d[j] = s2, d
        self.i = (self.i + 1) % self.k
        self.dolu = min(self.dolu + 1, self.k)

    def ornekle(self, n):
        idx = self.rng.integers(0, self.dolu, size=n)
        return (
            torch.as_tensor(self.s[idx]),
            torch.as_tensor(self.a[idx]),
            torch.as_tensor(self.r[idx]),
            torch.as_tensor(self.s2[idx]),
            torch.as_tensor(self.d[idx]),
        )


def egit_bir_adim(q, hedef, opt, tampon, double):
    s, a, r, s2, d = tampon.ornekle(BATCH)
    with torch.no_grad():
        if double:
            # secim: cevrimici ag; degerlendirme: hedef ag
            a_star = q(s2).argmax(dim=1, keepdim=True)
            q2 = hedef(s2).gather(1, a_star).squeeze(1)
        else:
            q2 = hedef(s2).max(dim=1).values
        y = r + GAMMA * (1.0 - d) * q2
    qsa = q(s).gather(1, a.unsqueeze(1)).squeeze(1)
    kayip = F.smooth_l1_loss(qsa, y)  # Huber
    opt.zero_grad()
    kayip.backward()
    nn.utils.clip_grad_norm_(q.parameters(), 10.0)
    opt.step()
    return float(kayip.item())


def degerlendir(q, adet, tohum):
    env = CartPole(rng=np.random.default_rng(tohum))
    getiriler = []
    for ep in range(adet):
        s = env.reset(seed=tohum * 1000 + ep)
        G, bitti, kesildi = 0.0, False, False
        while not (bitti or kesildi):
            with torch.no_grad():
                a = int(
                    q(
                        torch.as_tensor(s, dtype=torch.float32)
                    ).argmax()
                )
            s, r, bitti, kesildi = env.step(a)
            G += r
        getiriler.append(G)
    return float(np.mean(getiriler))


def calistir(args):
    yapi, tohum = args
    torch.set_num_threads(4)
    torch.manual_seed(tohum)
    rng = np.random.default_rng(tohum)
    env = CartPole(rng=np.random.default_rng(tohum + 77))
    q = ag_kur()
    hedef = ag_kur()
    hedef.load_state_dict(q.state_dict())
    if yapi == "hedef_yok":
        hedef = q  # ayni ag: hareketli hedef
    kapasite = BATCH if yapi == "replay_yok" else 50000
    tampon = Tampon(kapasite, rng)
    opt = torch.optim.Adam(q.parameters(), lr=LR)
    double = yapi == "double"
    s = env.reset(seed=tohum)
    egri = []
    kayiplar = []
    t0 = time.time()
    for adim in range(1, ADIM + 1):
        eps = max(
            EPS_BIT,
            EPS_BASLA - (EPS_BASLA - EPS_BIT) * adim / EPS_SURE,
        )
        if rng.random() < eps:
            a = int(rng.integers(2))
        else:
            with torch.no_grad():
                a = int(
                    q(
                        torch.as_tensor(s, dtype=torch.float32)
                    ).argmax()
                )
        s2, r, bitti, kesildi = env.step(a)
        tampon.ekle(s, a, r, s2, float(bitti))  # kesilme != bitis
        s = s2
        if bitti or kesildi:
            s = env.reset()
        if tampon.dolu >= BASLAMA:
            kayiplar.append(
                egit_bir_adim(q, hedef, opt, tampon, double)
            )
        if yapi != "hedef_yok" and adim % HEDEF_GUNCELLE == 0:
            hedef.load_state_dict(q.state_dict())
        if adim % DEGERLENDIR_HER == 0:
            egri.append((adim, degerlendir(q, 5, 500 + tohum)))
    son = degerlendir(q, 20, 900 + tohum)
    return {
        "yapi": yapi,
        "tohum": tohum,
        "egri": egri,
        "son": son,
        "sure": time.time() - t0,
    }


if __name__ == "__main__":
    import json
    import sys

    yapilar = ["tam", "hedef_yok", "replay_yok", "double"]
    kismi = os.path.join(BASE, "dqn_kismi")
    os.makedirs(kismi, exist_ok=True)
    if len(sys.argv) == 3:
        # tek kosu: python dqn74.py <yapi> <tohum>
        yapi, t = sys.argv[1], int(sys.argv[2])
        r = calistir((yapi, t))
        r["egri"] = [[int(a), float(g)] for a, g in r["egri"]]
        with open(
            os.path.join(kismi, "%s_%d.json" % (yapi, t)),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(r, f)
        print(
            "kayit yazildi:",
            yapi,
            t,
            "son=%.1f" % r["son"],
            flush=True,
        )
    else:
        # birlestirme
        sonuclar = []
        for y in yapilar:
            for t in TOHUMLAR:
                with open(
                    os.path.join(kismi, "%s_%d.json" % (y, t)),
                    encoding="utf-8",
                ) as f:
                    sonuclar.append(json.load(f))
        os.makedirs(VERI, exist_ok=True)
        satirlar = ["yapi,adim,ort,sd"]
        for y in yapilar:
            R = [z for z in sonuclar if z["yapi"] == y]
            adimlar = [a for a, _ in R[0]["egri"]]
            M = np.array([[g for _, g in z["egri"]] for z in R])
            for i, a in enumerate(adimlar):
                satirlar.append(
                    "%s,%d,%.2f,%.2f"
                    % (y, a, M[:, i].mean(), M[:, i].std(ddof=1))
                )
            son = np.array([z["son"] for z in R])
            print(
                "%-10s ort=%.1f sd=%.1f tohumlar=%s"
                % (
                    y,
                    son.mean(),
                    son.std(ddof=1),
                    np.round(son).astype(int).tolist(),
                )
            )
        with open(
            os.path.join(VERI, "b74_dqn_egri.csv"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write("\n".join(satirlar) + "\n")
        print(
            "sure (ort, sn):",
            round(np.mean([z["sure"] for z in sonuclar]), 1),
        )
