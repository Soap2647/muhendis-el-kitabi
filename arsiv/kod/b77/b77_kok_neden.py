# -*- coding: utf-8 -*-
"""Uretim hatasinda kok neden analizi: simule edilmis gunluk kayitlar.

Senaryo: 40. gunde cihazlarin %30'unda (firmware v2) sicaklik sensoru
bazen okunamiyor. Yeni seri hatti eksik degeri 0,0 yaziyor. Model bu
degeri sicaklik = 0 C sanip dusuk risk tahmin ediyor. Kok nedeni
bulmak icin dort kontrol yapiyoruz. Tohum: 7.
"""
import numpy as np
from sklearn.metrics import roc_auc_score

from b77_drift import psi
from b77_telemetri import model_kur, uret

SEED = 7
GUN = 60
KIRILMA = 40
GUNLUK = 300


def gunlukler():
    """Her satir bir kayit: gun, cihaz, firmware, ham girdi (4 sutun),
    gercek etiket ve model tahmini. Ham girdi, seri hattindan sonra
    kaydedilen degerdir."""
    rng = np.random.default_rng(SEED)
    egitim = model_kur().fit(*uret(4000, rng))
    satirlar = []
    for gun in range(GUN):
        X, y = uret(GUNLUK, rng)
        cihaz = rng.integers(0, 100, GUNLUK)
        v2 = cihaz >= 70
        bozuk = v2 & (gun >= KIRILMA) & (rng.random(GUNLUK) < 0.5)
        Xk = X.copy()
        Xk[bozuk, 0] = 0.0              # seri hattinin hatasi
        p = egitim.predict_proba(Xk)[:, 1]
        satirlar.append(np.column_stack([
            np.full(GUNLUK, gun), cihaz, v2, Xk, y, p]))
    return egitim, np.vstack(satirlar)


if __name__ == "__main__":
    egitim, D = gunlukler()
    gun, v2, sic = D[:, 0], D[:, 2] == 1, D[:, 3]
    y, p = D[:, 7], D[:, 8]
    once, sonra = gun < KIRILMA, gun >= KIRILMA
    ref = sic[once]

    print("1) Genel performans (AUC)")
    print("   40. gune kadar: %.4f" % roc_auc_score(y[once], p[once]))
    print("   40. gunden sonra: %.4f" %
          roc_auc_score(y[sonra], p[sonra]))

    print("2) Ortam kaymasi mi? (PSI, sicaklik, referans 0-39. gun)")
    print("   tum cihazlar : %.3f" % psi(ref, sic[sonra]))
    print("   yalniz v1    : %.3f" % psi(sic[once & ~v2],
                                       sic[sonra & ~v2]))
    print("   yalniz v2    : %.3f" % psi(sic[once & v2],
                                       sic[sonra & v2]))

    print("3) Sicaklik = 0,0 orani (sensor okunamadi isareti)")
    grup = [("v1, 0-39", once & ~v2), ("v2, 0-39", once & v2),
            ("v1, 40-59", sonra & ~v2), ("v2, 40-59", sonra & v2)]
    for ad, kume in grup:
        print("   %-10s : %.3f" % (ad, np.mean(sic[kume] == 0.0)))

    print("4) Cevrimdisi yeniden hesap farki (serving - offline)")
    yeniden = egitim.predict_proba(D[:, 3:7])[:, 1]
    print("   en buyuk fark: %.2e" % np.max(np.abs(yeniden - p)))

    print("5) Hata nerede? (40-59. gunler, gercek pozitifler)")
    poz = sonra & (y == 1)
    sifir = poz & (sic == 0.0)
    print("   sicaklik=0 olan pozitiflerde kacirma: %.3f" %
          np.mean(p[sifir] < 0.5))
    print("   diger pozitiflerde kacirma        : %.3f" %
          np.mean(p[poz & ~(sic == 0.0)] < 0.5))
    print("   referans (0-39. gun) kacirma      : %.3f" %
          np.mean(p[once & (y == 1)] < 0.5))
