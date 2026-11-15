# -*- coding: utf-8 -*-
"""Bolum 61 - Anomali tespiti: istatistiksel ve yogunluk yontemleri.

Isolation Forest sifirdan yazilmistir.
"""
import csv
import os
import warnings

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import LocalOutlierFactor

warnings.filterwarnings("ignore")
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
EULER = 0.5772156649


def c_n(n):
    if n <= 1:
        return 0.0
    return 2 * (np.log(n - 1) + EULER) - 2 * (n - 1) / n


def agac_kur(X, derinlik, azami, rng):
    n = len(X)
    if derinlik >= azami or n <= 1:
        return ("yaprak", n)
    j = int(rng.integers(X.shape[1]))
    lo, hi = X[:, j].min(), X[:, j].max()
    if lo == hi:
        return ("yaprak", n)
    s = rng.uniform(lo, hi)
    sol = X[X[:, j] < s]
    sag = X[X[:, j] >= s]
    return ("dal", j, s, agac_kur(sol, derinlik + 1, azami, rng),
            agac_kur(sag, derinlik + 1, azami, rng))


def yol_uzunlugu(x, dugum, derinlik=0):
    if dugum[0] == "yaprak":
        return derinlik + c_n(dugum[1])
    _, j, s, sol, sag = dugum
    return yol_uzunlugu(x, sol if x[j] < s else sag, derinlik + 1)


class IsolationForestSifirdan:
    def __init__(self, agac=100, psi=128, seed=61):
        self.agac, self.psi, self.seed = agac, psi, seed

    def fit(self, X):
        rng = np.random.default_rng(self.seed)
        azami = int(np.ceil(np.log2(self.psi)))
        self.agaclar = []
        for _ in range(self.agac):
            m = min(self.psi, len(X))
            alt = X[rng.choice(len(X), size=m, replace=False)]
            self.agaclar.append(agac_kur(alt, 0, azami, rng))
        self.c = c_n(min(self.psi, len(X)))
        return self

    def skor(self, X):
        """Anomali skoru 2^(-E[h]/c(psi)); 1'e yakin = anomali."""
        ort = np.array([
            np.mean([yol_uzunlugu(x, t) for t in self.agaclar])
            for x in X])
        return 2.0 ** (-ort / self.c)


def korelasyonlu_veri(rho, n, rng):
    S = np.array([[1.0, rho], [rho, 1.0]])
    return rng.multivariate_normal([0.0, 0.0], S, size=n)


def mahal_kare(X, mu, S):
    Si = np.linalg.inv(S)
    f = X - mu
    return np.einsum("ni,ij,nj->n", f, Si, f)


def bolum_a_korelasyon_tuzagi():
    rng = np.random.default_rng(61)
    Xe = korelasyonlu_veri(0.9, 2000, rng)
    Xt_n = korelasyonlu_veri(0.9, 1000, rng)
    # ayni marjinaller, ters korelasyon
    Xt_a = korelasyonlu_veri(-0.9, 60, rng)
    Xt = np.vstack([Xt_n, Xt_a])
    y = np.r_[np.zeros(len(Xt_n)), np.ones(len(Xt_a))].astype(int)
    print("A) 2B, ayni marjinal, ters korelasyon anomalisi")
    print("   egitim: 2000 normal (rho=0,9)")
    print("   test: 1000 normal + 60 anomali")
    mu = Xe.mean(axis=0)
    S = np.cov(Xe.T)
    sd = Xe.std(axis=0)
    z_max = np.max(np.abs((Xt - mu) / sd), axis=1)
    okl = np.linalg.norm(Xt - mu, axis=1)
    mah = np.sqrt(mahal_kare(Xt, mu, S))
    pca = PCA(n_components=1).fit(Xe)
    C = pca.components_
    res = np.linalg.norm((Xt - mu) - (Xt - mu) @ C.T @ C, axis=1)
    print("   AUC tek-degiskenli max|z| = %.4f" % roc_auc_score(
        y, z_max))
    print("   AUC Oklid uzakligi        = %.4f" % roc_auc_score(
        y, okl))
    print("   AUC Mahalanobis           = %.4f" % roc_auc_score(
        y, mah))
    print("   AUC PCA artigi (1 bilesen) = %.4f" % roc_auc_score(
        y, res))
    lof = LocalOutlierFactor(n_neighbors=20, novelty=True).fit(Xe)
    print("   AUC LOF (novelty)         = %.4f" % roc_auc_score(
        y, -lof.score_samples(Xt)))
    gm = GaussianMixture(n_components=1, covariance_type="full",
                         random_state=61).fit(Xe)
    print("   AUC Gauss (GMM k=1) -llh  = %.4f" % roc_auc_score(
        y, -gm.score_samples(Xt)))
    print("   Mahalanobis: normal ort=%.3f, anomali ort=%.3f" % (
        mah[y == 0].mean(), mah[y == 1].mean()))
    return Xe, Xt, y, mu, S


