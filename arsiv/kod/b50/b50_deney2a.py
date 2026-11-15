# -*- coding: utf-8 -*-
# Ogrenme orani, zikzak ve optimizer karsilastirmasi (sabit tohum yok:
# deterministik yontemler).
import csv
import numpy as np
from b50_core import (kuad, kuad_g, kot, kot_g, rosen, rosen_g, gd,
                      momentum, nesterov, adagrad, rmsprop, adam)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
np.seterr(all="ignore")


def kalici(fk, esik=1e-6):
    """Eşiğin altına İNİP bir daha çıkmayan ilk adım (None: yok)."""
    kotu = np.where(np.asarray(fk) >= esik)[0]
    if len(kotu) == 0:
        return 0
    if kotu[-1] == len(fk) - 1:
        return None
    return int(kotu[-1]) + 1


# 1) Ogrenme orani uc durum: kuad, lambda_max = 20, kararli esik 2/20
print("kararli esik 2/lambda_max = 0.1")
yollar = {}
for eta in (0.005, 0.08, 0.11):
    y = gd(kuad_g, [1.0, 1.0], eta, 200)
    yollar[eta] = y
    fk = np.array([kuad(x) for x in y])
    adim = kalici(fk)
    print("eta=%.3f  f(50)=%.3e  f(200)=%.3e  adim(f<1e-6)=%s"
          % (eta, fk[50], fk[200], adim))

with open(VERI + "b50_ogrenme_orani.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["eta", "adim", "x", "y"])
    for eta, y in yollar.items():
        for k, p in enumerate(y[:60]):
            w.writerow(["%.3f" % eta, k,
                        "%.6f" % p[0], "%.6f" % p[1]])

