# -*- coding: utf-8 -*-
# sayma.py - bozuk permutasyon, Catalan ve Binet denetimi.
import itertools
import math


def bozuk_formul(n):
    """D_n = sum_{k=0}^{n} (-1)^k * n!/k!"""
    return sum((-1) ** k * (math.factorial(n) // math.factorial(k))
               for k in range(n + 1))


def bozuk_kaba(n):
    return sum(1 for p in itertools.permutations(range(n))
               if all(p[i] != i for i in range(n)))


def catalan(n):
    return math.comb(2 * n, n) // (n + 1)


def dengeli_kaba(n):
    """Uzunlugu 2n olan dengeli parantez dizgilerini sayar."""
    say = 0
    for dizgi in itertools.product("()", repeat=2 * n):
        d, gecerli = 0, True
        for c in dizgi:
            d += 1 if c == "(" else -1
            if d < 0:
                gecerli = False
                break
        if gecerli and d == 0:
            say += 1
    return say


def binet(n):
    s5 = math.sqrt(5)
    return round(((1 + s5) / 2) ** n / s5
                 - ((1 - s5) / 2) ** n / s5)


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


if __name__ == "__main__":
    print("n  kaba  formul")
    for n in range(9):
        print(n, bozuk_kaba(n), bozuk_formul(n))
    print("n  dengeli  catalan")
    for n in range(7):
        print(n, dengeli_kaba(n), catalan(n))
    ilk = next(n for n in range(200) if binet(n) != fib(n))
    print("Binet ilk yanlis n:", ilk)
    print("F(71) =", fib(71), " binet(71) =", binet(71))
