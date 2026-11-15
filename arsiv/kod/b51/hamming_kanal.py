# hamming_kanal.py: Hamming(7,4) kodlayıcı ve sendrom çözücü;
# ikili simetrik kanal (BSC) üzerinde kodsuz, tekrar(3) ve
# Hamming(7,4) bit hata oranı.
# Kullanım: python hamming_kanal.py <veri klasörü>
import csv
import itertools
import os
import random
import sys

def kodla(d):
    # d = [d1, d2, d3, d4]; çıktı konumları 1..7 sırasıyla:
    # p1 p2 d1 p3 d2 d3 d4
    d1, d2, d3, d4 = d
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return [p1, p2, d1, p3, d2, d3, d4]

def sendrom(c):
    # s = H c. Bitler: s1 s2 s3 (s1 en düşük değerlikli).
    s1 = c[0] ^ c[2] ^ c[4] ^ c[6]
    s2 = c[1] ^ c[2] ^ c[5] ^ c[6]
    s3 = c[3] ^ c[4] ^ c[5] ^ c[6]
    return s1 + 2 * s2 + 4 * s3      # 0: hata yok, 1..7: hatalı konum

def coz(c):
    s = sendrom(c)
    c = list(c)
    if s:
        c[s - 1] ^= 1                # tek bit hatasını düzelt
    return [c[2], c[4], c[5], c[6]], s

def bsc(bitler, p, rnd):
    # Her bit, bağımsız olarak p olasılıkla çevrilir.
    return [b ^ (1 if rnd.random() < p else 0) for b in bitler]

def tekrar_kodla(bitler):
    return [b for b in bitler for _ in range(3)]

def tekrar_coz(bitler):
    return [1 if sum(bitler[i:i + 3]) >= 2 else 0
            for i in range(0, len(bitler), 3)]

def dogrula():
    # 16 mesaj: kodla, sıfır veya tek bit hatası, çöz
    kod = {}
    for d in itertools.product([0, 1], repeat=4):
        c = kodla(list(d))
        kod[d] = c
        assert coz(c)[0] == list(d)
        for k in range(7):
            e = list(c)
            e[k] ^= 1
            assert coz(e)[0] == list(d), (d, k)
    minimum = min(sum(a != b for a, b in zip(kod[x], kod[y]))
                  for x, y in itertools.combinations(kod, 2))
    print("16 mesaj x (hatasiz + 7 tek bit hatasi): hepsi dogru")
    print("kod sozcuklerinin en kucuk Hamming mesafesi: %d" % minimum)
    return kod

def main(veri):
    kod = dogrula()
    c = "".join(map(str, kodla([1, 0, 1, 1])))
    print("ornek: 1011 -> %s" % c)
    rnd = random.Random(51)
    n_mesaj = 40000
    veri_bitler = [rnd.randrange(2) for _ in range(4 * n_mesaj)]
    satirlar = []
    print("%-7s %-10s %-10s %s" % ("p", "kodsuz", "tekrar3",
                                  "hamming74"))
    for p in [0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.15]:
        # kodsuz
        al = bsc(veri_bitler, p, rnd)
        ber0 = sum(a != b for a, b in zip(al, veri_bitler)) / len(
            veri_bitler)
        # tekrar kodu
        al = tekrar_coz(bsc(tekrar_kodla(veri_bitler), p, rnd))
        ber3 = sum(a != b for a, b in zip(al, veri_bitler)) / len(
            veri_bitler)
        # Hamming(7,4)
        cozulen = []
        for i in range(n_mesaj):
            c = kodla(veri_bitler[4 * i:4 * i + 4])
            cozulen.extend(coz(bsc(c, p, rnd))[0])
        hata = sum(a != b for a, b in zip(cozulen, veri_bitler))
        berh = hata / len(veri_bitler)
        print("%-7.3f %-10.5f %-10.5f %.5f" % (p, ber0, ber3, berh))
        formul = 3 * p * p - 2 * p ** 3
        satirlar.append([p, "%.6f" % ber0, "%.6f" % ber3,
                         "%.6f" % berh, "%.6f" % formul])
    yol = os.path.join(veri, "b51_ber.csv")
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["p", "kodsuz", "tekrar3", "hamming74",
                    "tekrar3_formul"])
        w.writerows(satirlar)


if __name__ == "__main__":
    main(sys.argv[1])
