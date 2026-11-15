# cubuk.py: cubuk kesimi (rod cutting) ve kaba kuvvet kontrolu
import random


def cubuk_kes(fiyat, n):
    # fiyat[k]: k uzunluktaki parcanin fiyati (fiyat[0] = 0)
    dp = [0] * (n + 1)          # dp[u]: uzunluk u icin en iyi gelir
    for u in range(1, n + 1):
        for k in range(1, min(u, len(fiyat) - 1) + 1):
            dp[u] = max(dp[u], fiyat[k] + dp[u - k])
    return dp[n]


def kaba(fiyat, n):
    if n == 0:
        return 0
    return max(fiyat[k] + kaba(fiyat, n - k)
               for k in range(1, min(n, len(fiyat) - 1) + 1))


def main():
    fiyat = [0, 1, 5, 8, 9, 10, 17, 17, 20]
    for n in range(1, 9):
        print(f"uzunluk {n}: gelir {cubuk_kes(fiyat, n)}")
    rnd = random.Random(42)
    hata = 0
    for _ in range(200):
        m = rnd.randint(1, 8)
        f = [0] + [rnd.randint(1, 20) for _ in range(m)]
        n = rnd.randint(0, 10)
        if cubuk_kes(f, n) != kaba(f, n):
            hata += 1
    print("200 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
