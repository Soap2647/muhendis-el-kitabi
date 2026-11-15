import random


def medyan(a, b):
    """İki sıralı dizinin birleşiminin medyanı, O(log min(m, n))."""
    if len(a) > len(b):
        a, b = b, a
    m, n = len(a), len(b)
    toplam = m + n
    yarim = (toplam + 1) // 2        # sol kümedeki eleman sayısı
    lo, hi = 0, m
    while lo <= hi:
        i = (lo + hi) // 2           # a'dan sol kümeye alınan
        j = yarim - i                # b'den sol kümeye alınan
        a_sol = a[i - 1] if i > 0 else float("-inf")
        a_sag = a[i] if i < m else float("inf")
        b_sol = b[j - 1] if j > 0 else float("-inf")
        b_sag = b[j] if j < n else float("inf")
        if a_sol <= b_sag and b_sol <= a_sag:
            if toplam % 2 == 1:
                return float(max(a_sol, b_sol))
            return (max(a_sol, b_sol) + min(a_sag, b_sag)) / 2
        if a_sol > b_sag:
            hi = i - 1
        else:
            lo = i + 1
    raise ValueError("girdi siralı degil")


if __name__ == "__main__":
    random.seed(42)
    print("ornek:", medyan([1, 3, 8], [2, 4, 6, 9]))
    hatali = 0
    for _ in range(3000):
        a = sorted(random.randint(-50, 50)
                   for _ in range(random.randint(0, 12)))
        b = sorted(random.randint(-50, 50)
                   for _ in range(random.randint(0, 12)))
        c = sorted(a + b)
        if not c:
            continue
        k = len(c)
        if k % 2:
            beklenen = c[k // 2]
        else:
            beklenen = (c[k // 2 - 1] + c[k // 2]) / 2
        if medyan(a, b) != beklenen:
            hatali += 1
    print("3000 rastgele test, hatali:", hatali)
