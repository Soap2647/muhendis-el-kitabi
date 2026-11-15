import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))

def kayip(w, b, X, y, C):
    # sklearn'in amaci: C * sum(logloss) + 0.5 ||w||^2, n'e bolunmus
    p = np.clip(sigmoid(X @ w + b), 1e-12, 1 - 1e-12)
    ll = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return ll + np.sum(w * w) / (2 * C * len(y))

def lojistik_gd(X, y, C=1.0, eta=0.1, adim=100000):
    n, d = X.shape
    w, b = np.zeros(d), 0.0
    for _ in range(adim):
        p = sigmoid(X @ w + b)
        g_w = X.T @ (p - y) / n + w / (C * n)   # L2 terimi
        g_b = np.mean(p - y)                    # bias'a ceza yok
        w, b = w - eta * g_w, b - eta * g_b
    return w, b

veri = load_breast_cancer()
X_tr, _, y_tr, _ = train_test_split(
    veri.data, veri.target, test_size=0.2, stratify=veri.target,
    random_state=54)
mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)   # sadece egitim
Z = (X_tr - mu) / sd

# Gradyan denetimi (Bolum 50.3): analitik ve sonlu fark
rng = np.random.default_rng(0)
w0, b0 = rng.normal(size=30) * 0.1, 0.0
p = sigmoid(Z @ w0 + b0)
g = Z.T @ (p - y_tr) / len(y_tr) + w0 / (len(y_tr))
h = 1e-6
num = np.array([(kayip(w0 + h * e, b0, Z, y_tr, 1.0)
                 - kayip(w0 - h * e, b0, Z, y_tr, 1.0)) / (2 * h)
                for e in np.eye(30)])
print("gradyan denetimi, en buyuk fark:",
      "%.2e" % np.max(np.abs(g - num)))

w, b = lojistik_gd(Z, y_tr)   # 100000 adim: yakinsama
sk = LogisticRegression(C=1.0, max_iter=10000, tol=1e-10).fit(Z, y_tr)
print("max |w_sifirdan - w_sklearn| =",
      "%.2e" % np.max(np.abs(w - sk.coef_[0])))
print("|b_sifirdan - b_sklearn|     =",
      "%.2e" % abs(b - sk.intercept_[0]))
print("egitim dogrulugu (sifirdan):",
      round(np.mean(((Z @ w + b) > 0) == y_tr), 4))
print("egitim dogrulugu (sklearn): ",
      round(sk.score(Z, y_tr), 4))
