# -*- coding: utf-8 -*-
# b58_08_softmax.py: softmax regresyon ve OvR karsilastirmasi
import csv
import numpy as np
from scipy.optimize import minimize
from sklearn.datasets import load_digits, make_blobs
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.multiclass import OneVsRestClassifier
from b58_core import softmax_kayip

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"


def softmax_egit(X, y, lam, K):
    Y = np.eye(K)[y]
    d = X.shape[1]
    th0 = np.zeros(d * K + K)
    sol = minimize(
        softmax_kayip,
        th0,
        args=(X, Y, lam, K),
        jac=True,
        method="L-BFGS-B",
        options={"maxiter": 5000, "gtol": 1e-9, "ftol": 1e-15},
    )
    th = sol.x
    return th[: d * K].reshape(d, K), th[d * K :], sol


def tahmin(X, W, b):
    return np.argmax(X @ W + b, axis=1)


# 1) Digits: veriyi [0,1]'e olcekle (sabit bolum, sizinti yok)
veri = load_digits()
X = veri.data / 16.0
y = veri.target
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=58
)
K, n = 10, len(y_tr)

# 2) Gradyan denetimi (sonlu fark, Bolum 50.3)
rng = np.random.default_rng(0)
Ytr = np.eye(K)[y_tr]
th = rng.normal(0, 0.01, X_tr.shape[1] * K + K)
f0, g0 = softmax_kayip(th, X_tr, Ytr, 1e-3, K)
h = 1e-6
en_buyuk = 0.0
for j in rng.choice(len(th), 20, replace=False):
    e = np.zeros_like(th)
    e[j] = h
    num = (
        softmax_kayip(th + e, X_tr, Ytr, 1e-3, K)[0]
        - softmax_kayip(th - e, X_tr, Ytr, 1e-3, K)[0]
    ) / (2 * h)
    en_buyuk = max(en_buyuk, abs(num - g0[j]))
print(
    "gradyan denetimi (20 koordinat), en buyuk fark = %.2e" % en_buyuk
)

# 3) lambda secimi: yalnizca egitim verisinde 5 katli CV
kf = StratifiedKFold(5, shuffle=True, random_state=58)
adaylar = [1e-4, 1e-3, 1e-2, 1e-1]
cv_skor = []
for lam in adaylar:
    dogru = []
    for tr, va in kf.split(X_tr, y_tr):
        W, b, _ = softmax_egit(X_tr[tr], y_tr[tr], lam, K)
        dogru.append(np.mean(tahmin(X_tr[va], W, b) == y_tr[va]))
    cv_skor.append(np.mean(dogru))
    print("lambda=%.0e  CV dogruluk = %.4f" % (lam, cv_skor[-1]))
lam_sec = adaylar[int(np.argmax(cv_skor))]
print("secilen lambda (yalnizca egitim CV'si) = %.0e" % lam_sec)

# 4) Egitim, sklearn karsilastirma (lambda = 1/(C n))
W, b, sol = softmax_egit(X_tr, y_tr, lam_sec, K)
print("L-BFGS basarili = %s, adim = %d" % (sol.success, sol.nit))
C = 1.0 / (lam_sec * n)
sk = LogisticRegression(C=C, tol=1e-12, max_iter=20000).fit(
    X_tr, y_tr
)
print("max|W - W_sk| = %.2e" % np.max(np.abs(W - sk.coef_.T)))
print(
    "tahmin uyumu (test) = %.4f"
    % np.mean(tahmin(X_te, W, b) == sk.predict(X_te))
)

# 5) Test: model, OvR, baseline
tr_acc = np.mean(tahmin(X_tr, W, b) == y_tr)
te_acc = np.mean(tahmin(X_te, W, b) == y_te)
print(
    "softmax: egitim dogrulugu = %.4f, test dogrulugu = %.4f"
    % (tr_acc, te_acc)
)
ovr = OneVsRestClassifier(
    LogisticRegression(C=C, tol=1e-12, max_iter=20000)
).fit(X_tr, y_tr)
print("OvR (sklearn): test dogrulugu = %.4f" % ovr.score(X_te, y_te))
cogunluk = np.bincount(y_tr).argmax()
print("baseline hep cogunluk = %.4f" % np.mean(y_te == cogunluk))
pk = np.bincount(y_tr) / n
print("baseline rastgele oran (beklenen) = %.4f" % np.sum(pk * pk))

# Hangi rakamlar karisiyor? (test)
tt = tahmin(X_te, W, b)
cift = {}
for g_, t_ in zip(y_te, tt):
    if g_ != t_:
        cift[(g_, t_)] = cift.get((g_, t_), 0) + 1
for (g_, t_), c_ in sorted(cift.items(), key=lambda z: -z[1])[:3]:
    print("  gercek %d -> tahmin %d : %d kez" % (g_, t_, c_))

# 6) Iki boyutlu ornek (sekil icin): 3 sinif
P, q = make_blobs(
    n_samples=180,
    centers=[[-2, 0], [2, 0], [0, 3]],
    cluster_std=1.0,
    random_state=58,
)
W2, b2, _ = softmax_egit(P, q, 1e-3, 3)
print("2B: dogruluk = %.4f" % np.mean(tahmin(P, W2, b2) == q))
with open(
    VERI + "b58_softmax2d.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["x1", "x2", "y"])
    for (a_, c_), d_ in zip(P, q):
        yaz.writerow(["%.5f" % a_, "%.5f" % c_, int(d_)])
with open(
    VERI + "b58_softmax2d_w.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["sinif", "w1", "w2", "b"])
    for k in range(3):
        yaz.writerow(
            [k, "%.6f" % W2[0, k], "%.6f" % W2[1, k], "%.6f" % b2[k]]
        )

# 7) Birden cok tohum: test dogrulugu ortalama +- sapma (5 bolme)
sm, ov = [], []
for s_ in range(5):
    Xa_, Xb_, ya_, yb_ = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=s_
    )
    Wa, ba, _ = softmax_egit(Xa_, ya_, lam_sec, K)
    sm.append(np.mean(tahmin(Xb_, Wa, ba) == yb_))
    o_ = OneVsRestClassifier(
        LogisticRegression(
            C=1.0 / (lam_sec * len(ya_)), tol=1e-12, max_iter=20000
        )
    ).fit(Xa_, ya_)
    ov.append(o_.score(Xb_, yb_))
print(
    "5 tohum softmax: %.4f +- %.4f"
    % (np.mean(sm), np.std(sm, ddof=1))
)
print(
    "5 tohum OvR:     %.4f +- %.4f"
    % (np.mean(ov), np.std(ov, ddof=1))
)
print(
    "tohum basina softmax - OvR:",
    np.round(np.array(sm) - np.array(ov), 4),
)
