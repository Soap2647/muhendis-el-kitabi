# ornek2.py: 3x3 sistem, kismi pivotlu Gauss, adim adim
import numpy as np

A = np.array([[2.0, 1.0, -1.0],
              [-3.0, -1.0, 2.0],
              [-2.0, 1.0, 2.0]])
b = np.array([8.0, -11.0, -3.0])
n = 3
M = np.hstack([A, b[:, None]])          # artirilmis matris [A | b]


def goster(baslik):
    print(baslik)
    for satir in M:
        print("  ", "  ".join("%7.3f" % x for x in satir))


goster("baslangic [A | b]:")
for k in range(n - 1):
    p = k + int(np.argmax(np.abs(M[k:, k])))
    if p != k:
        M[[k, p]] = M[[p, k]]
        print("satir %d <-> %d (pivot %.3f)"
              % (k + 1, p + 1, M[k, k]))
    for i in range(k + 1, n):
        m = M[i, k] / M[k, k]
        M[i, k:] -= m * M[k, k:]
    goster("k=%d sonrasi:" % (k + 1))
x = np.zeros(n)
for i in range(n - 1, -1, -1):
    x[i] = (M[i, -1] - M[i, i + 1:n] @ x[i + 1:]) / M[i, i]
print("x =", np.round(x, 6))
print("numpy =", np.round(np.linalg.solve(A, b), 6))
