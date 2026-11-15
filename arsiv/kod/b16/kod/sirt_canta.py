# sirt_canta.py: 0/1 ve sinirsiz sirt cantasi, kaba kuvvet kontrolu
import itertools
import random


def sirtcanta_01(agirlik, deger, W, yon="ters"):
    # dp[c]: kapasite c icin ulasilabilen en iyi deger
    dp = [0] * (W + 1)
    aralik = range(W, -1, -1) if yon == "ters" else range(W + 1)
    for w, v in zip(agirlik, deger):
        for c in aralik:
            if w <= c and dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
    return dp[W]


def sinirsiz(agirlik, deger, W):
    dp = [0] * (W + 1)
    for c in range(1, W + 1):
        for w, v in zip(agirlik, deger):
            if w <= c and dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
    return dp[W]


def tablo_01(agirlik, deger, W):
    # dp[i][c]: ilk i esya ile kapasite c; geri izleme icin tam tablo
    n = len(agirlik)
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = agirlik[i - 1], deger[i - 1]
        for c in range(W + 1):
            dp[i][c] = dp[i - 1][c]
            if w <= c and dp[i - 1][c - w] + v > dp[i][c]:
                dp[i][c] = dp[i - 1][c - w] + v
    return dp


def secilenler(dp, agirlik, W):
    secim, c = [], W
    for i in range(len(agirlik), 0, -1):
        if dp[i][c] != dp[i - 1][c]:   # esya i alinmis olmali
            secim.append(i - 1)
            c -= agirlik[i - 1]
    return sorted(secim)


def kaba_01(agirlik, deger, W):
    best = 0
    n = len(agirlik)
    for mask in range(1 << n):
        w = sum(agirlik[i] for i in range(n) if mask >> i & 1)
        v = sum(deger[i] for i in range(n) if mask >> i & 1)
        if w <= W:
            best = max(best, v)
    return best


def kaba_sinirsiz(agirlik, deger, W):
    best = 0
    k = len(agirlik)
    sinir = [W // w for w in agirlik]
    for sayilar in itertools.product(*[range(s + 1) for s in sinir]):
        w = sum(s * a for s, a in zip(sayilar, agirlik))
        v = sum(s * d for s, d in zip(sayilar, deger))
        if w <= W:
            best = max(best, v)
    return best


def main():
    print("ornek: w=[2,3] v=[3,4] W=4")
    w, v = [2, 3], [3, 4]
    print("0/1 ters  :", sirtcanta_01(w, v, 4, "ters"))
    print("0/1 ileri :", sirtcanta_01(w, v, 4, "ileri"))
    print("sinirsiz  :", sinirsiz(w, v, 4))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n = rnd.randint(1, 7)
        w = [rnd.randint(1, 6) for _ in range(n)]
        v = [rnd.randint(1, 9) for _ in range(n)]
        W = rnd.randint(0, 15)
        if sirtcanta_01(w, v, W) != kaba_01(w, v, W):
            hata += 1
        if sinirsiz(w, v, W) != kaba_sinirsiz(w, v, W):
            hata += 1
    print("300 rastgele ornek, 0/1 ve sinirsiz hata:", hata)
    # kapasite 0 ve bos esya kenar durumlari
    print("W=0:", sirtcanta_01([2], [5], 0), sinirsiz([2], [5], 0))
    print("bos:", sirtcanta_01([], [], 5), sinirsiz([], [], 5))
    w, v = [1, 3, 4, 5], [1, 4, 5, 7]
    dp = tablo_01(w, v, 7)
    print("0/1 W=7 en iyi:", dp[-1][-1], "secilen:",
          secilenler(dp, w, 7))


if __name__ == "__main__":
    main()
