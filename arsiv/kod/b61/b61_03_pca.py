# -*- coding: utf-8 -*-
"""Bolum 61 - PCA (sifirdan, kovaryans ve SVD), olcek, kernel PCA."""
import csv
import os

import numpy as np
from sklearn.datasets import load_digits, load_wine, make_circles
from sklearn.decomposition import PCA, KernelPCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def pca_sifirdan(X, k):
    mu = X.mean(axis=0)
    Z = X - mu
    S = Z.T @ Z / (len(X) - 1)
    lam, V = np.linalg.eigh(S)
    idx = np.argsort(lam)[::-1]
    lam, V = lam[idx], V[:, idx]
    return mu, V[:, :k], lam


def pca_svd_sifirdan(X, k):
    mu = X.mean(axis=0)
    Z = X - mu
    _, s, Vt = np.linalg.svd(Z, full_matrices=False)
    return mu, Vt[:k].T, s ** 2 / (len(X) - 1)


def yeniden_yapilandir(X, mu, V):
    return (X - mu) @ V @ V.T + mu


def bolum_a_esdegerlik():
    dg = load_digits()
    X = dg.data
    mu, V, lam = pca_sifirdan(X, 64)
    mu2, V2, lam2 = pca_svd_sifirdan(X, 64)
    sk = PCA(n_components=64).fit(X)
    print("A) digits (1797 x 64): kovaryans, SVD, sklearn")
    print("   max|ozdeger_cov - sigma^2/(n-1)| = %.2e" % np.max(
        np.abs(lam - lam2)))
    print("   max|oran_cov - sklearn oran| = %.2e" % np.max(
        np.abs(lam / lam.sum() - sk.explained_variance_ratio_)))
    cos = np.abs(np.sum(V[:, :5] * sk.components_[:5].T, axis=0))
    print("   ilk 5 bilesen |cos| (sklearn):", np.round(cos, 6))
    oran = lam / lam.sum()
    kum = np.cumsum(oran)
    print("   ilk 1 bilesen = %.4f, ilk 2 = %.4f" % (kum[0], kum[1]))
    k90 = np.searchsorted(kum, 0.90) + 1
    k95 = np.searchsorted(kum, 0.95) + 1
    print("   90%% icin k = %d, 95%% icin k = %d" % (k90, k95))
    for k in [2, 8, 16, 32]:
        m, Vk, _ = pca_sifirdan(X, k)
        R = yeniden_yapilandir(X, m, Vk)
        mse = np.mean((X - R) ** 2)
        print("   k=%2d kum.varyans=%.4f MSE=%.4f" % (
            k, kum[k - 1], mse))
    yol = os.path.join(VERI, "b61_pca_varyans.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["k", "aciklanan", "kumulatif"])
        for i in range(64):
            w.writerow([i + 1, "%.6f" % oran[i], "%.6f" % kum[i]])
    m, V2d, _ = pca_sifirdan(X, 2)
    Y = (X - m) @ V2d
    yol2 = os.path.join(VERI, "b61_pca_digits2d.csv")
    with open(yol2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y", "rakam"])
        for p, t in zip(Y, dg.target):
            w.writerow(["%.5f" % p[0], "%.5f" % p[1], t])
    print("   CSV yazildi")


def bolum_b_merkezleme_ve_olcek():
    X = load_digits().data
    Xm = X + 3.0                         # ortalama kaymasi, veri ayni
    _, V_c, _ = pca_sifirdan(Xm, 1)
    _, s, Vt = np.linalg.svd(Xm, full_matrices=False)
    _, V_t, _ = pca_sifirdan(X, 1)
    print("B) merkezlemenin onemi (digits + 3 ofset)")
    print("   merkezli PC1 - merkezsiz SVD-1: |cos| = %.4f" % abs(
        V_c[:, 0] @ Vt[0]))
    print("   merkezli PC1 - orijinal PC1:    |cos| = %.4f" % abs(
        V_c[:, 0] @ V_t[:, 0]))
    print("   merkezsiz SVD-1 - orijinal PC1: |cos| = %.4f" % abs(
        Vt[0] @ V_t[:, 0]))
    rng = np.random.default_rng(61)
    Z = rng.normal(size=(1000, 2)) * [3.0, 0.5]
    a = 0.4
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    Y = Z @ R.T + np.array([20.0, 0.0])
    _, s2, Vt2 = np.linalg.svd(Y, full_matrices=False)
    _, Vc2, _ = pca_sifirdan(Y, 1)
    dogru = R[:, 0]
    print("   sentetik (ort=(20,0)), dogru yon:")
    print("   merkezli PC1 |cos| = %.4f" % abs(Vc2[:, 0] @ dogru))
    print("   merkezsiz SVD-1 |cos| = %.4f" % abs(Vt2[0] @ dogru))
    w = load_wine()
    Xw = w.data
    ham = PCA(n_components=2).fit(Xw)
    yuk = np.abs(ham.components_[0])
    print("   wine ham: PC1 orani=%.4f" %
          ham.explained_variance_ratio_[0])
    print("   en buyuk yuk:", w.feature_names[int(np.argmax(yuk))])
    Xs = StandardScaler().fit_transform(Xw)
    olcekli = PCA(n_components=2).fit(Xs)
    print("   wine olcekli: PC1 orani=%.4f" %
          olcekli.explained_variance_ratio_[0])


def bolum_c_beyazlatma():
    X = load_digits().data
    Y = PCA(n_components=5, whiten=True).fit_transform(X)
    print("C) whitening: ilk 5 bilesenin varyansi (1'e yakin)")
    print("   diag =", np.round(np.var(Y, axis=0, ddof=1), 4))


def bolum_d_kernel_pca():
    X, y = make_circles(n_samples=400, factor=0.3, noise=0.05,
                        random_state=61)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                          stratify=y, random_state=61)
    lin = PCA(n_components=2).fit(Xtr)
    m = LogisticRegression(max_iter=1000).fit(lin.transform(Xtr), ytr)
    print("D) halka: lojistik regresyon, test dogrulugu")
    print("   dogrusal PCA (2 bilesen): %.4f" % m.score(
        lin.transform(Xte), yte))
    for g in [1.0, 4.0, 10.0]:
        kp = KernelPCA(n_components=2, kernel="rbf", gamma=g).fit(Xtr)
        m2 = LogisticRegression(max_iter=1000)
        m2.fit(kp.transform(Xtr), ytr)
        print("   RBF kernel PCA gamma=%-4.1f: %.4f" % (
            g, m2.score(kp.transform(Xte), yte)))


if __name__ == "__main__":
    bolum_a_esdegerlik()
    bolum_b_merkezleme_ve_olcek()
    bolum_c_beyazlatma()
    bolum_d_kernel_pca()
