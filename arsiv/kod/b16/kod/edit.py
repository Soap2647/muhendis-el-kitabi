# edit.py: edit distance, islem dizisi ve BFS ile dogrulama
import random
from collections import deque


def edit_tablo(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i                    # a'nin i harfini silmek
    for j in range(m + 1):
        dp[0][j] = j                    # bos diziye j harf eklemek
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1],   # degistir
                                   dp[i - 1][j],       # sil
                                   dp[i][j - 1])       # ekle
    return dp


def islemler(a, b, dp):
    i, j, adim = len(a), len(b), []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            adim.append(f"ESLE {a[i - 1]}")
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            adim.append(f"DEGISTIR {a[i - 1]}->{b[j - 1]}")
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            adim.append(f"SIL {a[i - 1]}")
            i -= 1
        else:
            adim.append(f"EKLE {b[j - 1]}")
            j -= 1
    return list(reversed(adim))


def uygula(a, adim):
    # Islemleri soldan sağa a'ya uygular; sonucu dondurur.
    cikti, p = [], 0
    for op in adim:
        if op.startswith("ESLE"):
            cikti.append(a[p]); p += 1
        elif op.startswith("DEGISTIR"):
            cikti.append(op[-1]); p += 1
        elif op.startswith("SIL"):
            p += 1
        else:
            cikti.append(op[-1])
    assert p == len(a)
    return "".join(cikti)


def bfs(a, b, alfabe="ab"):
    # Ust sinir: uzunluk en fazla max(|a|,|b|)+2 olan dizgiler
    sinir = max(len(a), len(b)) + 2
    kuyruk, gorulen = deque([(a, 0)]), {a}
    while kuyruk:
        s, d = kuyruk.popleft()
        if s == b:
            return d
        komsu = []
        for k in range(len(s) + 1):
            for c in alfabe:
                komsu.append(s[:k] + c + s[k:])          # ekle
        for k in range(len(s)):
            komsu.append(s[:k] + s[k + 1:])              # sil
            for c in alfabe:
                komsu.append(s[:k] + c + s[k + 1:])      # degistir
        for t in komsu:
            if len(t) <= sinir and t not in gorulen:
                gorulen.add(t)
                kuyruk.append((t, d + 1))
    return -1


def main():
    a, b = "kitten", "sitting"
    dp = edit_tablo(a, b)
    print("mesafe:", dp[-1][-1])
    for op in islemler(a, b, dp):
        print("  ", op)
    print("uygula:", uygula(a, islemler(a, b, dp)))
    rnd = random.Random(42)
    hata = 0
    for _ in range(150):
        x = "".join(rnd.choice("ab")
                    for _ in range(rnd.randint(0, 4)))
        y = "".join(rnd.choice("ab")
                    for _ in range(rnd.randint(0, 4)))
        t = edit_tablo(x, y)
        adim = islemler(x, y, t)
        if t[-1][-1] != bfs(x, y) or uygula(x, adim) != y:
            hata += 1
        duzenleme = [o for o in adim if not o.startswith("ESLE")]
        if len(duzenleme) != t[-1][-1]:
            hata += 1
    print("150 rastgele ornek (BFS ve uygulama), hata:", hata)
    print("bos-bos:", edit_tablo("", "")[0][0], "bos-abc:",
          edit_tablo("", "abc")[0][3])


if __name__ == "__main__":
    main()
