# -*- coding: utf-8 -*-
"""Bölüm 68.2: adım sayısına göre Jacobian çarpımının normu.
h_t = tanh(W h_{t-1}); P_T = J_T ... J_1, J_t = diag(1-h_t^2) W.
Ölçüm: ||P_T||_2, 20 tohum üzerinden medyan."""
import numpy as np
from ortak import yaz_csv

H, T_MAX, TOHUM = 32, 100, 20


def kumulatif_norm(rho, tohum):
    rng = np.random.default_rng(tohum)
    G = rng.normal(0, 1, (H, H))
    yaricap = np.max(np.abs(np.linalg.eigvals(G)))
    W = G * (rho / yaricap)                     # yarıçap = rho
    h = np.tanh(rng.normal(0, 1, H))
    P = np.eye(H)
    norm = []
    for _ in range(T_MAX):
        h = np.tanh(W @ h)
        J = (1 - h ** 2)[:, None] * W
        P = J @ P
        norm.append(np.linalg.norm(P, 2))
    return np.array(norm)


rhos = (0.9, 1.0, 1.1)
tablo = {}
for rho in rhos:
    M = np.array([kumulatif_norm(rho, s) for s in range(TOHUM)])
    tablo[rho] = np.median(M, axis=0)

print("T    " + "  ".join("rho=%.1f" % r for r in rhos))
for T in (1, 2, 5, 10, 20, 50, 100):
    satir = ["%9.2e" % tablo[r][T - 1] for r in rhos]
    print("%-4d " % T + "  ".join(satir))
basl = ["T"] + ["rho_%.1f" % r for r in rhos]
yaz_csv("b68_gradyan_adim.csv", basl,
        [(T,) + tuple("%.6e" % tablo[r][T - 1] for r in rhos)
         for T in range(1, T_MAX + 1)])
