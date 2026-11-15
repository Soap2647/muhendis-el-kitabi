# maxsub.py: maksimum alt dizi toplami: D&C ve Kadane
import random
import time


def dc_max(a, lo, hi):
    """a[lo:hi] icinde (toplam, bas, son) dondurur; son exclusive."""
    if hi - lo == 1:
        return a[lo], lo, lo + 1
    mid = (lo + hi) // 2
    sol = dc_max(a, lo, mid)
    sag = dc_max(a, mid, hi)
    # Ortayi kesen en iyi aralik: sol kisim mid'den geriye,
    # sag kisim mid'den ileriye dogru genisler.
    bl_top, bl_bas, s = -10 ** 18, mid, 0
    for i in range(mid - 1, lo - 1, -1):
        s += a[i]
        if s > bl_top:
            bl_top, bl_bas = s, i
    br_top, br_son, s = -10 ** 18, mid, 0
    for j in range(mid, hi):
        s += a[j]
        if s > br_top:
            br_top, br_son = s, j + 1
    orta = (bl_top + br_top, bl_bas, br_son)
    return max(sol, sag, orta, key=lambda t: t[0])


def kadane(a):
    """dp[i] = en buyuk toplam, a[i] ile biten aralik."""
    dp, bas = a[0], 0
    en = (a[0], 0, 1)
    for i in range(1, len(a)):
        if dp > 0:    # onceki birikimi surdur
            dp += a[i]
        else:                         # yeni aralik baslat
            dp, bas = a[i], i
        if dp > en[0]:
            en = (dp, bas, i + 1)
    return en


def brute(a):
    """O(n^2): tum (i, j) cifti icin on toplamlarla."""
    on = [0]
    for x in a:
        on.append(on[-1] + x)
    n = len(a)
    return max(on[j] - on[i] for i in range(n)
               for j in range(i + 1, n + 1))


if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(500):
        n = rnd.randint(1, 40)
        a = [rnd.randint(-20, 20) for _ in range(n)]
        ref = brute(a)
        t1, l1, r1 = dc_max(a, 0, n)
        t2, l2, r2 = kadane(a)
        assert t1 == ref and sum(a[l1:r1]) == ref
        assert t2 == ref and sum(a[l2:r2]) == ref
    print("500 rastgele dizi: D&C = Kadane = O(n^2)")
    a = [rnd.randint(-10 ** 6, 10 ** 6) for _ in range(10 ** 5)]
    t0 = time.perf_counter()
    r1 = dc_max(a, 0, len(a))
    t1 = time.perf_counter()
    r2 = kadane(a)
    t2 = time.perf_counter()
    print("n = 10^5: D&C %.3f s, Kadane %.3f s" % (t1 - t0, t2 - t1))
    print("ayni toplam:", r1[0] == r2[0], "| toplam =", r2[0])
