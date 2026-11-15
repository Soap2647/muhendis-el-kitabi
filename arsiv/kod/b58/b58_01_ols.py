# -*- coding: utf-8 -*-
# b58_01_ols.py: dogrusal regresyon, uc kapali form cozum
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

veri = load_diabetes()
X, y = veri.data, veri.target
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.25, random_state=58
)
mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
Z_tr, Z_te = (X_tr - mu) / sd, (
    X_te - mu
) / sd  # olcekleyici yalniz egitimden
A = np.hstack([np.ones((len(Z_tr), 1)), Z_tr])  # ilk sutun: sapma
B = np.hstack([np.ones((len(Z_te), 1)), Z_te])

# (1) Normal denklem: (A^T A) w = A^T y
w_ne = np.linalg.solve(A.T @ A, A.T @ y_tr)
# (2) QR: A = QR, R w = Q^T y
Q, R = np.linalg.qr(A)
w_qr = np.linalg.solve(R, Q.T @ y_tr)
# (3) SVD: A = U S V^T, w = V S^-1 U^T y
U, s, Vt = np.linalg.svd(A, full_matrices=False)
w_svd = Vt.T @ ((U.T @ y_tr) / s)
# (4) scikit-learn
sk = LinearRegression().fit(Z_tr, y_tr)
w_sk = np.concatenate([[sk.intercept_], sk.coef_])

print("max|w_NE - w_QR|   = %.2e" % np.max(np.abs(w_ne - w_qr)))
print("max|w_NE - w_SVD|  = %.2e" % np.max(np.abs(w_ne - w_svd)))
print("max|w_NE - w_sk|   = %.2e" % np.max(np.abs(w_ne - w_sk)))
print("cond(A)     = %.2f" % np.linalg.cond(A))
print("cond(A^T A) = %.2f" % np.linalg.cond(A.T @ A))


def olcut(w, M, t):
    tahmin = M @ w
    rmse = np.sqrt(np.mean((t - tahmin) ** 2))
    r2 = 1 - np.sum((t - tahmin) ** 2) / np.sum((t - t.mean()) ** 2)
    return rmse, r2


rm, r2 = olcut(w_ne, B, y_te)
print("test RMSE = %.2f, test R^2 = %.4f" % (rm, r2))
rm0 = np.sqrt(np.mean((y_te - y_tr.mean()) ** 2))
print("baseline (egitim ortalamasi) RMSE = %.2f" % rm0)

# Polinom Vandermonde matrisi: kosul sayisi karesel buyur
t = np.linspace(0, 1, 50)
V = np.vander(t, 9)  # derece 8
x_gercek = np.ones(9)
b_vec = V @ x_gercek  # tam uyumlu sistem
x_ne = np.linalg.solve(V.T @ V, V.T @ b_vec)
Qv, Rv = np.linalg.qr(V)
x_qr = np.linalg.solve(Rv, Qv.T @ b_vec)
print("Vandermonde cond(V)     = %.3e" % np.linalg.cond(V))
print("Vandermonde cond(V^T V) = %.3e" % np.linalg.cond(V.T @ V))
print(
    "normal denklem hatasi   = %.2e" % np.max(np.abs(x_ne - x_gercek))
)
print(
    "QR hatasi               = %.2e" % np.max(np.abs(x_qr - x_gercek))
)
