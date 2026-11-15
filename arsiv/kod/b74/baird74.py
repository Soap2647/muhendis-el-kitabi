# -*- coding: utf-8 -*-
"""Bolum 74 - Olumcul ucluu (deadly triad): Baird'in karsi ornegi.

Dogrusal fonksiyon yaklasimi + onyukleme (bootstrap) + politika disi
(off-policy) ogrenme birlikte kararsizlik uretebilir. Sutton & Barto
(2018), Ornek 11.1'in yapisinin sadelestirilmis gerceklemesi (genel
bilgi).
7 durum (0..5 ust, 6 alt-sag), 8 agirlik, odul 0, gamma = 0.99, alfa =
0.01.

Beklenen (sentetik, senkron) TD guncellemesi:
  theta <- theta + alfa * sum_s d(s) * rho_bek(s) * delta_s * x(s)
Iki guncelleme dagilimi:
  on-policy : d = hedef politikanin duragan dagilimi (yalnizca durum
  6)
  off-policy: d = duzgun (her durum 1/7); davranis-hedef farki burada
Ust durumlarda E_b[rho] = 1 (dashed rho=0, solid rho=7 w.p. 1/7).
"""

import numpy as np

GAMMA, ALFA = 0.99, 0.01


def ozellik(s):
    x = np.zeros(8)
    if s < 6:
        x[s] = 2.0
        x[7] = 1.0
    else:
        x[6] = 1.0
        x[7] = 2.0
    return x


def adim(th, dagilim):
    x6 = ozellik(6)
    yeni = th.copy()
    for s in range(7):
        if dagilim[s] == 0:
            continue
        xs = ozellik(s)
        delta = GAMMA * th @ x6 - th @ xs
        yeni = yeni + ALFA * dagilim[s] * delta * xs
    return yeni


if __name__ == "__main__":
    th0 = np.array([1, 1, 1, 1, 1, 1, 10, 1], dtype=float)
    on = np.array([0, 0, 0, 0, 0, 0, 1.0])
    off = np.full(7, 1 / 7)
    th_on, th_off = th0.copy(), th0.copy()
    print(
        "sweep   ||theta|| on-policy   ||theta|| off-policy (uniform)"
    )
    for k in range(1, 1001):
        th_on = adim(th_on, on)
        th_off = adim(th_off, off)
        if k in (1, 50, 100, 200, 300, 500, 1000):
            print(
                "%5d   %15.4f   %25.4e"
                % (k, np.linalg.norm(th_on), np.linalg.norm(th_off))
            )
    print("off-policy theta (1000 sweep):")
    print(np.array2string(th_off, precision=2, max_line_width=70))
