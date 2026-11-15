# -*- coding: utf-8 -*-
"""Bolum 49 - A: Kosullu olasilik, Bayes, bagimsizlik, Monty Hall."""

import random
from fractions import Fraction
from itertools import product


def bayes_pozitif(pH, duyarlilik, ozgulluk):
    """P(H | +) ve P(+) hesabi; toplam olasilik kullanilir."""
    p_pozitif = duyarlilik * pH + (1 - ozgulluk) * (1 - pH)
    return duyarlilik * pH / p_pozitif, p_pozitif


def hastalik_frekans(n=1_000_000, seed=49):
    """n kisi uret; pozitifleri ve gercek hastalari say."""
    rnd = random.Random(seed)
    poz = hasta_poz = 0
    for _ in range(n):
        hasta = rnd.random() < 0.001
        if hasta:
            test_poz = rnd.random() < 0.99
        else:
            test_poz = rnd.random() < 0.05
        if test_poz:
            poz += 1
            if hasta:
                hasta_poz += 1
    return hasta_poz / poz


def monty_hall(n=100_000, seed=49):
    """Kapi degistir / degistirme stratejilerinin kazanma oranlari."""
    rnd = random.Random(seed)
    degistir = koru = 0
    for _ in range(n):
        odul = rnd.randrange(3)
        secim = rnd.randrange(3)
        # Sunucu, ne secilen ne de odul olan bir kapiyi acar.
        acilan = next(k for k in range(3) if k != secim and k != odul)
        yeni = next(k for k in range(3) if k != secim and k != acilan)
        degistir += yeni == odul
        koru += secim == odul
    return koru / n, degistir / n


def bagimsizlik_kontrol():
    """Iki zar: A = ilk zar cift, B = toplam 7. Tam sayim."""
    uzay = list(product(range(1, 7), repeat=2))
    a = [w for w in uzay if w[0] % 2 == 0]
    b = [w for w in uzay if w[0] + w[1] == 7]
    ab = [w for w in a if w in b]
    p = lambda k: Fraction(len(k), len(uzay))
    return p(a), p(b), p(ab), p(a) * p(b)


def main():
    pH = 0.001
    p, pp = bayes_pozitif(pH, 0.99, 0.95)
    print("Hastalik: P(H|+) = %.4f  P(+) = %.5f" % (p, pp))
    print("Simulasyon (1 000 000 kisi): %.4f" % hastalik_frekans())

    # Iha hedef tanima: 10 000 olay, 200 gercek tehdit.
    p, pp = bayes_pozitif(0.02, 0.95, 0.97)
    print(
        "IHA alarm: P(tehdit|alarm) = %.4f  P(alarm) = %.4f" % (p, pp)
    )

    k, d = monty_hall()
    print(
        "Monty Hall (100 000 deneme): koru=%.4f degistir=%.4f"
        % (k, d)
    )

    pa, pb, pab, prod = bagimsizlik_kontrol()
    print("P(A)=%s P(B)=%s P(A n B)=%s" % (pa, pb, pab))
    print("P(A) P(B) = %s -> bagimsiz: %s" % (prod, pab == prod))


if __name__ == "__main__":
    main()
