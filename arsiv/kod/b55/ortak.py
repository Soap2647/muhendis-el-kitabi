# ortak.py: sentetik veri, başlangıç ağırlıkları, sayısal gradyan.
# Tüm deneyler aynı veriyi ve aynı başlangıç ağırlıklarını kullanır.
import math
import random


def veri_uret(n=80, tohum=55):
    # İç içe iki yarım ay. Sınıf +1 ve -1; sabit tohumla tekrarlanır.
    rnd = random.Random(tohum)
    X, Y = [], []
    for _ in range(n // 2):
        t = rnd.uniform(0.0, math.pi)
        X.append([math.cos(t) + rnd.gauss(0, 0.1),
                  math.sin(t) + rnd.gauss(0, 0.1)])
        Y.append(1.0)
        X.append([1 - math.cos(t) + rnd.gauss(0, 0.1),
                  0.5 - math.sin(t) + rnd.gauss(0, 0.1)])
        Y.append(-1.0)
    return X, Y


def agirlik_uret(boyutlar, tohum=55):
    # Döndürür: [(W, b), ...]; W[i][j] girdi i -> çıktı j.
    rnd = random.Random(tohum + 1)
    katmanlar = []
    for giris, cikis in zip(boyutlar, boyutlar[1:]):
        olcek = 1.0 / math.sqrt(giris)
        W = [[rnd.uniform(-olcek, olcek) for _ in range(cikis)]
             for _ in range(giris)]
        katmanlar.append((W, [0.0] * cikis))
    return katmanlar


def merkezi_fark(f, x, h=1e-6):
    # Her x_i için (f(x + h e_i) - f(x - h e_i)) / 2h.
    g = []
    for i in range(len(x)):
        xp, xm = list(x), list(x)
        xp[i] += h
        xm[i] -= h
        g.append((f(xp) - f(xm)) / (2 * h))
    return g
