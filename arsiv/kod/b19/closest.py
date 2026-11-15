# closest.py: en yakin nokta cifti, kaba kuvvet ve bol-fethet
import heapq
import math
import random
import time

ISARET = {"max_komsu": 0}


def mesafe(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def kaba(P):
    """Tum ciftler: O(n^2). Dogrulama referansi."""
    en = (math.inf, None)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = mesafe(P[i], P[j])
            if d < en[0]:
                en = (d, (P[i], P[j]))
    return en


def bol_fethet(px):
    """px x'e gore sirali. Donus: (d, cift, y sirali liste)."""
    n = len(px)
    if n <= 3:
        d, cift = kaba(px)
        return d, cift, sorted(px, key=lambda p: p[1])
    mid = n // 2
    xm = px[mid][0]                                  # bolme cizgisi
    dl, cl, yl = bol_fethet(px[:mid])
    dr, cr, yr = bol_fethet(px[mid:])
    d, cift = (dl, cl) if dl <= dr else (dr, cr)
    y = list(heapq.merge(yl, yr, key=lambda p: p[1]))  # birlestir
    serit = [p for p in y if abs(p[0] - xm) < d]
    for i, p in enumerate(serit):
        sayac = 0
        for q in serit[i + 1:]:
            if q[1] - p[1] >= d:   # y farki d'den buyuk
                break
            sayac += 1
            dd = mesafe(p, q)
            if dd < d:
                d, cift = dd, (p, q)
        ISARET["max_komsu"] = max(ISARET["max_komsu"], sayac)
    return d, cift, y


def en_yakin(P):
    px = sorted(P)                                   # once x'e gore
    d, cift, _ = bol_fethet(px)
    return d, cift


if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(300):
        n = rnd.randint(2, 60)
        P = [(rnd.randint(0, 500), rnd.randint(0, 500))
             for _ in range(n)]
        d1, _ = kaba(P)
        d2, _ = en_yakin(P)
        assert abs(d1 - d2) < 1e-12, (d1, d2)
    print("300 rastgele kume: bol-fethet == kaba kuvvet")
    print("serit icinde bir noktanin en fazla komsu sayisi:",
          ISARET["max_komsu"])
    for n in (500, 2000):
        P = [(rnd.random(), rnd.random()) for _ in range(n)]
        t0 = time.perf_counter()
        d1, _ = kaba(P)
        t1 = time.perf_counter()
        d2, _ = en_yakin(P)
        t2 = time.perf_counter()
        print("n=%5d kaba=%.3fs bol-fethet=%.3fs"
              % (n, t1 - t0, t2 - t1))
        assert abs(d1 - d2) < 1e-12
