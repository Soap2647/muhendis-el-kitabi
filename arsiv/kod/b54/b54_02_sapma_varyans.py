import numpy as np
from numpy.polynomial import Polynomial

rng = np.random.default_rng(54)
f = lambda x: np.sin(2 * np.pi * x)     # gercek fonksiyon
sigma = 0.2                              # gurultu (sigma^2 = 0.04)
xg = np.linspace(0.1, 0.9, 81)           # ic izgara: veri yogun
xk = np.linspace(0, 1, 101)              # kenar dahil izgara
R = 300                                  # 300 bagimsiz egitim seti
print("derece  bias^2   varyans   bias^2+var+sigma^2   kenar_var")
for d in (1, 3, 9):
    tahmin = np.empty((R, xg.size))
    kenar = np.empty((R, xk.size))
    for r in range(R):
        x = rng.uniform(0, 1, 30)
        y = f(x) + rng.normal(0, sigma, 30)
        p = Polynomial.fit(x, y, d)
        tahmin[r] = p(xg)
        kenar[r] = p(xk)
    ortalama = tahmin.mean(axis=0)
    bias2 = np.mean((ortalama - f(xg)) ** 2)
    var = np.mean(tahmin.var(axis=0))
    kv = np.mean(kenar.var(axis=0))
    print("%5d  %7.4f  %8.4f  %18.4f  %10.2f"
          % (d, bias2, var, bias2 + var + sigma ** 2, kv))
