# zincir.py: zincir kuralı. Tek değişkende f(x) = sin(x^2), sonra
# çok değişkende f = g(h(x)) için Jacobian çarpımı J_f = J_g J_h.
import math

from ortak import merkezi_fark


def f(x):
    return math.sin(x * x)


def turev_elle(x):
    # u = x^2, f = sin(u): f' = cos(u) * u' = cos(x^2) * 2x
    return math.cos(x * x) * 2 * x


def tek_degisken():
    basliklar = ("x", "f(x)", "elle f'", "sayisal", "fark")
    print("%6s %12s %12s %12s %10s" % basliklar)
    for x in [0.5, 1.2, -0.8, 2.0]:
        sayisal = merkezi_fark(lambda z: f(z[0]), [x])[0]
        elle = turev_elle(x)
        print("%6.2f %12.6f %12.6f %12.6f %10.1e"
              % (x, f(x), elle, sayisal, abs(elle - sayisal)))


# Çok değişkenli: h: R^2 -> R^2, g: R^2 -> R, f = g o h
def h(x):
    return [x[0] * x[1], x[0] + x[1] ** 2]


def g(u):
    return u[0] ** 2 + math.sin(u[1])


def F(x):
    return g(h(x))


def jakobiyen_h(x):
    return [[x[1], x[0]], [1.0, 2 * x[1]]]


def gradyan_g(u):
    return [2 * u[0], math.cos(u[1])]


def coklu_degisken(x):
    Jh = jakobiyen_h(x)
    Jg = gradyan_g(h(x))
    # Satır vektörü (1x2) ile matris (2x2) çarpımı
    carpim = [sum(Jg[k] * Jh[k][j] for k in range(2))
              for j in range(2)]
    sayisal = merkezi_fark(F, x)
    print("u = h(x)  =", ["%.4f" % v for v in h(x)])
    print("J_h       =", Jh)
    print("J_g       =", ["%.4f" % v for v in Jg])
    print("J_g J_h   =", ["%.6f" % v for v in carpim])
    print("sayisal   =", ["%.6f" % v for v in sayisal])


if __name__ == "__main__":
    tek_degisken()
    print()
    coklu_degisken([1.0, 0.5])
