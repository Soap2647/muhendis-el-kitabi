# -*- coding: utf-8 -*-
# kume_graf.py - Hasse kenarlari, topolojik sira, dogum gunu.
import graphlib
import itertools
import math
import random


def hasse_kenarlari(sayilar):
    """a -> b: a | b ve arada baska bolen yok (orten kenar)."""
    kenar = []
    for a, b in itertools.permutations(sayilar, 2):
        if a < b and b % a == 0:
            ara = [c for c in sayilar
                   if a < c < b and c % a == 0 and b % c == 0]
            if not ara:
                kenar.append((a, b))
    return sorted(kenar)


def dogum_gunu(M, deneme, rnd):
    """M kovaya rastgele atarken ilk cakisma icin ortalama adim."""
    toplam = 0
    for _ in range(deneme):
        gorulen, k = set(), 0
        while True:
            k += 1
            h = rnd.randrange(M)
            if h in gorulen:
                break
            gorulen.add(h)
        toplam += k
    return toplam / deneme


if __name__ == "__main__":
    kenar = hasse_kenarlari([1, 2, 3, 4, 6, 12])
    print("Hasse kenarlari:", " ".join(f"{a}->{b}" for a, b in kenar))
    ts = graphlib.TopologicalSorter()
    for a, b in kenar:
        ts.add(b, a)
    print("Topolojik sira:", list(ts.static_order()))
    rnd = random.Random(47)
    for M in (365, 10000):
        ort = dogum_gunu(M, 4000, rnd)
        print("M =", M, " ort. ilk cakisma:", round(ort, 1),
              " sqrt(pi*M/2) =", round(math.sqrt(math.pi * M / 2), 1))
