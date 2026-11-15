# -*- coding: utf-8 -*-
"""Bolum 49 - J: Sensor fuzyonu, Beta guncellemesi, ML koprusu,
bakip durdurma."""

import math
import random

import numpy as np
from scipy import stats


def fuzyon():
    """Iki sensor, onsel N(5,4): z1=6.2 (s1=2), z2=4.9 (s2=1)."""
    m0, v0 = 5.0, 4.0
    z = [(6.2, 4.0), (4.9, 1.0)]
    prec = 1 / v0
    mu = m0 * prec
    for zi, vi in z:
        prec += 1 / vi
        mu += zi / vi
    print(
        "Fuzyon: sonsal ortalama = %.4f, sonsal sigma = %.4f"
        % (mu / prec, math.sqrt(1 / prec))
    )
    rnd = np.random.default_rng(49)
    x = rnd.normal(5.0, 1.0, 100_000)
    # Gercek x ~ N(5, 1); sensor hatalari sigma1=2, sigma2=1
    y1 = x + rnd.normal(0, 2, x.size)
    y2 = x + rnd.normal(0, 1, x.size)
    p = 1 / 4.0 + 1 / 1.0
    birlesik = (y1 / 4.0 + y2 / 1.0) / p
    print(
        "  Simulasyon: var(birlesik-x) = %.4f "
        "(teorik 1/(1/4+1) = %.4f)" % (np.var(birlesik - x), 1 / p)
    )


def beta_guncelleme():
    a, b = 2, 2
    yazi = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0]
    print("Beta(2,2) on dagilimi, sirayla gozlemler:")
    print(" n  k   a  b   sonsal_ort   MAP")
    k = 0
    for n, x in enumerate(yazi, 1):
        k += x
        a2, b2 = 2 + k, 2 + (n - k)
        ort = a2 / (a2 + b2)
        mp = (a2 - 1) / (a2 + b2 - 2)
        print(
            "%2d %2d %3d %2d   %.4f     %.4f"
            % (n, k, a2, b2, ort, mp)
        )


def capraz_entropi():
    """Bernoulli: CE = -(1/n) sum [y log p + (1-y) log(1-p)]."""
    rnd = random.Random(49)
    n = 2000
    p = [rnd.random() for _ in range(n)]
    y = [1 if rnd.random() < q else 0 for q in p]
    ce = (
        -sum(
            t * math.log(q) + (1 - t) * math.log(1 - q)
            for t, q in zip(y, p)
        )
        / n
    )
    ll = sum(
        math.log(q) if t else math.log(1 - q) for t, q in zip(y, p)
    )
    print("Capraz entropi = %.6f  -ll/n = %.6f" % (ce, -ll / n))
    # Kalibrasyon: ayni p'yi karesi ile bozarak asiri ozguvenli model.
    bozuk = [q**0.3 for q in p]
    ce2 = (
        -sum(
            t * math.log(q) + (1 - t) * math.log(1 - q)
            for t, q in zip(y, bozuk)
        )
        / n
    )
    print("Kalibre model CE=%.4f  Bozuk (p^0.3) CE=%.4f" % (ce, ce2))
    print(
        "  Ortalama: kalibre tahmin=%.4f  gozlenen=%.4f"
        % (sum(p) / n, sum(y) / n)
    )


def bakip_durdurma(deney=20_000, seed=49):
    """H0 dogru; her 10 gozlemde bir t-testi; ilk anlamlida dur."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, (deney, 100))
    mask = np.zeros(deney, dtype=bool)
    for k in range(10, 101, 10):
        sub = x[:, :k]
        m = sub.mean(axis=1)
        s = sub.std(axis=1, ddof=1)
        t = m / (s / math.sqrt(k))
        p = 2 * stats.t.sf(np.abs(t), k - 1)
        mask = mask | (p < 0.05)
    print(
        "Bakip durdurma: en az bir bakista p<0.05: %.4f "
        "(sabit n=100: 0.05)" % np.mean(mask)
    )


def main():
    fuzyon()
    beta_guncelleme()
    capraz_entropi()
    bakip_durdurma()


if __name__ == "__main__":
    main()
