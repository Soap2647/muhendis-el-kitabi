# gauss.py: Gauss eliminasyonu, kismi pivotlama ve pivotsuz felaket
import numpy as np


def gauss_coz(A, b, pivot=True):
    M = np.array(A, dtype=float)
    y = np.array(b, dtype=float)
    n = len(y)
    for k in range(n - 1):
        if pivot:                       # en buyuk |.| satiri
            p = k + np.argmax(np.abs(M[k:, k]))
            M[[k, p]] = M[[p, k]]
            y[[k, p]] = y[[p, k]]
        for i in range(k + 1, n):      # k. sutunun altini sifirla
            m = M[i, k] / M[k, k]
            M[i, k:] -= m * M[k, k:]
            y[i] -= m * y[k]
    x = np.zeros(n)                     # geri yerine koyma
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - M[i, i+1:] @ x[i+1:]) / M[i, i]
    return x


for eps in [1e-4, 1e-8, 1e-12, 1e-16, 1e-20]:
    A = [[eps, 1.0], [1.0, 1.0]]
    b = [1.0, 2.0]                      # gercek cozum: x = 1, y = 1
    x0 = gauss_coz(A, b, pivot=False)
    x1 = gauss_coz(A, b, pivot=True)
    print("eps=%-6g pivotsuz: x=%-10.6g pivotlu: x=%.6g"
          % (eps, x0[0], x1[0]))

rng = np.random.default_rng(42)
enb = 0.0
for _ in range(200):
    n = int(rng.integers(2, 8))
    A = rng.standard_normal((n, n))
    b = rng.standard_normal(n)
    fark = np.max(np.abs(gauss_coz(A, b) - np.linalg.solve(A, b)))
    enb = max(enb, fark)
print("200 rastgele sistem, en buyuk fark:", "%.2e" % enb)
