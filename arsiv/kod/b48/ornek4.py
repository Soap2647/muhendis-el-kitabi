# ornek4.py: SVD ile rank-k hata ve sikistirma orani hesabi
import numpy as np

m, n = 8, 6
u1 = np.array([1.0, 2, 3, 4, 3, 2, 1, 0])
u2 = np.array([0.0, 1, 0, -1, 0, 1, 0, -1])
v1 = np.array([1.0, 1, 1, 1, 1, 1])
v2 = np.array([1.0, -1, 1, -1, 1, -1])
A = 5.0 * np.outer(u1, v1) + 1.0 * np.outer(u2, v2)

U, s, Vt = np.linalg.svd(A, full_matrices=False)
print("tekil degerler:", np.round(s, 4))
print("rank(A) =", np.linalg.matrix_rank(A))
for k in [1, 2]:
    Ak = (U[:, :k] * s[:k]) @ Vt[:k]
    hata = np.linalg.norm(A - Ak, "fro")
    tahmin = np.sqrt(np.sum(s[k:] ** 2))
    oran = k * (m + n + 1) / (m * n)
    print("k=%d  ||A-Ak||_F = %.4f  (sqrt toplam s^2 = %.4f)"
          % (k, hata, tahmin))
    print("     sikistirma orani = %d*(8+6+1)/(8*6) = %.4f"
          % (k, oran))
