# karatsuba.py: okul yontemi ve Karatsuba (sayilar 10^4 tabanli)
import random
import sys
import time

TABAN = 10 ** 4
ESIK = 32                 # bu uzunlukun altinda okul yontemi


def normal(a):
    """Sondaki sifir basamaklari at; en az bir basamak kalir."""
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a


def topla(a, b):
    c, elde = [], 0
    for i in range(max(len(a), len(b))):
        s = elde
        if i < len(a):
            s += a[i]
        if i < len(b):
            s += b[i]
        c.append(s % TABAN)
        elde = s // TABAN
    if elde:
        c.append(elde)
    return normal(c)


def cikar(a, b):
    """a - b, a >= b varsayilir."""
    c, borc = [], 0
    for i in range(len(a)):
        s = a[i] - borc - (b[i] if i < len(b) else 0)
        borc = 1 if s < 0 else 0
        c.append(s + borc * TABAN)
    return normal(c)


def kaydir(a, k):
    """a * TABAN^k (sola k basamak ekle)."""
    return [0] * k + a


def okul(a, b):
    """O(n*m) okul yontemi: her basamak ciftini carp, topla."""
    c = [0] * (len(a) + len(b))
    for i, x in enumerate(a):
        elde = 0
        for j, y in enumerate(b):
            t = c[i + j] + x * y + elde
            c[i + j] = t % TABAN
            elde = t // TABAN
        c[i + len(b)] += elde
    return normal(c)


def bol(a, m):
    """a = high * TABAN^m + low; iki parcayi dondurur."""
    low = normal(a[:m]) or [0]
    high = normal(a[m:]) or [0]
    return low, high


def karatsuba(a, b):
    if min(len(a), len(b)) <= ESIK:
        return okul(a, b)
    m = max(len(a), len(b)) // 2
    a0, a1 = bol(a, m)
    b0, b1 = bol(b, m)
    z0 = karatsuba(a0, b0)                       # a0 * b0
    z2 = karatsuba(a1, b1)                       # a1 * b1
    z1 = karatsuba(topla(a0, a1), topla(b0, b1))  # (a0+a1)(b0+b1)
    z1 = cikar(cikar(z1, z0), z2)                # a0*b1 + a1*b0
    sonuc = topla(z0, kaydir(z1, m))
    return topla(sonuc, kaydir(z2, 2 * m))


def deger(a):
    return sum(d * TABAN ** i for i, d in enumerate(a))


def digitler(n):
    d = []
    while n:
        d.append(n % TABAN)
        n //= TABAN
    return d or [0]


if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(400):
        a = [rnd.randrange(TABAN) for _ in range(rnd.randint(1, 300))]
        b = [rnd.randrange(TABAN) for _ in range(rnd.randint(1, 300))]
        ref = digitler(deger(a) * deger(b))
        assert okul(a, b) == ref
        assert karatsuba(a, b) == ref
    print("400 rastgele cift: okul == karatsuba == tam sayi carpimi")
    print("TABAN =", TABAN, "| bit/basamak (CPython):",
          sys.int_info.bits_per_digit)
    print("\nlimb  ondalik  okul(s)  karats(s)  yerlesik(s)")
    rows = []
    for L in (128, 256, 512, 1024, 2048):
        a = [rnd.randrange(TABAN) for _ in range(L)]
        b = [rnd.randrange(TABAN) for _ in range(L)]
        t0 = time.perf_counter()
        okul(a, b)
        t1 = time.perf_counter()
        karatsuba(a, b)
        t2 = time.perf_counter()
        x, y = deger(a), deger(b)
        t3 = time.perf_counter()
        x * y
        t4 = time.perf_counter()
        r = (L, 4 * L, t1 - t0, t2 - t1, t4 - t3)
        rows.append(r)
        print("%4d  %7d  %7.3f  %9.3f  %11.6f" % r)
    csv_ad = "karatsuba_olcum.csv"
    if len(sys.argv) > 1:
        csv_ad = sys.argv[1]
    with open(csv_ad, "w", encoding="utf-8") as f:
        f.write("limb,ondalik,okul,karatsuba,yerlesik\n")
        for r in rows:
            f.write("%d,%d,%.6f,%.6f,%.9f\n" % r)
