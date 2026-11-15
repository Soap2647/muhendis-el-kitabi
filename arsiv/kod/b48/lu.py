# lu.py: kismi pivotlu LU ayrisimi PA = LU ve rank
import numpy as np


def lu_pivot(A):
    U = np.array(A, dtype=float)
    n = U.shape[0]
    L = np.eye(n)
    P = np.eye(n)
    for k in range(n - 1):
        p = k + np.argmax(np.abs(U[k:, k]))
        if p != k:
            U[[k, p], :] = U[[p, k], :]
            P[[k, p], :] = P[[p, k], :]
            L[[k, p], :k] = L[[p, k], :k]
        for i in range(k + 1, n):
            L[i, k] = U[i, k] / U[k, k]
            U[i, k:] -= L[i, k] * U[k, k:]
    return P, L, U


rng = np.random.default_rng(42)
A = rng.integers(-5, 6, size=(4, 4)).astype(float)
P, L, U = lu_pivot(A)
print("PA == LU ?", np.allclose(P @ A, L @ U))
print("L (alt ucgen, birler koseguede):")
print(L)
print("rank(A) =", np.linalg.matrix_rank(A))

# ikinci satir = 2 * birinci satir
tekil = np.array([[1.0, 2.0], [2.0, 4.0]])
_, _, U2 = lu_pivot(tekil)
print("tekil matris U:")
print(U2)
print("rank =", np.linalg.matrix_rank(tekil))
