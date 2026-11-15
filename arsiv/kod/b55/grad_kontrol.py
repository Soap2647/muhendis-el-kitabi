# grad_kontrol.py: her işlemi ve rastgele ifadeleri sayısal gradyanla
# karşılaştırır. Tohum sabit: sonuçlar her çalıştırmada aynıdır.
import math
import random

from deger import Deger
from ortak import merkezi_fark


def tanh_(a):
    return a.tanh() if isinstance(a, Deger) else math.tanh(a)


def exp_(a):
    return a.exp() if isinstance(a, Deger) else math.exp(a)


def log_(a):
    return a.log() if isinstance(a, Deger) else math.log(a)


def relu_(a):
    return a.relu() if isinstance(a, Deger) else max(0.0, a)


def goreli_hata(a, b):
    return abs(a - b) / max(1.0, abs(a), abs(b))


def tek_tek(x):
    basliklar = ("ifade", "otomatik", "sayisal", "hata")
    print("%-12s %12s %12s %10s" % basliklar)
    testler = [
        ("x0 + x1", lambda v: v[0] + v[1]),
        ("x0 * x1", lambda v: v[0] * v[1]),
        ("x0 / x1", lambda v: v[0] / v[1]),
        ("x0 ** 3", lambda v: v[0] ** 3),
        ("tanh(x0)", lambda v: tanh_(v[0])),
        ("exp(x0)", lambda v: exp_(v[0])),
        ("log(x0)", lambda v: log_(v[0])),
        ("relu(x0-1)", lambda v: relu_(v[0] - 1.0)),
        ("sigmoid(x0)", lambda v: 1 / (1 + exp_(-v[0]))),
    ]
    for ad, f in testler:
        xs = [Deger(v) for v in x]
        y = f(xs)
        y.geri()
        otomatik = [v.grad for v in xs]
        sayisal = merkezi_fark(lambda z: f(z), x)
        hata = max(goreli_hata(p, q)
                   for p, q in zip(otomatik, sayisal))
        print("%-12s %12.6f %12.6f %10.1e" % (ad, otomatik[0],
                                             sayisal[0], hata))


# Rastgele ifadeler: adım adım bir program. Her adım iki önceki değeri
# bir işlemle birleştirip listeye ekler.
ISLEMLER = ["+", "-", "*", "tanh", "relu", "kare"]


def program_uret(rnd, adim=6, girdi=3):
    prog, sayi = [], girdi
    for _ in range(adim):
        prog.append((rnd.choice(ISLEMLER), rnd.randrange(sayi),
                     rnd.randrange(sayi)))
        sayi += 1
    return prog


def calistir(prog, girdi):
    deger = list(girdi)
    for op, i, j in prog:
        a, b = deger[i], deger[j]
        if op == "+":
            c = a + b
        elif op == "-":
            c = a - b
        elif op == "*":
            c = a * b
        elif op == "tanh":
            c = tanh_(a)
        elif op == "relu":
            c = relu_(a)
        else:
            c = a ** 2
        deger.append(c)
    return deger[-1]


def rastgele_denetim(n=300, tohum=55):
    rnd = random.Random(tohum)
    en_buyuk, kotu = 0.0, 0
    for _ in range(n):
        prog = program_uret(rnd)
        x = [rnd.uniform(-1.0, 1.0) for _ in range(3)]
        xs = [Deger(v) for v in x]
        calistir(prog, xs).geri()
        otomatik = [v.grad for v in xs]
        sayisal = merkezi_fark(lambda z: calistir(prog, z), x)
        hata = max(goreli_hata(p, q)
                   for p, q in zip(otomatik, sayisal))
        en_buyuk = max(en_buyuk, hata)
        kotu += hata > 1e-6
    print("rastgele ifade sayisi:", n)
    print("en buyuk goreli hata: %.2e" % en_buyuk)
    print("1e-6 esigini asan    :", kotu)


if __name__ == "__main__":
    tek_tek([0.7, 1.3])
    print()
    rastgele_denetim()
