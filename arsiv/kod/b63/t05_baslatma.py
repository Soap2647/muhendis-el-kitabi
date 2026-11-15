# -*- coding: utf-8 -*-
"""Bölüm 63.9: ağırlık başlatma, simetri ve aktivasyon dağılımı."""
import csv, os
import numpy as np
from sinir import (VERI, ReLU, Tanh, Dogrusal, Ag, SoftmaxCE, mlp,
                   ileri_geri, sgd_adim, veri_yukle, dogruluk)

YONTEMLER = ["sifir", "kucuk", "buyuk", "xavier", "he"]


def dagilim(yontem, X):
    ag = mlp([64, 128, 128, 128, 10], ReLU, np.random.default_rng(0),
             yontem)
    satir, H = [], X
    for k in ag.katmanlar:
        H = k.ileri(H)
        if isinstance(k, ReLU):          # her gizli katmandan sonra
            satir.append((np.std(H), float(np.mean(H == 0))))
    return satir


def simetri_deneyi(w1, w2, adim=200, lr=0.1):
    (Xt, Yt, yt), (_, _, _), (Xs, _, ys) = veri_yukle()
    rng = np.random.default_rng(1)
    ag = Ag([Dogrusal(64, 16, rng), Tanh(), Dogrusal(16, 10, rng)])
    ag.katmanlar[0].W[:] = w1(ag.katmanlar[0].W.shape)
    ag.katmanlar[2].W[:] = w2(ag.katmanlar[2].W.shape)
    kayip = SoftmaxCE()
    for _ in range(adim):
        ileri_geri(ag, kayip, Xt, Yt)
        sgd_adim(ag, lr)
    W1 = ag.katmanlar[0].W
    fark = np.max(np.abs(W1 - W1[:, [0]]))   # gizli birimler arası
    return fark, dogruluk(ag, Xs, ys), kayip.ileri(ag.ileri(Xt), Yt)


if __name__ == "__main__":
    (Xt, _, _), _, _ = veri_yukle()
    satirlar = []
    print("Katman bazında std, sıfır oranı (ReLU):")
    for y in YONTEMLER:
        d = dagilim(y, Xt)
        print("%-7s " % y + "  ".join(
            "%.2e/%.2f" % (s, z) for s, z in d))
        for i, (s, z) in enumerate(d):
            satirlar.append([y, i + 1, s, z])
    with open(os.path.join(VERI, "b63_baslatma_dagilim.csv"), "w",
              newline="", encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(["baslatma", "gizli_katman", "std",
                     "sifir_orani"])
        yz.writerows(satirlar)
    sabit = lambda s: np.full(s, 0.1)
    sifir = lambda s: np.zeros(s)
    rastgele = lambda s: np.random.default_rng(2).normal(0, 0.1, s)
    for ad, f1, f2 in (("sabit 0.1 (her iki katman)", sabit, sabit),
                       ("rastgele küçük (sd 0.1)", rastgele,
                        rastgele)):
        fark, acc, kay = simetri_deneyi(f1, f2)
        print("%-27s birim fark=%.2e  test doğr.=%.3f"
              % (ad, fark, acc))
    fark, acc, kay = simetri_deneyi(sifir, rastgele)
    print("W1 = 0 (tanh), W2 rastgele: fark=%.2e  test doğr.=%.3f"
          % (fark, acc))
    fark, acc, kay = simetri_deneyi(sifir, sifir)
    print("W1=W2=0 (tanh): fark=%.2e  test=%.3f kayıp=%.4f"
          % (fark, acc, kay))
