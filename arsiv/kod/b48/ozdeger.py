# ozdeger.py: ozdeger, guc yinelemesi, PageRank, simetrik matris
import numpy as np


def guc_yineleme(A, iters=200, seed=42):
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(A.shape[0])
    v /= np.linalg.norm(v)
    for _ in range(iters):
        w = A @ v
        lam = v @ w                       # Rayleigh bolumu
        v = w / np.linalg.norm(w)
    return lam, v


A = np.array([[2.0, 1.0], [1.0, 2.0]])
lam, v = guc_yineleme(A)
print("guc yineleme: lambda =", round(lam, 10),
      " v =", np.round(v, 6))
vals, vecs = np.linalg.eigh(A)
print("eigh        : lambda =", vals, " vektorler (sutun):")
print(np.round(vecs, 6))
print("V^T V == I ?", np.allclose(vecs.T @ vecs, np.eye(2)))

# PageRank: 4 sayfa, A -> B, A -> C, B -> C, C -> A, D -> C
# G[i, j] = 1: j'den i'ye link
G = np.array([[0, 0, 1, 0],
              [1, 0, 0, 0],
              [1, 1, 0, 1],
              [0, 0, 0, 0]], dtype=float)
# sutun-stokastik M: M[i, j] = 1/outdeg(j) (i'ye giden link)
M = np.zeros((4, 4))
for j in range(4):
    if G[:, j].sum() > 0:
        M[:, j] = G[:, j] / G[:, j].sum()
d, n = 0.85, 4
Gg = d * M + (1 - d) / n * np.ones((4, 4))
x = np.full(n, 1 / n)
for _ in range(100):
    x = Gg @ x
print("PageRank (guc yineleme):", np.round(x, 4))
vals2, vecs2 = np.linalg.eig(Gg)
i = np.argmax(vals2.real)
pi = np.real(vecs2[:, i] / vecs2[:, i].sum())
print("PageRank (eig, lambda=1):", np.round(pi, 4))
