# -*- coding: utf-8 -*-
"""Sentetik batarya telemetrisi (kisa, kontrollu bir veri kaynagi).

Her satir bir olcum penceresi: sicaklik, akim, gerilim, dongu sayisi.
Etiket: pencerede ariza var (1) ya da yok (0). Gercek kural bilindigi
icin kaymanin etkisini kontrollu olarak olcebiliriz.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

OZELLIKLER = ["sicaklik", "akim", "gerilim", "dongu"]
ESIK = 2.6   # risk bu degeri asarsa ariza; oran yaklasik %10


def uret(n, rng, ortam_kaymasi=0.0, katsayi_kaymasi=0.0):
    """n ornek uretir. Doner: X (n x 4), y (n,)

    ortam_kaymasi:  sicaklik dagiliminin otelenmesi (kovaryat).
                     Kural degismez, yalnizca girdi dagilimi kayar.
    katsayi_kaymasi: sicakligin arizaya etkisinin degismesi
                     (kavram kaymasi). p(y|x) degisir.
    """
    sicaklik = rng.normal(30.0, 4.0, n) + ortam_kaymasi
    akim = rng.normal(10.0, 3.0, n)
    gerilim = rng.normal(3.7, 0.05, n)
    dongu = rng.uniform(0, 1000, n)
    risk = ((0.25 + katsayi_kaymasi) * (sicaklik - 30.0)
            + 0.12 * (akim - 10.0)
            - 30.0 * (gerilim - 3.7)
            + 0.0015 * (dongu - 500.0)
            + rng.normal(0.0, 1.0, n))
    y = (risk > ESIK).astype(int)
    X = np.column_stack([sicaklik, akim, gerilim, dongu])
    return X, y


def model_kur(C=1.0):
    """Olcekleme + lojistik regresyon. Tek bir boru hatti."""
    return make_pipeline(StandardScaler(),
                         LogisticRegression(C=C, max_iter=1000))
