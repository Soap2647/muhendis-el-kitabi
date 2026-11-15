import random


def ikili(a, x):
    lo, hi, say = 0, len(a) - 1, 0
    while lo <= hi:
        say += 1
        orta = (lo + hi) // 2
        if a[orta] == x:
            return orta, say
        if a[orta] < x:
            lo = orta + 1
        else:
            hi = orta - 1
    return -1, say


def enterpolasyon(a, x):
    lo, hi, say = 0, len(a) - 1, 0
    while lo <= hi and a[lo] <= x <= a[hi]:
        say += 1
        if a[hi] == a[lo]:
            pos = lo
        else:
            pos = lo + (x - a[lo]) * (hi - lo) // (a[hi] - a[lo])
        if a[pos] == x:
            return pos, say
        if a[pos] < x:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1, say


def ort_adim(a, sorgular, f):
    toplam = 0
    for x in sorgular:
        toplam += f(a, x)[1]
    return toplam / len(sorgular)


if __name__ == "__main__":
    random.seed(42)
    print("tekduzen veri (rastgele tamsayilar)")
    print("   n  ikili  enterp.")
    for n in [1000, 10000, 100000, 1000000]:
        a = sorted(random.sample(range(10**9), n))
        sorgular = [random.choice(a) for _ in range(2000)]
        print("%7d %6.2f %7.2f" % (n, ort_adim(a, sorgular, ikili),
              ort_adim(a, sorgular, enterpolasyon)))
    print("ussel veri (a[i] = 2^i)")
    print("   n  ikili  enterp.")
    for n in [10, 20, 40, 60]:
        a = [2**i for i in range(n)]
        sorgular = a
        print("%7d %6.2f %7.2f" % (n, ort_adim(a, sorgular, ikili),
              ort_adim(a, sorgular, enterpolasyon)))
