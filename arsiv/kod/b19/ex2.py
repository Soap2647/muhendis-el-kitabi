# ex2.py: cogunluk elemani, D&C ve Boyer-Moore
import random
from collections import Counter


def cogunluk_dc(a, lo, hi, iz=False):
    """[lo, hi) icinde bir aday dondurur; cogunluk varsa odur."""
    if hi - lo == 1:
        return a[lo]
    mid = (lo + hi) // 2
    sol = cogunluk_dc(a, lo, mid, iz)
    sag = cogunluk_dc(a, mid, hi, iz)
    if sol == sag:
        return sol
    cs = sum(1 for x in a[lo:hi] if x == sol)
    cg = sum(1 for x in a[lo:hi] if x == sag)
    aday = sol if cs > cg else sag
    if iz:
        print("[%d,%d) sol=%d sag=%d cs=%d cg=%d -> %d"
              % (lo, hi, sol, sag, cs, cg, aday))
    return aday


def boyer_moore(a):
    aday, sayac = None, 0
    for x in a:
        if sayac == 0:
            aday = x
        sayac += 1 if x == aday else -1
    return aday


if __name__ == "__main__":
    rnd = random.Random(42)
    a = [2, 2, 1, 1, 1, 2, 2]
    print("Iz (n=7):")
    cogunluk_dc(a, 0, len(a), iz=True)
    for _ in range(300):
        n = rnd.randint(1, 30)
        b = [rnd.randint(0, 3) for _ in range(n)]
        ad = cogunluk_dc(b, 0, n)
        sayi = Counter(b).most_common(1)[0]
        if sayi[1] * 2 > n:
            assert ad == sayi[0] == boyer_moore(b)
    print("300 rastgele dizi: D&C ve Boyer-Moore cogunlugu bulur")
