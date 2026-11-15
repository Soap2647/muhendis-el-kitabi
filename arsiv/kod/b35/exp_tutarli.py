# -*- coding: utf-8 -*-
"""Naif hash % N ile tutarlı hash halkasını karşılaştırır (Bölüm
35.7).
Tohum yok: anahtarlar deterministik. Çıktı:
engine/veri/b35_tutarli_hash.csv
"""
import bisect
import csv
import hashlib
import statistics

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ANAHTAR = 100000


def h32(metin):
    return int.from_bytes(hashlib.blake2b(metin.encode(),
                                          digest_size=8).digest()[:4],
                          "little")


KEYS = ["anahtar-%06d" % i for i in range(ANAHTAR)]


class Halka:
    def __init__(self, dugumler, v):
        self.v = v
        self.nokta = []  # (konum, dugum)
        for d in dugumler:
            self.dugum_ekle(d)

    def dugum_ekle(self, d):
        for i in range(self.v):
            self.nokta.append((h32("%s#%d" % (d, i)), d))
        self.nokta.sort()

    def dugum_sil(self, d):
        self.nokta = [p for p in self.nokta if p[1] != d]

    def sahip(self, anahtar):
        konum = h32(anahtar)
        i = bisect.bisect_right(self.nokta, (konum, "\uffff"))
        if i == len(self.nokta):
            i = 0  # halkayı tamamla: en küçük konuma dön
        return self.nokta[i][1]


def naif(anahtar, n):
    return h32(anahtar) % n


def dugumler(n):
    return ["dugum-%02d" % i for i in range(n)]


def yuk_cv(sahipler, n):
    sayac = {}
    for s in sahipler:
        sayac[s] = sayac.get(s, 0) + 1
    degerler = [sayac.get(d, 0) for d in dugumler(n)]
    ort = statistics.mean(degerler)
    return statistics.pstdev(degerler) / ort


def tasinan_naif(n):
    once = [naif(k, n) for k in KEYS]
    sonra = [naif(k, n + 1) for k in KEYS]
    return sum(1 for a, b in zip(once, sonra) if a != b) / ANAHTAR


def tasinan_halka(v, n):
    once = Halka(dugumler(n), v)
    sahip_once = [once.sahip(k) for k in KEYS]
    yeni = dugumler(n + 1)[-1]
    sonra_h = Halka(dugumler(n + 1), v)
    sahip_sonra = [sonra_h.sahip(k) for k in KEYS]
    tasinan = 0
    for a, b in zip(sahip_once, sahip_sonra):
        if a != b:
            tasinan += 1
            # kanıt: taşınan her anahtar YENİ düğüme gitmeli
            assert b == yeni, "beklenmeyen taşıma"
    return tasinan / ANAHTAR


if __name__ == "__main__":
    satirlar = []
    print("Anahtar sayısı: %d, düğüm: 10 -> 11" % ANAHTAR)
    t_naif = tasinan_naif(10)
    print("naif hash%%N   taşınan oranı: %.4f  (ideal 1/11 = %.4f)"
          % (t_naif, 1 / 11))
    satirlar.append(["naif", 1, 10, 11, "%.6f" % t_naif,
                     "%.6f" % (1 / 11), "%.4f" % yuk_cv(
                         ["dugum-%02d" % naif(k, 10) for k in KEYS],
                         10)])
    for v in (1, 10, 40, 100, 200):
        t = tasinan_halka(v, 10)
        sahipler = [Halka(dugumler(10), v).sahip(k) for k in KEYS]
        cv = yuk_cv(sahipler, 10)
        print("halka v=%-4d taşınan=%.4f  "
              "yük_cv=%.4f" % (v, t, cv))
        satirlar.append(["halka", v, 10, 11, "%.6f" % t,
                         "%.6f" % (1 / 11), "%.4f" % cv])
    naif_sahip = ["dugum-%02d" % naif(k, 10) for k in KEYS]
    print("naif yük_cv = %.4f" % yuk_cv(naif_sahip, 10))
    with open(VERI + "/b35_tutarli_hash.csv", "w", encoding="utf-8",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["yontem", "vnode", "n_once", "n_sonra", "tasinan",
                    "ideal", "yuk_cv"])
        w.writerows(satirlar)
    print("CSV yazildı")
