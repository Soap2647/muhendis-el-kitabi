# -*- coding: utf-8 -*-
# sayilar_test.py - sayilar.py icin denetim ve RSA ornegi.
import math
from sayilar import ext_gcd, mod_ters, crt, eleme, asal_mi, mr, phi

if __name__ == "__main__":
    print("ext_gcd(240, 46) =", ext_gcd(240, 46))
    print("17^-1 mod 3120 =", mod_ters(17, 3120))
    print("CRT:", crt([2, 3, 2], [3, 5, 7]))
    asal, ops = eleme(10 ** 6)
    print("N=10^6: asal =", len(asal), " ic dongu =", ops)
    print("1000000007 asal mi:", asal_mi(1000000007))
    print("3215031751, taban (2,3,5,7):",
          mr(3215031751, (2, 3, 5, 7)))
    print("2047, taban (2):", mr(2047, (2,)))
    kume = set(eleme(10 ** 5)[0])
    hata = sum(asal_mi(n) != (n in kume) for n in range(10 ** 5))
    print("n < 10^5 icin eleme ile hata:", hata)
    tasar = [a for a in range(2, 561) if math.gcd(a, 561) == 1]
    print("561 Fermat'i geciren taban:",
          sum(pow(a, 560, 561) == 1 for a in tasar), "/", len(tasar))
    print("phi(36) =", phi(36), " phi(3233) =", phi(3233))
    # RSA: p=61, q=53
    p, q = 61, 53
    n, f, e = p * q, (p - 1) * (q - 1), 17
    d = mod_ters(e, f)
    print("n, phi, e, d =", n, f, e, d)
    c = pow(65, e, n)
    print("65 sifreli:", c, " cozulmus:", pow(c, d, n))
    print("tum m icin (m^e)^d == m:",
          all(pow(pow(m, e, n), d, n) == m for m in range(n)))
