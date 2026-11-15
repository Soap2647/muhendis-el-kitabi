# fastpow.py: hizli us, matris ustu ve fast doubling ile Fibonacci
import random

CAGRI = 0


def us_ozyineli(x, n, m):
    """x^n mod m. Her cagri tek bir alt cagri yapar."""
    global CAGRI
    CAGRI += 1
    if n == 0:
        return 1 % m
    yarim = us_ozyineli(x, n // 2, m)     # T(n/2)
    sonuc = yarim * yarim % m             # O(1) birlestirme
    if n % 2 == 1:
        sonuc = sonuc * x % m             # tek us: bir ek carpim
    return sonuc


def mat_carp(A, B, m):
    """2x2 matrislerin carpimi, her eleman mod m."""
    return [[(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % m,
             (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % m],
            [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % m,
             (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % m]]


def fib_matris(n, m):
    """[[1,1],[1,0]]^n = [[F(n+1), F(n)], [F(n), F(n-1)]]."""
    sonuc = [[1, 0], [0, 1]]              # birim matris
    taban = [[1, 1], [1, 0]]
    while n > 0:
        if n & 1:
            sonuc = mat_carp(sonuc, taban, m)
        taban = mat_carp(taban, taban, m)
        n >>= 1
    return sonuc[0][1]                    # F(n)


def fib_cift(n, m):
    """Fast doubling: (F(n), F(n+1)) dondurur."""
    if n == 0:
        return 0, 1
    a, b = fib_cift(n // 2, m)            # a = F(k), b = F(k+1)
    c = a * (2 * b - a) % m               # F(2k)
    d = (a * a + b * b) % m               # F(2k+1)
    if n % 2 == 0:
        return c, d
    return d, (c + d) % m                 # F(2k+2) = F(2k) + F(2k+1)


def iteratif(n):
    """Tam sayi Fibonacci; kucuk n icin dogrulama referansi."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


if __name__ == "__main__":
    rnd = random.Random(42)
    BIG = 10 ** 400                       # mod'u tam sayi gibi kullan
    for n in range(0, 301):
        assert fib_matris(n, BIG) == iteratif(n)
        assert fib_cift(n, BIG)[0] == iteratif(n)
    print("n = 0..300: matris ve fast doubling tam sayi ile esit")
    for _ in range(300):
        n = rnd.randint(1, 10 ** 4)
        m = rnd.randint(2, 10 ** 9)
        ref = iteratif(n) % m
        assert fib_matris(n, m) == ref
        assert fib_cift(n, m)[0] == ref
    print("300 rastgele (n <= 10^4, m <= 10^9): mod sonucu esit")
    for _ in range(200):
        x = rnd.randint(2, 10 ** 9)
        n = rnd.randint(0, 10 ** 18)
        m = 10 ** 9 + 7
        assert us_ozyineli(x, n, m) == pow(x, n, m)
    print("200 rastgele us: us_ozyineli == pow(x, n, m)")
    m = 10 ** 9 + 7
    CAGRI = 0
    print("us_ozyineli cagri sayisi (n = 10^18):", end=" ")
    us_ozyineli(2, 10 ** 18, m)
    print(CAGRI)
    f1 = fib_matris(10 ** 18, m)
    f2 = fib_cift(10 ** 18, m)[0]
    print("F(10^18) mod (10^9+7), matris :", f1)
    print("F(10^18) mod (10^9+7), cift   :", f2)
    assert f1 == f2
