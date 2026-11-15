# -*- coding: utf-8 -*-
"""Ornek 2: veri hash'i degisince hangi deneyler gecersiz olur?"""
import os
import shutil

import numpy as np

from b77_takip import Takip, csv_oku, csv_yaz
from b77_telemetri import uret
from b77_veri import ekle

K = "calisma/ornek2"
HAM, OZEL = K + "/ham.csv", K + "/ozellik.csv"


def turet():
    """Turetilmis veri: sicaklik sensorunun tavanina kirpar."""
    X, y = csv_oku(HAM)
    X[:, 0] = np.clip(X[:, 0], 22, 38)
    csv_yaz(OZEL, X, y)
    return ekle(OZEL)


shutil.rmtree(K, ignore_errors=True)
os.makedirs(K)
csv_yaz(HAM, *uret(1500, np.random.default_rng(1)))
h1 = ekle(HAM)
o1 = turet()
soy = {o1: h1}                        # turev ozeti -> kaynak ozeti

takip = Takip(K + "/takip.db")
for C in [0.1, 1.0, 10.0]:
    d = takip.baslat("lojistik", o1, "calisma/kod")
    takip.parametre(d, {"C": C})
print("deneyler v1 turevi ile kaydedildi:", o1[:8])

# ham veriye bir satir eklenir
with open(HAM, "a", encoding="utf-8") as f:
    f.write("31.0,10.0,3.7,100,0\n")
h2 = ekle(HAM)
o2 = turet()
soy[o2] = h2
print("ham veri: %s -> %s" % (h1[:8], h2[:8]))
print("turev   : %s -> %s" % (o1[:8], o2[:8]))
print("v1 turevinin kaynagi hala guncel mi:", soy[o1] == h2)
print("guncel veriyle gecersiz deneyler:")
for did, ad in takip.gecersiz(o2):
    print("   deney %d (%s) veri=%s" % (did, ad, o1[:8]))
