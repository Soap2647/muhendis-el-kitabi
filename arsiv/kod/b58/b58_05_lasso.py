# -*- coding: utf-8 -*-
# b58_05_lasso.py: Lasso ve Elastic Net, koordinat inisi (sifirdan)
import csv
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.linear_model import ElasticNet, Lasso, LassoCV
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from b58_core import enet_cd

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
veri = load_diabetes()
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data, veri.target, test_size=0.25, random_state=58
)
mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
Z, Zt = (X_tr - mu) / sd, (X_te - mu) / sd
ym = y_tr.mean()
yc = y_tr - ym
n = len(yc)

# Lasso icin lambda_max: bu degerin ustunde tum katsayilar sifirdir
lam_max = np.max(np.abs(Z.T @ yc)) / n
print("lambda_max = %.4f" % lam_max)
print(
    "her sutun (1/n)||z||^2 = 1 mi?", np.allclose((Z**2).mean(0), 1)
)

# 1) Lasso: sifirdan ve sklearn (1/(2n)||y-Zw||^2 + lam||w||_1)
for lam in (0.5, 5.0, 20.0):
    w_me = enet_cd(Z, yc, lam, rho=1.0)
    sk = Lasso(
        alpha=lam, tol=1e-12, max_iter=100000, fit_intercept=False
    ).fit(Z, yc)
    print(
        "Lasso lam=%5.1f  max|w - w_sk| = %.2e  sifir sayisi = %d"
        % (lam, np.max(np.abs(w_me - sk.coef_)), np.sum(w_me == 0))
    )

# lambda_max'in hemen ustunde ve altinda
for c in (1.001, 0.999):
    w_c = enet_cd(Z, yc, c * lam_max, rho=1.0)
    print(
        "lam = %.3f * lambda_max: sifir sayisi = %d"
        % (c, np.sum(np.abs(w_c) < 1e-12))
    )

# 2) Elastic net: sifirdan vs sklearn
for lam, rho in ((2.0, 0.5), (5.0, 0.2)):
    w_me = enet_cd(Z, yc, lam, rho=rho)
    sk = ElasticNet(
        alpha=lam,
        l1_ratio=rho,
        tol=1e-12,
        max_iter=100000,
        fit_intercept=False,
    ).fit(Z, yc)
    print(
        "ElasticNet lam=%.1f rho=%.1f max|w - w_sk| = %.2e"
        % (lam, rho, np.max(np.abs(w_me - sk.coef_)))
    )

# 3) Lasso yolu (csv): lambda logaritmik izgara
lamlar = np.logspace(-2, np.log10(lam_max), 50)[::-1]
yol = [enet_cd(Z, yc, l_, rho=1.0) for l_ in lamlar]
with open(
    VERI + "b58_lasso_yol.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["lambda"] + ["w%d" % j for j in range(Z.shape[1])])
    for l_, w_ in zip(lamlar, yol):
        yaz.writerow(["%.6e" % l_] + ["%.6f" % v for v in w_])
sifirlar = [int(np.sum(np.abs(w_) < 1e-12)) for w_ in yol]
print(
    "lambda=%.3f sifir sayisi=%d; lambda=%.4f sifir sayisi=%d"
    % (lamlar[0], sifirlar[0], lamlar[-1], sifirlar[-1])
)

# 4) lambda secimi: CV (pipeline icinde olcekleme), sonra test
kf = KFold(5, shuffle=True, random_state=58)
pipe = make_pipeline(
    StandardScaler(),
    LassoCV(
        alphas=np.logspace(-2, 1, 30),
        cv=kf,
        tol=1e-10,
        max_iter=100000,
    ),
)
pipe.fit(X_tr, y_tr)
lam_cv = pipe[-1].alpha_
print("LassoCV secilen lambda = %.4f (sklearn olcegi)" % lam_cv)
w_c = enet_cd(Z, yc, lam_cv, rho=1.0)
t_ = Zt @ w_c + ym
rm = np.sqrt(np.mean((y_te - t_) ** 2))
r2 = 1 - np.sum((y_te - t_) ** 2) / np.sum((y_te - y_te.mean()) ** 2)
print(
    "test RMSE = %.2f, R^2 = %.4f, sifir katsayi = %d / %d"
    % (rm, r2, np.sum(np.abs(w_c) < 1e-12), len(w_c))
)
print("sklearn pipeline test R^2 = %.4f" % pipe.score(X_te, y_te))
