# birlikte.py: komut + gozlemci + durum, tek mini sistemde (22.13)
from durum import Ucak, GecersizGecis


class Kayit:
    """Gozlemci: her gecisi bir satir olarak saklar."""
    def __init__(self):
        self.satirlar = []

    def guncelle(self, eski, yeni, olay):
        self.satirlar.append("%s -%s-> %s" % (eski, olay, yeni))


class OlayKomutu:
    """Command: bir olayi nesne olarak tutar, geri alabilir."""
    def __init__(self, ucak, olay):
        self.ucak = ucak
        self.olay = olay
        self.eski = None

    def calistir(self):
        self.eski = self.ucak.durum       # geri almak icin sakla
        self.ucak.olay(self.olay)

    def geri_al(self):
        self.ucak.durum = self.eski


class Yonetici:
    def __init__(self, ucak):
        self.ucak = ucak
        self.gecmis = []
        self.gozlemciler = []

    def yap(self, olay):
        eski = self.ucak.durum.ad
        k = OlayKomutu(self.ucak, olay)
        k.calistir()                      # GecersizGecis yukari cikar
        self.gecmis.append(k)
        self._bildir(eski, self.ucak.durum.ad, olay)

    def geri(self):
        if not self.gecmis:
            return
        eski = self.ucak.durum.ad
        k = self.gecmis.pop()
        k.geri_al()
        self._bildir(eski, self.ucak.durum.ad, "geri")

    def _bildir(self, eski, yeni, olay):
        for g in self.gozlemciler:
            g(eski, yeni, olay)


if __name__ == "__main__":
    u = Ucak()
    y = Yonetici(u)
    kayit = Kayit()
    y.gozlemciler.append(kayit.guncelle)
    for e in ["kalkis_emri", "inis_emri", "irtifa_ulasti",
              "inis_emri", "geri"]:
        try:
            if e == "geri":
                y.geri()
            else:
                y.yap(e)
        except GecersizGecis:
            print("reddedildi:", e)
    for s in kayit.satirlar:
        print(s)
    print("son durum:", u.durum.ad)
