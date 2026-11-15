# -*- coding: utf-8 -*-
# b58_02_gd.py: gradyan inisi, SGD ve olceklemenin yakinsamaya etkisi
import csv
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
veri = load_diabetes()
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data, veri.target, test_size=0.25, random_state=58
)


def en_kucuk_kareler(A, y):
    return np.linalg.lstsq(A, y, rcond=None)[0]


def kayip(w, A, y):
    r = A @ w - y
    return np.mean(r * r)


def gradyan(w, A, y):
    return 2.0 / len(y) * A.T @ (A @ w - y)


def gd(A, y, eta, adim, w0=None):
    # Sabit adim boyu tam gradyan inisi; her adimin kaybini dondurur.
    w = np.zeros(A.shape[1]) if w0 is None else w0.copy()
    gecmis = []
    for _ in range(adim):
        w = w - eta * gradyan(w, A, y)
        gecmis.append(kayip(w, A, y))
    return w, np.array(gecmis)


def sgd(A, y, eta, epoch, grup=16, tohum=58):
    # Mini-batch SGD: her epoch karistirilir, her grup icin bir adim
    rng = np.random.default_rng(tohum)
    w = np.zeros(A.shape[1])
    n = len(y)
    for e in range(epoch):
        sira = rng.permutation(n)
        for k in range(0, n, grup):
            idx = sira[k : k + grup]
            r = A[idx] @ w - y[idx]
            w = w - eta * 2.0 / len(idx) * A[idx].T @ r
    return w


# ---- 1) Tam gradyan inisi: sabit adimi L'ye gore sec ----
A = np.hstack(
    [np.ones((len(X_tr), 1)), (X_tr - X_tr.mean(0)) / X_tr.std(0)]
)
w_star = en_kucuk_kareler(A, y_tr)
L = np.linalg.eigvalsh(2.0 / len(y_tr) * A.T @ A).max()
print(
    "L = lambda_max(2/n A^T A) = %.4f, eta = 1/L = %.4f" % (L, 1 / L)
)
w_gd, _ = gd(A, y_tr, eta=1.0 / L, adim=20000)
print(
    "20000 adim sonrasi |w_GD - w*|_inf = %.2e"
    % np.max(np.abs(w_gd - w_star))
)

# ---- 2) SGD: gurultulu ama ucuz adim ----
w_sgd = sgd(A, y_tr, eta=0.01, epoch=50)
print(
    "SGD (grup 16, eta 0.01, 50 epoch) |w_SGD - w*|_inf = %.3f"
    % np.max(np.abs(w_sgd - w_star))
)
print(
    "kayip: kapali form = %.2f, SGD = %.2f"
    % (kayip(w_star, A, y_tr), kayip(w_sgd, A, y_tr))
)

# ---- 3) Olceklemenin etkisi: ham ozniteliklerle GD ----
# Ham sutunlar (sklearn olcegi) ile standartlastirilmis sutunlar ayni
# minimizeri ima etmez; ama her iki problemin de kayip degeri vardir.
Araw = np.hstack([np.ones((len(X_tr), 1)), X_tr])
Ast = A
out = {}
for ad, M in (("ham", Araw), ("std", Ast)):
    ws = en_kucuk_kareler(M, y_tr)
    kstar = kayip(ws, M, y_tr)
    Lm = np.linalg.eigvalsh(2.0 / len(y_tr) * M.T @ M).max()
    _, gecmis = gd(M, y_tr, eta=1.0 / Lm, adim=20000)
    gap = gecmis - kstar
    out[ad] = gap
    sonuc = []
    for e in (1e-2, 1e-4):
        esik = np.where(gap < e)[0]
        sonuc.append(str(esik[0] + 1) if len(esik) else ">20000")
    print(
        "%s: cond(A)=%.1f, L=%.2f, adim (fark<1e-2)=%s, (<1e-4)=%s"
        % (ad, np.linalg.cond(M), Lm, sonuc[0], sonuc[1])
    )

# Kayip farki csv: adim, ham, std
with open(
    VERI + "b58_olcekleme.csv", "w", newline="", encoding="utf-8"
) as f:
    yaz = csv.writer(f)
    yaz.writerow(["adim", "ham_kayip_farki", "std_kayip_farki"])
    for k in range(0, 20000, 100):
        yaz.writerow(
            [
                k + 1,
                "%.6e" % max(out["ham"][k], 1e-16),
                "%.6e" % max(out["std"][k], 1e-16),
            ]
        )
print("csv yazildi:", VERI + "b58_olcekleme.csv")
