# -*- coding: utf-8 -*-
# Kisitli optimizasyon: Lagrange, KKT, projeksiyon, ceza, bariyer.
import numpy as np
from scipy.optimize import minimize, minimize_scalar, linprog

# ---- 1) Sabit cevreli dikdortgen: max xy, 2x+2y=20 ----
r = minimize(lambda p: -p[0] * p[1], [2.0, 8.0], method="SLSQP",
             constraints=[{"type": "eq",
                           "fun": lambda p: 2 * p[0] + 2 * p[1]
                           - 20}])
print("dikdortgen (SLSQP): x=%.5f y=%.5f alan=%.5f"
      % (r.x[0], r.x[1], -r.fun))
print("Lagrange analitik: x=y=5, lambda=x/2=2.5")

# ---- 2) Butce: max 3 ln x + ln y, 2x + y = 12 ----
r = minimize(lambda p: -(3 * np.log(p[0]) + np.log(p[1])), [3.0, 4.0],
             method="SLSQP",
             constraints=[{"type": "eq",
                           "fun": lambda p: 2 * p[0] + p[1] - 12}])
print("\nbutce (SLSQP): x=%.5f y=%.5f f=%.5f"
      % (r.x[0], r.x[1], -r.fun))
print("Lagrange analitik: x=4.5, y=3, lambda=1/3, f=%.5f"
      % (3 * np.log(4.5) + np.log(3)))

# ---- 3) KKT: min (x-3)^2+(y-2)^2, x+y<=4 (aktif), x+y<=6 ----
def kkt_kontrol(c, sinir):
    cons = [{"type": "ineq", "fun": lambda p: sinir - p[0] - p[1]}]
    r = minimize(lambda p: (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2,
                 [0.0, 0.0], method="SLSQP", constraints=cons)
    x, y = r.x
    grad = np.array([2 * (x - c[0]), 2 * (y - c[1])])
    g_val = sinir - x - y
    mu = max(0.0, -(grad @ np.array([1.0, 1.0])) / 2.0)
    kalan = np.round(grad + mu * np.array([1, 1]), 4) + 0.0
    print("x=(%.4f, %.4f) g=%.4f mu=%.4f"
          % (x, y, g_val, mu))
    print("  KKT kalani: %s" % kalan)


print("\nKKT aktif (sinir 4):", end=" ")
kkt_kontrol((3.0, 2.0), 4.0)
print("KKT pasif (sinir 6):", end=" ")
kkt_kontrol((3.0, 2.0), 6.0)

# ---- 4) Projeksiyonlu gradyan: kutu [0,1]^2 ----
g = lambda p: np.array([2 * (p[0] - 2), 2 * (p[1] + 1)])
p = np.array([0.5, 0.5])
for k in range(200):
    p = np.clip(p - 0.25 * g(p), 0.0, 1.0)
print("\nproj. GD kutu: x=%s  adim=200" % np.round(p, 6))

# ---- 5) Ceza ve bariyer: min x^2, x>=1 ----
print("\nCeza yontemi  rho   x(rho)      x=rho/(1+rho)   ihlal 1-x")
for rho in (1.0, 10.0, 100.0, 1000.0):
    F = lambda x, rho=rho: x * x + rho * max(0.0, 1 - x) ** 2
    s = minimize_scalar(F, bounds=(0.0, 2.0), method="bounded",
                        options={"xatol": 1e-12})
    print("            %6.0f  %.8f  %.8f   %.2e"
          % (rho, s.x, rho / (1 + rho), 1 - s.x))

print("\nBariyer       mu    x(mu)       (1+sqrt(1+2mu))/2")
for mu in (1.0, 0.1, 0.01, 0.0001):
    F = lambda x, mu=mu: x * x - mu * np.log(x - 1.0)
    s = minimize_scalar(F, bounds=(1.0 + 1e-12, 10.0),
                        method="bounded", options={"xatol": 1e-12})
    print("            %7.4f  %.8f  %.8f"
          % (mu, s.x, (1 + np.sqrt(1 + 2 * mu)) / 2))

