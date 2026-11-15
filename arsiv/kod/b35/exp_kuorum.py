# -*- coding: utf-8 -*-
"""Quorum (R, W, N=3): bayat okuma olasılığı (Bölüm 35.8).
Model: bir yazma W kopyaya ulaşınca tamamlanmış sayılır. Ardından
hemen bir okuma R rastgele kopyadan okur ve en yüksek sürümü alır.
Bayat okuma: okunan en yüksek sürüm, tamamlanmış yazmadan eski.
Tohum: 35. Çıktı: engine/veri/b35_quorum.csv
"""
import csv
import random
from math import comb

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
N = 3
DENEME = 200000


def teorik(r, w):
    # Yazılmayan kopya sayısı N-W; okunan R kopyanın hepsi onlardan
    # oluşursa bayat okuma olur.
    if r + w > N:
        return 0.0
    return comb(N - w, r) / comb(N, r)


def simule(r, w, rnd):
    bayat = 0
    kopyalar = list(range(N))
    for _ in range(DENEME):
        yazilan = set(rnd.sample(kopyalar, w))
        okunan = rnd.sample(kopyalar, r)
        if not (yazilan & set(okunan)):
            bayat += 1
    return bayat / DENEME


if __name__ == "__main__":
    rnd = random.Random(35)
    satirlar = []
    print("N=%d, deneme=%d" % (N, DENEME))
    print("R W  R+W>N  teorik    olculen")
    for r, w in [(1, 1), (1, 2), (2, 1), (2, 2), (1, 3), (3, 1)]:
        t = teorik(r, w)
        o = simule(r, w, rnd)
        print("%d %d  %-5s  %.5f  %.5f"
              % (r, w, r + w > N, t, o))
        satirlar.append([r, w, N, "%.6f" % t, "%.6f" % o])
    with open(VERI + "/b35_quorum.csv", "w", encoding="utf-8",
              newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["R", "W", "N", "teorik", "olculen"])
        wr.writerows(satirlar)
