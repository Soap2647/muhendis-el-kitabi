# -*- coding: utf-8 -*-
# b58_10_huber.py: aykiri degerlere duyarlilik: MSE, MAE (LAD), Huber
import csv
import numpy as np
from scipy.optimize import linprog, minimize
from sklearn.linear_model import HuberRegressor
from b58_core import huber_kayip

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
DELTA = 1.345
BETA = np.array([2.0, 0.5])  # gercek: y = 2 + 0.5 x + gurultu


def veri_uret(rng, n=200, oran=0.05):
    x = rng.uniform(0, 10, n)
    y = BETA[0] + BETA[1] * x + rng.normal(0, 1, n)
    k = rng.choice(n, int(oran * n), replace=False)
    y[k] += 20.0  # ayikri degerler: yukari sicrama
    return np.column_stack([np.ones(n), x]), y


def mse_coz(A, y):
    return np.linalg.lstsq(A, y, rcond=None)[0]


def lad_coz(A, y):
    # min sum|r|: r = y - A w = u - v, u, v >= 0 (dogrusal program)
    n, d = A.shape
    c = np.concatenate([np.zeros(d), np.ones(n), np.ones(n)])
    Aeq = np.hstack([A, np.eye(n), -np.eye(n)])
    sol = linprog(
        c,
        A_eq=Aeq,
        b_eq=y,
        bounds=[(None, None)] * d + [(0, None)] * (2 * n),
        method="highs",
    )
    return sol.x[:d]


def huber_coz(A, y, delta=DELTA):
    w0 = np.linalg.lstsq(A, y, rcond=None)[0]

    def f(w):
        return huber_kayip(w, A, y, delta)

    sol = minimize(
        f,
        w0,
        jac=True,
        method="L-BFGS-B",
        options={"gtol": 1e-10, "maxiter": 10000},
    )
    return sol.x


# 1) Tek veri kumesi: tahmin ve gercek parametre
rng = np.random.default_rng(58)
A, y = veri_uret(rng)
w_mse, w_lad, w_hub = mse_coz(A, y), lad_coz(A, y), huber_coz(A, y)
for ad, w_ in (("MSE", w_mse), ("LAD", w_lad), ("Huber", w_hub)):
    print("%-6s  kesim = %6.3f  egim = %6.3f" % (ad, w_[0], w_[1]))
sk = HuberRegressor(epsilon=DELTA, alpha=0.0, max_iter=1000).fit(
    A[:, 1:], y
)
print(
    "sklearn HuberRegressor egim = %.3f (sigma ogrenilir)"
    % sk.coef_[0]
)

# 2) Tekrarli deney: 200 veri kumesi, egim hatasi istatistigi
hata = {"MSE": [], "LAD": [], "Huber": []}
for s_ in range(200):
    A_, y_ = veri_uret(np.random.default_rng(1000 + s_))
    hata["MSE"].append(mse_coz(A_, y_)[1] - BETA[1])
    hata["LAD"].append(lad_coz(A_, y_)[1] - BETA[1])
    hata["Huber"].append(huber_coz(A_, y_)[1] - BETA[1])
for ad in ("MSE", "LAD", "Huber"):
    e = np.array(hata[ad])
    print(
        "%-6s egim hatasi: ortalama = %+.4f, std = %.4f, RMSE = %.4f"
        % (ad, e.mean(), e.std(ddof=1), np.sqrt(np.mean(e * e)))
    )

# 3) Sekil icin csv: veri ve uc cozum
with open(
    VERI + "b58_huber_veri.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["x", "y"])
    for xi, yi in zip(A[:, 1], y):
        yaz.writerow(["%.5f" % xi, "%.5f" % yi])
with open(
    VERI + "b58_huber_cizgi.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["ad", "kesim", "egim"])
    for ad, w_ in (
        ("MSE", w_mse),
        ("LAD", w_lad),
        ("Huber", w_hub),
        ("Gercek", BETA),
    ):
        yaz.writerow([ad, "%.6f" % w_[0], "%.6f" % w_[1]])
