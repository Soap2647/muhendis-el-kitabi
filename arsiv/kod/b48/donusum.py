# donusum.py: 2B donusumler, determinant ve bilesim sirasi
import numpy as np

kare = np.array([[0, 1, 1, 0, 0],       # birim karenin kose noktalari
                 [0, 0, 1, 1, 0]], dtype=float)   # 1. satir x, 2. y

R = np.array([[0.0, -1.0], [1.0, 0.0]])  # 90 derece dondurme
S = np.array([[2.0, 0.0], [0.0, 1.0]])   # x ekseninde 2 kat olcekleme
K = np.array([[1.0, 1.0], [0.0, 1.0]])   # kayma
P = np.array([[1.0, 0.0], [0.0, 0.0]])   # x eksenine izdusum

for ad, M in [("R", R), ("S", S), ("K", K), ("P", P)]:
    print(ad, "det =", round(np.linalg.det(M), 6))

print("R kareyi dondurur (sutunlar kose):")
print(np.round(R @ kare, 3))

e1 = np.array([1.0, 0.0])
e2 = np.array([0.0, 1.0])
print("R(S e1) =", R @ (S @ e1), "  S(R e1) =", S @ (R @ e1))
print("R @ S =")
print(R @ S)
print("S @ R =")
print(S @ R)
print("AB == BA ?", np.allclose(R @ S, S @ R))
print("R e2 =", R @ e2)
