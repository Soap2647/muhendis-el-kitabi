# lcs.py: en uzun ortak altdizi, tablo ve geri izleme
import itertools


def lcs_tablo(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp


def geri_izle(dp, a, b):
    i, j, harf = len(a), len(b), []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            harf.append(a[i - 1])
            i, j = i - 1, j - 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(harf))


def kaba(a, b):
    best = 0
    for k in range(len(a) + 1):
        for alt in itertools.combinations(a, k):
            s = "".join(alt)
            it = iter(b)
            if all(ch in it for ch in s):   # s, b'nin altdizisi mi?
                best = max(best, k)
    return best


def main():
    a, b = "ABCBDAB", "BDCABA"
    dp = lcs_tablo(a, b)
    print("     " + " ".join(f"{ch:>2}" for ch in " " + b))
    for i, row in enumerate(dp):
        ch = " " if i == 0 else a[i - 1]
        print(f"{ch:>2}  " + " ".join(f"{x:>2}" for x in row))
    s = geri_izle(dp, a, b)
    print("LCS uzunlugu:", dp[-1][-1], "LCS:", s)
    import random
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        x = "".join(rnd.choice("ab")
                    for _ in range(rnd.randint(0, 7)))
        y = "".join(rnd.choice("ab")
                    for _ in range(rnd.randint(0, 7)))
        t = lcs_tablo(x, y)
        g = geri_izle(t, x, y)
        if t[-1][-1] != kaba(x, y) or len(g) != t[-1][-1]:
            hata += 1
    print("300 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
