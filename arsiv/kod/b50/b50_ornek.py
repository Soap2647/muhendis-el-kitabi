# -*- coding: utf-8 -*-
# Cozumlu ornekler icin izler (elle yapilanla karsilastirma).
import numpy as np

print("Ornek 1: GD, f=x^2+10y^2, eta=0.08, x0=(1,1)")
x, y, eta = 1.0, 1.0, 0.08
for k in range(6):
    f = x * x + 10 * y * y
    print("k=%d x=%.4f y=%.4f gx=%.4f gy=%.4f f=%.4f"
          % (k, x, y, 2 * x, 20 * y, f))
    x, y = x - eta * 2 * x, y - eta * 20 * y

print("\nOrnek 2: dikdortgen, 2x+2y=20 (y=10-x)")
for x in range(1, 10):
    print("x=%d y=%d alan=%d" % (x, 10 - x, x * (10 - x)))

print("\nOrnek 3: Newton sqrt2, x0=1")
r = np.sqrt(2)
x = 1.0
for k in range(6):
    e = abs(x - r)
    dig = -np.log10(e) if e > 0 else float("inf")
    print("k=%d x=%.12f hata=%.3e dogru_basamak=%.2f"
          % (k, x, e, dig))
    x = x - (x * x - 2) / (2 * x)

print("\nOrnek 4: Adam, f=(t-3)^2, t0=0, eta=0.1")
b1, b2, eta, eps = 0.9, 0.999, 0.1, 1e-8
t, m, v = 0.0, 0.0, 0.0
for k in range(1, 4):
    g = 2 * (t - 3)
    m = b1 * m + (1 - b1) * g
    v = b2 * v + (1 - b2) * g * g
    mh = m / (1 - b1 ** k)
    vh = v / (1 - b2 ** k)
    adim = eta * mh / (np.sqrt(vh) + eps)
    dz = eta * m / (np.sqrt(v) + eps)
    print("t%d g=%.5f m=%.5f v=%.6f mh=%.5f vh=%.5f"
          % (k, g, m, v, mh, vh))
    print("   duzeltmeli adim=%.6f  duzeltmesiz adim=%.6f"
          % (adim, dz))
    t = t - adim
    print("   yeni t=%.6f" % t)
