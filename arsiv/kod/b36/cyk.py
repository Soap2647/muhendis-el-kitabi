# CYK: Chomsky normal formda (CNF) tanıma ve türetme ağacı sayımı.
from itertools import product
import random

# Dengeli parantez dili (boş olmayan), CNF:
#   S -> S S | L R | L T     T -> S R     L -> (     R -> )
CNF = {
    "S": [("S", "S"), ("L", "R"), ("L", "T")],
    "T": [("S", "R")],
    "L": ["("],
    "R": [")"],
}


def cyk(G, bas, w):
    """T[i][j]: w[i..j]'yi türeten {değişken: ağaç sayısı}."""
    n = len(w)
    T = [[{} for _ in range(n)] for _ in range(n)]
    for i, harf in enumerate(w):              # uzunluk 1: A -> harf
        for A, uretimler in G.items():
            if harf in uretimler:
                T[i][i][A] = 1
    for uz in range(2, n + 1):                # kısa aralıktan uzuna
        for i in range(n - uz + 1):
            j = i + uz - 1
            for k in range(i, j):   # sol [i..k], sağ [k+1..j]
                for A, uretimler in G.items():
                    for u in uretimler:
                        if isinstance(u, str):
                            continue          # uç üretim: atla
                        B, C = u
                        sol = T[i][k].get(B, 0)
                        sag = T[k + 1][j].get(C, 0)
                        if sol and sag:
                            T[i][j][A] = T[i][j].get(A, 0) + sol * sag
    return T, (T[0][n - 1].get(bas, 0) if n else 0)


def dengeli_mi(w):
    """Bağımsız doğru: tek tür parantez için sayaçla kontrol."""
    sayac = 0
    for c in w:
        sayac += 1 if c == "(" else -1
        if sayac < 0:
            return False
    return sayac == 0


def dogrula(maks=10):
    sinanan = 0
    for n in range(1, maks + 1):
        for t in product("()", repeat=n):
            w = "".join(t)
            _, sayi = cyk(CNF, "S", w)
            assert (sayi > 0) == dengeli_mi(w), w
            sinanan += 1
    return sinanan


if __name__ == "__main__":
    w = "()()()"
    T, sayi = cyk(CNF, "S", w)
    print("ağaç sayısı:", sayi)
    for i in range(len(w)):
        print(" ".join(str(T[i][j].get("S", 0)) if j >= i else "."
                       for j in range(len(w))))
    print("sinanan:", dogrula())
