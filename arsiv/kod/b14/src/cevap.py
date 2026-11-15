import math


def tam_karekok(n):
    """floor(sqrt(n)): en büyük k, k*k <= n. Yüklem: k*k > n."""
    lo, hi = 0, n + 1
    while lo < hi:
        orta = lo + (hi - lo) // 2
        if orta * orta <= n:
            lo = orta + 1
        else:
            hi = orta
    return lo - 1


def kok_ikili(c, tur=60):
    """c >= 1 için karekök: sabit sayıda yarılama."""
    lo, hi = 0.0, max(1.0, c)
    for _ in range(tur):
        orta = (lo + hi) / 2
        if orta * orta < c:
            lo = orta
        else:
            hi = orta
    return lo


if __name__ == "__main__":
    for n in range(10000):
        assert tam_karekok(n) == math.isqrt(n), n
    print("tam_karekok: 0..9999 icin math.isqrt ile ayni")
    print("kok_ikili(2):", repr(kok_ikili(2.0)))
    print("math.sqrt(2):", repr(math.sqrt(2.0)))
    print("fark:", abs(kok_ikili(2.0) - math.sqrt(2.0)))
