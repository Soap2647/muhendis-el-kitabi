# huffman_dogrula.py: Huffman'in maliyeti, tum gecerli uzunluk
# vektorleri arasindaki en kucuk maliyete esit mi? Kraft-McMillan
# esitsizligine gore bir uzunluk vektorunun prefix kodu olmasi icin
# gerek ve yeter kosul sum 2^-l <= 1'dir. Kaba kuvvet, uzunluk
# vektorlerini tarar ve bu kosulu denetler.
import itertools
import random
from huffman import huffman_agaci, kodlar


def kraft_kaba(f):
    n = len(f)
    L = n - 1 if n > 1 else 1      # optimal derinlik en fazla n-1
    en_iyi = None
    for l in itertools.product(range(1, L + 1), repeat=n):
        # Kraft toplamini tam sayi olarak: sum 2^(L-l) <= 2^L
        if sum(1 << (L - x) for x in l) > (1 << L):
            continue
        maliyet = sum(fi * li for fi, li in zip(f, l))
        if en_iyi is None or maliyet < en_iyi:
            en_iyi = maliyet
    return en_iyi


def huffman_maliyeti(f):
    sembol = {i: fi for i, fi in enumerate(f)}
    agac, _ = huffman_agaci({str(i): fi for i, fi in sembol.items()})
    tablo = kodlar(agac)
    return sum(fi * len(tablo[str(i)]) for i, fi in sembol.items())


def main():
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n = rnd.randint(2, 5)
        f = [rnd.randint(1, 50) for _ in range(n)]
        if huffman_maliyeti(f) != kraft_kaba(f):
            hata += 1
    print("300 rastgele frekans vektoru, uyusmayan:", hata)
    for f in ([5, 2, 2, 1, 1], [1, 1, 2, 4, 8]):
        print("f =", f, "huffman:", huffman_maliyeti(f),
              "kaba:", kraft_kaba(f))


if __name__ == "__main__":
    main()
