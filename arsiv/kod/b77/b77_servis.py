# -*- coding: utf-8 -*-
"""Egitim/servis carpikligi: ayni model, farkli on isleme.

Model egitimde dogru olceklenmis veriyle egitilir. Servis tarafinda
ayni boru hatti her varyantta biraz farkli calisir. Test kumesinde
AUC'nin ne kadar dustugunu olcuyoruz (3 tohum).
"""
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from b77_telemetri import uret

SEEDS = [11, 22, 33]
VARYANTLAR = ["dogru", "olcek_yok", "birim", "yuvarlama"]


def ozellik_donustur(ham, scaler):
    """Tek kaynak: egitim ve servis bu fonksiyonu cagirmali."""
    return scaler.transform(ham)


def servis_donusumu(ham, scaler, varyant):
    """Servis tarafindaki (bozuk olabilen) on isleme."""
    if varyant == "dogru":
        return ozellik_donustur(ham, scaler)
    if varyant == "olcek_yok":          # sicaklik olceklenmeden gecer
        x = scaler.transform(ham)
        x[:, 0] = ham[:, 0]
        return x
    if varyant == "birim":              # akim A yerine mA gider
        h = ham.copy()
        h[:, 1] *= 1000.0
        return ozellik_donustur(h, scaler)
    if varyant == "yuvarlama":  # gerilim 1 ondalik
        h = ham.copy()
        h[:, 2] = np.round(h[:, 2], 1)
        return ozellik_donustur(h, scaler)
    raise ValueError(varyant)


def deney(seed):
    rng = np.random.default_rng(seed)
    Xe, ye = uret(3000, rng)
    Xt, yt = uret(3000, rng)
    scaler = StandardScaler().fit(Xe)
    clf = LogisticRegression(max_iter=500).fit(
        ozellik_donustur(Xe, scaler), ye)
    sonuc = {}
    ref = clf.predict(ozellik_donustur(Xt, scaler))
    for v in VARYANTLAR:
        p = clf.predict_proba(servis_donusumu(Xt, scaler, v))[:, 1]
        sonuc[v] = (roc_auc_score(yt, p),
                    float(np.mean((p >= 0.5) != ref)))
    return sonuc


if __name__ == "__main__":
    sonuclar = {seed: deney(seed) for seed in SEEDS}
    os.makedirs("calisma/veri", exist_ok=True)
    with open("calisma/veri/b77_servis_auc.csv", "w",
              encoding="utf-8") as f:
        f.write("varyant,tohum,auc,tahmin_degisimi\n")
        for seed in SEEDS:
            for v in VARYANTLAR:
                a, dg = sonuclar[seed][v]
                f.write("%s,%d,%.6f,%.6f\n" % (v, seed, a, dg))
    print("varyant      AUC(11)  AUC(22)  AUC(33)  ort.   tahmin")
    for v in VARYANTLAR:
        aucs = [sonuclar[s][v][0] for s in SEEDS]
        dg = np.mean([sonuclar[s][v][1] for s in SEEDS])
        print("%-12s %.4f   %.4f   %.4f   %.4f  %6.1f%%" %
              (v, aucs[0], aucs[1], aucs[2], np.mean(aucs), 100 * dg))
