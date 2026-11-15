# -*- coding: utf-8 -*-
# b33_6_bplus.py: bellek içi B+ ağacı (ekleme ve aralık)
import bisect
import math
import random


class Dugum:
    def __init__(self, yaprak):
        self.yaprak = yaprak
        self.anahtar = []   # ayırıcılar (iç) ya da anahtarlar
        self.cocuk = []     # iç düğüm: çocuk düğümler
        self.deger = []     # yaprak: anahtarın değeri
        self.sonraki = None  # yaprak zinciri, sağ komşu


class BPlus:
    def __init__(self, m):
        self.m = m          # bir düğümde en fazla m anahtar
        self.kok = Dugum(True)

    def _yaprağa_in(self, k):
        """Kökten yaprağa iner; (yaprak, yol) döner."""
        yol, d = [], self.kok
        while not d.yaprak:
            i = bisect.bisect_right(d.anahtar, k)
            yol.append((d, i))
            d = d.cocuk[i]
        return d, yol

    def ekle(self, k, v):
        yaprak, yol = self._yaprağa_in(k)
        i = bisect.bisect_left(yaprak.anahtar, k)
        if i < len(yaprak.anahtar) and yaprak.anahtar[i] == k:
            yaprak.deger[i] = v
            return
        yaprak.anahtar.insert(i, k)
        yaprak.deger.insert(i, v)
        if len(yaprak.anahtar) > self.m:
            self._bol(yaprak, yol)

    def aralik(self, lo, hi):
        """lo <= k <= hi olan (anahtar, değer) çiftleri."""
        d, _ = self._yaprağa_in(lo)
        sonuc = []
        while d is not None:
            for k, v in zip(d.anahtar, d.deger):
                if k > hi:
                    return sonuc
                if k >= lo:
                    sonuc.append((k, v))
            d = d.sonraki
        return sonuc

    def _bol(self, d, yol):
        if d.yaprak:
            mid = (len(d.anahtar) + 1) // 2
            sag = Dugum(True)
            sag.anahtar = d.anahtar[mid:]
            sag.deger = d.deger[mid:]
            d.anahtar = d.anahtar[:mid]
            d.deger = d.deger[:mid]
            sag.sonraki, d.sonraki = d.sonraki, sag
            ayirici = sag.anahtar[0]     # yapraktan KOPYALANIR
        else:
            mid = len(d.anahtar) // 2
            ayirici = d.anahtar[mid]     # iç düğümden YUKARI İTİLİR
            sag = Dugum(False)
            sag.anahtar = d.anahtar[mid + 1:]
            sag.cocuk = d.cocuk[mid + 1:]
            d.anahtar = d.anahtar[:mid]
            d.cocuk = d.cocuk[:mid + 1]
        if not yol:                      # kök bölündü: ağaç büyür
            kok = Dugum(False)
            kok.anahtar = [ayirici]
            kok.cocuk = [d, sag]
            self.kok = kok
            return
        ata, i = yol.pop()
        ata.anahtar.insert(i, ayirici)
        ata.cocuk.insert(i + 1, sag)
        if len(ata.anahtar) > self.m:
            self._bol(ata, yol)

    def dok(self, d=None, seviye=0, satirlar=None):
        """Seviye seviye anahtarları yazdırır (ders amaçlı)."""
        if satirlar is None:
            satirlar = {}
            self.dok(self.kok, 0, satirlar)
            for s in sorted(satirlar):
                print("  seviye %d: %s"
                      % (s, " | ".join(satirlar[s])))
            return
        satirlar.setdefault(seviye, []).append(str(d.anahtar))
        if not d.yaprak:
            for c in d.cocuk:
                self.dok(c, seviye + 1, satirlar)


if __name__ == "__main__":
    print("--- ekleme izi (m = 3) ---")
    agac = BPlus(3)
    for k in [10, 20, 5, 6, 12, 30, 7, 17]:
        agac.ekle(k, k * 100)
        print("ekle %2d:" % k)
        agac.dok()
    print("aralik [6, 17]:",
          [k for k, _ in agac.aralik(6, 17)])


def yaprak_zinciri(agac):
    d = agac.kok
    while not d.yaprak:
        d = d.cocuk[0]
    zincir = []
    while d is not None:
        zincir.extend(d.anahtar)
        d = d.sonraki
    return zincir


def yapi_gecerli_mi(agac):
    """Tüm yapraklar aynı derinlikte; düğüm dolulukları uygun."""
    derinlikler, sorun = set(), []

    def gez(d, seviye, kok_mu):
        if len(d.anahtar) > agac.m:
            sorun.append("fazla")
        if not kok_mu and len(d.anahtar) < agac.m // 2:
            sorun.append("az")
        if d.yaprak:
            derinlikler.add(seviye)
            return
        if len(d.cocuk) != len(d.anahtar) + 1:
            sorun.append("cocuk")
        for c in d.cocuk:
            gez(c, seviye + 1, False)

    gez(agac.kok, 0, True)
    return len(derinlikler) == 1 and not sorun


if __name__ == "__main__":
    print("--- rastgele test (tohum 33) ---")
    rnd = random.Random(33)
    for m in (3, 4, 8):
        anah = rnd.sample(range(10 ** 6), 2000)
        agac = BPlus(m)
        for k in anah:
            agac.ekle(k, -k)
        duz = sorted(anah)
        aralik_ok = True
        for _ in range(300):
            lo = rnd.randrange(10 ** 6)
            hi = lo + rnd.randrange(50000)
            bekl = [k for k in duz if lo <= k <= hi]
            if [k for k, _ in agac.aralik(lo, hi)] != bekl:
                aralik_ok = False
        print("m=%d zincir=%s yapi=%s aralik=%s" % (
            m, yaprak_zinciri(agac) == duz,
            yapi_gecerli_mi(agac), aralik_ok))

    print("--- yükseklik (N = 10^6) ---")
    N = 10 ** 6
    ikili = math.ceil(math.log2(N + 1))
    f = (4096 - 12) // (8 + 4)   # başlık 12, anahtar 8, işaretçi 4
    seviye = 1
    while f ** seviye < N:
        seviye += 1
    print("dallanma (kaba):", f)
    print("ikili agac yuksekligi:", ikili)
    print("B+ agac seviyesi:", seviye)
