# -*- coding: utf-8 -*-
"""Bolum 49 - B: Dagilimlar ve belleksizlik."""

import math
import random

from scipy import stats


def binom_pmf(n, p, k):
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)


def poisson_pmf(lam, k):
    return math.exp(-lam) * lam**k / math.factorial(k)


def paket_kaybi():
    # 20 paket, her biri %5 olasilikla kayboluyor (binom).
    p0 = binom_pmf(20, 0.05, 0)
    p1 = binom_pmf(20, 0.05, 1)
    print(
        "Binom(20, 0.05): P(0)=%.4f P(1)=%.4f P(>=2)=%.4f"
        % (p0, p1, 1 - p0 - p1)
    )
    print(
        "  scipy: P(0)=%.4f P(>=2)=%.4f"
        % (stats.binom.pmf(0, 20, 0.05), stats.binom.sf(1, 20, 0.05))
    )
    # Saatte ortalama 3 kayip (Poisson).
    lam = 3.0
    p_ge5 = 1 - sum(poisson_pmf(lam, k) for k in range(5))
    print(
        "Poisson(3): P(0)=%.4f P(>=5)=%.4f"
        % (poisson_pmf(lam, 0), p_ge5)
    )
    print("  scipy: P(>=5)=%.4f" % stats.poisson.sf(4, lam))


def geometrik():
    # Basari olasiligi p=0.1; ilk basariya kadar deneme sayisi.
    p = 0.1
    print(
        "Geometrik(0.1): P(X=1)=%.3f P(X=10)=%.5f E[X]=%.1f"
        % (p, (1 - p) ** 9 * p, 1 / p)
    )
    print("  scipy E=%.1f" % stats.geom.mean(p))


def ustel_belleksizlik(n=1_000_000, seed=49):
    """Arizalar arasi sure ~ Ustel(lambda=0.5 / saat)."""
    lam = 0.5
    rnd = random.Random(seed)
    sure = [rnd.expovariate(lam) for _ in range(n)]
    kosul = [t for t in sure if t > 3.0]
    ust = sum(1 for t in kosul if t > 5.0) / len(kosul)
    print(
        "Ustel(0.5): P(T>2)=%.4f (teorik %.4f)"
        % (sum(t > 2 for t in sure) / n, math.exp(-lam * 2))
    )
    print(
        "P(T>5 | T>3) = %.4f  (P(T>2) = %.4f): belleksiz"
        % (ust, math.exp(-lam * 2))
    )


def normal_kurali(n=1_000_000, seed=49):
    rnd = random.Random(seed)
    x = [rnd.gauss(0.0, 1.0) for _ in range(n)]
    for k in (1, 2, 3):
        oran = sum(abs(t) <= k for t in x) / n
        print(
            "P(|Z| <= %d) = %.4f  scipy: %.4f"
            % (k, oran, stats.norm.cdf(k) - stats.norm.cdf(-k))
        )


def sabit_nokta(n=10, deneme=200_000, seed=49):
    """Sapka problemi: beklenen dogru eslesme sayisi (sabit nokta)."""
    rnd = random.Random(seed)
    toplam = 0
    sifir = 0
    for _ in range(deneme):
        p = list(range(n))
        rnd.shuffle(p)
        s = sum(1 for i, v in enumerate(p) if i == v)
        toplam += s
        sifir += s == 0
    return toplam / deneme, sifir / deneme


def main():
    paket_kaybi()
    geometrik()
    ustel_belleksizlik()
    normal_kurali()
    ort, d = sabit_nokta()
    print(
        "Sapka (n=10): ortalama eslesme=%.4f  hic eslesmeme=%.4f"
        % (ort, d)
    )
    print("  1/e = %.4f" % (1 / math.e))


if __name__ == "__main__":
    main()
