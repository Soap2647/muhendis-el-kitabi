# -*- coding: utf-8 -*-
"""Bolum 61 - DBSCAN, GMM ve EM (sifirdan), BIC."""
import csv
import os

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.datasets import make_blobs, make_circles
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def dbscan(X, eps, min_pts):
    """Yigin tabanli DBSCAN. Gurultu = -1.

    Komsu sayisi noktanin kendisini de icerir; bu, sklearn'deki
    min_samples tanimiyla aynidir.
    """
    n = len(X)
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2))
    komsu = [np.where(D[i] <= eps)[0] for i in range(n)]
    cekirdek = np.array([len(k) >= min_pts for k in komsu])
    etiket = np.full(n, -1)
    c = 0
    for i in range(n):
        if etiket[i] != -1 or not cekirdek[i]:
            continue
        etiket[i] = c
        yigin = [i]
        while yigin:
            p = yigin.pop()
            if not cekirdek[p]:
                continue
            for q in komsu[p]:
                if etiket[q] == -1:
                    etiket[q] = c
                    yigin.append(q)
        c += 1
    return etiket, cekirdek


def gauss_pdf(X, mu, S):
    d = X.shape[1]
    Si = np.linalg.inv(S)
    fark = X - mu
    q = np.einsum("ni,ij,nj->n", fark, Si, fark)
    payda = np.sqrt(((2 * np.pi) ** d) * np.linalg.det(S))
    return np.exp(-0.5 * q) / payda


def em(X, pi, mu, S, iters=60, reg=1e-6):
    """Tam kovaryansli GMM icin EM.

    Her E adiminda log-olabilirlik kaydedilir.
    """
    k, d = len(pi), X.shape[1]
    llh = []
    for _ in range(iters):
        N = np.column_stack([pi[j] * gauss_pdf(X, mu[j], S[j])
                             for j in range(k)])
        tot = N.sum(axis=1)
        llh.append(float(np.log(tot).sum()))
        R = N / tot[:, None]
        Nk = R.sum(axis=0)
        pi = Nk / len(X)
        mu = (R.T @ X) / Nk[:, None]
        for j in range(k):
            fark = X - mu[j]
            S[j] = (R[:, j, None] * fark).T @ fark / Nk[j]
            S[j] += reg * np.eye(d)
    tot = sum(pi[j] * gauss_pdf(X, mu[j], S[j]) for j in range(k))
    llh.append(float(np.log(tot).sum()))
    return pi, mu, S, llh


def bolum_a_dbscan():
    X, y = make_circles(n_samples=800, factor=0.4, noise=0.05,
                        random_state=61)
    print("A) DBSCAN (sifirdan) eps ve minPts taramasi")
    for eps in [0.08, 0.12, 0.15, 0.25]:
        lab, cek = dbscan(X, eps, 5)
        sk = DBSCAN(eps=eps, min_samples=5).fit(X).labels_
        kume = len(set(lab)) - (1 if -1 in lab else 0)
        print("   eps=%.2f kume=%d gurultu=%3d ARI(gercek)=%.4f"
              % (eps, kume, np.sum(lab == -1),
                 adjusted_rand_score(y, lab)))
        print("   ARI(sklearn ile)=%.4f"
              % adjusted_rand_score(sk, lab))
    lab, cek = dbscan(X, 0.15, 5)
    yol = os.path.join(VERI, "b61_dbscan_halka.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y", "etiket", "cekirdek"])
        for p, e, c in zip(X, lab, cek):
            w.writerow(["%.5f" % p[0], "%.5f" % p[1], e, int(c)])
    print("   CSV yazildi")


def uc_kume_veri(seed=61):
    X, y = make_blobs(n_samples=600, centers=[[0, 0], [5, 1], [2, 5]],
                      random_state=seed)
    X = X @ np.array([[0.6, -0.8], [0.8, 0.6]])
    X[y == 1] = X[y == 1] @ np.array([[1.6, 0.0], [0.0, 0.5]])
    return X, y


def bolum_b_em():
    X, y = uc_kume_veri()
    km = KMeans(n_clusters=3, n_init=10, random_state=61).fit(X)
    mu0 = np.array([X[km.labels_ == j].mean(axis=0)
                    for j in range(3)])
    S0 = [np.cov(X[km.labels_ == j].T) for j in range(3)]
    pi0 = np.array([np.mean(km.labels_ == j) for j in range(3)])
    S_kopya = [s.copy() for s in S0]
    pi, mu, S, llh = em(X, pi0.copy(), mu0.copy(), S_kopya)
    print("B) EM (sifirdan), 2B, 3 bilesen")
    print("   llh ilk = %.4f son = %.4f iter = %d" % (
        llh[0], llh[-1], len(llh) - 1))
    fark = np.diff(llh)
    print("   llh hic azalmadi mi:", bool(np.all(fark >= -1e-9)))
    print("   en buyuk artis = %.4f" % fark.max())
    precs = np.array([np.linalg.inv(s) for s in S0])
    g = GaussianMixture(n_components=3, covariance_type="full",
                        weights_init=pi0, means_init=mu0,
                        precisions_init=precs, max_iter=200,
                        tol=1e-8, reg_covar=1e-6).fit(X)
    print("   sklearn ortalama llh = %.6f" % g.score(X))
    print("   scratch  ortalama llh = %.6f" % (llh[-1] / len(X)))
    print("   mu(scratch):\n", np.round(mu, 3))
    print("   mu(sklearn):\n", np.round(g.means_, 3))
    yol = os.path.join(VERI, "b61_em_llh.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["iter", "llh"])
        for i, v in enumerate(llh):
            w.writerow([i, "%.6f" % v])
    yol2 = os.path.join(VERI, "b61_gmm_bilesen.csv")
    with open(yol2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y", "kume"])
        R = np.column_stack([pi[j] * gauss_pdf(X, mu[j], S[j])
                             for j in range(3)])
        R = R / R.sum(axis=1, keepdims=True)
        for p, r in zip(X, R.argmax(axis=1)):
            w.writerow(["%.5f" % p[0], "%.5f" % p[1], int(r)])
    with open(os.path.join(VERI, "b61_gmm_parametre.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bilesen", "pi", "mu_x", "mu_y",
                    "s11", "s12", "s22"])
        for j in range(3):
            w.writerow([j, "%.6f" % pi[j], "%.6f" % mu[j][0],
                        "%.6f" % mu[j][1], "%.6f" % S[j][0, 0],
                        "%.6f" % S[j][0, 1], "%.6f" % S[j][1, 1]])
    return X


def bolum_c_bic(X):
    print("C) BIC ile bilesen sayisi (sklearn, n_init=5)")
    n, d = X.shape
    for k in range(1, 7):
        g = GaussianMixture(n_components=k, covariance_type="full",
                            n_init=5, random_state=61,
                            max_iter=300).fit(X)
        p = (k - 1) + k * d + k * d * (d + 1) // 2
        bic_el = -2 * g.score(X) * n + p * np.log(n)
        print("   k=%d BIC=%9.2f formul=%9.2f p=%d" % (
            k, g.bic(X), bic_el, p))


if __name__ == "__main__":
    bolum_a_dbscan()
    X = bolum_b_em()
    bolum_c_bic(X)
