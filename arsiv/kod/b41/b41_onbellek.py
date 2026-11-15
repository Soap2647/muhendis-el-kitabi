# -*- coding: utf-8 -*-
"""Bölüm 41.7 - Önbellek isabet oranı ve ortalama gecikme.

1) Formül: ort = h * t_onb + (1 - h) * t_kaynak.
2) Zipf erişim örüntüsü ile LRU önbelleği simülasyonu (Bölüm 9'daki
   LRU fikrinin OrderedDict ile gerçeklemesi). Tohum: 41.
"""

import bisect
import random
from collections import OrderedDict

ANAHTAR = 100000  # farklı anahtar sayısı
ERISIM = 1000000  # toplam istek
S = 1.0  # Zipf üssü (s=1: klasik Zipf)
T_ONB_MS = 0.5  # ağ önbelleği gecikmesi (genel bilgi)
T_KAYNAK_MS = 20.0  # veritabanı gecikmesi (varsayım)


#@@
class LRU:
    def __init__(self, kapasite):
        self.k = kapasite
        self.v = OrderedDict()

    def al(self, anahtar):
        if anahtar in self.v:
            self.v.move_to_end(anahtar)
            return True
        return False

    def koy(self, anahtar):
        self.v[anahtar] = True
        self.v.move_to_end(anahtar)
        if len(self.v) > self.k:
            self.v.popitem(last=False)


#@@
def zipf_kumulatif(n, s):
    agirlik = [1.0 / (i**s) for i in range(1, n + 1)]
    toplam = sum(agirlik)
    kum, acc = [], 0.0
    for a in agirlik:
        acc += a / toplam
        kum.append(acc)
    return kum


def isabet_orani(oran, rnd, kum):
    kapasite = int(ANAHTAR * oran)
    onb = LRU(kapasite)
    isabet = 0
    for _ in range(ERISIM):
        a = bisect.bisect_left(kum, rnd.random())
        if onb.al(a):
            isabet += 1
        else:
            onb.koy(a)
    return isabet / ERISIM


#@@
if __name__ == "__main__":
    print(
        "1) Formül: t_onb = %.2f ms, t_kaynak = %.1f ms"
        % (T_ONB_MS, T_KAYNAK_MS)
    )
    print("h      ort_ms")
    for h in (0.0, 0.5, 0.9, 0.99, 0.999):
        ort = h * T_ONB_MS + (1 - h) * T_KAYNAK_MS
        print("%-6.3f %7.3f" % (h, ort))
    print()
    print(
        "2) Zipf(s=%.1f), %d anahtar, %d istek, LRU"
        % (S, ANAHTAR, ERISIM)
    )
    kum = zipf_kumulatif(ANAHTAR, S)
    print("onbellek(%)  isabet    ort_ms (formül)")
    for oran in (0.01, 0.05, 0.10, 0.20):
        rnd = random.Random(41)
        h = isabet_orani(oran, rnd, kum)
        ort = h * T_ONB_MS + (1 - h) * T_KAYNAK_MS
        print("%-12.0f %7.4f  %8.3f" % (oran * 100, h, ort))
