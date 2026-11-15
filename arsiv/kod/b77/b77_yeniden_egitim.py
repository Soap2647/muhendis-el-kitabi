# -*- coding: utf-8 -*-
"""Yeniden egitim politikalari: maliyet simulasyonu (3 tohum).

Kayma kademeli: ortam 20. pencerede baslar (en fazla +6 C), kavram
kaymasi 40. pencerede baslar (katsayi en fazla +0,30). Etiketler 5
pencere gecikmeli gelir. Maliyet: yanlis negatif 5, yanlis pozitif 1,
her yeniden egitim 60 birim.
"""
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from b77_telemetri import uret

SEEDS = [11, 22, 33]
PENCERE = 300
W = 120
GECIKME = 5
FN, FP, EGITIM = 5.0, 1.0, 60.0
PERF_DUSUS = 0.05
POLITIKALAR = [("hic", None, False), ("her_10", 10, False),
               ("her_30", 30, False), ("tetikli", None, True)]


def ortam(w):
    return 6.0 * min(1.0, max(0.0, (w - 20) / 80))


def katsayi(w):
    return 0.30 * min(1.0, max(0.0, (w - 40) / 80))


def egit(X, y):
    sc = StandardScaler().fit(X)
    lr = LogisticRegression(max_iter=500)
    return sc, lr.fit(sc.transform(X), y)


def tahmin(model, X):
    sc, m = model
    return m.predict_proba(sc.transform(X))[:, 1]


def calistir(seed, periyot, tetikli):
    rng = np.random.default_rng(seed)
    model = egit(*uret(PENCERE * 10, rng))
    aucs, gecmis = [], []
    maliyet, yeniden = 0.0, 0
    ref_bas, ref_auc, bekleme = 0, None, -1
    for w in range(W):
        X, y = uret(PENCERE, rng, ortam(w), katsayi(w))
        p = tahmin(model, X)
        pred = p >= 0.5
        maliyet += FN * np.sum(~pred & (y == 1))
        maliyet += FP * np.sum(pred & (y == 0))
        aucs.append(roc_auc_score(y, p))
        gecmis.append((X, y))
        t = w - GECIKME    # etiketi simdi gelen pencere
        if ref_auc is None and t >= ref_bas + 9:
            ref_auc = float(np.mean(aucs[ref_bas:ref_bas + 10]))
        tetik = periyot is not None and w > 0 and w % periyot == 0
        if tetikli and ref_auc is not None and t >= ref_bas + 10 \
                and w >= bekleme and aucs[t] < ref_auc - PERF_DUSUS:
            tetik = True
        if tetik and t >= 5:                 # son 6 etiketli pencere
            Xs = np.vstack([g[0] for g in gecmis[t - 5:t + 1]])
            ys = np.concatenate([g[1] for g in gecmis[t - 5:t + 1]])
            model = egit(Xs, ys)
            maliyet += EGITIM
            yeniden += 1
            ref_bas, ref_auc, bekleme = w + 1, None, w + 10
    return maliyet, float(np.mean(aucs)), yeniden


if __name__ == "__main__":
    print("politika  maliyet (ort +- ss)  AUC (ort)  yeniden")
    for ad, periyot, tetikli in POLITIKALAR:
        s = [calistir(seed, periyot, tetikli) for seed in SEEDS]
        m = np.array([x[0] for x in s])
        print("%-9s %9.0f +- %-7.0f     %.4f      %.1f" %
              (ad, m.mean(), m.std(ddof=1),
               np.mean([x[1] for x in s]),
               np.mean([x[2] for x in s])))
