# ornek1.py: birim karenin bilesik donusumu (once R, sonra K)
import numpy as np

R = np.array([[0, -1], [1, 0]])     # 90 derece dondurme
K = np.array([[1, 1], [0, 1]])      # kayma
M = K @ R                           # once R, sonra K

kose = np.array([[0, 1, 1, 0],      # (0,0) (1,0) (1,1) (0,1)
                 [0, 0, 1, 1]])
print("M = K @ R =")
print(M)
print("det(M) =", round(np.linalg.det(M), 6))
adim1 = R @ kose
adim2 = K @ adim1
print("adim 1 (R)   x:", adim1[0], " y:", adim1[1])
print("adim 2 (K)   x:", adim2[0], " y:", adim2[1])
print("M @ kose == K @ (R @ kose):", np.array_equal(M @ kose, adim2))
rng = np.random.default_rng(42)
P = rng.integers(-5, 6, size=(2, 100))
print("100 rastgele nokta:", np.array_equal(M @ P, K @ (R @ P)))
