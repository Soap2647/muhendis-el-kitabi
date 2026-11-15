# belady.py: onbellek degistirme. FIFO, LRU ve Belady (en uzak
# gelecek). Belady'nin en az hatayi verdigi, tum kurban secimlerini
# deneyen bir kaba kuvvet ile dogrulanir (kucuk dizilerde).
import random
from functools import lru_cache


def hata_say(seq, k, kurban):
    onb, hata = [], 0
    for i, p in enumerate(seq):
        if p in onb:
            continue
        hata += 1
        if len(onb) == k:
            onb.remove(kurban(onb, i, seq))
        onb.append(p)
    return hata


def fifo_kurban(onb, i, seq):
    return onb[0]


def lru_kurban(onb, i, seq):
    def son_kullanim(p):
        for j in range(i - 1, -1, -1):
            if seq[j] == p:
                return j
        return -1
    return min(onb, key=son_kullanim)


def belady_kurban(onb, i, seq):
    def sonraki(p):
        for j in range(i + 1, len(seq)):
            if seq[j] == p:
                return j
        return float("inf")
    return max(onb, key=sonraki)


def en_az_hata(seq, k):
    @lru_cache(maxsize=None)
    def f(i, onb):
        if i == len(seq):
            return 0
        p = seq[i]
        if p in onb:
            return f(i + 1, onb)
        if len(onb) < k:
            return 1 + f(i + 1, onb | {p})
        return 1 + min(f(i + 1, (onb - {q}) | {p}) for q in onb)
    return f(0, frozenset())


def main():
    seq = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    for k in (3, 4):
        print("k=%d FIFO:%d LRU:%d Belady:%d" % (
            k, hata_say(seq, k, fifo_kurban),
            hata_say(seq, k, lru_kurban),
            hata_say(seq, k, belady_kurban)))
    rnd = random.Random(42)
    hata_b = hata_l = 0
    for _ in range(300):
        s = [rnd.randint(1, 6) for _ in range(rnd.randint(4, 12))]
        k = rnd.randint(2, 3)
        opt = en_az_hata(tuple(s), k)
        if hata_say(s, k, belady_kurban) != opt:
            hata_b += 1
        if hata_say(s, k, lru_kurban) != opt:
            hata_l += 1
    print("300 dizi: Belady optimumdan farkli:", hata_b)
    print("300 dizi: LRU optimumdan farkli   :", hata_l)


if __name__ == "__main__":
    main()
