# para_bozma.py: en az madeni para ve yol sayilari
import random


def en_az_madeni(paralar, tutar):
    inf = tutar + 1               # tutar'i asla asmaz: sonsuz yerine
    dp = [0] + [inf] * tutar      # dp[t]: t'yi toplayan en az adet
    for t in range(1, tutar + 1):
        for p in paralar:
            if p <= t and dp[t - p] + 1 < dp[t]:
                dp[t] = dp[t - p] + 1
    return dp[tutar] if dp[tutar] < inf else -1


def yol_kombinasyon(paralar, tutar):
    # once madeni para, sonra tutar: siralama onemsiz (kombinasyon)
    ways = [1] + [0] * tutar
    for p in paralar:
        for t in range(p, tutar + 1):
            ways[t] += ways[t - p]
    return ways[tutar]


def yol_permutasyon(paralar, tutar):
    # once tutar, sonra madeni para: siralama onemli (permutasyon)
    ways = [1] + [0] * tutar
    for t in range(1, tutar + 1):
        for p in paralar:
            if p <= t:
                ways[t] += ways[t - p]
    return ways[tutar]


def kaba_kombinasyon(paralar, tutar, bas=0):
    if tutar == 0:
        return [()]
    sonuc = []
    for i in range(bas, len(paralar)):
        if paralar[i] <= tutar:
            kalan_listesi = kaba_kombinasyon(paralar,
                                             tutar - paralar[i], i)
            for kalan in kalan_listesi:
                sonuc.append((paralar[i],) + kalan)
    return sonuc


def kaba_permutasyon(paralar, tutar):
    if tutar == 0:
        return 1
    return sum(kaba_permutasyon(paralar, tutar - p)
               for p in paralar if p <= tutar)


def main():
    paralar = [1, 2, 5]
    for t in (0, 3, 5, 11):
        print(f"tutar={t:2d} en_az={en_az_madeni(paralar, t):2d}",
              f"kombinasyon={yol_kombinasyon(paralar, t):2d}",
              f"permutasyon={yol_permutasyon(paralar, t):2d}")
    print("paralar [2], tutar 3 -> en_az =", en_az_madeni([2], 3))
    rnd = random.Random(42)
    hata = 0
    for _ in range(200):
        k = rnd.randint(1, 4)
        p = sorted(rnd.sample(range(1, 8), k))
        t = rnd.randint(0, 12)
        if yol_kombinasyon(p, t) != len(kaba_kombinasyon(p, t)):
            hata += 1
        if yol_permutasyon(p, t) != kaba_permutasyon(p, t):
            hata += 1
    print("200 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
