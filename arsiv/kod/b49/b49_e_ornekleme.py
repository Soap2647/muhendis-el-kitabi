# -*- coding: utf-8 -*-
"""Bolum 49 - E: Ornekleme (ters CDF, Box-Muller, reddetme)."""

import math
import random
import secrets


def ters_cdf_ustel(lam, rnd):
    """F(x) = 1 - e^(-lam x) -> F^-1(u) = -ln(1 - u) / lam."""
    u = rnd.random()
    return -math.log(1.0 - u) / lam


def box_muller(rnd):
    """Iki bagimsiz U(0,1) -> iki bagimsiz N(0,1)."""
    u1 = 1.0 - rnd.random()  # log(0) olmasin diye (0,1]
    u2 = rnd.random()
    r = math.sqrt(-2.0 * math.log(u1))
    return r * math.cos(2 * math.pi * u2), r * math.sin(
        2 * math.pi * u2
    )


def reddetme(rnd):
    """Hedef f(x) = 6x(1-x) (Beta(2,2)), oneri g(x) = 1 (U(0,1)).

    M = max f = 1.5 (x = 1/2). Kabul olasiligi f(x) / (M g(x)).
    Her denemede: x ~ U(0,1), v ~ U(0,1); v <= f(x)/M ise kabul.
    Beklenen kabul orani 1/M = 2/3.
    """
    M = 1.5
    deneme = 0
    while True:
        deneme += 1
        x = rnd.random()
        v = rnd.random()
        if v <= 6 * x * (1 - x) / M:
            return x, deneme


def ozet(ad, veri, teorik_ort, teorik_var):
    n = len(veri)
    ort = sum(veri) / n
    var = sum((t - ort) ** 2 for t in veri) / (n - 1)
    print(
        "%-22s ort=%.4f (%.4f)  var=%.4f (%.4f)"
        % (ad, ort, teorik_ort, var, teorik_var)
    )


def main():
    rnd = random.Random(49)
    n = 200_000

    ustel = [ters_cdf_ustel(2.0, rnd) for _ in range(n)]
    ozet("Ters CDF Ustel(2)", ustel, 0.5, 0.25)

    z = []
    while len(z) < n:
        a, b = box_muller(rnd)
        z.extend((a, b))
    ozet("Box-Muller N(0,1)", z[:n], 0.0, 1.0)

    kabul = []
    toplam_deneme = 0
    for _ in range(n // 2):
        x, d = reddetme(rnd)
        kabul.append(x)
        toplam_deneme += d
    ozet("Reddetme Beta(2,2)", kabul, 0.5, 0.05)
    print(
        "Kabul orani = %.4f (beklenen 0.6667)"
        % (len(kabul) / toplam_deneme)
    )

    # Tohum: ayni tohum ayni dizi, secrets ise her seferinde farkli.
    a = random.Random(42)
    b = random.Random(42)
    print("Tohum 42 iki kez: %s" % (a.random() == b.random()))
    print(
        "secrets uzunluk: %d bit" % (len(secrets.token_bytes(16)) * 8)
    )


if __name__ == "__main__":
    main()
