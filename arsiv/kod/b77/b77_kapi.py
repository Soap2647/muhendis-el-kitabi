# -*- coding: utf-8 -*-
"""Veri dogrulama ve model kalite kapisi (sifirdan)."""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from b77_telemetri import OZELLIKLER, model_kur, uret

ARALIK = {"sicaklik": (-20, 80), "akim": (-5, 40),
          "gerilim": (3.0, 4.3), "dongu": (0, 5000)}
EKSIK_ESIK = 0.01
SEEDS = [11, 22, 33]


def veri_denetle(df):
    """Hata listesi doner; bos liste, parti gecti demektir."""
    hatalar = []
    for c in OZELLIKLER:
        if c not in df.columns:
            hatalar.append("eksik sutun: " + c)
        elif not pd.api.types.is_numeric_dtype(df[c]):
            hatalar.append("sayisal degil: " + c)
    for c, (lo, hi) in ARALIK.items():
        if c in df.columns:
            d = int(((df[c] < lo) | (df[c] > hi)).sum())
            if d:
                hatalar.append("%s aralik disi: %d" % (c, d))
    eksik = float(df.isna().mean().max())
    if eksik > EKSIK_ESIK:
        hatalar.append("eksik orani %.1f%%" % (100 * eksik))
    return hatalar


def fark_dagilimi(y, p_yeni, p_eski, B, rng):
    """Eslestirilmis onyukleme: AUC farkinin B ornekli dagilimi."""
    n = len(y)
    farklar = []
    while len(farklar) < B:
        i = rng.integers(0, n, n)
        if len(np.unique(y[i])) < 2:
            continue
        farklar.append(roc_auc_score(y[i], p_yeni[i])
                       - roc_auc_score(y[i], p_eski[i]))
    return np.array(farklar)


def kapi(y, p_yeni, p_eski, marj=0.01, B=1000, rng=None):
    """Yeni model, eskisinden marjdan fazla kotuyse reddedilir.

    Doner: (gecti, fark ortalamasi, %2,5 alt sinir)
    """
    rng = rng or np.random.default_rng(0)
    f = fark_dagilimi(y, p_yeni, p_eski, B, rng)
    alt = float(np.percentile(f, 2.5))
    return alt > -marj, float(f.mean()), alt


def aday_kur(ad, rng):
    """Dort adaydan birini egitir. Doner: (model, sutun dilimi)."""
    tum = slice(None)
    if ad == "daha_fazla_veri":
        X, y = uret(6000, rng)
    elif ad == "etiket_gurultulu":          # etiketlerin %30'u ters
        X, y = uret(2000, rng)
        ters = rng.random(len(y)) < 0.3
        y = np.where(ters, 1 - y, y)
    elif ad == "ozellik_eksik":             # sicaklik sutunu yok
        X, y = uret(2000, rng)
        X, tum = X[:, 1:], slice(1, None)
    else:                                   # yeni_tohum
        X, y = uret(2000, rng)
    return model_kur().fit(X, y), tum


if __name__ == "__main__":
    print("--- veri denetimi")
    df = pd.DataFrame(uret(500, np.random.default_rng(5))[0],
                      columns=OZELLIKLER)
    print("temiz parti     :", veri_denetle(df) or "gecti")
    print("gerilim yok     :",
          veri_denetle(df.drop(columns="gerilim")))
    b = df.copy()
    b.loc[:9, "akim"] = 999.0
    print("akim bozuk      :", veri_denetle(b))
    b = df.copy()
    b.loc[:19, "sicaklik"] = np.nan
    print("eksik deger     :", veri_denetle(b))
    print("--- kalite kapisi (3 tohum, B=1000)")
    print("tohum aday            fark     alt    karar")
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        Xt, yt = uret(2000, rng)
        taban = model_kur().fit(Xt, yt)
        Xs, ys = uret(2000, rng)            # tutulmus test kumesi
        p_eski = taban.predict_proba(Xs)[:, 1]
        for ad in ["yeni_tohum", "daha_fazla_veri",
                   "etiket_gurultulu", "ozellik_eksik"]:
            m, dil = aday_kur(ad, rng)
            p_yeni = m.predict_proba(Xs[:, dil])[:, 1]
            gecti, ort, alt = kapi(ys, p_yeni, p_eski,
                                   rng=np.random.default_rng(seed))
            print("%-5d %-17s %+.4f %+.4f  %s" %
                  (seed, ad, ort, alt, "KABUL" if gecti else "RED"))
