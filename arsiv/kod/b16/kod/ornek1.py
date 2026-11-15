# ornek1.py: engelli izgarada yol sayisi (tabulation + kaba kuvvet)
import random


def yol_say(izgara):
    n, m = len(izgara), len(izgara[0])
    dp = [[0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            if izgara[i][j] == 1:           # engel: yol yok
                continue
            if i == 0 and j == 0:
                dp[i][j] = 1
                continue
            yukari = dp[i - 1][j] if i > 0 else 0
            sol = dp[i][j - 1] if j > 0 else 0
            dp[i][j] = yukari + sol
    return dp[n - 1][m - 1], dp


def kaba(izgara):
    n, m = len(izgara), len(izgara[0])
    def git(i, j):
        if i >= n or j >= m or izgara[i][j] == 1:
            return 0
        if (i, j) == (n - 1, m - 1):
            return 1
        return git(i + 1, j) + git(i, j + 1)
    return git(0, 0)


def main():
    izgara = [[0, 0, 0, 0],
              [0, 1, 0, 0],
              [0, 0, 0, 1],
              [1, 0, 0, 0]]
    sayi, dp = yol_say(izgara)
    print("yol sayisi:", sayi)
    for satir in dp:
        print(" ".join(f"{x:2d}" for x in satir))
    print("kaba kuvvet:", kaba(izgara))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n, m = rnd.randint(1, 5), rnd.randint(1, 5)
        g = [[1 if rnd.random() < 0.2 else 0 for _ in range(m)]
             for _ in range(n)]
        if yol_say(g)[0] != kaba(g):
            hata += 1
    print("300 rastgele izgara, hata:", hata)


if __name__ == "__main__":
    main()
