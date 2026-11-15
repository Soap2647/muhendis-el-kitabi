# jakobiyen.py: f: R^3 -> R^2 için Jacobian'ı üç yolla hesaplar:
# ileri mod (Dual), ters mod (Deger) ve merkezi fark (sayısal).
import math

import ileri_mod as im
from deger import Deger, topo
from ortak import merkezi_fark


def f_dual(x):
    return [x[0] * x[1] + im.exp(x[2]), x[1] ** 2 * x[2]]


def f_deger(x):
    return [x[0] * x[1] + x[2].exp(), x[1] ** 2 * x[2]]


def f_float(x):
    return [x[0] * x[1] + math.exp(x[2]), x[1] ** 2 * x[2]]


def jakobiyen_ters(f, x):
    # Bir ileri geçiş, sonra çıktı başına bir geri geçiş.
    xs = [Deger(v) for v in x]
    ys = f(xs)
    J = []
    for y in ys:
        # Önceki geri geçişin gradyanlarını sil. Yapraklar (xs) her
        # çıktıda okunduğu için, bağlı olmasalar bile silinir.
        for v in topo(y) + xs:
            v.grad = 0.0
        y.geri()
        J.append([v.grad for v in xs])
    return J


if __name__ == "__main__":
    x = [1.0, 2.0, 0.5]
    n, m = len(x), len(f_float(x))

    Jd = im.jakobiyen_ileri(f_dual, x)
    Jr = jakobiyen_ters(f_deger, x)
    Js = [merkezi_fark(lambda z, i=i: f_float(z)[i], x)
          for i in range(m)]

    print("ileri mod (n = %d geçiş):" % n)
    for satir in Jd:
        print("  ", ["%.6f" % v for v in satir])
    print("ters mod  (1 ileri + m = %d geri geçiş):" % m)
    for satir in Jr:
        print("  ", ["%.6f" % v for v in satir])
    print("sayısal fark:")
    for satir in Js:
        print("  ", ["%.6f" % v for v in satir])

    en_buyuk = 0.0
    for i in range(m):
        for j in range(n):
            en_buyuk = max(en_buyuk, abs(Jd[i][j] - Jr[i][j]),
                           abs(Jd[i][j] - Js[i][j]))
    print("en büyük fark (ileri, ters, sayısal): %.2e" % en_buyuk)
