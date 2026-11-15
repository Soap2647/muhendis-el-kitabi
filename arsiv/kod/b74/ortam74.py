# -*- coding: utf-8 -*-
"""Bolum 74 - Ortamlar (sifirdan). Gymnasium kullanilmaz.

Icerik: GridWorld (kayganlik ve ruzgar), ucurum yuruyusu, Bernoulli
haydut, CartPole (Barto, Sutton, Anderson 1983 denklemleri, Euler),
1B IHA irtifa tutma (ivme, surukleme, ruzgar bozucusu, itki siniri).
"""

import math
import numpy as np

HAREKETLER = [
    (-1, 0),
    (0, 1),
    (1, 0),
    (0, -1),
]  # yukari sag asagi sol


class GridWorld:
    """Durum s = r*W + c. Ruzgar: sutun basina yukari kaydirma.
    Kayganlik: slip olasiligiyla eylem rastgele bir eylemle degisir.
    Her adim odulu -1; hedef mutlak (absorbing), hedefte odul 0."""

    def __init__(
        self, H=4, W=4, start=0, goal=None, slip=0.0, wind=None
    ):
        self.H, self.W, self.S = H, W, H * W
        self.start = start
        self.goal = self.S - 1 if goal is None else goal
        self.slip = slip
        self.wind = [0] * W if wind is None else list(wind)
        self.nA = 4
        self.P = self._kur()
        self.rng = np.random.default_rng(0)
        self.s = self.start

    def _adim(self, s, b):
        r, c = divmod(s, self.W)
        dr, dc = HAREKETLER[b]
        r = min(max(r + dr, 0), self.H - 1)
        c = min(max(c + dc, 0), self.W - 1)
        r = max(r - self.wind[c], 0)  # ruzgar yukari iter
        return r * self.W + c

    def _kur(self):
        P = {}
        for s in range(self.S):
            for a in range(self.nA):
                if s == self.goal:
                    P[(s, a)] = [(1.0, s, 0.0, True)]
                    continue
                sonuc = {}
                for b in range(self.nA):
                    p = (1 - self.slip) * (
                        b == a
                    ) + self.slip / self.nA
                    if p == 0:
                        continue
                    s2 = self._adim(s, b)
                    sonuc[s2] = sonuc.get(s2, 0.0) + p
                P[(s, a)] = [
                    (
                        p,
                        s2,
                        0.0 if s2 == self.goal else -1.0,
                        s2 == self.goal,
                    )
                    for s2, p in sonuc.items()
                ]
        return P

    def reset(self, seed=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.s = self.start
        return self.s

    def step(self, a):
        """Ornekleme: P'den bir sonuc cek."""
        olas = self.P[(self.s, a)]
        idx = self.rng.choice(len(olas), p=[o[0] for o in olas])
        _, s2, r, done = olas[idx]
        self.s = s2
        return s2, r, done


class UcurumYuruyusu:
    """4x12 ucurum yuruyusu (Sutton & Barto, genel bilgi). Baslangic
    sol alt,
    hedef sag alt. Alt satirdaki ara hucreler ucurum: -100 ve
    baslangica don.
    Her adim -1. Deterministik."""

    def __init__(self):
        self.H, self.W = 4, 12
        self.S = self.H * self.W
        self.start = 3 * self.W
        self.goal = 3 * self.W + 11
        self.nA = 4
        self.s = self.start

    def ucurum(self, s):
        return s >= 3 * self.W + 1 and s <= 3 * self.W + 10

    def reset(self):
        self.s = self.start
        return self.s

    def step(self, a):
        r, c = divmod(self.s, self.W)
        dr, dc = HAREKETLER[a]
        r = min(max(r + dr, 0), self.H - 1)
        c = min(max(c + dc, 0), self.W - 1)
        s2 = r * self.W + c
        if self.ucurum(s2):
            self.s = self.start
            return self.s, -100.0, False
        self.s = s2
        return s2, -1.0, s2 == self.goal


class Haydut:
    """Bernoulli cok kollu haydut. Odul 1 veya 0, olasilik p[k]."""

    def __init__(self, p, rng):
        self.p = np.asarray(p, dtype=float)
        self.rng = rng

    def cek(self, k):
        return float(self.rng.random() < self.p[k])


class CartPole:
    """Barto, Sutton, Anderson (1983) denklemleri, Euler integrasyonu.
    Gymnasium'daki CartPoleEnv ile ayni sabitler ve ayni guncelleme
    sirasi.
    Durum: [x, x_dot, theta, theta_dot]. Eylem: 0 sola, 1 saga iter.
    """

    def __init__(self, rng=None, max_adim=500):
        self.g, self.mc, self.mp = 9.8, 1.0, 0.1
        self.mt = self.mc + self.mp
        self.l = 0.5  # yarim sarkac uzunlugu
        self.mpl = self.mp * self.l
        self.F = 10.0
        self.tau = 0.02
        self.esik_t = 12 * 2 * math.pi / 360
        self.esik_x = 2.4
        self.max_adim = max_adim
        self.rng = (
            rng if rng is not None else np.random.default_rng(0)
        )
        self.durum = None
        self.adim = 0

    def ivme(self, kuvvet, th, thd):
        c, s = math.cos(th), math.sin(th)
        gecici = (kuvvet + self.mpl * thd * thd * s) / self.mt
        th_acc = (self.g * s - c * gecici) / (
            self.l * (4.0 / 3.0 - self.mp * c * c / self.mt)
        )
        x_acc = gecici - self.mpl * th_acc * c / self.mt
        return x_acc, th_acc

    def reset(self, seed=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.durum = self.rng.uniform(-0.05, 0.05, size=4)
        self.adim = 0
        return self.durum.copy()

    def step(self, a):
        x, xd, th, thd = self.durum
        kuvvet = self.F if a == 1 else -self.F
        x_acc, th_acc = self.ivme(kuvvet, th, thd)
        x = x + self.tau * xd
        xd = xd + self.tau * x_acc
        th = th + self.tau * thd
        thd = thd + self.tau * th_acc
        self.durum = np.array([x, xd, th, thd])
        self.adim += 1
        bitti = abs(x) > self.esik_x or abs(th) > self.esik_t
        kesildi = self.adim >= self.max_adim
        return self.durum.copy(), 1.0, bitti, kesildi


class IhaIrtifa:
    """1B IHA irtifa tutma (sadelestirilmis, arastirma amacli).
    Durum: h - h_ref [m], v [m/s]. Eylem: u in [-1,1], itki s=(u+1)/2.
    Dinamik (ileri Euler, dt = 0.05 s):
      a = twr*g*s/kutle - g - kd*v + w(t)
      v <- v + dt*a ; h <- h + dt*v
    w(t): ruzgar bozucusu (sinuzoidal + basamak ruzgar). Kutle,
    surukleme
    ve ruzgar genligi parametre olarak degistirilebilir (alan
    kaymasi).
    Odul: -(e^2 + 0.1 s^2); zemine dusme (h<=0): ek -100 ve bitis."""

    G = 9.81

    def __init__(
        self,
        rng=None,
        kutle=1.0,
        kd=0.3,
        twr=2.0,
        ruzgar=1.0,
        h_ref=10.0,
        T=400,
        dt=0.05,
    ):
        self.kutle, self.kd, self.twr = kutle, kd, twr
        self.ruzgar = ruzgar
        self.h_ref, self.T, self.dt = h_ref, T, dt
        self.rng = (
            rng if rng is not None else np.random.default_rng(0)
        )
        self.adim = 0

    def ruzgar_at(self, t):
        # sabit faz: test sonuclarini her kosuda ayni kilmak icin
        return self.ruzgar * (
            0.8 * math.sin(2 * math.pi * t / 8.0)
            + 0.5 * (1.0 if 6.0 <= t < 10.0 else 0.0)
        )

    def reset(self, seed=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.h = self.h_ref + self.rng.uniform(-3.0, 3.0)
        self.v = 0.0
        self.adim = 0
        return self.gozlem()

    def gozlem(self):
        return np.array([(self.h - self.h_ref) / 5.0, self.v / 2.0])

    def step(self, u):
        u = float(np.clip(u, -1.0, 1.0))
        s = (u + 1.0) / 2.0
        t = self.adim * self.dt
        a = (
            self.twr * self.G * s / self.kutle
            - self.G
            - self.kd * self.v
            + self.ruzgar_at(t)
        )
        self.v = self.v + self.dt * a
        self.h = self.h + self.dt * self.v
        self.adim += 1
        e = self.h - self.h_ref
        odul = -(e * e + 0.1 * s * s)
        yere = self.h <= 0.0
        if yere:
            odul -= 100.0
        bitti = yere or self.adim >= self.T
        return self.gozlem(), odul, yere, bitti, s
