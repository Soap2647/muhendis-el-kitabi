# gozlemci.py: yayinci/abone, zayif referans, yeniden giris (22.10)
import weakref


class Alarm:
    def __init__(self, ad, esik):
        self.ad = ad
        self.esik = esik
        self.kayitlar = []

    def olay(self, deger):
        self.kayitlar.append(deger)
        if deger > self.esik:
            print("  ALARM", self.ad, deger)


class Konu:
    def __init__(self):
        self._gozlemciler = []                # zayif referanslar

    def abone_ol(self, fonk):
        self._gozlemciler.append(weakref.WeakMethod(fonk))

    def cik(self, fonk):
        hedef = weakref.WeakMethod(fonk)
        self._gozlemciler[:] = [r for r in self._gozlemciler
                                if r != hedef]   # yerinde degisir

    def bildir(self, deger):
        for ref in list(self._gozlemciler):   # kopya uzerinde gez
            fonk = ref()
            if fonk is None:
                self._gozlemciler.remove(ref)  # olu referansi temizle
            else:
                fonk(deger)


class NaifKonu(Konu):
    """HATALI surum: liste gezilirken degisebilir."""
    def bildir(self, deger):
        for ref in self._gozlemciler:
            fonk = ref()
            if fonk is not None:
                fonk(deger)


class Tek:
    """Ilk olayda kendini abonelikten cikaran gozlemci."""
    def __init__(self, konu, ad):
        self.konu = konu
        self.ad = ad

    def olay(self, deger):
        print("  %s aldi: %s" % (self.ad, deger))
        self.konu.cik(self.olay)


def tekrar(sinif):
    k = sinif()
    t = Tek(k, "A")
    b = Alarm("B", 0)
    k.abone_ol(t.olay)
    k.abone_ol(b.olay)
    k.bildir(1)
    print(sinif.__name__, "-> B kayitlari:", b.kayitlar)


if __name__ == "__main__":
    tekrar(NaifKonu)
    tekrar(Konu)
    k = Konu()
    kritik = Alarm("kritik", 80)
    k.abone_ol(kritik.olay)
    gecici = Alarm("gecici", 0)
    k.abone_ol(gecici.olay)
    k.bildir(10)
    del gecici                      # Konu onu tutmaz
    k.bildir(85)
    print("abone sayisi:", len(k._gozlemciler))
