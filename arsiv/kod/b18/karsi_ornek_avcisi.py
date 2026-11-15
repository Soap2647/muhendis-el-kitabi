# karsi_ornek_avcisi.py: acgozlu bir kuralin kaba kuvvete karsi
# en kucuk karsi ornegini rastgele arama ile bulur (tohum 42).
import random


def para_acgozlu(paralar, tutar):
    # en buyuk parayi once al, kalan tutari kucuk paralarla dene
    sayi = 0
    for p in sorted(paralar, reverse=True):
        sayi += tutar // p
        tutar %= p
    return sayi


def para_dp(paralar, tutar):
    inf = float("inf")
    dp = [0] + [inf] * tutar
    for t in range(1, tutar + 1):
        dp[t] = min((dp[t - p] + 1 for p in paralar if p <= t),
                    default=inf)
    return dp[tutar]


def kanonik_mi(paralar):
    # Kozen-Zaks (1994): en kucuk karsi ornek c_n + c_(n-1)'den kucuk
    # oldugu icin bu sinira kadar kontrol yeterlidir (bilinen sonuc).
    c = sorted(paralar)
    sinir = c[-1] + c[-2]
    return all(para_acgozlu(c, t) == para_dp(c, t)
               for t in range(1, sinir + 1))


def sirt_acgozlu(esyalar, W):
    toplam, kalan = 0, W
    sirali = sorted(esyalar, key=lambda x: x[1] / x[0],
                    reverse=True)
    for w, v in sirali:
        if w <= kalan:
            toplam += v
            kalan -= w
    return toplam


def sirt_dp(esyalar, W):
    dp = [0] * (W + 1)
    for w, v in esyalar:
        for c in range(W, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[W]


def en_kucuk_karsi(uret, acgozlu, kaba, boyut, deneme, rnd):
    en_iyi = None
    for _ in range(deneme):
        g = uret(rnd)
        if acgozlu(*g) != kaba(*g):
            if en_iyi is None or boyut(g) < boyut(en_iyi):
                en_iyi = g
    return en_iyi


def uret_para(rnd):
    adaylar = rnd.sample(range(2, 13), rnd.randint(2, 4))
    return sorted(set([1] + adaylar)), rnd.randint(1, 30)


def uret_sirt(rnd):
    n = rnd.randint(2, 5)
    esyalar = [(rnd.randint(1, 8), rnd.randint(1, 12))
               for _ in range(n)]
    return esyalar, rnd.randint(3, 12)


def main():
    for sistem in ([1, 5, 10, 25], [1, 2, 5, 10, 20, 50, 100, 200],
                   [1, 3, 4]):
        print("kanonik mi %-32s %s" % (sistem, kanonik_mi(sistem)))
    rnd = random.Random(42)
    g = en_kucuk_karsi(uret_para, para_acgozlu, para_dp,
                       lambda g: (len(g[0]), g[1]), 3000, rnd)
    paralar, tutar = g
    print("para: en kucuk karsi ornek:", paralar, "tutar", tutar)
    print("   acgozlu:", para_acgozlu(paralar, tutar),
          "optimum:", para_dp(paralar, tutar))
    rnd = random.Random(42)
    g = en_kucuk_karsi(uret_sirt, sirt_acgozlu, sirt_dp,
                       lambda g: (len(g[0]), g[1]), 3000, rnd)
    esyalar, W = g
    print("sirt: en kucuk karsi ornek:", esyalar, "W", W)
    print("   acgozlu:", sirt_acgozlu(esyalar, W),
          "optimum:", sirt_dp(esyalar, W))


if __name__ == "__main__":
    main()
