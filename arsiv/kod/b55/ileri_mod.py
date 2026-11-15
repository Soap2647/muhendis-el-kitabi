# ileri_mod.py: ileri mod otomatik türev (ikili sayılar).
# Dual(a, b): a değer, b seçilen girdiye göre türevi.
import math


class Dual:
    def __init__(self, a, b=0.0):
        self.a = float(a)
        self.b = float(b)

    def __repr__(self):
        return f"Dual({self.a:.4f}, {self.b:.4f})"

    @staticmethod
    def _sar(x):
        return x if isinstance(x, Dual) else Dual(x)

    def __add__(self, diger):
        d = self._sar(diger)
        return Dual(self.a + d.a, self.b + d.b)

    def __mul__(self, diger):
        d = self._sar(diger)
        # Çarpım kuralı: (uv)' = u'v + uv'
        return Dual(self.a * d.a, self.a * d.b + self.b * d.a)

    def __pow__(self, n):
        return Dual(self.a ** n, n * self.a ** (n - 1) * self.b)

    def __neg__(self):
        return self * -1

    def __sub__(self, diger):
        return self + (-self._sar(diger))

    def __rsub__(self, diger):
        return self._sar(diger) + (-self)

    __radd__ = __add__
    __rmul__ = __mul__


def exp(x):
    e = math.exp(x.a)
    return Dual(e, e * x.b)


def tanh(x):
    t = math.tanh(x.a)
    return Dual(t, (1 - t * t) * x.b)


def jakobiyen_ileri(f, x):
    # f, Dual listesi alıp Dual listesi döndürür. Her girdi için bir
    # geçiş: o girdinin teğet değeri 1, diğerleri 0 yapılır.
    n = len(x)
    sutunlar = []
    for j in range(n):
        xd = [Dual(x[i], 1.0 if i == j else 0.0) for i in range(n)]
        sutunlar.append([y.b for y in f(xd)])
    m = len(sutunlar[0])
    return [[sutunlar[j][i] for j in range(n)] for i in range(m)]
