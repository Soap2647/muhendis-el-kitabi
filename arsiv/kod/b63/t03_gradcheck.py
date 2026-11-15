# -*- coding: utf-8 -*-
"""Bölüm 63.8: geri yayılımın gradient check ile doğrulanması."""
import numpy as np
from sinir import (Dogrusal, ReLU, Tanh, SoftmaxCE, Ag, ileri_geri)


class ReLUBozuk(ReLU):
    """Türev maskesini unutan HATALI geri geçiş (bilerek)."""
    def geri(self, d):
        return d


def gradyan_kontrol(ag, kayip, X, Y, eps=1e-5):
    ileri_geri(ag, kayip, X, Y)          # analitik gradyan
    sonuc = []
    for i, k in enumerate(ag.parametreler()):
        for ad, P, G in (("W", k.W, k.dW), ("b", k.b, k.db)):
            num = np.zeros_like(P)
            for idx in np.ndindex(P.shape):
                eski = P[idx]
                P[idx] = eski + eps
                Lp = kayip.ileri(ag.ileri(X), Y)
                P[idx] = eski - eps
                Lm = kayip.ileri(ag.ileri(X), Y)
                P[idx] = eski
                num[idx] = (Lp - Lm) / (2 * eps)
            pay = np.abs(G - num)
            payda = np.maximum(np.abs(G) + np.abs(num), 1e-12)
            sonuc.append((i, ad, P.shape, np.max(pay / payda)))
    return sonuc


def kur(rng, aktivasyon):
    return Ag([Dogrusal(4, 5, rng, "he"), aktivasyon(),
               Dogrusal(5, 6, rng, "he"), aktivasyon(),
               Dogrusal(6, 3, rng, "he")])


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    X = rng.normal(size=(7, 4))
    Y = np.eye(3)[rng.integers(0, 3, size=7)]
    kayip = SoftmaxCE()
    for ad, akt in (("dogru", ReLU), ("bozuk", ReLUBozuk)):
        ag = kur(np.random.default_rng(11), akt)
        print("Ağ:", ad)
        enk = 0.0
        for i, p, sekil, hata in gradyan_kontrol(ag, kayip, X, Y):
            print("  katman %d %s %-8s maks. göreli hata = %.2e"
                  % (i, p, str(sekil), hata))
            enk = max(enk, hata)
        print("  EN BÜYÜK = %.2e" % enk)
        print("  durum:", "GEÇTİ" if enk <= 1e-7 else "BAŞARISIZ")
