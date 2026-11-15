# fib_mat.py: Fibonacci matrisi, kopegenleme, Markov dagilimi
import numpy as np

F = np.array([[1, 1], [1, 0]], dtype=np.int64)
print("F^10 =")
print(np.linalg.matrix_power(F, 10))        # [[F11 F10], [F10 F9]]

vals, V = np.linalg.eig(F.astype(float))
print("ozdegerler:", np.round(vals, 6))
print("(1+sqrt5)/2 =", round((1 + 5 ** 0.5) / 2, 6))


def fib_kop(n):
    # F^n = V diag(lambda^n) V^-1 ; F_n = (F^n)[0, 1]
    P = V @ np.diag(vals ** n) @ np.linalg.inv(V)
    return round(P[0, 1].real)


print("kosegenlestirme F_10 =", fib_kop(10), " F_30 =", fib_kop(30))
print("matris uslu F_30   =",
      np.linalg.matrix_power(F, 30)[0, 1])

# Markov zinciri: hava durumu (1: gunes, 2: yagmur)
# P[i, j]: i'den j'ye gecis olasiligi
P = np.array([[0.9, 0.1],
              [0.5, 0.5]])
# pi P = pi  <=>  P^T pi^T = pi^T
vals_p, vecs_p = np.linalg.eig(P.T)
k = np.argmin(np.abs(vals_p - 1))
pi = np.real(vecs_p[:, k] / vecs_p[:, k].sum())
print("durağan dagilim pi =", np.round(pi, 6))
dist = np.array([1.0, 0.0])
for _ in range(50):
    dist = dist @ P
print("50 adim sonra     =", np.round(dist, 6))
