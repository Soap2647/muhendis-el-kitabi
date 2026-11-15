# -*- coding: utf-8 -*-
# b58_11_taban.py: dogrusal modelin siniri (XOR, yarim aylar) ve temel
# fonksiyonlar (polinom, RBF) ile doğrusal olmayan uydurma
import numpy as np
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from b58_core import logistik_newton, ridge_fit


def dogruluk_lojistik(Xtr, ytr, Xte, yte):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    A, B = (Xtr - mu) / sd, (Xte - mu) / sd
    w, _ = logistik_newton(A, ytr, lam=1e-4)
    t = (np.hstack([np.ones((len(B), 1)), B]) @ w) > 0
    return np.mean(t == yte)


# 1) XOR: dogrusal ayrilamaz
rng = np.random.default_rng(58)
merkez = np.array([[0, 0], [1, 1], [0, 1], [1, 0]], dtype=float)
etik = np.array([0, 0, 1, 1])
X = np.vstack([m + rng.normal(0, 0.1, (100, 2)) for m in merkez])
y = np.repeat(etik, 100)
Xtr, Xte, ytr, yte = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=58
)
print(
    "XOR: dogrusal model test dogrulugu = %.3f"
    % dogruluk_lojistik(Xtr, ytr, Xte, yte)
)
Xp = np.column_stack([X, X[:, 0] * X[:, 1]])  # x1*x2 ozniteligi
Xptr, Xpte, ytr2, yte2 = train_test_split(
    Xp, y, test_size=0.25, stratify=y, random_state=58
)
print(
    "XOR: x1*x2 eklenince test dogrulugu = %.3f"
    % dogruluk_lojistik(Xptr, ytr2, Xpte, yte2)
)

# 2) Yarim aylar: polinom ozniteligi ile dogrusal sinirin kurtarilmasi
Xm, ym = make_moons(n_samples=400, noise=0.2, random_state=58)
Mtr, Mte, mtr, mte = train_test_split(
    Xm, ym, test_size=0.25, stratify=ym, random_state=58
)
print(
    "yarim ay: dogrusal test dogrulugu = %.3f"
    % dogruluk_lojistik(Mtr, mtr, Mte, mte)
)
for d in (2, 3, 5):
    pf = PolynomialFeatures(degree=d, include_bias=False)
    print(
        "yarim ay: polinom derece %d (%d oz.) test dogrulugu = %.3f"
        % (
            d,
            pf.fit(Mtr).n_output_features_,
            dogruluk_lojistik(
                pf.transform(Mtr), mtr, pf.transform(Mte), mte
            ),
        )
    )

# 3) Temel fonksiyonlar: sin(x) uydurma, dogrulama ile secim
rng = np.random.default_rng(58)
xs = rng.uniform(0, 2 * np.pi, 120)
ys = np.sin(xs) + rng.normal(0, 0.2, 120)
xa, xb, ya, yb = train_test_split(
    xs, ys, test_size=0.3, random_state=58
)
t_of = lambda x: x / np.pi - 1.0  # [-1, 1] araligina


def polinom_oz(x, k):
    # Chebyshev tabanli polinom (sayisal kararlilik icin)
    return np.polynomial.chebyshev.chebvander(t_of(x), k)


def rbf_oz(x, merk, s):
    return np.exp(-((x[:, None] - merk[None, :]) ** 2) / (2 * s * s))


def uydur(Xf, y_, alfa=1e-6):
    w, b = ridge_fit(Xf, y_, alfa)
    return w, b


def mse_(Xf, y_, w, b):
    return np.mean((y_ - (Xf @ w + b)) ** 2)


secim = []
for ad, kur in [
    ("poly%d" % k, lambda x, k=k: polinom_oz(x, k))
    for k in (3, 5, 9, 15)
] + [
    (
        "rbf%d" % m,
        lambda x, m=m: rbf_oz(
            x, np.linspace(0, 2 * np.pi, m), 2 * np.pi / m
        ),
    )
    for m in (4, 8, 16)
]:
    Fa, Fb = kur(xa), kur(xb)
    w, b = uydur(Fa, ya)
    secim.append((mse_(Fb, yb, w, b), ad, mse_(Fa, ya, w, b)))
    print(
        "%-7s egitim MSE = %.4f, dogrulama MSE = %.4f"
        % (ad, mse_(Fa, ya, w, b), mse_(Fb, yb, w, b))
    )
en = min(secim)
print(
    "dogrulamaya gore secilen: %s (dogrulama MSE %.4f)"
    % (en[1], en[0])
)
