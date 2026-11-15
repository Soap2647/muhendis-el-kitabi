# Kesir (Python): ayni invariant; Fraction ile rastgele sinama
import math
import random
from fractions import Fraction


class Kesir:
    # invariant: payda > 0, gcd(pay, payda) == 1
    __slots__ = ("_pay", "_payda")

    def __init__(self, pay, payda=1):
        if payda == 0:
            raise ValueError("payda sifir")
        if payda < 0:
            pay, payda = -pay, -payda
        g = math.gcd(pay, payda)           # gcd(0, q) = q
        self._pay, self._payda = pay // g, payda // g

    @property
    def pay(self):
        return self._pay

    @property
    def payda(self):
        return self._payda

    def __add__(self, o):
        return Kesir(self._pay * o._payda + o._pay * self._payda,
                     self._payda * o._payda)

    def __mul__(self, o):
        return Kesir(self._pay * o._pay, self._payda * o._payda)

    def __eq__(self, o):
        return (self._pay, self._payda) == (o._pay, o._payda)

    def __hash__(self):
        return hash((self._pay, self._payda))

    def __repr__(self):
        return "Kesir(%d, %d)" % (self._pay, self._payda)


rng = random.Random(42)
hata = 0
for _ in range(100000):
    p, q = rng.randint(-20, 20), rng.randint(-20, 20)
    if q == 0:
        q = 1
    a = Kesir(p, q)
    fa = Fraction(p, q)
    b_p, b_q = rng.randint(-20, 20) or 1, 3
    b = Kesir(b_p, b_q)
    fb = Fraction(b_p, b_q)
    if (a + b).pay != (fa + fb).numerator or \
       (a * b).payda != (fa * fb).denominator:
        hata += 1
print("100000 islemde Fraction ile uyusmazlik:", hata)
print(Kesir(6, -4), Kesir(0, 5), Kesir(1, 2) + Kesir(1, 3))
print("kume:", {Kesir(1, 2), Kesir(2, 4)})
