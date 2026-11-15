# -*- coding: utf-8 -*-
"""Bolum 49 - F: Kestirim: MLE, MAP, yanlilik ve varyans."""

import csv
import os
import math
import random

VERI = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "engine",
    "veri",
)


def log_olabilirlik_ustel(lam, veri):
    """l(lam) = n ln(lam) - lam * sum(x)."""
    return len(veri) * math.log(lam) - lam * sum(veri)


def altin_oran_maks(f, a, b, tol=1e-10):
    """Tek tepeli f icin altin oran aramasi: maksimum noktasi."""
    g = (math.sqrt(5) - 1) / 2
    c, d = b - g * (b - a), a + g * (b - a)
    while abs(b - a) > tol:
        if f(c) > f(d):
            b = d
        else:
            a = c
        c, d = b - g * (b - a), a + g * (b - a)
    return (a + b) / 2


def ustel_mle(seed=49, n=50, lam_gercek=0.5):
    rnd = random.Random(seed)
    veri = [rnd.expovariate(lam_gercek) for _ in range(n)]
    kapali = n / sum(veri)
    sayisal = altin_oran_maks(
        lambda l: log_olabilirlik_ustel(l, veri), 0.01, 5.0
    )
    print(
        "Ustel MLE: kapali=%.6f  sayisal=%.6f  gercek=%.2f"
        % (kapali, sayisal, lam_gercek)
    )
    # Log-olabilirlik egrisi (Sekil 49.6 icin).
    satirlar = [["lambda", "log_olabilirlik", "kapali_mle"]]
    for i in range(0, 201):
        l = 0.05 + i * (1.2 - 0.05) / 200
        satirlar.append(
            [
                "%.4f" % l,
                "%.4f" % log_olabilirlik_ustel(l, veri),
                "%.6f" % kapali,
            ]
        )
    with open(
        VERI + "/b49_mle.csv", "w", encoding="utf-8", newline=""
    ) as f:
        csv.writer(f).writerows(satirlar)
    print("  b49_mle.csv yazildi (%d satir)" % (len(satirlar) - 1))


def bernoulli_mle(seed=49):
    rnd = random.Random(seed)
    n, p = 100, 0.3
    veri = [1 if rnd.random() < p else 0 for _ in range(n)]
    k = sum(veri)
    print("Bernoulli: k=%d n=%d  MLE p = k/n = %.4f" % (k, n, k / n))


def normal_yanlilik(seed=49, n=5, tekrar=200_000):
    """E[sigma^2_MLE] = (n-1)/n sigma^2 ; E[s^2] = sigma^2."""
    rnd = random.Random(seed)
    s_mle = s_ust = 0.0
    for _ in range(tekrar):
        x = [rnd.gauss(0.0, 1.0) for _ in range(n)]
        m = sum(x) / n
        kare = sum((t - m) ** 2 for t in x)
        s_mle += kare / n
        s_ust += kare / (n - 1)
    print(
        "Normal n=%d (sigma^2=1): E[MLE]=%.4f (%.2f)  E[s^2]=%.4f"
        % (n, s_mle / tekrar, (n - 1) / n, s_ust / tekrar)
    )


def uniform_momentler_mle(seed=49, n=10, teta=1.0, tekrar=200_000):
    rnd = random.Random(seed)
    mm = []
    ml = []
    for _ in range(tekrar):
        x = [rnd.uniform(0.0, teta) for _ in range(n)]
        mm.append(2 * sum(x) / n)
        ml.append(max(x))
    o1 = sum(mm) / tekrar
    v1 = sum((t - o1) ** 2 for t in mm) / tekrar
    o2 = sum(ml) / tekrar
    v2 = sum((t - o2) ** 2 for t in ml) / tekrar
    print(
        "Momentler: ort=%.4f var=%.5f (teorik %.5f)"
        % (o1, v1, teta * teta / (3 * n))
    )
    print(
        "MLE max:   ort=%.4f var=%.5f (teorik %.5f)"
        % (o2, v2, n * teta * teta / ((n + 1) ** 2 * (n + 2)))
    )


def beta_bernoulli():
    n, k = 10, 0
    mle = k / n
    laplace = (k + 1) / (n + 2)
    map22 = (k + 1) / (n + 2)  # Beta(2,2) icin (k+a-1)/(n+a+b-2)
    ort22 = (k + 2) / (n + 4)  # Beta(2,2) sonsal ortalama
    print("n=%d k=%d: MLE=%.4f Laplace=%.4f" % (n, k, mle, laplace))
    print(
        "  Beta(2,2): MAP=%.4f  sonsal ortalama=%.4f" % (map22, ort22)
    )


def main():
    ustel_mle()
    bernoulli_mle()
    normal_yanlilik()
    uniform_momentler_mle()
    beta_bernoulli()


if __name__ == "__main__":
    main()
