# -*- coding: utf-8 -*-
# ornek4.py - kucuk RSA: kare-carpma izi ve neden calistigi.


def ikili_us(a, e, m, izle=True):
    """a^e mod m; e'nin bitlerini en dusukten basa tarar."""
    sonuc, taban = 1, a % m
    if izle:
        print("bit  taban  sonuc")
    while e > 0:
        bit = e & 1
        if bit:
            sonuc = sonuc * taban % m
        taban = taban * taban % m
        if izle:
            print("%3d %6d %6d" % (bit, taban, sonuc))
        e >>= 1
    return sonuc


if __name__ == "__main__":
    p, q = 61, 53
    n, f = p * q, (p - 1) * (q - 1)
    e = 17
    d = 2753
    c = ikili_us(65, e, n)
    print("sifreli c =", c, " pow kontrol:", pow(65, e, n))
    print("e*d =", e * d, " e*d - 1 =", e * d - 1,
          " = 15 * phi?", (e * d - 1) == 15 * f)
    m = ikili_us(c, d, n, izle=False)
    print("cozulmus m =", m)
