# -*- coding: utf-8 -*-
# sayilar.py - Oklid ailesi, CRT, Euler totient, asallik testleri.
import math

TABAN = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def ext_gcd(a, b):
    """Doner: (g, x, y), oyle ki a*x + b*y = g = gcd(a, b)."""
    if b == 0:
        return a, 1, 0
    g, x1, y1 = ext_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def mod_ters(a, m):
    g, x, _ = ext_gcd(a % m, m)
    if g != 1:
        raise ValueError("ters yok")
    return x % m


def crt(kalanlar, modler):
    """x = kalan_i (mod m_i); moduller ikişerli asal olmali."""
    x, M = 0, 1
    for r, m in zip(kalanlar, modler):
        t = (r - x) * mod_ters(M, m) % m
        x += M * t
        M *= m
    return x % M, M


def eleme(n):
    """Eratosthenes. Doner: (asal listesi, ic dongu sayisi)."""
    ele = [True] * (n + 1)
    ele[0:2] = [False, False]
    ops = 0
    for p in range(2, math.isqrt(n) + 1):
        if ele[p]:
            for k in range(p * p, n + 1, p):
                ele[k] = False
                ops += 1
    return [i for i in range(n + 1) if ele[i]], ops


def mr(n, tabanlar=TABAN):
    """Saf Miller-Rabin. n tek ve 37'den buyuk varsayilir."""
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in tabanlar:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def asal_mi(n):
    if n < 2:
        return False
    for p in TABAN:
        if n % p == 0:
            return n == p
    return mr(n)


def phi(n):
    """Euler totient: asal carpanlari uzerinden."""
    sonuc, m, p = n, n, 2
    while p * p <= m:
        if m % p == 0:
            while m % p == 0:
                m //= p
            sonuc -= sonuc // p
        p += 1
    if m > 1:
        sonuc -= sonuc // m
    return sonuc
