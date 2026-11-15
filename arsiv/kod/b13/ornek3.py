def kinci_en_kucuk(a, k):
    """a icinde k. en kucuk (0 tabanli) deger. Beklenen O(n)."""
    a = list(a)
    lo, hi = 0, len(a) - 1
    while True:
        if lo == hi:
            return a[lo]
        p = a[hi]
        i = lo
        for j in range(lo, hi):
            if a[j] < p:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[i], a[hi] = a[hi], a[i]
        if k == i:
            return a[i]
        if k < i:
            hi = i - 1
        else:
            lo = i + 1


if __name__ == "__main__":
    veri = [7, 2, 9, 4, 1, 8, 3]
    for k in range(len(veri)):
        print(k, kinci_en_kucuk(veri, k))
