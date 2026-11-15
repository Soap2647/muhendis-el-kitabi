# cfg.py: bağlamdan bağımsız gramerde türetme ağacı sayımı
import random
from functools import lru_cache

# Belirsiz: E -> E + E | E * E | n
G_ISLEM = {"E": [("E", "+", "E"), ("E", "*", "E"), ("n",)]}
# Belirsiz asılı else: S -> iEtS | iEtSeS | a ; E -> b
G_ASILI = {"S": [("i", "E", "t", "S"),
                 ("i", "E", "t", "S", "e", "S"), ("a",)],
           "E": [("b",)]}
# Tek ağaçlı: E -> T + E | T ; T -> F * T | F ; F -> n | ( E )
G_TEK = {"E": [("T", "+", "E"), ("T",)],
         "T": [("F", "*", "T"), ("F",)],
         "F": [("n",), ("(", "E", ")")]}


def agac_sayisi(G, bas, w):
    """w kaç farklı türetme ağacıyla bas'tan türetilir?
    G'de ε-üretimi ve birim döngüsü olmadığı varsayılır."""
    @lru_cache(maxsize=None)
    def A(X, i, j):              # X, w[i:j]'yi kaç ağaçla türer?
        if X not in G:           # uç sembol: tek harf
            return int(j == i + 1 and w[i] == X)
        return sum(B(rhs, i, j) for rhs in G[X])

    @lru_cache(maxsize=None)
    def B(seq, i, j):            # seq dizisi w[i:j]'yi kaç ağaçla?
        if len(seq) == 1:
            return A(seq[0], i, j)
        return sum(A(seq[0], i, k) * B(seq[1:], k, j)
                   for k in range(i + 1, j))

    return A(bas, 0, len(w))


def agaclar(G, bas, w):
    """Tüm ağaçlar: (X, (alt ağaçlar...)); uç harf düz metin."""
    def A(X, i, j):
        if X not in G:
            return [X] if j == i + 1 and w[i] == X else []
        return [(X, o) for rhs in G[X] for o in B(rhs, i, j)]

    def B(seq, i, j):
        if len(seq) == 1:
            return [(t,) for t in A(seq[0], i, j)]
        return [(t,) + kal for k in range(i + 1, j)
                for t in A(seq[0], i, k) for kal in B(seq[1:], k, j)]

    return A(bas, 0, len(w))


def ayristirici_tek(w):
    """G_TEK için özyinelemeli iniş tanıyıcı (Bölüm 15)."""
    konum = [0]

    def bak():
        return w[konum[0]] if konum[0] < len(w) else None

    def ileri(c):
        if bak() != c:
            raise SyntaxError(c)
        konum[0] += 1

    def E():
        T()
        if bak() == "+":
            ileri("+")
            E()

    def T():
        F()
        if bak() == "*":
            ileri("*")
            T()

    def F():
        if bak() == "n":
            ileri("n")
        else:
            ileri("(")
            E()
            ileri(")")

    try:
        E()
    except SyntaxError:
        return False
    return konum[0] == len(w)


def dogrula(seed=36, n=3000):
    rng = random.Random(seed)
    for _ in range(n):
        w = "".join(rng.choice("n+*()")
                    for _ in range(rng.randint(1, 9)))
        dogru = ayristirici_tek(w)
        k = agac_sayisi(G_TEK, "E", w)
        assert k == (1 if dogru else 0), w   # tek ağaç
    return n


if __name__ == "__main__":
    for w in ["n+n*n", "n+n", "n*n+n*n"]:
        print(w, "belirsiz:", agac_sayisi(G_ISLEM, "E", w),
              "tek:", agac_sayisi(G_TEK, "E", w))
    print("asılı else:", agac_sayisi(G_ASILI, "S", "ibtibtaea"))
    for t in agaclar(G_ISLEM, "E", "n+n*n"):
        print(t)
    print("dogrulanan:", dogrula())
