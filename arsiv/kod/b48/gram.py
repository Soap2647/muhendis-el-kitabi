# gram.py: Gram-Schmidt (klasik ve degistirilmis) ve QR kararliligi
import numpy as np


def cgs(A):
    Q = np.zeros(A.shape)
    for j in range(A.shape[1]):
        a = A[:, j]
        r = Q[:, :j].T @ a                 # hepsi ORIJINAL a ile
        v = a - Q[:, :j] @ r
        Q[:, j] = v / np.linalg.norm(v)
    return Q


def mgs(A):
    Q = np.array(A, dtype=float)
    for j in range(Q.shape[1]):
        Q[:, j] /= np.linalg.norm(Q[:, j])
        for k in range(j + 1, Q.shape[1]):
            Q[:, k] -= (Q[:, j] @ Q[:, k]) * Q[:, j]   # guncel v ile
    return Q


def hilbert(n):
    i = np.arange(n)
    return 1.0 / (i[:, None] + i[None, :] + 1)


def dikgenlik_kaybi(Q):
    return np.linalg.norm(Q.T @ Q - np.eye(Q.shape[1]))


print(" n  klasik_GS   degistirilmis  numpy_QR")
for n in [4, 6, 8, 10, 12]:
    A = hilbert(n)
    k1 = dikgenlik_kaybi(cgs(A))
    k2 = dikgenlik_kaybi(mgs(A))
    k3 = dikgenlik_kaybi(np.linalg.qr(A)[0])
    print("%2d  %9.2e  %12.2e  %9.2e" % (n, k1, k2, k3))
