# -*- coding: utf-8 -*-
"""b53_scan.py - Blelloch dislayici tarama (exclusive prefix sum).

Calistirma: python -I b53_scan.py
Her yukari/asagi super adimi, ayni seviyedeki bagimsiz toplamalardan
olusur; bunlar paralel calistirilabilir. Adim sayisi = 2 log2(n).
"""
import random
from itertools import accumulate


def blelloch(a):
    """Dislayici onek toplami. Doner: (sonuc, islem, izler)."""
    n = len(a)
    x = list(a)
    izler = []
    islem = 0
    # Yukari super (indirgeme): her seviyede 2d'lik bloklarin sonu.
    d = 1
    while d < n:
        for k in range(0, n, 2 * d):
            x[k + 2 * d - 1] += x[k + d - 1]
            islem += 1
        izler.append(("yukari", d, list(x)))
        d *= 2
    x[n - 1] = 0                       # kok sifirlanir
    # Asagi super (dagitma): toplamlar yeniden yayilir.
    d = n // 2
    while d >= 1:
        for k in range(0, n, 2 * d):
            t = x[k + d - 1]
            x[k + d - 1] = x[k + 2 * d - 1]
            x[k + 2 * d - 1] += t
            islem += 1
        izler.append(("asagi", d, list(x)))
        d //= 2
    return x, islem, izler


def dogrula(n, tohum):
    """Rastgele dizilerde Blelloch'u seri referansla sinar."""
    rnd = random.Random(tohum)
    for _ in range(50):
        a = [rnd.randint(-100, 100) for _ in range(n)]
        ref = list(accumulate(a, initial=0))[:-1]
        sonuc, _, _ = blelloch(a)
        if sonuc != ref:
            return False
    return True


if __name__ == "__main__":
    a = [3, 1, 7, 0, 4, 1, 6, 3]
    sonuc, islem, izler = blelloch(a)
    print("girdi :", a)
    for tur, d, durum in izler:
        print(f"{tur:6s} d={d}  {durum}")
    print("cikti :", sonuc)
    print("sirali:", list(accumulate(a, initial=0))[:-1])
    print()
    print("n     toplama   2(n-1)  adim(2log2n)  dogru")
    for k in range(1, 11):
        n = 2 ** k
        arr = list(range(1, n + 1))
        _, islem, _ = blelloch(arr)
        adim = 2 * k
        print(f"{n:<5d} {islem:<9d} {2*(n-1):<7d} {adim:<13d}"
              f" {dogrula(n, 53)}")
