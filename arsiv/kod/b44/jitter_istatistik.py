# -*- coding: utf-8 -*-
"""jitter.c ciktisinin ozet istatistikleri (aralik, mikrosaniye).
Kullanim: python jitter_istatistik.py jitter_1ms.csv 1000
"""
import statistics as st
import sys

satirlar = open(sys.argv[1], encoding="utf-8").read().split()[1:]
hedef = float(sys.argv[2])
xs = sorted(float(s) for s in satirlar)
n = len(xs)


def yuzdelik(q):
    return xs[int(q * (n - 1))]


print("ornek sayisi      : %d" % n)
print("ortalama          : %.3f us" % st.mean(xs))
print("standart sapma   : %.3f us" % st.pstdev(xs))
print("hedef periyot    : %.1f us" % hedef)
print("medyan (p50)     : %.3f us" % yuzdelik(0.5))
print("p99              : %.3f us" % yuzdelik(0.99))
print("en kucuk / buyuk : %.3f / %.3f us" % (xs[0], xs[-1]))
