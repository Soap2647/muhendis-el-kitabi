# ornek2.py: ev soygunu, dairesel varyant (iki dogrusal DP)
import random


def dogrusal(degerler):
    onceki, simdiki = 0, 0          # iki onceki ve onceki sonuc
    for v in degerler:
        onceki, simdiki = simdiki, max(simdiki, onceki + v)
    return simdiki


def dairesel(degerler):
    n = len(degerler)
    if n == 1:
        return degerler[0]
    return max(dogrusal(degerler[:-1]), dogrusal(degerler[1:]))


def kaba(degerler, dairesel_mi):
    n = len(degerler)
    best = 0
    for mask in range(1 << n):
        secim = [i for i in range(n) if mask >> i & 1]
        ok = all(b - a > 1 for a, b in zip(secim, secim[1:]))
        if dairesel_mi and n > 1 and 0 in secim and n - 1 in secim:
            ok = False
        if ok:
            best = max(best, sum(degerler[i] for i in secim))
    return best


def main():
    evler = [2, 3, 2]
    print("dairesel [2,3,2]:", dairesel(evler))
    evler = [1, 2, 3, 1]
    print("dairesel [1,2,3,1]:", dairesel(evler))
    print("dogrusal [1,2,3,1]:", dogrusal(evler))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n = rnd.randint(1, 8)
        d = [rnd.randint(0, 20) for _ in range(n)]
        if dogrusal(d) != kaba(d, False):
            hata += 1
        if dairesel(d) != kaba(d, True):
            hata += 1
    print("300 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
