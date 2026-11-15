# entropi_temel.py: öz bilgi, entropi, ortak ve koşullu entropi,
# karşılıklı bilgi. Tüm hesaplar bit (log2) cinsinden yapılır.
import math
import random

def ozbilgi(p):
    # p olasılıklı bir olay gerçekleşince kazanılan şaşırma: -log2 p.
    return -math.log2(p)

def entropi(dagilim):
    # H = sum p * (-log2 p). p = 0 olan terim 0 katkı verir.
    return sum(p * ozbilgi(p) for p in dagilim if p > 0)

# Ortak tablo P(X=x, Y=y). Satır: X (sensör okuması),
# sütun: Y (gerçek durum: boş, küçük hedef, büyük hedef).
ORTAK = [
    [0.4400, 0.0300, 0.0050],   # x = boş diyor
    [0.2400, 0.0900, 0.0150],   # x = belirsiz
    [0.0300, 0.0700, 0.0800],   # x = hedef diyor
]

def marjinal(ortak):
    px = [sum(satir) for satir in ortak]
    py = [sum(ortak[i][j] for i in range(len(ortak)))
          for j in range(len(ortak[0]))]
    return px, py

def ortak_entropi(ortak):
    # H(X,Y): tüm hücrelerin entropisi.
    return entropi([v for satir in ortak for v in satir])

def kosullu_entropi(ortak):
    # H(Y|X) = H(X,Y) - H(X)  (zincir kuralı)
    px, _ = marjinal(ortak)
    return ortak_entropi(ortak) - entropi(px)

def karsilikli_bilgi(ortak):
    # I(X;Y) = H(X) + H(Y) - H(X,Y)
    px, py = marjinal(ortak)
    return entropi(px) + entropi(py) - ortak_entropi(ortak)

def denetle():
    toplam = sum(v for satir in ORTAK for v in satir)
    assert abs(toplam - 1.0) < 1e-12, toplam

def main():
    denetle()
    print("Zar (6 yüz):  H = %.4f bit" % entropi([1/6]*6))
    print("Adil yazı-tura: H = %.4f bit" % entropi([0.5, 0.5]))
    print("Çarpık yazı-tura (0.9): H = %.4f bit"
          % entropi([0.9, 0.1]))
    print("Öz bilgi, p=1/8: %.1f bit" % ozbilgi(1/8))
    px, py = marjinal(ORTAK)
    print("P(X) =", [round(v, 4) for v in px])
    print("P(Y) =", [round(v, 4) for v in py])
    hx, hy = entropi(px), entropi(py)
    hxy = ortak_entropi(ORTAK)
    hyx = kosullu_entropi(ORTAK)
    i = karsilikli_bilgi(ORTAK)
    print("H(X)   = %.4f" % hx)
    print("H(Y)   = %.4f" % hy)
    print("H(X,Y) = %.4f" % hxy)
    print("H(Y|X) = %.4f" % hyx)
    print("I(X;Y) = %.4f" % i)
    print("zincir kurali hatasi: %.1e" % abs(hxy - (hx + hyx)))
    # Tekdüze dağılım en büyük entropiyi verir: H <= log2 n
    rnd = random.Random(51)
    ihlal = 0
    for _ in range(1000):
        w = [rnd.random() for _ in range(6)]
        s = sum(w)
        if entropi([v / s for v in w]) > math.log2(6) + 1e-12:
            ihlal += 1
    print("1000 rastgele 6'lı dağılım, H > log2 6 olan: %d" % ihlal)
    # Bağımsız X,Y için I(X;Y) = 0 olmalı.
    bagimsiz = [[a * b for b in py] for a in px]
    print("Bağımsız tablo için I(X;Y) = %.1e"
          % karsilikli_bilgi(bagimsiz))
    # Rastgele tablolarda I(X;Y) negatif olabilir mi? Olamaz.
    negatif = 0
    for _ in range(1000):
        w = [[rnd.random() for _ in range(3)] for _ in range(3)]
        s = sum(v for satir in w for v in satir)
        t = [[v / s for v in satir] for satir in w]
        if karsilikli_bilgi(t) < -1e-12:
            negatif += 1
    print("1000 rastgele ortak tablo, I < 0 olan: %d" % negatif)


if __name__ == "__main__":
    main()
