# -*- coding: utf-8 -*-
# b58_06_coklu.py: coklu dogrusallik, OLS ve Ridge
import csv
import numpy as np
from sklearn.datasets import load_diabetes
from b58_core import ridge_fit

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
N, SEEDS, ALFA = 100, 300, 1.0
sonuc = []
for tohum in range(SEEDS):
    rng = np.random.default_rng(tohum)
    x1 = rng.normal(0, 1, N)
    x2 = x1 + 0.01 * rng.normal(0, 1, N)  # neredeyse ayni sutun
    y = x1 + x2 + rng.normal(0, 0.5, N)  # gercek: beta = (1, 1)
    X = np.column_stack([x1, x2])
    w_ols = np.linalg.lstsq(X, y, rcond=None)[0]
    w_rid, _ = ridge_fit(X, y, ALFA)
    sonuc.append([w_ols[0], w_ols[1], w_rid[0], w_rid[1]])
S = np.array(sonuc)

rng = np.random.default_rng(0)
x1 = rng.normal(0, 1, N)
x2 = x1 + 0.01 * rng.normal(0, 1, N)
X0 = np.column_stack([x1, x2])
print("corr(x1, x2) = %.5f" % np.corrcoef(x1, x2)[0, 1])
print("cond(X^T X) = %.3e" % np.linalg.cond(X0.T @ X0))
print(
    "OLS  beta1: ortalama = %.2f, std = %.2f"
    % (S[:, 0].mean(), S[:, 0].std())
)
print(
    "OLS  beta2: ortalama = %.2f, std = %.2f"
    % (S[:, 1].mean(), S[:, 1].std())
)
print(
    "Ridge beta1: ortalama = %.3f, std = %.3f"
    % (S[:, 2].mean(), S[:, 2].std())
)
print(
    "Ridge beta2: ortalama = %.3f, std = %.3f"
    % (S[:, 3].mean(), S[:, 3].std())
)
toplam_ols = S[:, 0] + S[:, 1]
print(
    "OLS beta1+beta2 std = %.3f (toplam iyi belirlenir)"
    % toplam_ols.std()
)

with open(
    VERI + "b58_coklu.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["ols_b1", "ols_b2", "ridge_b1", "ridge_b2"])
    for satir in S:
        yaz.writerow(["%.5f" % v for v in satir])

# VIF: diyabet verisi (Bolum 58.5). VIF_j = 1 / (1 - R_j^2)
veri = load_diabetes()
X = veri.data
ad = ["age", "sex", "bmi", "bp", "s1", "s2", "s3", "s4", "s5", "s6"]
print("VIF (diyabet verisi):")
for j in range(X.shape[1]):
    diger = np.delete(X, j, axis=1)
    A = np.hstack([np.ones((len(X), 1)), diger])
    b = np.linalg.lstsq(A, X[:, j], rcond=None)[0]
    artik = X[:, j] - A @ b
    r2 = 1 - artik @ artik / np.sum((X[:, j] - X[:, j].mean()) ** 2)
    print("  %-4s VIF = %6.2f" % (ad[j], 1 / (1 - r2)))
