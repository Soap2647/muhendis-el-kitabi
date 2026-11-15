# -*- coding: utf-8 -*-
# b62_02_bn.py: 3 dugumlu Bayes agi (F -> A <- H), sayimla cikarim,
# aciklama gucu (explaining away) ve reddetme ornekleme ile yaklasik
# cikarim.
import numpy as np

# F: sensor arizasi, H: gercek hedef var, A: alarm (1 = alarm)
P_F = {0: 0.98, 1: 0.02}
P_H = {0: 0.95, 1: 0.05}
# P(A = 1 | F, H): kosullu olasilik tablosu (CPT)
P_A1 = {(0, 0): 0.01, (1, 0): 0.60, (0, 1): 0.90, (1, 1): 0.92}


def ortak(f, h, a):
    """Ortak olasilik: P(F,H,A) = P(F) P(H) P(A|F,H)."""
    pa = P_A1[(f, h)]
    return P_F[f] * P_H[h] * (pa if a == 1 else 1 - pa)


def olasilik(sart, hedef):
    """Sayimla cikarim: P(hedef|sart) = T(hedef,sart)/T(sart).
    sart ve hedef: {'F':1} gibi sozlukler."""

    def topla(kisit):
        s = 0.0
        for f in (0, 1):
            for h in (0, 1):
                for a in (0, 1):
                    v = {"F": f, "H": h, "A": a}
                    if all(v[k] == x for k, x in kisit.items()):
                        s += ortak(f, h, a)
        return s

    pay = topla(sart)
    return topla({**sart, **hedef}) / pay


def reddetme(n, seed=62):
    """Reddetme ornekleme: ornekle, A=1 olmayanlari at."""
    rng = np.random.default_rng(seed)
    f = (rng.random(n) < P_F[1]).astype(int)
    h = (rng.random(n) < P_H[1]).astype(int)
    p = np.array([P_A1[(a, b)] for a, b in zip(f, h)])
    a = (rng.random(n) < p).astype(int)
    kabul = a == 1
    return f[kabul], h[kabul], kabul.mean()


if __name__ == "__main__":
    toplam = sum(
        ortak(f, h, a) for f in (0, 1) for h in (0, 1) for a in (0, 1)
    )
    print("Toplam olasilik (1 olmali):", round(toplam, 10))
    print(
        "P(A=1)                   =", round(olasilik({}, {"A": 1}), 5)
    )
    print(
        "P(F=1 | A=1)             =",
        round(olasilik({"A": 1}, {"F": 1}), 4),
    )
    print(
        "P(F=1 | A=1, H=0)        =",
        round(olasilik({"A": 1, "H": 0}, {"F": 1}), 4),
    )
    print(
        "P(F=1 | A=1, H=1)        =",
        round(olasilik({"A": 1, "H": 1}, {"F": 1}), 4),
    )
    print(
        "P(H=1 | A=1)             =",
        round(olasilik({"A": 1}, {"H": 1}), 4),
    )
    print(
        "P(H=1 | A=1, F=1)        =",
        round(olasilik({"A": 1, "F": 1}, {"H": 1}), 4),
    )
    print()
    print("Reddetme ornekleme (N = 200000, tohum 62):")
    for n in [200000]:
        f, h, kabul = reddetme(n)
        print("  kabul orani            =", round(kabul, 4))
        print("  P(F=1 | A=1)  tahmin   =", round(f.mean(), 4))
        print(
            "  P(F=1 | A=1, H=1) tah. =",
            round(f[h == 1].mean(), 4),
            " (kabul sayisi:",
            int((h == 1).sum()),
            ")",
        )
