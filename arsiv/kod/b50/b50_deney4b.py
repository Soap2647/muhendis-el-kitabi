# -*- coding: utf-8 -*-
# Kisitli optimizasyon: LP ve dal-sinir (tamsayi).
import numpy as np
from scipy.optimize import minimize, minimize_scalar, linprog

# ---- 6) Dogrusal programlama: max 3x+2y, kisitlar ----
c = np.array([3.0, 2.0])
A = np.array([[1.0, 1.0], [1.0, 3.0], [-1.0, 0.0], [0.0, -1.0]])
b = np.array([4.0, 6.0, 0.0, 0.0])
kose = []
for i in range(4):
    for j in range(i + 1, 4):
        M = A[[i, j]]
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        v = np.linalg.solve(M, b[[i, j]])
        if np.all(A @ v <= b + 1e-9):
            kose.append((float(round(v[0], 6)) + 0.0,
                         float(round(v[1], 6)) + 0.0, float(c @ v)))
kose = sorted(set(kose), key=lambda t: -t[2])
print("\nkose noktalar (x, y, 3x+2y):")
for t_ in kose:
    print("  ", t_)
lp = linprog(-c, A_ub=A[:2], b_ub=b[:2], bounds=[(0, None)] * 2,
             method="highs")
print("linprog: x=%s  amac=%.4f" % (np.round(lp.x, 6), -lp.fun))
dl = linprog(b[:2], A_ub=-A[:2].T, b_ub=-c, bounds=[(0, None)] * 2,
             method="highs")
print("dual: u,v=%s  dual amac=%.4f"
      % (np.round(dl.x, 6), dl.fun))

# ---- 7) Tam sayi: 0/1 sirt cantasi, dal-sinir, DP ----
def dal_sinir(w, v, cap):
    n = len(w)
    sira = sorted(range(n), key=lambda i: -v[i] / w[i])
    W = [w[i] for i in sira]
    V = [v[i] for i in sira]
    en = [0]
    dugum = [0]

    def sinir(i, kap, deg):
        s = deg
        for j in range(i, n):
            if W[j] <= kap:
                kap -= W[j]
                s += V[j]
            else:
                s += V[j] * kap / W[j]
                break
        return s

    def dfs(i, kap, deg):
        dugum[0] += 1
        if deg > en[0]:
            en[0] = deg
        if i == n or sinir(i, kap, deg) <= en[0]:
            return
        if W[i] <= kap:
            dfs(i + 1, kap - W[i], deg + V[i])
        dfs(i + 1, kap, deg)

    dfs(0, cap, 0)
    return en[0], dugum[0]


def dp(w, v, cap):
    t = [0] * (cap + 1)
    for wi, vi in zip(w, v):
        for k in range(cap, wi - 1, -1):
            t[k] = max(t[k], t[k - wi] + vi)
    return t[cap]


rng = np.random.default_rng(2)
for n in (12, 20, 30):
    w = list(rng.integers(3, 30, n))
    v = list(rng.integers(5, 60, n))
    cap = int(sum(w) // 3)
    deg, nd = dal_sinir(w, v, cap)
    print("n=%2d kapasite=%3d  B&B=%d  DP=%d  dugum=%d"
          % (n, cap, deg, dp(w, v, cap), nd))

