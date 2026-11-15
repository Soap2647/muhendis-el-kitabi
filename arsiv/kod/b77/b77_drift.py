# -*- coding: utf-8 -*-
"""Kayma (drift) tespiti: PSI, KS ve alan siniflandiricisi.

Sentetik bir akis uzerinde: 60. pencerede ortam kaymasi (kovaryat),
90. pencerede kavram kaymasi (etiket iliskisi) baslar. Etiketler 5
pencere gecikmeli gelir. Her yontem icin yanlis alarm orani ve tespit
gecikmesi 3 tohumla olculur.
"""
import csv
import os

import numpy as np
from scipy.stats import ks_2samp
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from b77_telemetri import model_kur, uret

SEEDS = [11, 22, 33]
PENCERE = 600           # her pencerede ornek sayisi
W = 120                 # toplam pencere
KAYMA_BAS = 60          # ortam kaymasi (kovaryat)
KAYMA_ARTIS = 2.0       # sicaklik dagiliminin otelenmesi (C)
KAVRAM_BAS = 90         # etiket iliskisi kaymasi
KAVRAM_ARTIS = 0.35     # sicaklik katsayisi 0,25 -> 0,60
GECIKME = 5             # etiketler 5 pencere sonra gelir
PSI_ESIK = 0.2
KS_ESIK = 0.01
ALAN_ESIK = 0.6
PERF_DUSUS = 0.05
YONTEMLER = ["a_psi", "a_ks", "a_alan", "a_perf"]


def psi(ref, yeni, kutu=10):
    """Populasyon Kararlilik Indeksi: referans kuantillerine gore."""
    kenar = np.quantile(ref, np.linspace(0, 1, kutu + 1))
    kenar[0], kenar[-1] = -np.inf, np.inf
    e = np.histogram(ref, kenar)[0] / len(ref)
    a = np.histogram(yeni, kenar)[0] / len(yeni)
    e, a = np.clip(e, 1e-4, None), np.clip(a, 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))


def alan_auc(ref, yeni, rng):
    """Referans mi, yeni pencere mi? Ayirt edilemiyorsa AUC ~ 0,5."""
    X = np.vstack([ref, yeni])
    y = np.r_[np.zeros(len(ref)), np.ones(len(yeni))]
    cv = StratifiedKFold(5, shuffle=True,
                         random_state=int(rng.integers(10**6)))
    m = make_pipeline(StandardScaler(),
                      LogisticRegression(max_iter=500))
    skor = cross_val_predict(m, X, y, cv=cv, method="predict_proba")
    return roc_auc_score(y, skor[:, 1])


def akis(seed):
    """Bir tohum icin W pencerelik akis; satir listesi doner."""
    rng = np.random.default_rng(seed)
    X0, y0 = uret(4000, rng)
    model = model_kur().fit(X0, y0)           # egitim dagilimi, donuk
    ref, _ = uret(2000, rng)     # referans: egitim dagilimi
    aucs, satirlar = [], []
    ref_auc = None
    for w in range(W):
        ortam = KAYMA_ARTIS if w >= KAYMA_BAS else 0.0
        kat = KAVRAM_ARTIS if w >= KAVRAM_BAS else 0.0
        X, y = uret(PENCERE, rng, ortam, kat)
        p = model.predict_proba(X)[:, 1]
        aucs.append(roc_auc_score(y, p))
        psis = [psi(ref[:, j], X[:, j]) for j in range(4)]
        kss = [ks_2samp(ref[:, j], X[:, j]).pvalue for j in range(4)]
        alan = alan_auc(ref[:PENCERE], X, rng)
        # Gecikmeli performans: pencere t'nin etiketi simdi geldi.
        t = w - GECIKME
        if ref_auc is None and t >= 9:
            ref_auc = float(np.mean(aucs[:10]))
        perf = ref_auc is not None and t >= 10 and \
            aucs[t] < ref_auc - PERF_DUSUS
        satirlar.append({
            "tohum": seed, "pencere": w,
            "psi_max": max(psis), "ks_min_p": min(kss),
            "alan_auc": alan, "auc": aucs[-1],
            "a_psi": max(psis) > PSI_ESIK,
            "a_ks": min(kss) < KS_ESIK,
            "a_alan": alan > ALAN_ESIK, "a_perf": perf})
    return satirlar


def ilk_alarm(satirlar, anahtar, bas, son=W):
    """[bas, son) araligindaki ilk alarm penceresi; yoksa None."""
    for s in satirlar:
        if bas <= s["pencere"] < son and s[anahtar]:
            return s["pencere"]
    return None


def yontem_ozeti(satirlar):
    """Yontem basina: yanlis alarm orani, iki tespit gecikmesi."""
    sonuc = []
    for yontem in YONTEMLER:
        once = [s[yontem] for s in satirlar
                if s["pencere"] < KAYMA_BAS]
        g1 = ilk_alarm(satirlar, yontem, KAYMA_BAS, KAVRAM_BAS)
        g2 = ilk_alarm(satirlar, yontem, KAVRAM_BAS)
        sonuc.append((yontem, float(np.mean(once)),
                      None if g1 is None else g1 - KAYMA_BAS,
                      None if g2 is None else g2 - KAVRAM_BAS))
    return sonuc


def yaz(yol, satirlar):
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)


if __name__ == "__main__":
    os.makedirs("calisma/veri", exist_ok=True)
    tum, tohum_satir = [], {}
    for seed in SEEDS:
        tohum_satir[seed] = akis(seed)
        tum.extend(tohum_satir[seed])
    yaz("calisma/veri/b77_drift_seri.csv", tum)

    print("tohum  AUC(0-59)  AUC(90-119)")
    for seed in SEEDS:
        s = tohum_satir[seed]
        a1 = np.mean([r["auc"] for r in s if r["pencere"] < 60])
        a2 = np.mean([r["auc"] for r in s if r["pencere"] >= 90])
        print("%-6d %.4f    %.4f" % (seed, a1, a2))

    print("yontem   yanlis-alarm  kayma-gecikme   kavram-gecikme")
    ozetler = {seed: yontem_ozeti(tohum_satir[seed])
               for seed in SEEDS}
    for k, yontem in enumerate(YONTEMLER):
        fa = np.mean([ozetler[s][k][1] for s in SEEDS])
        g1 = [ozetler[s][k][2] for s in SEEDS]
        g2 = [ozetler[s][k][3] for s in SEEDS]
        print("%-8s %-13.3f %-15s %s" % (yontem, fa, g1, g2))

    print("PSI esigi  yanlis-alarm  kayma-gecikme (3 tohum)")
    for esik in [0.05, 0.1, 0.2, 0.3]:
        fa, gec = [], []
        for seed in SEEDS:
            s = tohum_satir[seed]
            fa.append(np.mean([r["psi_max"] > esik for r in s
                               if r["pencere"] < KAYMA_BAS]))
            ilk = [r["pencere"] for r in s
                   if r["pencere"] >= KAYMA_BAS
                   and r["psi_max"] > esik]
            gec.append(ilk[0] - KAYMA_BAS if ilk else None)
        print("%-10.2f %-13.3f %s" % (esik, np.mean(fa), gec))
