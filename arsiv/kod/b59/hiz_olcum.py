# hiz_olcum.py -- naif O(n^2) ve sirali O(n log n) bolme
import time
import numpy as np
from agac import en_iyi_bolme_siniflama


def naif_en_iyi(x, y, k):
    # Her aday esik icin tum ornekleri yeniden say
    u = np.unique(x)
    en_iyi = (-np.inf, None)
    n = len(y)
    toplam = np.bincount(y, minlength=k).astype(float)
    ust = 1.0 - np.sum((toplam / n) ** 2)
    for i in range(len(u) - 1):
        t = (u[i] + u[i + 1]) / 2
        sol = x <= t
        cl = np.bincount(y[sol], minlength=k).astype(float)
        cr = np.bincount(y[~sol], minlength=k).astype(float)
        gl = 1.0 - np.sum((cl / cl.sum()) ** 2)
        gr = 1.0 - np.sum((cr / cr.sum()) ** 2)
        g = ust - (cl.sum() * gl + cr.sum() * gr) / n
        if g > en_iyi[0]:
            en_iyi = (g, t)
    return en_iyi


def esit_mi(a, b):
    if a is None or b[1] is None:
        return a is None and b[1] is None
    return (abs(a[0] - b[0]) < 1e-12
            and abs(a[1] - b[1]) < 1e-12)


rng = np.random.default_rng(59)
esles = 0
for _ in range(2000):
    n = rng.integers(2, 40)
    x = rng.integers(0, 8, n).astype(float)   # bilerek cok bag
    y = rng.integers(0, 3, n)
    a = en_iyi_bolme_siniflama(x, y, 3, "gini", 1)
    if esit_mi(a, naif_en_iyi(x, y, 3)):
        esles += 1
print("esit sonuc veren deneme: %d / 2000" % esles)
print()
for n in [500, 1000, 2000, 4000]:
    x = rng.normal(size=n)
    y = (x + rng.normal(0, 0.5, n) > 0).astype(int)
    t0 = time.perf_counter()
    en_iyi_bolme_siniflama(x, y, 2, "gini", 1)
    hizli = time.perf_counter() - t0
    t0 = time.perf_counter()
    naif_en_iyi(x, y, 2)
    naif = time.perf_counter() - t0
    print("n=%5d  hizli %.5f s  naif %.4f s  oran %4.0fx"
          % (n, hizli, naif, naif / hizli))
