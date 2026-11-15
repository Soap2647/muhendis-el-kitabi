# -*- coding: utf-8 -*-
"""Bolum 49 - Ornek 2 (Poisson) ve 3 (MLE + bootstrap)."""

import math
import random

from scipy import stats


def ornek2_poisson(saat=100_000, lam=3.0, seed=49):
    """Poisson sureci: ardisik olaylar arasi Ustel(lam) bekleme.
    Her birim saat icinde kac olay oldugunu say."""
    rnd = random.Random(seed)
    sayilar = []
    for _ in range(saat):
        t = 0.0
        k = 0
        while True:
            t += rnd.expovariate(lam)
            if t > 1.0:
                break
            k += 1
        sayilar.append(k)
    n = len(sayilar)
    print("Simulasyon: %d saat, lam=%.1f" % (n, lam))
    for k in range(0, 6):
        emp = sayilar.count(k) / n
        teo = math.exp(-lam) * lam**k / math.factorial(k)
        print("  k=%d  simule=%.4f  teorik=%.4f" % (k, emp, teo))
    ge5 = sum(1 for s in sayilar if s >= 5) / n
    print(
        "  P(k>=5) simule=%.4f  teorik=%.4f"
        % (ge5, stats.poisson.sf(4, lam))
    )
    print("  ortalama=%.4f (lam=%.1f)" % (sum(sayilar) / n, lam))


def ornek3_mle_bootstrap(seed=49, B=10_000):
    sureler = [1.8, 0.4, 3.1, 2.2, 0.9, 5.6, 1.2, 0.7, 2.9, 1.5]
    n = len(sureler)
    s = sum(sureler)
    lam = n / s
    print(
        "n=%d  toplam=%.1f  MLE lambda=%.4f  ort=%.4f saat"
        % (n, s, lam, s / n)
    )
    for l in (0.3, 0.4926, 0.6, 0.8):
        ll = n * math.log(l) - l * s
        print("  l(%.4f) = %.4f" % (l, ll))
    rnd = random.Random(seed)
    lam_dag = []
    ort_dag = []
    for _ in range(B):
        ornek = [sureler[rnd.randrange(n)] for _ in range(n)]
        t = sum(ornek)
        lam_dag.append(n / t)
        ort_dag.append(t / n)
    lam_dag.sort()
    ort_dag.sort()
    print(
        "Bootstrap GA (lambda): [%.4f, %.4f]"
        % (lam_dag[int(0.025 * B)], lam_dag[int(0.975 * B) - 1])
    )
    print(
        "Bootstrap GA (ortalama sure): [%.4f, %.4f]"
        % (ort_dag[int(0.025 * B)], ort_dag[int(0.975 * B) - 1])
    )


def main():
    ornek2_poisson()
    ornek3_mle_bootstrap()


if __name__ == "__main__":
    main()
