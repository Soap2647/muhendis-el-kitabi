# ayar.py: parametre sayisi arttiginda iki yaklasim (Bolum 22.4)
from dataclasses import dataclass


@dataclass(frozen=True)
class UcusAyar:
    hiz: float = 10.0          # m/s
    irtifa: float = 50.0       # m
    batarya: float = 80.0      # yuzde
    gps: bool = True
    kayit: bool = False

    def __post_init__(self):   # dogrulama tek yerde
        if not 0 < self.hiz <= 30:
            raise ValueError("hiz 0..30 m/s olmali")
        if not 0 <= self.batarya <= 100:
            raise ValueError("batarya 0..100 olmali")


class AyarInsaatcisi:
    def __init__(self):
        self._deger = {}

    def hiz(self, v):
        self._deger["hiz"] = v
        return self                  # zincir icin kendini dondur

    def irtifa(self, v):
        self._deger["irtifa"] = v
        return self

    def kayit(self, v=True):
        self._deger["kayit"] = v
        return self

    def build(self):
        return UcusAyar(**self._deger)


if __name__ == "__main__":
    a = UcusAyar(hiz=12.0, irtifa=120.0)
    b = AyarInsaatcisi().hiz(12.0).irtifa(120.0).build()
    print("esit:", a == b)
    print(b)
    for hiz in (0, 40):
        try:
            AyarInsaatcisi().hiz(hiz).build()
        except ValueError as e:
            print("reddedildi:", e)
