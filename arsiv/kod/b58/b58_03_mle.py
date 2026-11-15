# -*- coding: utf-8 -*-
# b58_03_mle.py: Gauss gurultusu altinda MSE = MLE, artik analizi,
# katsayi yorumu ve standardizasyon
import csv
import numpy as np
from scipy.optimize import minimize
from scipy.stats import shapiro, spearmanr
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
veri = load_diabetes()
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data, veri.target, test_size=0.25, random_state=58
)
mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
Z = (X_tr - mu) / sd
A = np.hstack([np.ones((len(Z), 1)), Z])
n, p = A.shape

w = np.linalg.lstsq(A, y_tr, rcond=None)[0]
r = y_tr - A @ w
sse = r @ r


# Olabilirlik: y_i ~ N(w^T a_i, sigma^2). Negatif log-olabilirlik:
# -l = (n/2) ln(2 pi s^2) + SSE/(2 s^2); s'yi log olarak tut.
def nll(theta):
    # Analitik gradyan: d/d beta = -A^T (y - A beta) / s^2,
    # d/d log(s) = n - SSE / s^2  (Bolum 58.3'te turetildi)
    beta, ls = theta[:-1], theta[-1]
    s2 = np.exp(2 * ls)
    rr = y_tr - A @ beta
    sse_ = rr @ rr
    f = 0.5 * n * np.log(2 * np.pi * s2) + sse_ / (2 * s2)
    g = np.concatenate([-(A.T @ rr) / s2, [n - sse_ / s2]])
    return f, g


sol = minimize(
    nll,
    np.zeros(p + 1),
    jac=True,
    method="BFGS",
    options={"gtol": 1e-8, "maxiter": 20000},
)
print(
    "OLS noktasinda |gradyan| = %.2e"
    % np.linalg.norm(
        nll(np.append(w, np.log(np.sqrt(sse / n))))[1][:-1]
    )
)
print(
    "BFGS yakinsadi mi: %s, max|beta_MLE - beta_OLS| = %.2e"
    % (sol.success, np.max(np.abs(sol.x[:-1] - w)))
)
print(
    "sigma_MLE = %.4f, sqrt(SSE/n) = %.4f"
    % (np.exp(sol.x[-1]), np.sqrt(sse / n))
)
print("sigma (sapmasiz, SSE/(n-p)) = %.4f" % np.sqrt(sse / (n - p)))

# Artik analizi: gercek veri (diyabet)
fit = A @ w
print("artik ortalamasi = %.2e" % r.mean())
print("Shapiro-Wilk p (artiklar) = %.4f" % shapiro(r).pvalue)
print(
    "Spearman(|artik|, tahmin) = %.3f, p = %.3f"
    % spearmanr(np.abs(r), fit)
)

# Sentetik: varyans x ile buyuyor (heteroskedastisite)
rng = np.random.default_rng(58)
xs = rng.uniform(1, 10, 300)
ys = 3 + 2 * xs + rng.normal(0, 0.3 * xs)
As = np.column_stack([np.ones_like(xs), xs])
ws = np.linalg.lstsq(As, ys, rcond=None)[0]
rs = ys - As @ ws
rho_s, p_s = spearmanr(np.abs(rs), As @ ws)
print("sentetik: w = (%.3f, %.3f)" % (ws[0], ws[1]))
print("sentetik: Spearman(|artik|, tahmin) = %.3f, p = %.1e"
      % (rho_s, p_s))

# Katsayi yorumu: standardize katsayi, ham birime donusum.
# Z = (X - mu)/sd oldugu icin ham katsayi = standart katsayi / sd.
ham_w = w[1:] / sd
ham_b = w[0] - np.sum(w[1:] * mu / sd)
tahmin_std = A @ w
tahmin_ham = ham_b + X_tr @ ham_w
print(
    "ham birime donusum tahmin farki = %.2e"
    % np.max(np.abs(tahmin_std - tahmin_ham))
)
print("standart katsayi (ilk 4):", np.round(w[1:5], 2))
print(
    "en buyuk |standart katsayi| sutunu:",
    int(np.argmax(np.abs(w[1:]))),
)

# csv: diyabet artiklari ve sentetik heteroskedastik veri
with open(
    VERI + "b58_artik.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(
        ["tahmin", "artik", "sentetik_tahmin", "sentetik_artik"]
    )
    sentetik_t = As @ ws
    for i in range(max(len(y_tr), len(xs))):
        satir = ["", "", "", ""]
        if i < len(y_tr):
            satir[0], satir[1] = "%.4f" % fit[i], "%.4f" % r[i]
        if i < len(xs):
            satir[2], satir[3] = (
                "%.4f" % sentetik_t[i],
                "%.4f" % rs[i],
            )
        yaz.writerow(satir)
print("csv yazildi: b58_artik.csv")
