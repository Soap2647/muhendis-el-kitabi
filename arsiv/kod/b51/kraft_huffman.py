# kraft_huffman.py: Kraft eşitsizliği, Huffman kod uzunlukları,
# entropiye uzaklık (H <= L < H + 1) ve Huffman'ın optimalliğinin
# kaba kuvvet denetimi.
import heapq
import itertools
import math
import random

def entropi(p):
    return -sum(x * math.log2(x) for x in p if x > 0)

def kraft_toplam(uzunluk):
    # Öneksiz (prefix) kod için sum 2^(-l_i) <= 1 olmalıdır.
    return sum(2.0 ** -l for l in uzunluk)

def huffman_uzunluk(p):
    # Her yaprak için kod uzunluğu: birleştirilen her düğümde
    # o düğümdeki yaprakların derinliği 1 artar.
    uz = [0] * len(p)
    kuyruk = [(x, [i]) for i, x in enumerate(p)]
    heapq.heapify(kuyruk)
    while len(kuyruk) > 1:
        a, ga = heapq.heappop(kuyruk)
        b, gb = heapq.heappop(kuyruk)
        for i in ga + gb:
            uz[i] += 1
        heapq.heappush(kuyruk, (a + b, ga + gb))
    return uz

def ortalama(p, uz):
    return sum(x * l for x, l in zip(p, uz))

def kaba_kuvvet(p, enbuyuk=4):
    # Tüm tamsayı uzunluk vektörlerini dene; Kraft <= 1 olanlar
    # arasında
    # en küçük ortalama uzunluğu bul.
    en = math.inf
    for uz in itertools.product(range(1, enbuyuk + 1), repeat=len(p)):
        if kraft_toplam(uz) <= 1.0 + 1e-12:
            en = min(en, ortalama(p, uz))
    return en

def main():
    p = [0.4, 0.3, 0.2, 0.1]
    h = entropi(p)
    uz = huffman_uzunluk(p)
    print("p      =", p)
    print("H(p)   = %.4f bit" % h)
    print("uzunluk =", uz, " Kraft toplam =", kraft_toplam(uz))
    print("L      = %.4f bit" % ortalama(p, uz))
    print("L - H  = %.4f bit" % (ortalama(p, uz) - h))
    rnd = random.Random(51)
    en_buyuk_fark, sayi = 0.0, 0
    for _ in range(1000):
        n = rnd.randint(2, 8)
        w = [rnd.random() ** 3 + 1e-6 for _ in range(n)]
        s = sum(w)
        q = [v / s for v in w]
        u = huffman_uzunluk(q)
        L, H = ortalama(q, u), entropi(q)
        assert H - 1e-12 <= L < H + 1.0 + 1e-12
        en_buyuk_fark = max(en_buyuk_fark, L - H)
        sayi += 1
    print("%d rastgele kaynak: en buyuk L - H = %.4f (sinir 1)" % (
        sayi, en_buyuk_fark))
    # Optimallik: 300 rastgele 4'lü dağılımda kaba kuvvet = Huffman
    eslesen = 0
    for _ in range(300):
        w = [rnd.random() + 0.01 for _ in range(4)]
        s = sum(w)
        q = [v / s for v in w]
        opt = ortalama(q, huffman_uzunluk(q))
        if abs(kaba_kuvvet(q) - opt) < 1e-9:
            eslesen += 1
    print("300 rastgele 4'lu kaynakta Huffman = kaba kuvvet: %d"
          % eslesen)


if __name__ == "__main__":
    main()
