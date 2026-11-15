# ornek4.py: onbellek + olcum + yeniden deneme zinciri (Ornek 4)
from sarici import Okuyucu, Onbellek, Yeniden


class Saat:
    def __init__(self):
        self.t = 0.0


class SaatliHam(Okuyucu):
    """Her deneme 5 ms surer; basarisiz denemeler de sure harcar."""
    def __init__(self, saat, hatali):
        self.saat = saat
        self.hatali = hatali
        self.deneme = 0

    def oku(self):
        self.deneme += 1
        self.saat.t += 0.005
        if self.deneme in self.hatali:
            raise IOError("deneme %d basarisiz" % self.deneme)
        return 20.0 + self.deneme


class Olcum(Okuyucu):
    """Ic cagrinin harcadigi toplam sureyi biriktirir."""
    def __init__(self, ic, saat):
        self._ic = ic
        self._saat = saat
        self.sure = 0.0

    def oku(self):
        t0 = self._saat.t
        try:
            return self._ic.oku()
        finally:
            self.sure += self._saat.t - t0


def zincir_a():
    saat = Saat()
    ham = SaatliHam(saat, hatali={2})
    olc = Olcum(Yeniden(ham), saat)          # onbellek yok
    return olc, ham


def zincir_b():
    saat = Saat()
    ham = SaatliHam(saat, hatali={2})
    olc = Olcum(Yeniden(ham), saat)
    return Onbellek(olc), olc, ham           # onbellek en dis katman


if __name__ == "__main__":
    olc, ham = zincir_a()
    for i in (1, 2):
        v = olc.oku()
        print("A %d: deger=%.1f deneme=%d sure=%.3f s"
              % (i, v, ham.deneme, olc.sure))
    z, olc, ham = zincir_b()
    for i in (1, 2):
        v = z.oku()
        print("B %d: deger=%.1f deneme=%d sure=%.3f s"
              % (i, v, ham.deneme, olc.sure))
