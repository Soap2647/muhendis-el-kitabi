# -*- coding: utf-8 -*-
# SGD gurultusu, Newton karesel yakinsama, LM, cizgi aramasi, BFGS.
import csv
import numpy as np
from scipy.optimize import minimize, least_squares
from b50_core import rosen, rosen_g

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 5) Tek boyutlu arama: ikiye bolme, altin oran, Armijo ----
def bisect_turev(dF, a, b, tol=1e-8):
    cnt = 0
    while b - a > tol:
        m = 0.5 * (a + b)
        cnt += 1
        if dF(m) > 0:
            b = m
        else:
            a = m
    return 0.5 * (a + b), cnt


dF = lambda x: x ** 3 - 1.0
xb, cnt = bisect_turev(dF, 0.0, 3.0)
print("\nBisection (f'=x^3-1): x=%.8f  f' cagrisi=%d" % (xb, cnt))

G = lambda x: (x - 1.3) ** 4 + (x - 1.3) ** 2


def altin(f, a, b, tol=1e-6):
    phi = (np.sqrt(5) - 1) / 2
    c_ = b - phi * (b - a)
    d_ = a + phi * (b - a)
    fc, fd = f(c_), f(d_)
    ev = 2
    while b - a > tol:
        if fc < fd:
            b, d_, fd = d_, c_, fc
            c_ = b - phi * (b - a)
            fc = f(c_)
        else:
            a, c_, fc = c_, d_, fd
            d_ = a + phi * (b - a)
            fd = f(d_)
        ev += 1
    return 0.5 * (a + b), ev


def uclu(f, a, b, tol=1e-6):
    ev = 0
    while b - a > tol:
        m1 = a + (b - a) / 3
        m2 = b - (b - a) / 3
        ev += 2
        if f(m1) < f(m2):
            b = m2
        else:
            a = m1
    return 0.5 * (a + b), ev


xa, ea = altin(G, -2, 4)
xu, eu = uclu(G, -2, 4)
print("Altin oran: x=%.6f degerlendirme=%d" % (xa, ea))
print("Ucluk (ternary): x=%.6f degerlendirme=%d" % (xu, eu))


def armijo_gd(f, g, x0, n=5000, c=1e-4, rho=0.5):
    x = np.asarray(x0, float).copy()
    ev = 0
    for k in range(n):
        gr = g(x)
        fx = f(x)
        ev += 1
        if np.linalg.norm(gr) < 1e-8:
            break
        t = 1.0
        while True:
            ev += 1
            if f(x - t * gr) <= fx - c * t * gr @ gr:
                break
            t *= rho
        x = x - t * gr
    return x, k, ev


xa_, ka, eva = armijo_gd(rosen, rosen_g, [-1.2, 1.0])
print("\nArmijo GD (Rosenbrock): adim=%d f=%.3e f-cagrisi=%d"
      % (ka, rosen(xa_), eva))

# ---- 6) BFGS / L-BFGS-B (scipy) ----
for yontem in ("BFGS", "L-BFGS-B"):
    s = minimize(rosen, [-1.2, 1.0], jac=rosen_g, method=yontem)
    print("%-9s x=%s f=%.3e nit=%d nfev=%d"
          % (yontem, np.round(s.x, 6), s.fun, s.nit, s.nfev))

