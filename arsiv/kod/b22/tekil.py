# tekil.py: Python'da tekil nesne ve test sorunu (Bolum 22.5)
import json as a
import json as b

print("modul onbellegi:", a is b)


class Yapilandirma:
    _ornek = None

    @classmethod
    def al(cls):
        if cls._ornek is None:
            cls._ornek = cls()
            cls._ornek.ayarlar = {"mod": "normal"}
        return cls._ornek


def test_a():
    Yapilandirma.al().ayarlar["mod"] = "test"


def test_b():
    # bagimsiz olmasi gereken test; test_a ayni nesneyi degistirdi
    assert Yapilandirma.al().ayarlar["mod"] == "normal"


class Kaydedici:
    def __init__(self, depo):          # bagimlilik disaridan gelir
        self.depo = depo

    def kaydet(self, veri):
        self.depo.append(veri)


def test_c():
    sahte = []                         # test icin sahte depo
    Kaydedici(sahte).kaydet(1)
    assert sahte == [1]


if __name__ == "__main__":
    test_a()
    try:
        test_b()
        print("test_b gecti")
    except AssertionError:
        print("test_b basarisiz: gizli durum sizdi")
    test_c()
    print("test_c gecti")
