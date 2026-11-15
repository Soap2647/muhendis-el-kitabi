import random


def ilk_dogru(lo, hi, p):
    """[lo, hi) üzerinde p monoton (F...F T...T) olsun.
    İlk T'nin indeksini döndürür; hiç T yoksa hi."""
    while lo < hi:
        orta = lo + (hi - lo) // 2
        if p(orta):
            hi = orta
        else:
            lo = orta + 1
    return lo


def dogrusal_ilk(lo, hi, p):
    """Karşılaştırma için doğrusal tarama."""
    for i in range(lo, hi):
        if p(i):
            return i
    return hi


if __name__ == "__main__":
    random.seed(42)
    p = lambda i: i * i >= 50
    dizi = "".join("T" if p(i) else "F" for i in range(10))
    print("p(0..9):", dizi)
    print("ilk T (i*i >= 50):", ilk_dogru(0, 100, p))
    hatali = 0
    for _ in range(2000):
        n = random.randint(0, 200)
        esik = random.randint(0, n)
        q = lambda i, e=esik: i >= e
        if ilk_dogru(0, n, q) != dogrusal_ilk(0, n, q):
            hatali += 1
    print("2000 rastgele test, hatali:", hatali)
