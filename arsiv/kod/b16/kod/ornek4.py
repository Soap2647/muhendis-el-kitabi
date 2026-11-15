# ornek4.py: yazim denetimi, en yakin sozcukler ve islem dizisi
def mesafe_tablo(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j],
                                   dp[i][j - 1])
    return dp


def islemler(a, b, dp):
    i, j, adim = len(a), len(b), []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            adim.append(f"{a[i - 1]}->{b[j - 1]}")
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            adim.append(f"sil {a[i - 1]}")
            i -= 1
        else:
            adim.append(f"ekle {b[j - 1]}")
            j -= 1
    return list(reversed(adim))


def main():
    sozluk = ["kitap", "kapi", "kopya", "kedi", "kitle", "kapak"]
    girdi = "kitp"
    adaylar = []
    for w in sozluk:
        dp = mesafe_tablo(girdi, w)
        adaylar.append((dp[-1][-1], w, dp))
    adaylar.sort()
    for d, w, dp in adaylar[:3]:
        print(f"{girdi} -> {w}: mesafe {d}")
    d, w, dp = adaylar[0]
    print("islemler:", islemler(girdi, w, dp))
    print("tablo (en iyi aday):")
    for satir in dp:
        print(" ".join(f"{x:2d}" for x in satir))


if __name__ == "__main__":
    main()
