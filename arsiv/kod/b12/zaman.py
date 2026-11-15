import math
import random
import sys
import time

import numpy as np

random.seed(42)
TEKRAR = 5


def en_iyi_sure(fonk, tekrar=TEKRAR):
    en = float("inf")
    for _ in range(tekrar):
        t0 = time.perf_counter()
        fonk()
        t1 = time.perf_counter()
        en = min(en, t1 - t0)
    return en


def egim(xs, ys):
    lx = np.log2(np.array(xs, dtype=float))
    ly = np.log2(np.array(ys, dtype=float))
    return float(np.polyfit(lx, ly, 1)[0])


def deney(ad, boyutlar, kurucu, ustel=False):
    xs, ys = [], []
    print(f"-- {ad}")
    for n in boyutlar:
        veri = kurucu(n)
        sure = en_iyi_sure(veri)
        xs.append(n)
        ys.append(sure)
        print(f"   n={n:8d}  sure={sure * 1e3:12.4f} ms")
    e = egim(xs, ys)
    print(f"   log-log egim = {e:.3f}")
    print()
    return xs, ys, e


# 1) O(1): n elemanlı sözlükte 100000 arama; her n için iş sabit
def kur_sozluk(n):
    d = {i: i * 2 for i in range(n)}
    anahtarlar = [random.randrange(n) for _ in range(100000)]
    def is_():
        s = 0
        for k in anahtarlar:
            s += d[k]
        return s
    return is_

# 2) O(n): Python döngüsüyle toplam
def kur_toplam(n):
    a = [random.randrange(1000) for _ in range(n)]
    def is_():
        s = 0
        for x in a:
            s += x
        return s
    return is_

# 3) O(n log n): sıralama
def kur_sirala(n):
    a = [random.randrange(10**9) for _ in range(n)]
    def is_():
        return sorted(a)
    return is_

# 4) O(n^2): iç içe döngü, çift sayma
def kur_ciftler(n):
    a = [random.randrange(1000) for _ in range(n)]
    def is_():
        s = 0
        for i in range(n):
            ai = a[i]
            for j in range(n):
                if a[j] < ai:
                    s += 1
        return s
    return is_


print("Makine: AMD Ryzen 7 6800H, 8 çekirdek / 16 iş parçacığı, Windows 11")
print(f"Python {sys.version.split()[0]}, numpy {np.__version__}, "
      f"tekrar sayısı={TEKRAR} (en iyi süre alındı)")
print()

deney("O(1) sözlük: 100000 arama", [2**k for k in range(10, 21, 2)],
      kur_sozluk)
deney("O(n) toplam", [2**k for k in range(12, 21)], kur_toplam)
deney("O(n log n) sorted", [2**k for k in range(12, 21)], kur_sirala)
deney("O(n^2) çift karşılaştırma", [250, 500, 1000, 2000], kur_ciftler)
