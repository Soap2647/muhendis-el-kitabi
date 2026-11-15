# -*- coding: utf-8 -*-
# SGD gurultusu, Newton karesel yakinsama, LM, cizgi aramasi, BFGS.
import csv
import numpy as np
from scipy.optimize import minimize, least_squares
from b50_core import rosen, rosen_g

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 2) Newton (karesel): F(x) = x^3/3 - 2x, F' = x^2-2 ----
F1 = lambda x: x ** 3 / 3 - 2 * x
g1 = lambda x: x ** 2 - 2
h1 = lambda x: 2 * x
r = np.sqrt(2)
x = 1.0
satir = []
for k in range(7):
    satir.append(("newton", k, abs(x - r)))
    x = x - g1(x) / h1(x)
x = 1.0
for k in range(60):
    satir.append(("gd", k, abs(x - r)))
    x = x - 0.1 * g1(x)
print("\nNewton hatasi (sqrt2):")
for m, k, e in satir[:7]:
    print(k, "%.3e" % e)
print("GD(eta=0.1) adim 10,30,59 hata:",
      ["%.3e" % s[2] for s in satir
       if s[0] == "gd" and s[1] in (10, 30, 59)])
with open(VERI + "b50_newton_iz.csv", "w", newline="") as f:
    w_ = csv.writer(f)
    w_.writerow(["yontem", "adim", "hata"])
    for m, k, e in satir:
        w_.writerow([m, k, "%.6e" % e])

# ---- 3) Newton, Rosenbrock (tam Hessian) ----
def ros_h(p):
    x, y_ = p
    return np.array([[2 - 400 * y_ + 1200 * x * x, -400 * x],
                     [-400 * x, 200.0]])


p = np.array([-1.2, 1.0])
for k in range(100):
    gr = rosen_g(p)
    if np.linalg.norm(gr) < 1e-10:
        break
    p = p - np.linalg.solve(ros_h(p), gr)
print("\nNewton Rosenbrock: adim=%d  x=%s  f=%.3e" % (k, p, rosen(p)))

# ---- 4) Gauss-Newton / Levenberg-Marquardt: us(t) = a e^{bt} ----
rng2 = np.random.default_rng(1)
t = np.linspace(0, 4, 30)
yd = 2.0 * np.exp(-0.7 * t) + 0.02 * rng2.standard_normal(30)


def artik(th):
    return th[0] * np.exp(th[1] * t) - yd


def jac(th):
    e = np.exp(th[1] * t)
    return np.column_stack([e, th[0] * t * e])


def lm(th, adim=50):
    th = np.asarray(th, float).copy()
    lam = 1e-3
    c = 0.5 * np.sum(artik(th) ** 2)
    for k in range(adim):
        R, J = artik(th), jac(th)
        A = J.T @ J
        dlt = -np.linalg.solve(A + lam * np.eye(2), J.T @ R)
        yeni = th + dlt
        cy = 0.5 * np.sum(artik(yeni) ** 2)
        if cy < c:
            th, c, lam = yeni, cy, lam / 3
        else:
            lam *= 2
        if np.linalg.norm(dlt) < 1e-10:
            break
    return th, c, k


th, c, k = lm([1.0, 0.0])
print("\nLM: a=%.4f b=%.4f maliyet=%.6f adim=%d"
      % (th[0], th[1], c, k))
sc = least_squares(artik, [1.0, 0.0], jac=jac, method="lm")
print("scipy lm: a=%.4f b=%.4f maliyet=%.6f nfev=%d"
      % (sc.x[0], sc.x[1], sc.cost, sc.nfev))

