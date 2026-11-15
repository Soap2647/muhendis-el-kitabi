# huffman.py: Huffman agacini heap ile kur, kodlari uret, dogrula.
# Her adimda en kucuk iki dugum birlestirilir (acgozlu secim).
import heapq
import math
from collections import Counter


def huffman_agaci(frekans):
    # kuyruk elemani: (frekans, sayac, dugum); sayac esitlikte
    # dugumlerin karsilastirilmasini onler
    kuyruk = []
    for sayac, (sembol, f) in enumerate(sorted(frekans.items())):
        heapq.heappush(kuyruk, (f, sayac, sembol))
    sayac = len(kuyruk)
    adimlar = []
    while len(kuyruk) > 1:
        f1, _, d1 = heapq.heappop(kuyruk)
        f2, _, d2 = heapq.heappop(kuyruk)
        adimlar.append((d1, f1, d2, f2))
        heapq.heappush(kuyruk, (f1 + f2, sayac, (d1, d2)))
        sayac += 1
    return kuyruk[0][2], adimlar


def kodlar(agac, onek=""):
    if isinstance(agac, str):
        return {agac: onek or "0"}
    tablo = kodlar(agac[0], onek + "0")
    tablo.update(kodlar(agac[1], onek + "1"))
    return tablo


def ort_uzunluk(frekans, tablo):
    toplam = sum(frekans.values())
    return sum(f * len(tablo[s]) for s, f in frekans.items()) / toplam


def entropi(frekans):
    toplam = sum(frekans.values())
    return -sum((f / toplam) * math.log2(f / toplam)
                for f in frekans.values())


def ada(d):
    if isinstance(d, str):
        return d
    return "(" + "".join(map(ada, d)) + ")"


def main():
    metin = "abracadabra"
    frekans = Counter(metin)
    print("frekanslar:", dict(sorted(frekans.items())))
    agac, adimlar = huffman_agaci(frekans)
    for i, (d1, f1, d2, f2) in enumerate(adimlar, 1):
        print("adim %d: %s(%d) + %s(%d)"
              % (i, ada(d1), f1, ada(d2), f2))
    tablo = kodlar(agac)
    for s in sorted(tablo, key=lambda s: (len(tablo[s]), s)):
        print("  %s -> %s" % (s, tablo[s]))
    kodlanmis = "".join(tablo[c] for c in metin)
    print("bit sayisi:", len(kodlanmis), "(sabit uzunluk: 3*11 = 33)")
    print("ortalama:", round(ort_uzunluk(frekans, tablo), 4),
          "entropi:", round(entropi(frekans), 4))
    ters = {v: k for k, v in tablo.items()}
    cozulmus, akim = [], ""
    for bit in kodlanmis:
        akim += bit
        if akim in ters:
            cozulmus.append(ters[akim])
            akim = ""
    print("geri cozum dogru:", "".join(cozulmus) == metin)


if __name__ == "__main__":
    main()
