# -*- coding: utf-8 -*-
"""Bloom filtresi: teorik ve gözlenen yanlış pozitif oranı (Bölüm
35.6).
Tohum: 35. Çıktı: engine/veri/b35_bloom.csv"""
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bloom import BloomFilter, teorik_yanlis_pozitif, optimal_k

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
N = 10000
SORGU = 100000


def olc(m, k, rnd):
    bf = BloomFilter(m, k)
    for i in range(N):
        bf.ekle("anahtar-%d" % i)
    yanlis = 0
    for j in range(SORGU):
        if bf.icerir("yok-%d" % j):
            yanlis += 1
    return yanlis / SORGU


if __name__ == "__main__":
    rnd = random.Random(35)
    satirlar = []
    print("m/n  k   teorik      olculen     (n=%d, sorgu=%d)"
          % (N, SORGU))
    for oran in (4, 8, 10, 16):
        m = oran * N
        kopt = optimal_k(m, N)
        for k in range(1, 11):
            t = teorik_yanlis_pozitif(m, N, k)
            o = olc(m, k, rnd)
            satirlar.append([oran, k, N, SORGU,
                             "%.6f" % t, "%.6f" % o])
            if k == kopt or k in (1, 4, 10):
                print("%-4d %-3d %.6f    %.6f%s" % (oran, k, t, o,
                      "   <- optimal" if k == kopt else ""))
    with open(os.path.join(VERI, "b35_bloom.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["m_n", "k", "n", "sorgu", "teorik", "olculen"])
        w.writerows(satirlar)
    print("CSV yazildi:", len(satirlar), "satir")
