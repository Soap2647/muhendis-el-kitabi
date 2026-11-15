# -*- coding: utf-8 -*-
"""Bolum 61 - k-means: Lloyd, k-means++, dirsek, siluet.

Sifirdan yazilan kodlar sklearn ile karsilastirilir."""
import csv
import os

import numpy as np
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs, make_circles
from sklearn.metrics import adjusted_rand_score, silhouette_score

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def atama(X, C):
    d2 = ((X[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)
    return np.argmin(d2, axis=1)


def sse(X, C, y):
    return float(((X - C[y]) ** 2).sum())


def guncelle(X, y, C_eski):
    C = C_eski.copy()
    for j in range(len(C)):
        m = y == j
        if np.any(m):
            C[j] = X[m].mean(axis=0)
    return C


def lloyd(X, C0, en_fazla=300):
    """Lloyd algoritmasi. Her iterasyonda J = SSE kaydedilir."""
    C = C0.copy()
    J = []
    for _ in range(en_fazla):
        y = atama(X, C)
        J.append(sse(X, C, y))
        Cn = guncelle(X, y, C)
        if np.allclose(Cn, C):
            break
        C = Cn
    y = atama(X, C)
    return C, y, J


def kmeanspp(X, k, rng, yerel=None):
    """k-means++ baslangici (Arthur ve Vassilvitskii).

    yerel=None ise yerel deneme sayisi 2+ln(k) olur.
    """
    n = len(X)
    if yerel is None:
        yerel = 2 + int(np.log(k))
    secilen = [int(rng.integers(n))]
    d2 = ((X - X[secilen[0]]) ** 2).sum(axis=1)
    for _ in range(1, k):
        olas = d2 / d2.sum()
        adaylar = rng.choice(n, size=yerel, p=olas)
        en_pot, en_a, en_d2 = np.inf, None, None
        for a in adaylar:
            yeni = np.minimum(d2, ((X - X[a]) ** 2).sum(axis=1))
            if yeni.sum() < en_pot:
                en_pot, en_a, en_d2 = yeni.sum(), int(a), yeni
        secilen.append(en_a)
        d2 = en_d2
    return X[secilen].copy()


def rastgele_baslangic(X, k, rng):
    return X[rng.choice(len(X), size=k, replace=False)].copy()


def silhouette_sifirdan(X, y):
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2))
    kumeler = np.unique(y)
    s = np.zeros(len(X))
    for i in range(len(X)):
        ci = y[i]
        m = y == ci
        m[i] = False
        if not np.any(m):
            continue
        a = D[i, m].mean()
        b = min(D[i, y == cj].mean() for cj in kumeler if cj != ci)
        s[i] = (b - a) / max(a, b)
    return s.mean()


def bolum_a_amac_ve_yakinsama():
    """Blobs verisi, tek tohum: J her iterasyonda azalir mi?"""
    X, _ = make_blobs(n_samples=300, centers=3, cluster_std=1.0,
                      random_state=61)
    rng = np.random.default_rng(61)
    C0 = rastgele_baslangic(X, 3, rng)
    C, y, J = lloyd(X, C0)
    print("A) J iterasyonlari:", ["%.2f" % v for v in J])
    fark = np.diff(J)
    print("   J hic artmadi mi:", bool(np.all(fark <= 1e-9)))
    print("   yakinsama iterasyonu:", len(J))


def bolum_b_baslangic_dagilimi():
    """Rastgele ve k-means++ baslangiclari: 200 tohumda son SSE."""
    X, _ = make_blobs(n_samples=500, centers=[[0, 0], [3, 0], [6, 0],
                      [1.5, 3], [4.5, 3]], cluster_std=0.55,
                      random_state=61)
    satirlar = []
    for tohum in range(200):
        rng = np.random.default_rng(tohum)
        for ad, uret in [("rastgele", rastgele_baslangic),
                         ("kmeanspp", kmeanspp)]:
            C0 = uret(X, 5, rng)
            C, y, J = lloyd(X, C0)
            satirlar.append((ad, tohum, sse(X, C, y), len(J)))
    en_iyi = min(s[2] for s in satirlar)
    for ad in ["rastgele", "kmeanspp"]:
        v = np.array([s[2] for s in satirlar if s[0] == ad])
        it = np.array([s[3] for s in satirlar if s[0] == ad])
        kotu = np.mean(v > en_iyi + 1e-6)
        print("B) %-9s SSE min=%.2f medyan=%.2f" % (
            ad, v.min(), np.median(v)))
        print("   maks=%.2f en iyi olmayan=%%%.1f iter=%.1f" % (
            v.max(), 100 * kotu, it.mean()))
    yol = os.path.join(VERI, "b61_kmeans_init.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["yontem", "tohum", "sse", "iter"])
        for s in satirlar:
            w.writerow([s[0], s[1], "%.6f" % s[2], s[3]])
    print("   CSV yazildi")


def bolum_c_dirsek_siluet():
    """Dirsek (SSE) ve siluet; sifirdan siluet sklearn ile esit mi?"""
    X, _ = make_blobs(n_samples=600, centers=4, cluster_std=0.9,
                      random_state=61)
    satirlar = []
    fark_max = 0.0
    for k in range(1, 9):
        km = KMeans(n_clusters=k, n_init=10, random_state=61).fit(X)
        if k >= 2:
            sil = silhouette_score(X, km.labels_)
            sil_s = silhouette_sifirdan(X, km.labels_)
            fark_max = max(fark_max, abs(sil - sil_s))
        else:
            sil, sil_s = float("nan"), float("nan")
        satirlar.append((k, km.inertia_, sil, sil_s))
        s1 = "%.4f" % sil if k >= 2 else "  -  "
        s2 = "%.4f" % sil_s if k >= 2 else "  -  "
        print("C) k=%d inertia=%9.2f siluet=%s sifirdan=%s" % (
            k, km.inertia_, s1, s2))
    print("   en buyuk fark = %.1e" % fark_max)
    yol = os.path.join(VERI, "b61_dirsek.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["k", "inertia", "siluet"])
        for k, ine, sil, _ in satirlar:
            w.writerow([k, "%.4f" % ine,
                        "" if np.isnan(sil) else "%.6f" % sil])
    print("   CSV yazildi")


def bolum_d_halka_basarisizlik():
    """Halka verisinde k-means: ARI sifira yakin."""
    X, y = make_circles(n_samples=800, factor=0.4, noise=0.05,
                        random_state=61)
    km = KMeans(n_clusters=2, n_init=10, random_state=61).fit(X)
    ari = adjusted_rand_score(y, km.labels_)
    print("D) halka: k-means ARI = %.4f" % ari)
    yol = os.path.join(VERI, "b61_halka.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y", "gercek", "kmeans"])
        for p, g, e in zip(X, y, km.labels_):
            w.writerow(["%.5f" % p[0], "%.5f" % p[1], g, e])


if __name__ == "__main__":
    bolum_a_amac_ve_yakinsama()
    bolum_b_baslangic_dagilimi()
    bolum_c_dirsek_siluet()
    bolum_d_halka_basarisizlik()
