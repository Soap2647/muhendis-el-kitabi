# -*- coding: utf-8 -*-
"""Bolum 49 - C: Beklenen deger, varyans, kovaryans, korelasyon."""

import math
import random

import numpy as np

# Anscombe ceyreklisi (Anscombe 1973). Dort veri kumesi ayni ozet
# istatistiklere sahiptir ama tamamen farkli sekillerdedir.
X1 = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]
Y1 = [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26,
      10.84, 4.82, 5.68]
Y2 = [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10,
      9.13, 7.26, 4.74]
Y3 = [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39,
      8.15, 6.42, 5.73]
X4 = [8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8]
Y4 = [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50,
      5.56, 7.91, 6.89]


def ortalama(v):
    return sum(v) / len(v)


def kovaryans(x, y):
    """Cov(X,Y) = E[(X - mu_x)(Y - mu_y)] (n bolu n-1 ile)."""
    n = len(x)
    mx, my = ortalama(x), ortalama(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (n - 1)


def korelasyon(x, y):
    sx = math.sqrt(kovaryans(x, x))
    sy = math.sqrt(kovaryans(y, y))
    return kovaryans(x, y) / (sx * sy)


def anscombe():
    seriler = [
        ("I", X1, Y1),
        ("II", X1, Y2),
        ("III", X1, Y3),
        ("IV", X4, Y4),
    ]
    for ad, x, y in seriler:
        print(
            "%-3s ort_y=%.2f  var_y=%.3f  r=%.3f"
            % (ad, ortalama(y), kovaryans(y, y), korelasyon(x, y))
        )
    print("numpy r (I): %.3f" % np.corrcoef(X1, Y1)[0, 1])


def sapka_dogrusallik(n=10, deneme=100_000, seed=49):
    """Dogrusallik: S = sum I_i, E[S] = n * (1/n) = 1."""
    rnd = random.Random(seed)
    top = 0.0
    kare = 0.0
    for _ in range(deneme):
        p = list(range(n))
        rnd.shuffle(p)
        s = sum(1 for i, v in enumerate(p) if i == v)
        top += s
        kare += s * s
    ort = top / deneme
    var = kare / deneme - ort * ort
    return ort, var


def main():
    anscombe()
    ort, var = sapka_dogrusallik()
    print(
        "Sapka n=10: E[S] ~ %.4f, Var(S) ~ %.4f (teorik 1)"
        % (ort, var)
    )


if __name__ == "__main__":
    main()
