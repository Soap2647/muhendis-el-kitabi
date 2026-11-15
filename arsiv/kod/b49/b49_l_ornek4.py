# -*- coding: utf-8 -*-
"""Bolum 49 - Ornek 4: iki pivot stratejisinin permutasyon testi."""

import random
from itertools import combinations


def quicksort_karsilastirma(a, pivot):
    """Lomuto bolmeli yinelemeli quicksort: karsilastirma sayisi."""
    sayac = 0
    yigin = [(0, len(a) - 1)]
    while yigin:
        lo, hi = yigin.pop()
        if lo >= hi:
            continue
        if pivot == "rastgele":
            p = random.randint(lo, hi)
        else:  # medyan-uc
            m = (lo + hi) // 2
            uc = sorted([(a[lo], lo), (a[m], m), (a[hi], hi)])
            p = uc[1][1]
        a[p], a[hi] = a[hi], a[p]
        x = a[hi]
        i = lo
        for j in range(lo, hi):
            sayac += 1
            if a[j] < x:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[i], a[hi] = a[hi], a[i]
        yigin.append((lo, i - 1))
        yigin.append((i + 1, hi))
    return sayac


def tam_permutasyon(a, b):
    """5+5 ornek: |fark| >= gozlenen olan bolmeler."""
    havuz = a + b
    na, nb = len(a), len(b)
    gozlenen = sum(a) / na - sum(b) / nb
    toplam = say = 0
    for idx in combinations(range(len(havuz)), na):
        secili = set(idx)
        x = [havuz[i] for i in idx]
        y = [havuz[i] for i in range(len(havuz)) if i not in secili]
        f = sum(x) / na - sum(y) / nb
        toplam += 1
        if abs(f) >= abs(gozlenen) - 1e-12:
            say += 1
    return gozlenen, say, toplam


def buyuk_ornek(seed=49, B=10_000):
    """25+25 ornek, n=300: yaklasik permutasyon testi (B=10000)."""
    random.seed(seed)
    rnd = random.Random(seed)
    a, b = [], []
    for _ in range(25):
        dizi = list(range(300))
        rnd.shuffle(dizi)
        a.append(quicksort_karsilastirma(list(dizi), "rastgele"))
        b.append(quicksort_karsilastirma(list(dizi), "medyan3"))
    g = sum(a) / 25 - sum(b) / 25
    havuz = a + b
    say = 0
    for _ in range(B):
        rnd.shuffle(havuz)
        f = sum(havuz[:25]) / 25 - sum(havuz[25:]) / 25
        if abs(f) >= abs(g):
            say += 1
    print(
        "25+25: ort A=%.1f B=%.1f fark=%.2f"
        % (sum(a) / 25, sum(b) / 25, g)
    )
    print(
        "25+25: permutasyon p = %.4f (B=10000)"
        % ((say + 1) / (B + 1))
    )


def main(seed=49, n=50):
    random.seed(seed)  # quicksort pivotu global RNG kullanir
    rnd = random.Random(seed)
    rastgele, medyan3 = [], []
    for _ in range(5):
        dizi = list(range(n))
        rnd.shuffle(dizi)
        rastgele.append(
            quicksort_karsilastirma(list(dizi), "rastgele")
        )
        medyan3.append(quicksort_karsilastirma(list(dizi), "medyan3"))
    print("A (rastgele):", rastgele, "ort=%.1f" % (sum(rastgele) / 5))
    print("B (medyan3): ", medyan3, "ort=%.1f" % (sum(medyan3) / 5))
    g, say, top = tam_permutasyon(rastgele, medyan3)
    print("gozlenen fark (A-B) = %.2f" % g)
    print("bolme sayisi = %d" % top)
    print("|fark| >= gozlenen olan bolme = %d" % say)
    print("exact p = %d/%d = %.4f" % (say, top, say / top))
    havuz = rastgele + medyan3
    for esik in (0, 5, 10, 15, 20):
        c = 0
        for idx in combinations(range(10), 5):
            secili = set(idx)
            x = [havuz[i] for i in idx]
            y = [havuz[i] for i in range(10) if i not in secili]
            if abs(sum(x) / 5 - sum(y) / 5) >= esik - 1e-12:
                c += 1
        print("  |fark| >= %2d : %3d bolme" % (esik, c))


if __name__ == "__main__":
    main()
    buyuk_ornek()
