# fraksiyonel_sirt.py: kesirli sirt cantasi (acgozlu) ve 0/1 sirt
# cantasi karsilastirmasi. Kaba kuvvet dogrulamasi tam kesirlerle
# (Fraction) yapilir; LP'nin koseleri en fazla bir kesirli degisken
# icerir, bu yuzden o noktalari tarayarak optimum bulunur.
from fractions import Fraction
import random


def kesirli_acgozlu(esyalar, W):
    kalan, toplam = Fraction(W), Fraction(0)
    sirali = sorted(esyalar, key=lambda x: Fraction(x[1], x[0]),
                    reverse=True)
    for w, v in sirali:
        if kalan == 0:
            break
        al = min(Fraction(w), kalan)
        toplam += Fraction(v, w) * al
        kalan -= al
    return toplam


def kesirli_kaba(esyalar, W):
    n, en_iyi = len(esyalar), Fraction(0)
    for maske in range(1 << n):
        s_w = sum(esyalar[i][0] for i in range(n) if maske >> i & 1)
        s_v = sum(esyalar[i][1] for i in range(n) if maske >> i & 1)
        if s_w > W:
            continue
        en_iyi = max(en_iyi, Fraction(s_v))
        for j in range(n):
            if not (maske >> j & 1):
                w, v = esyalar[j]
                f = min(Fraction(W - s_w, w), Fraction(1))
                en_iyi = max(en_iyi, s_v + v * f)
    return en_iyi


def sirt_01_acgozlu(esyalar, W):
    kalan, toplam = W, 0
    sirali = sorted(esyalar, key=lambda x: Fraction(x[1], x[0]),
                    reverse=True)
    for w, v in sirali:
        if w <= kalan:
            toplam += v
            kalan -= w
    return toplam


def sirt_01(esyalar, W):
    dp = [0] * (W + 1)
    for w, v in esyalar:
        for c in range(W, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[W]


def main():
    ornek = [(10, 60), (20, 100), (30, 120)]
    W = 50
    print("ornek (agirlik, deger):", ornek, "W =", W)
    print("kesirli acgozlu:", kesirli_acgozlu(ornek, W))
    print("kesirli kaba   :", kesirli_kaba(ornek, W))
    print("0/1 acgozlu   :", sirt_01_acgozlu(ornek, W))
    print("0/1 optimum    :", sirt_01(ornek, W))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n = rnd.randint(1, 6)
        es = [(rnd.randint(1, 9), rnd.randint(1, 20))
              for _ in range(n)]
        W = rnd.randint(1, 25)
        if kesirli_acgozlu(es, W) != kesirli_kaba(es, W):
            hata += 1
    print("300 rastgele ornek, kesirli hata:", hata)


if __name__ == "__main__":
    main()
