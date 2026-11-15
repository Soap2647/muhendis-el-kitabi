# konvolusyon.py - Bolum 52.4: dogrudan konvolusyon ve dogrulama
import numpy as np

def konv(x, h):
    """y[n] = sum_k x[k] * h[n-k], dogrudan tanim."""
    N, M = len(x), len(h)
    y = np.zeros(N + M - 1)
    for n in range(N + M - 1):
        for k in range(N):
            if 0 <= n - k < M:
                y[n] += x[k] * h[n - k]
    return y

x = np.array([1.0, 2.0, 3.0])
h = np.array([0.5, 0.5])
print("elle ornek y =", konv(x, h))
print("np.convolve  =", np.convolve(x, h))

rng = np.random.default_rng(52)
x = rng.standard_normal(200)
h = rng.standard_normal(31)
fark = np.max(np.abs(konv(x, h) - np.convolve(x, h)))
print("200 x 31 rastgele, max fark =", f"{fark:.2e}")

# birim durtu (delta) ile konvolusyon, sistemin kendisini verir
delta = np.array([1.0, 0.0, 0.0])
print("delta * h =", np.round(konv(delta, h[:4]), 4))
print("h[:4]     =", np.round(h[:4], 4))
