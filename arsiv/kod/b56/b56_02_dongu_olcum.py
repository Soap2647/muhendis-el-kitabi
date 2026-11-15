import csv, os, time
import numpy as np

def dongu(x, a, b):
    s = 0.0
    for v in x:                    # her eleman icin Python dongusu
        t = a * v + b
        s += t * t
    return s

def vektor(x, a, b):
    t = a * x + b                  # tum dizi tek seferde
    return np.dot(t, t)

def en_iyi(f, *args, tekrar=9):
    zaman = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f(*args)
        zaman.append(time.perf_counter() - t0)
    return float(np.median(zaman))  # gurultuye dayanikli

rng = np.random.default_rng(56)
satirlar = []
print("%10s %12s %12s %8s" % ("n", "dongu (s)", "vektor (s)", "oran"))
for n in [10**3, 10**4, 10**5, 10**6]:
    x = rng.standard_normal(n)
    d_s = en_iyi(dongu, x, 2.0, 0.5)
    v_s = en_iyi(vektor, x, 2.0, 0.5)
    assert abs(dongu(x, 2.0, 0.5) - vektor(x, 2.0, 0.5)) < 1e-6 * n
    print("%10d %12.6f %12.6f %8.1f" % (n, d_s, v_s, d_s / v_s))
    satirlar.append((n, "%.6f" % d_s, "%.6f" % v_s))

yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_dongu_olcum.csv")
with open(yol, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["n", "dongu_s", "vektor_s"])
    w.writerows(satirlar)
print("csv yazildi")
