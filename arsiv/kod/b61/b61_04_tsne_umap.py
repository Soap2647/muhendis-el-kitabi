# -*- coding: utf-8 -*-
"""Bolum 61 - t-SNE, UMAP ve guvenilirlik olcusu.

Ayrica saf gurultude t-SNE'nin urettigi sahte kumeleri gosterir.
"""
import csv
import os
import warnings

import numpy as np
from sklearn.cluster import KMeans
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE, trustworthiness
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def yaz(ad, satirlar, baslik):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(baslik)
        for s in satirlar:
            w.writerow(s)
    return yol


def tsne(X, p):
    return TSNE(n_components=2, perplexity=p, init="pca",
                learning_rate="auto", random_state=61)


def main():
    dg = load_digits()
    rng = np.random.default_rng(61)
    idx = rng.choice(len(dg.data), size=500, replace=False)
    X = dg.data[idx] / 16.0
    y = dg.target[idx]

    print("A) digits alt kumesi (500 x 64): perplexity etkisi")
    kl_satir = []
    for p in [5, 30, 50]:
        ts = tsne(X, p)
        Y = ts.fit_transform(X)
        kl_satir.append([p, "%.4f" % ts.kl_divergence_])
        guven = trustworthiness(X, Y, n_neighbors=10)
        print("   perp=%2d KL=%.4f guven(k=10)=%.4f" % (
            p, ts.kl_divergence_, guven))
        yaz("b61_tsne_digits_p%d.csv" % p,
            [["%.5f" % a, "%.5f" % b, c] for (a, b), c in zip(Y, y)],
            ["x", "y", "rakam"])
    yaz("b61_tsne_kl.csv", kl_satir, ["perplexity", "kl"])

    print("B) yontem karsilastirmasi (guvenilirlik, k=10)")
    Yp = PCA(n_components=2).fit_transform(X)
    g_pca = trustworthiness(X, Yp, n_neighbors=10)
    print("   PCA-2:    %.4f" % g_pca)
    Yt = tsne(X, 30).fit_transform(X)
    g_ts = trustworthiness(X, Yt, n_neighbors=10)
    print("   t-SNE-30: %.4f" % g_ts)
    try:
        import umap
        um = umap.UMAP(n_neighbors=15, min_dist=0.1, n_components=2,
                       random_state=61)
        Yu = um.fit_transform(X)
        print("   UMAP-15:  %.4f (umap-learn %s)" % (
            trustworthiness(X, Yu, n_neighbors=10), umap.__version__))
    except ImportError:
        print("   UMAP kurulu degil")

    print("C) gurultuda sahte kume: 500 x 50 saf Gauss")
    G = np.random.default_rng(61).normal(size=(500, 50))
    km_ham = KMeans(n_clusters=8, n_init=10, random_state=61).fit(G)
    print("   ham uzayda siluet (k=8) = %.4f" % silhouette_score(
        G, km_ham.labels_))
    Yg = tsne(G, 30).fit_transform(G)
    km_g = KMeans(n_clusters=8, n_init=10, random_state=61).fit(Yg)
    print("   t-SNE uzayinda siluet (k=8) = %.4f" % silhouette_score(
        Yg, km_g.labels_))
    yaz("b61_tsne_gurultu.csv",
        [["%.5f" % a, "%.5f" % b] for a, b in Yg], ["x", "y"])


if __name__ == "__main__":
    main()
