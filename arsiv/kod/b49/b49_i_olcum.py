# -*- coding: utf-8 -*-
"""Bolum 49 - I: Muhendislik olcumu: kesme gecikmesi karsilastirmasi.

Veri: engine/veri/b44_gecikme.csv (Bolum 44, cevrim olcegi).
Iki grup: kesme/TIM (n=283) ve kesme/ADC (n=723).
"""

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


def oku(tur, kaynak):
    with open(VERI + "/b44_gecikme.csv", encoding="utf-8") as f:
        return [
            float(r["gecikme_cevrim"])
            for r in csv.DictReader(f)
            if r["tur"] == tur and r["kaynak"] == kaynak
        ]


def yuzdelik(v, p):
    """Dogrusal enterpolasyonlu yuzdelik (numpy varsayilani)."""
    s = sorted(v)
    h = (len(s) - 1) * p
    lo = math.floor(h)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def medyan(v):
    return yuzdelik(v, 0.5)


def ortalama(v):
    return sum(v) / len(v)


def ozet(ad, v):
    print(
        "%-12s n=%4d ort=%6.2f med=%5.1f "
        "p90=%6.1f p99=%6.1f max=%5.0f"
        % (
            ad,
            len(v),
            ortalama(v),
            medyan(v),
            yuzdelik(v, 0.9),
            yuzdelik(v, 0.99),
            max(v),
        )
    )


def cohen_d(a, b):
    va = sum((x - ortalama(a)) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - ortalama(b)) ** 2 for x in b) / (len(b) - 1)
    sp = math.sqrt(
        ((len(a) - 1) * va + (len(b) - 1) * vb)
        / (len(a) + len(b) - 2)
    )
    return (ortalama(a) - ortalama(b)) / sp


def cliff_delta(a, b):
    """P(A > B) - P(A < B), sayarak hesaplanir. Olcek-bagimsiz."""
    gt = lt = 0
    for x in a:
        for y in b:
            if x > y:
                gt += 1
            elif x < y:
                lt += 1
    return (gt - lt) / (len(a) * len(b))


def permutasyon(a, b, istat, B=10_000, seed=49):
    rnd = random.Random(seed)
    gozlenen = abs(istat(a) - istat(b))
    havuz = a + b
    na = len(a)
    say = 0
    for _ in range(B):
        rnd.shuffle(havuz)
        if abs(istat(havuz[:na]) - istat(havuz[na:])) >= gozlenen:
            say += 1
    return gozlenen, (say + 1) / (B + 1)


def bootstrap_fark(a, b, istat, B=10_000, seed=49):
    rnd = random.Random(seed)
    fark = []
    for _ in range(B):
        ra = [a[rnd.randrange(len(a))] for _ in range(len(a))]
        rb = [b[rnd.randrange(len(b))] for _ in range(len(b))]
        fark.append(istat(ra) - istat(rb))
    fark.sort()
    return fark[int(0.025 * B)], fark[int(0.975 * B) - 1]


def main():
    tim = oku("kesme", "TIM")
    adc = oku("kesme", "ADC")
    print("== Ozet (cevrim) ==")
    ozet("kesme TIM", tim)
    ozet("kesme ADC", adc)

    print("== Ortalama farki (TIM - ADC) ==")
    print("Fark ort: %.3f" % (ortalama(tim) - ortalama(adc)))
    g, p = permutasyon(tim, adc, ortalama)
    print("Permutasyon (ortalama): gozlenen=%.3f  p=%.5f" % (g, p))
    lo, hi = bootstrap_fark(tim, adc, ortalama)
    print("Bootstrap GA (ortalama farki): [%.2f, %.2f]" % (lo, hi))
    print("Cohen d = %.3f" % cohen_d(tim, adc))
    print("Cliff delta = %.3f" % cliff_delta(tim, adc))

    print("== Medyan farki ==")
    g, p = permutasyon(tim, adc, medyan)
    print("Permutasyon (medyan): gozlenen=%.3f  p=%.5f" % (g, p))
    lo, hi = bootstrap_fark(tim, adc, medyan)
    print("Bootstrap GA (medyan farki): [%.2f, %.2f]" % (lo, hi))

    print("== p99 farki ==")
    g, p = permutasyon(tim, adc, lambda v: yuzdelik(v, 0.99))
    print("Permutasyon (p99): gozlenen=%.3f  p=%.5f" % (g, p))


if __name__ == "__main__":
    main()
