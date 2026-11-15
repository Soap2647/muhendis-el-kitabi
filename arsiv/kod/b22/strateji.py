# strateji.py: degistirilebilir filtre algoritmalari (Bolum 22.9)
import statistics


def ortalama(pencere):
    return sum(pencere) / len(pencere)


def medyan(pencere):
    return statistics.median(pencere)


def ustel(pencere, alfa=0.5):
    s = pencere[0]
    for x in pencere[1:]:
        s = alfa * x + (1 - alfa) * s
    return s


class Filtreleyici:                    # baglam (context)
    def __init__(self, strateji):
        self.strateji = strateji       # calisma zamaninda secilir

    def uygula(self, veri, n):
        return [self.strateji(veri[i:i + n])
                for i in range(len(veri) - n + 1)]


if __name__ == "__main__":
    veri = [20, 21, 90, 22, 21, 23, 22]   # 90: bozuk olcum
    for ad, s in [("ortalama", ortalama), ("medyan", medyan),
                  ("ustel", ustel)]:
        sonuc = Filtreleyici(s).uygula(veri, 3)
        print("%-9s" % ad, [round(x, 2) for x in sonuc])
    print("key ile sirala:", sorted(["bb", "a", "ccc"], key=len))
