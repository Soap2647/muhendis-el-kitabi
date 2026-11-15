# -*- coding: utf-8 -*-
# b58_ornek.py: cozumlu orneklerdeki sayilarin kontrolu
import numpy as np
from b58_core import sigmoid

# Ornek 1 (*): bes nokta, y = a + b x, normal denklem
x = np.array([1, 2, 3, 4, 5.0])
y = np.array([2, 3, 5, 4, 6.0])
A = np.column_stack([np.ones(5), x])
print(
    "Ornek 1: X^T X =",
    (A.T @ A).tolist(),
    " X^T y =",
    (A.T @ y).tolist(),
)
a, b = np.linalg.solve(A.T @ A, A.T @ y)
r = y - A @ np.array([a, b])
print("a = %.4f, b = %.4f, artiklar = %s" % (a, b, np.round(r, 4)))
print(
    "SSE = %.4f, sum(r) = %.2e, sum(x r) = %.2e"
    % (r @ r, r.sum(), x @ r)
)

# Ornek 2 (**): iki ozellik, ortalanmis, XtX kosegen; ridge
X2 = np.array([[1, 1], [-1, 1], [0, -2.0]])
y2 = np.array([2, 1, -3.0])
print(
    "Ornek 2: X^T X =",
    (X2.T @ X2).tolist(),
    " X^T y =",
    (X2.T @ y2).tolist(),
)
for lam in (0.0, 2.0, 6.0):
    w = np.linalg.solve(X2.T @ X2 + lam * np.eye(2), X2.T @ y2)
    print("  lambda=%.0f  w = (%.4f, %.4f)" % (lam, w[0], w[1]))

# Ornek 3 (**): lojistik, odds orani
w1, b0 = 0.8, -1.2
for xv in (0.0, 1.0, 2.0):
    z = b0 + w1 * xv
    p = sigmoid(np.array(z))
    print(
        "  x=%.0f z=%.2f p=%.4f odds=%.4f" % (xv, z, p, p / (1 - p))
    )
print("  e^0.8 = %.4f" % np.exp(0.8))

# Ornek 4 (***): softmax, bir gradyan adimi
X4 = np.array([[1, 0], [0, 1], [1, 1.0]])
lab = np.array([0, 1, 2])
Y4 = np.eye(3)[lab]
W4 = np.zeros((2, 3))
b4 = np.zeros(3)
Z4 = X4 @ W4 + b4
P4 = np.exp(Z4) / np.exp(Z4).sum(1, keepdims=True)
G4 = X4.T @ (P4 - Y4) / 3
print(
    "Ornek 4: P (ilk adim) = 1/3 her yerde:", np.allclose(P4, 1 / 3)
)
print("G = X^T (P - Y)/n =\n", np.round(G4, 6))
W4n = W4 - 0.5 * G4
Z4n = X4 @ W4n
P4n = np.exp(Z4n) / np.exp(Z4n).sum(1, keepdims=True)
print("W_yeni =\n", np.round(W4n, 6))
print("yeni P =\n", np.round(P4n, 6))
kay = lambda P: -np.mean(np.log(P[np.arange(3), lab]))
print("kayip once = %.6f, sonra = %.6f" % (kay(P4), kay(P4n)))
