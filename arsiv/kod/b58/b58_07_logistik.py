# -*- coding: utf-8 -*-
# b58_07_logistik.py: lojistik regresyon, IRLS, L2, sinif agirligi,
# ayrilabilir veri ve karar siniri
import csv
import numpy as np
from sklearn.datasets import load_breast_cancer, make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from b58_core import logistik_newton, sigmoid

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"


def dengeli_dogruluk(y, t):
    return np.mean([np.mean(t[y == c] == c) for c in np.unique(y)])


# 1) Breast cancer: Newton ile L2'li lojistik, sklearn ile ayni amac
veri = load_breast_cancer()
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data,
    veri.target,
    test_size=0.2,
    stratify=veri.target,
    random_state=58,
)
mu, sd = X_tr.mean(0), X_tr.std(0)
Z, Zt = (X_tr - mu) / sd, (X_te - mu) / sd
C = 1.0
lam = 1.0 / (C * len(y_tr))  # sklearn: C*sum(kayip)+0.5||w||^2
w, adim = logistik_newton(Z, y_tr, lam=lam)
print("Newton adim sayisi = %d" % adim)
sk = LogisticRegression(C=C, tol=1e-12, max_iter=10000).fit(Z, y_tr)
print(
    "max|w - w_sk| = %.2e, |b - b_sk| = %.2e"
    % (
        np.max(np.abs(w[1:] - sk.coef_[0])),
        abs(w[0] - sk.intercept_[0]),
    )
)

t_ = (np.hstack([np.ones((len(Zt), 1)), Zt]) @ w) > 0
print(
    "egitim dogrulugu (sifirdan) = %.4f"
    % np.mean(
        ((np.hstack([np.ones((len(Z), 1)), Z]) @ w) > 0) == y_tr
    )
)
print(
    "test dogruluk = %.4f, test dengeli dogruluk = %.4f"
    % (np.mean(t_ == y_te), dengeli_dogruluk(y_te, t_.astype(int)))
)
baz = np.ones(len(y_te), dtype=int)
print(
    "baseline (hep cogunluk) dogruluk = %.4f, dengeli = %.4f"
    % (np.mean(baz == y_te), dengeli_dogruluk(y_te, baz))
)

# Odds orani: standardize katsayinin ustel degeri (1 SD artis icin)
sira = np.argsort(-np.abs(w[1:]))[:3]
for j in sira:
    print(
        "  %-22s w = %+.3f  OR = %.3f"
        % (veri.feature_names[j], w[1 + j], np.exp(w[1 + j]))
    )

# 2) Sinif agirligi: sentetik dengesiz veri, ayri bolme
Xs, ys = make_classification(
    n_samples=4000,
    n_features=8,
    n_informative=4,
    weights=[0.95, 0.05],
    flip_y=0.01,
    class_sep=1.0,
    random_state=58,
)
Xa, Xb, ya, yb = train_test_split(
    Xs, ys, test_size=0.3, stratify=ys, random_state=58
)
ma, sa = Xa.mean(0), Xa.std(0)
Za, Zb = (Xa - ma) / sa, (Xb - ma) / sa
n_c = np.bincount(ya)
sw = (len(ya) / (2.0 * n_c))[ya]  # sklearn'in 'balanced' formulu
for ad, ag in (("agirliksiz", None), ("balanced", sw)):
    wq, _ = logistik_newton(Za, ya, lam=1.0 / len(ya), sw=ag)
    t2 = (np.hstack([np.ones((len(Zb), 1)), Zb]) @ wq) > 0
    rec1 = np.mean(t2[yb == 1] == 1)
    print(
        "%-11s dengeli dogruluk = %.4f, pozitif duyarlilik = %.4f"
        % (ad, dengeli_dogruluk(yb, t2.astype(int)), rec1)
    )
skb = LogisticRegression(
    C=1.0, class_weight="balanced", tol=1e-12, max_iter=10000
).fit(Za, ya)
wb, _ = logistik_newton(Za, ya, lam=1.0 / len(ya), sw=sw)
print(
    "balanced: max|w - w_sk| = %.2e"
    % np.max(np.abs(wb[1:] - skb.coef_[0]))
)

# 3) Ayrilabilir veri: penaltisiz kayip, ||w|| sonsuza kacar
rng = np.random.default_rng(58)
A2 = np.vstack(
    [
        rng.normal([-3, 0], 0.5, (20, 2)),
        rng.normal([3, 0], 0.5, (20, 2)),
    ]
)
y2 = np.array([0] * 20 + [1] * 20)
A2s = np.hstack([np.ones((40, 1)), A2])


def gd_lojistik(lam_, adim, eta=0.5):
    w_ = np.zeros(3)
    R = lam_ * np.diag([0.0, 1.0, 1.0])
    kayit = []
    for k in range(1, adim + 1):
        p = sigmoid(A2s @ w_)
        w_ = w_ - eta * (A2s.T @ (p - y2) / len(y2) + R @ w_)
        if k % 50 == 0:
            kayit.append((k, np.linalg.norm(w_[1:])))
    return w_, kayit


w0, kayit0 = gd_lojistik(0.0, 20000)
wl, kayitl = gd_lojistik(0.01, 20000)
for k, nrm in kayit0:
    if k in (100, 1000, 10000, 20000):
        print("lambda=0: adim %5d  ||w|| = %.2f" % (k, nrm))
print("lambda=0.01: adim 20000  ||w|| = %.3f" % kayitl[-1][1])
print(
    "ayrilabilir mi? egitim dogrulugu = %.2f"
    % np.mean((A2s @ w0 > 0) == y2)
)
with open(
    VERI + "b58_ayrilabilir.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["adim", "norm_lambda0", "norm_lambda001"])
    for (k, a_), (_, b_) in zip(kayit0, kayitl):
        yaz.writerow([k, "%.5f" % a_, "%.5f" % b_])

# 4) Karar siniri: iki boyutlu, ustu kapali ornek (sekil icin)
rng = np.random.default_rng(58)
P = np.vstack(
    [
        rng.normal([-1, -1], 1.0, (100, 2)),
        rng.normal([1, 1], 1.0, (100, 2)),
    ]
)
q = np.array([0] * 100 + [1] * 100)
wk, _ = logistik_newton(P, q, lam=1.0 / len(q))
print("2B karar siniri: b = %.3f, w = (%.3f, %.3f)" % tuple(wk))
print(
    "2B egitim dogrulugu = %.3f"
    % np.mean(((np.hstack([np.ones((len(P), 1)), P]) @ wk) > 0) == q)
)
with open(
    VERI + "b58_lojistik2d.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["x1", "x2", "y"])
    for (a_, b_), c_ in zip(P, q):
        yaz.writerow(["%.5f" % a_, "%.5f" % b_, int(c_)])
with open(
    VERI + "b58_lojistik2d_w.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["b", "w1", "w2"])
    yaz.writerow(["%.6f" % v for v in wk])
