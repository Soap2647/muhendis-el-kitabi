# -*- coding: utf-8 -*-
"""Bolum 61 - Hiyerarsik kumeleme: baglanti turleri ve zincirleme."""
import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.datasets import make_blobs, make_moons
from sklearn.metrics import adjusted_rand_score


def kopru_verisi(seed=61):
    """Iki kume + aralarinda gurultulu bir kopru (30 ara nokta)."""
    X, y = make_blobs(n_samples=200, centers=[[0, 0], [6, 0]],
                      cluster_std=0.6, random_state=seed)
    rng = np.random.default_rng(seed)
    kopru = np.column_stack([rng.uniform(1.2, 4.8, 30),
                             rng.normal(0, 0.15, 30)])
    return np.vstack([X, kopru]), y, 200


def main():
    veriler = {
        "toplar (3 kume)": make_blobs(n_samples=300, centers=3,
                                      cluster_std=1.0,
                                      random_state=61),
        "ay (2 kume)": make_moons(n_samples=300, noise=0.06,
                                  random_state=61),
    }
    X, y, _ = kopru_verisi()
    etiket = np.r_[y, -np.ones(30)]
    veriler["kopru (2 kume + 30 ara nokta)"] = (X, etiket)

    for ad, (X, y) in veriler.items():
        k = 2 if "ay" in ad or "kopru" in ad else 3
        print("== %s (n=%d, k=%d)" % (ad, len(X), k))
        for bag in ["single", "complete", "average", "ward"]:
            m = AgglomerativeClustering(n_clusters=k,
                                        linkage=bag).fit(X)
            lab = m.labels_
            mask = y >= 0
            ari = adjusted_rand_score(y[mask], lab[mask])
            boy = np.sort(np.bincount(lab))[::-1]
            print("   %-9s ARI=%.4f  kume boyutlari=%s" % (
                bag, ari, boy.tolist()))
        km = KMeans(n_clusters=k, n_init=10, random_state=61).fit(X)
        mask = y >= 0
        ari_km = adjusted_rand_score(y[mask], km.labels_[mask])
        print("   k-means   ARI=%.4f" % ari_km)
        db = DBSCAN(eps=0.2, min_samples=5).fit(X)
        print("   DBSCAN(eps=0.2) ARI=%.4f  gurultu=%d" % (
            adjusted_rand_score(y[mask], db.labels_[mask]),
            np.sum(db.labels_ == -1)))


if __name__ == "__main__":
    main()
