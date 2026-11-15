# -*- coding: utf-8 -*-
"""Bolum 71 - Iki geri getirme sistemi arasindaki farkin bootstrap
testi."""

import numpy as np

from g01_parca import SORULAR
from g02_geri_getirme import alaka_kumeleri, degerlendir, parcalar

B = 10000


def karzi(rr):
    rr = np.array(rr, dtype=float)
    return np.where(np.isinf(rr), 0.0, 1.0 / rr)


def esli_bootstrap(a, b, seed=71):
    """a, b: sorgu basina olcumler (ayni sorgular). Ortalama farkinin
    %95 guven araligi ve farkin <= 0 olma orani (yaklasik p)."""
    d = np.asarray(a) - np.asarray(b)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(B, len(d)))
    ort = d[idx].mean(axis=1)
    lo, hi = np.percentile(ort, [2.5, 97.5])
    p = float(np.mean(ort <= 0))
    return float(d.mean()), float(lo), float(hi), p


if __name__ == "__main__":
    pl = parcalar("baslik", 600)
    rel = alaka_kumeleri(pl)
    _, yontemler, ndcg = degerlendir(pl, rel, "baslik", 600)
    rr = {k: karzi(v) for k, v in yontemler.items()}
    print(
        "sorgu sayisi:", len(SORULAR), " bootstrap:", B, " seed: 71"
    )
    cift = [
        ("BM25 kök5", "BM25 ham"),
        ("BM25 kök5", "melez RRF"),
        ("melez RRF", "LSA (128)"),
        ("BM25 kök5", "rastgele"),
    ]
    print(
        "%-28s %8s %8s %8s %6s"
        % ("fark (MRR)", "ort", "alt", "ust", "p~")
    )
    for a, b in cift:
        m, lo, hi, p = esli_bootstrap(rr[a], rr[b])
        print(
            "%-28s %8.3f %8.3f %8.3f %6.3f"
            % (a + " - " + b, m, lo, hi, p)
        )
    print("sorgu basina ters sira (BM25 kök5):")
    deger = ["%.2f" % x for x in rr["BM25 kök5"]]
    for i in range(0, len(deger), 12):
        print(" ".join(deger[i:i + 12]))
