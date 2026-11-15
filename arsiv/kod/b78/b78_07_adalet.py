# -*- coding: utf-8 -*-
"""Deney 7: adalet metrikleri ve esik takasi (sentetik veri)."""

import numpy as np
from sklearn.linear_model import LogisticRegression
from b78_ortak import SEEDS, csv_yaz


def veri_uret(n, rng):
    """Grup g in {0,1}; g=1 grubunun ozellikleri kayik (-0.6) ve
    temel pozitif orani daha dusuk (logit -0.8)."""
    g = (rng.uniform(size=n) < 0.3).astype(int)
    X = rng.normal(size=(n, 4)) + np.where(g[:, None] == 1, -0.6, 0.0)
    w = np.array([1.0, -0.8, 0.5, 0.3])
    logit = X @ w - 0.2 - 0.8 * g
    y = (rng.uniform(size=n) < 1 / (1 + np.exp(-logit))).astype(int)
    return X, y, g


def esik_tpr(s, y, hedef):
    """Pozitiflerin yaklasik 'hedef' oranini yakalayan esik."""
    return np.quantile(s[y == 1], 1 - hedef)


def olc(yhat, y, g):
    tpr = [yhat[(g == k) & (y == 1)].mean() for k in (0, 1)]
    fpr = [yhat[(g == k) & (y == 0)].mean() for k in (0, 1)]
    pr = [yhat[g == k].mean() for k in (0, 1)]
    return {
        "dogruluk": (yhat == y).mean(),
        "DP": abs(pr[0] - pr[1]),
        "EO": abs(tpr[0] - tpr[1]),
        "FPR": abs(fpr[0] - fpr[1]),
    }


def main():
    sonuc = {}
    for s in SEEDS:
        rng = np.random.default_rng(10 + s)
        X, y, g = veri_uret(6000, rng)
        tr, te = slice(0, 3000), slice(3000, 6000)
        clf = LogisticRegression(max_iter=1000).fit(X[tr], y[tr])
        p = clf.predict_proba(X[te])[:, 1]
        yt, gt = y[te], g[te]
        # 1) tek esik 0.5
        y1 = (p >= 0.5).astype(int)
        # 2) grup-bazli esik: iki grupta da TPR = global TPR (EO)
        tpr_hedef = (y1[yt == 1]).mean()
        y2 = np.zeros_like(y1)
        for k in (0, 1):
            m = gt == k
            e = esik_tpr(p[m], yt[m], tpr_hedef)
            y2[m] = (p[m] >= e).astype(int)
        # 3) grup-bazli esik: iki grupta da kabul orani esit (DP)
        oran = y1.mean()
        y3 = np.zeros_like(y1)
        for k in (0, 1):
            m = gt == k
            e = np.quantile(p[m], 1 - oran)
            y3[m] = (p[m] >= e).astype(int)
        for ad, yh in [
            ("tek esik 0.5", y1),
            ("EO esigi", y2),
            ("DP esigi", y3),
        ]:
            sonuc.setdefault(ad, []).append(olc(yh, yt, gt))
    print(
        "Kural            dogruluk      DP fark     EO fark"
        "     FPR fark"
    )
    satirlar = []
    for ad, lst in sonuc.items():
        v = {k: np.array([d[k] for d in lst]) for k in lst[0]}
        print(
            "%-15s  %.3f+-%.3f  %.3f+-%.3f  %.3f+-%.3f  %.3f+-%.3f"
            % (
                ad,
                v["dogruluk"].mean(),
                v["dogruluk"].std(),
                v["DP"].mean(),
                v["DP"].std(),
                v["EO"].mean(),
                v["EO"].std(),
                v["FPR"].mean(),
                v["FPR"].std(),
            )
        )
        satirlar.append(
            (
                ad,
                "%.4f" % v["dogruluk"].mean(),
                "%.4f" % v["DP"].mean(),
                "%.4f" % v["EO"].mean(),
                "%.4f" % v["FPR"].mean(),
            )
        )
    print("\n(3 veri tohumu; test n = 3000 her tohumda)")
    csv_yaz(
        "b78_adalet.csv",
        ["kural", "dogruluk", "dp_fark", "eo_fark", "fpr_fark"],
        satirlar,
    )


if __name__ == "__main__":
    main()
