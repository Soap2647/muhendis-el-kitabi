# ornek3.py: simetrik 2x2 matris: ozdeger, ozvektor, kosegenlestirme
import numpy as np

A = np.array([[3.0, 1.0], [1.0, 3.0]])
print("karakteristik: det(A - lam I) = lam^2 - 6 lam + 8")
print("kokler: lam1 = 4, lam2 = 2")
v1 = np.array([1.0, 1.0]) / np.sqrt(2)
v2 = np.array([1.0, -1.0]) / np.sqrt(2)
print("A v1 =", np.round(A @ v1, 6), " 4 v1 =", np.round(4 * v1, 6))
print("A v2 =", np.round(A @ v2, 6), " 2 v2 =", np.round(2 * v2, 6))

vals, V = np.linalg.eigh(A)
print("numpy lambda =", vals)
Lam = np.diag(vals)
print("V Lam V^T == A ?", np.allclose(V @ Lam @ V.T, A))
A5 = V @ np.diag(vals ** 5) @ V.T
print("A^5 (kopegel.) =")
print(np.round(A5, 3))
print("A^5 (matris_power) =")
print(np.round(np.linalg.matrix_power(A, 5), 3))
