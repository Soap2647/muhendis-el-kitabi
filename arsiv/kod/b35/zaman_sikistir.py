# -*- coding: utf-8 -*-
"""Zaman damgası delta-of-delta sıkıştırması (Gorilla tarzı, Bölüm
35.10).

Kodlama:
  ilk zaman damgası: 64 bit ham
  ilk delta (t1 - t0): 32 bit ham
  sonraki her nokta: dod = (t_i - t_{i-1}) - (t_{i-1} - t_{i-2})
    dod == 0          -> '0'                      (1 bit)
    -64 <= dod <= 63  -> '10' + 7 bit           (9 bit)
    -256 <= dod <= 255 -> '110' + 9 bit         (12 bit)
    -2048..2047       -> '1110' + 12 bit         (16 bit)
    diğerleri         -> '1111' + 32 bit         (36 bit)
Çıktı bit dizisidir (str '0'/'1'); boyut = len(bit dizisi).
Tohum: 35. Çıktı: engine/veri/b35_zaman.csv
"""
import csv
import random

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def ikili(deger, bit):
    # two's complement, bit genişliğinde
    return format(deger & ((1 << bit) - 1), "0%db" % bit)


def aralik_icinde(deger, bit):
    return -(1 << (bit - 1)) <= deger < (1 << (bit - 1))


def sikistir(zamanlar):
    bits = []
    bits.append(ikili(zamanlar[0], 64))
    if len(zamanlar) == 1:
        return "".join(bits)
    d_onceki = zamanlar[1] - zamanlar[0]
    bits.append(ikili(d_onceki, 32))
    for i in range(2, len(zamanlar)):
        d = zamanlar[i] - zamanlar[i - 1]
        dod = d - d_onceki
        if dod == 0:
            bits.append("0")
        elif aralik_icinde(dod, 7):
            bits.append("10" + ikili(dod, 7))
        elif aralik_icinde(dod, 9):
            bits.append("110" + ikili(dod, 9))
        elif aralik_icinde(dod, 12):
            bits.append("1110" + ikili(dod, 12))
        else:
            bits.append("1111" + ikili(dod, 32))
        d_onceki = d
    return "".join(bits)


def coz(bits, n):
    p = 0

    def oku(k):
        nonlocal p
        s = bits[p:p + k]
        p += k
        return s

    def isaretli(s):
        v = int(s, 2)
        return v - (1 << len(s)) if s[0] == "1" else v

    zamanlar = [isaretli(oku(64))]
    if n == 1:
        return zamanlar
    d_onceki = isaretli(oku(32))
    zamanlar.append(zamanlar[0] + d_onceki)
    for _ in range(2, n):
        if oku(1) == "0":
            dod = 0
        else:
            b = oku(1)
            if b == "0":
                dod = isaretli(oku(7))
            elif oku(1) == "0":
                dod = isaretli(oku(9))
            elif oku(1) == "0":
                dod = isaretli(oku(12))
            else:
                dod = isaretli(oku(32))
        d = d_onceki + dod
        zamanlar.append(zamanlar[-1] + d)
        d_onceki = d
    return zamanlar


def senaryo(ad, adim, jitter, kayip_orani, rnd, n=20000):
    # Telemetri: nominal periyot adim ms, her nokta +-jitter sapar.
    # Kayıp: bazı noktalar atlanır (boşluk), delta büyür.
    t = 1_700_000_000_000
    zamanlar = [t]
    while len(zamanlar) < n:
        t += adim + (rnd.randint(-jitter, jitter) if jitter else 0)
        if rnd.random() < kayip_orani:
            t += adim * rnd.randint(2, 40)  # birkaç periyot boşluk
        zamanlar.append(t)
    return ad, zamanlar


if __name__ == "__main__":
    rnd = random.Random(35)
    senaryolar = [
        senaryo("mükemmel periyodik (1 Hz)", 1000, 0, 0.0, rnd),
        senaryo("1 Hz, ±3 ms titreme", 1000, 3, 0.0, rnd),
        senaryo("1 Hz, ±40 ms titreme", 1000, 40, 0.0, rnd),
        senaryo("1 Hz, ±3 ms, %1 boşluk", 1000, 3, 0.01, rnd),
        senaryo("10 Hz, ±1 ms, %5 boşluk", 100, 1, 0.05, rnd),
    ]
    satirlar = []
    print("%-28s %10s %10s %8s"
          % ("senaryo", "bit/nokta", "ham64", "oran"))
    for ad, z in senaryolar:
        bits = sikistir(z)
        geri = coz(bits, len(z))
        assert geri == z, "çözme hatalı: " + ad
        bpn = len(bits) / len(z)
        print("%-28s %10.2f %10d %8.1f" % (ad, bpn, 64,
                                          64 / bpn))
        satirlar.append([ad, "%.4f" % bpn, 64, "%.2f" % (64 / bpn)])
    with open(VERI + "/b35_zaman.csv", "w", encoding="utf-8",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["senaryo", "bit_nokta", "ham", "oran"])
        w.writerows(satirlar)
    print("Geri çözme: tüm senaryolarda birebir eşleşti")
