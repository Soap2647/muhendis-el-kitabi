# fft_poly.py: Cooley-Tukey FFT ile polinom carpimi
import cmath
import random
import time

import numpy as np


def fft(a):
    """Uzunluk 2'nin kuvveti. O(n log n)."""
    n = len(a)
    if n == 1:
        return a[:]
    cift = fft(a[0::2])                 # cift indisler
    tek = fft(a[1::2])                  # tek indisler
    sonuc = [0j] * n
    for k in range(n // 2):
        t = cmath.exp(-2j * cmath.pi * k / n) * tek[k]
        sonuc[k] = cift[k] + t          # kelebek: ust kanat
        sonuc[k + n // 2] = cift[k] - t  # kelebek: alt kanat
    return sonuc


def ters_fft(F):
    n = len(F)
    g = fft([z.conjugate() for z in F])
    return [z.conjugate() / n for z in g]


def carp_fft(p, q):
    """Katsayi listeleri p, q; carpim katsayilari (yuvarlanmis)."""
    boyut = len(p) + len(q) - 1
    n = 1
    while n < boyut:
        n *= 2
    P = fft([complex(x) for x in p] + [0j] * (n - len(p)))
    Q = fft([complex(x) for x in q] + [0j] * (n - len(q)))
    R = [x * y for x, y in zip(P, Q)]    # noktasal carpim
    r = ters_fft(R)
    return [round(z.real) for z in r[:boyut]]


def carp_direkt(p, q):
    c = [0] * (len(p) + len(q) - 1)
    for i, x in enumerate(p):
        for j, y in enumerate(q):
            c[i + j] += x * y            # O(n^2)
    return c


if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(300):
        p = [rnd.randint(0, 9) for _ in range(rnd.randint(1, 40))]
        q = [rnd.randint(0, 9) for _ in range(rnd.randint(1, 40))]
        ref = carp_direkt(p, q)
        assert carp_fft(p, q) == ref
        assert list(np.convolve(p, q)) == ref
    print("300 rastgele cift: FFT == dogrudan == numpy.convolve")
    for n in (512, 1024, 2048):
        p = [rnd.randint(0, 9) for _ in range(n)]
        q = [rnd.randint(0, 9) for _ in range(n)]
        t0 = time.perf_counter()
        carp_direkt(p, q)
        t1 = time.perf_counter()
        carp_fft(p, q)
        t2 = time.perf_counter()
        print("n=%5d direkt=%.3fs fft=%.3fs" % (n, t1 - t0, t2 - t1))
