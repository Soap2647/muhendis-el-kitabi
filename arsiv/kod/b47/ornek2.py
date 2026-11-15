# -*- coding: utf-8 -*-
# ornek2.py - genisletilmis Oklid ile modüler ters izi.


def ters_iz(a, m):
    """Doner: (gcd, a'nin m'ye gore tersi).
    Her satir: r = s*a + t*m olacak bicimde tutulur."""
    satirlar = [(m, 0, 1), (a % m, 1, 0)]
    print("  q       r       s       t")
    while satirlar[-1][0] != 0:
        (r0, s0, t0), (r1, s1, t1) = satirlar[-2], satirlar[-1]
        q = r0 // r1
        yeni = (r0 - q * r1, s0 - q * s1, t0 - q * t1)
        satirlar.append(yeni)
        print("%3d %7d %7d %7d" % (q, yeni[0], yeni[1], yeni[2]))
    g, s, _ = satirlar[-2]
    return g, s % m


if __name__ == "__main__":
    g, ters = ters_iz(17, 3120)
    print("gcd =", g, "  ters =", ters)
    print("17 * ters mod 3120 =", 17 * ters % 3120)
    print("pow(17, -1, 3120) =", pow(17, -1, 3120))