def bolum_b_isolation_forest(Xe, Xt, y):
    print("B) Isolation Forest: sklearn ve sifirdan")
    sk = IsolationForest(n_estimators=200, max_samples=256,
                         random_state=61).fit(Xe)
    s_sk = -sk.score_samples(Xt)
    print("   AUC sklearn IF  = %.4f" % roc_auc_score(y, s_sk))
    sf = IsolationForestSifirdan(agac=100, psi=256, seed=61).fit(Xe)
    s_sf = sf.skor(Xt)
    print("   AUC sifirdan IF = %.4f" % roc_auc_score(y, s_sf))
    ap_sk = average_precision_score(y, s_sk)
    ap_sf = average_precision_score(y, s_sf)
    print("   AP sklearn = %.4f, sifirdan = %.4f" % (ap_sk, ap_sf))
    print("   normal ort skor = %.4f" % s_sf[y == 0].mean())
    print("   anomali ort skor = %.4f" % s_sf[y == 1].mean())
    return sf


def bolum_c_esik_butcesi(Xe, Xt, y, mu, S):
    print("C) esik ve yanlis alarm butcesi (%99 normal)")
    d_e = mahal_kare(Xe, mu, S)
    esik = np.quantile(d_e, 0.99)
    d_t = mahal_kare(Xt, mu, S)
    alarm = d_t > esik
    print("   Mahalanobis^2 esigi = %.4f" % esik)
    print("   (ki-kare 2 serb., %99 = 9,2103)")
    fa = alarm[y == 0].mean()
    tp = alarm[y == 1].mean()
    print("   normal test: yanlis alarm = %.4f" % fa)
    print("   anomali tespit            = %.4f" % tp)
    kayip = np.sum(~alarm & (y == 1))
    print("   kacan anomali = %d / %d" % (kayip, np.sum(y == 1)))
    yol = os.path.join(VERI, "b61_anomali_nokta.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y", "etiket"])
        for p, e in zip(Xt, y):
            w.writerow(["%.5f" % p[0], "%.5f" % p[1], int(e)])
    gx = np.linspace(-4, 4, 81)
    gx, gy = np.meshgrid(gx, gx)
    G = np.column_stack([gx.ravel(), gy.ravel()])
    sf = IsolationForestSifirdan(agac=100, psi=256, seed=61).fit(Xe)
    s_if = sf.skor(G)
    m_g = mahal_kare(G, mu, S)
    oklid = np.linalg.norm(G, axis=1)
    yol2 = os.path.join(VERI, "b61_anomali_harita.csv")
    with open(yol2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y", "mahal2", "if_skor", "oklid"])
        for a, b, c, d, e in zip(G[:, 0], G[:, 1], m_g, s_if, oklid):
            w.writerow(["%.4f" % a, "%.4f" % b, "%.5f" % c,
                        "%.5f" % d, "%.5f" % e])
    print("   CSV yazildi")


if __name__ == "__main__":
    Xe, Xt, y, mu, S = bolum_a_korelasyon_tuzagi()
    bolum_b_isolation_forest(Xe, Xt, y)
    bolum_c_esik_butcesi(Xe, Xt, y, mu, S)
