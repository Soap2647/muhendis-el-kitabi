# -*- coding: utf-8 -*-
# b58_04_ridge.py: Ridge (L2): kapali form, kosul, yol, CV
import csv
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.linear_model import Ridge
from sklearn.model_selection import (
    GridSearchCV,
    KFold,
    train_test_split,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from b58_core import ridge_fit

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
veri = load_diabetes()
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data, veri.target, test_size=0.25, random_state=58
)
mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
Z, Zt = (X_tr - mu) / sd, (X_te - mu) / sd
Zc = Z - Z.mean(axis=0)

# 1) Kapali form ile sklearn Ridge karsilastirmasi
for a in (0.1, 10.0, 1000.0):
    w, b = ridge_fit(Z, y_tr, a)
    sk = Ridge(alpha=a).fit(Z, y_tr)
    print(
        "alpha=%7.1f  max|w - w_sk| = %.2e, |b - b_sk| = %.2e"
        % (a, np.max(np.abs(w - sk.coef_)), abs(b - sk.intercept_))
    )

# 2) Spektral yorum: w = sum s/(s^2+a) (u^T y) v
U, s, Vt = np.linalg.svd(Zc, full_matrices=False)
a = 10.0
w_ret = Vt.T @ ((s / (s**2 + a)) * (U.T @ (y_tr - y_tr.mean())))
w_kf, _ = ridge_fit(Z, y_tr, a)
print(
    "spektral ve kapali form farki = %.2e"
    % np.max(np.abs(w_ret - w_kf))
)
df = np.sum(s**2 / (s**2 + a))
print(
    "etkin serbestlik df(alpha=10) = %.3f (p = %d)" % (df, Z.shape[1])
)

# 3) Kosul sayisi: Vandermonde ornegi (Bolum 58.2 ile ayni matris)
t = np.linspace(0, 1, 50)
V = np.vander(t, 9)
G = V.T @ V
for lam in (0.0, 1e-8, 1e-6, 1e-4, 1e-2):
    print(
        "lambda=%.0e  cond(V^T V + lam I) = %.3e"
        % (lam, np.linalg.cond(G + lam * np.eye(9)))
    )

# 4) Duzenlileştirme yolu: alpha'ya gore katsayilar (csv)
alfalar = np.logspace(-2, 4, 60)
yol = [ridge_fit(Z, y_tr, a_)[0] for a_ in alfalar]
with open(
    VERI + "b58_ridge_yol.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["alpha"] + ["w%d" % j for j in range(Z.shape[1])])
    for a_, w_ in zip(alfalar, yol):
        yaz.writerow(["%.6e" % a_] + ["%.6f" % v for v in w_])
print(
    "ridge yolu yazildi; alpha=10^4'te max|w| = %.4f"
    % np.max(np.abs(yol[-1]))
)

# 5) alpha secimi: 5 katli CV, olcekleyici her katta yeniden ogrenilir
grid = np.logspace(-2, 4, 25)
kf = KFold(5, shuffle=True, random_state=58)
ort = []
for a_ in grid:
    hatalar = []
    for tr, va in kf.split(X_tr):
        m, s_ = X_tr[tr].mean(0), X_tr[tr].std(0)
        A_, B_ = (X_tr[tr] - m) / s_, (X_tr[va] - m) / s_
        w_, b_ = ridge_fit(A_, y_tr[tr], a_)
        hatalar.append(np.mean((y_tr[va] - (B_ @ w_ + b_)) ** 2))
    ort.append(np.mean(hatalar))
en_iyi = grid[int(np.argmin(ort))]
print(
    "kendi CV: secilen alpha = %.4g, CV MSE = %.1f"
    % (en_iyi, min(ort))
)

gs = GridSearchCV(
    make_pipeline(StandardScaler(), Ridge()),
    {"ridge__alpha": grid},
    cv=kf,
    scoring="neg_mean_squared_error",
).fit(X_tr, y_tr)
print(
    "sklearn GridSearchCV secilen alpha = %.4g"
    % gs.best_params_["ridge__alpha"]
)


# 6) Test (bir kez): Ridge, OLS (alpha = 0) ve baseline
def test_skor(w, b):
    t_ = Zt @ w + b
    rm = np.sqrt(np.mean((y_te - t_) ** 2))
    r2 = 1 - np.sum((y_te - t_) ** 2) / np.sum(
        (y_te - y_te.mean()) ** 2
    )
    return rm, r2


w_r, b_r = ridge_fit(Z, y_tr, en_iyi)
w_o, b_o = ridge_fit(Z, y_tr, 0.0)
print(
    "test RMSE / R^2  Ridge(alpha*) = %.2f / %.4f"
    % test_skor(w_r, b_r)
)
print(
    "test RMSE / R^2  OLS           = %.2f / %.4f"
    % test_skor(w_o, b_o)
)
rm0 = np.sqrt(np.mean((y_te - y_tr.mean()) ** 2))
print("baseline RMSE (ortalama)       = %.2f" % rm0)
