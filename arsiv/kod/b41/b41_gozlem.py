# -*- coding: utf-8 -*-
"""Bölüm 41.10 - Yüzdelikler ve kuyruk gecikmesi (tail latency).

1) En yakın sıra (nearest-rank) yüzdeliği: sıralı n değerden q
   yüzdeliği = sirali[ceil(q*n) - 1].
2) Yayılım (fan-out): bir sayfa 10 servise paralel istek atar; her
   servisin p99'u 100 ms. Sayfa, en yavaş servisi bekler.
Tohum: 41.
"""

import math
import random


#@@
def yuzdelik(degerler, q):
    s = sorted(degerler)
    n = len(s)
    return s[math.ceil(q * n) - 1]


#@@
if __name__ == "__main__":
    # 100 istek: 95 tanesi 20 ms, 4 tanesi 100 ms, 1 tanesi 2000 ms
    ornek = [20] * 95 + [100] * 4 + [2000]
    print("ortalama = %.1f ms" % (sum(ornek) / len(ornek)))
    print("p50      = %d ms" % yuzdelik(ornek, 0.50))
    print("p90      = %d ms" % yuzdelik(ornek, 0.90))
    print("p99      = %d ms" % yuzdelik(ornek, 0.99))
    print("maks     = %d ms" % max(ornek))

    # Yayılım: 10 paralel servis, her birinin p99 = 100 ms
    n = 10
    p_yavas = 0.01
    print()
    print(
        "Analitik: P(en az biri > 100 ms) = 1 - 0,99^%d = %.4f"
        % (n, 1 - (1 - p_yavas) ** n)
    )
    rnd = random.Random(41)
    deneme = 200000
    yavas = 0
    for _ in range(deneme):
        if any(rnd.random() < p_yavas for _ in range(n)):
            yavas += 1
    print(
        "Simülasyon (%d deneme)                : %.4f"
        % (deneme, yavas / deneme)
    )
