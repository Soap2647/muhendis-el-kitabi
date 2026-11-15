# fasad.py: karmasik alt sistemin sade on yuzu (Bolum 22.8)
import zlib


class Ayristirici:
    def coz(self, metin):
        alanlar = metin.split(";")
        return {"id": alanlar[0], "deger": float(alanlar[1])}


class Dogrulayici:
    def gecerli_mi(self, paket):
        return 0 <= paket["deger"] <= 150


class Sikistirici:
    def paketle(self, metin):
        return zlib.compress(metin.encode("utf-8"))


class TelemetriFasad:
    """Istemci yalnizca gonder() cagirir; alt sistemleri bilmez."""
    def __init__(self):
        self._ayristir = Ayristirici()
        self._dogrula = Dogrulayici()
        self._sikistir = Sikistirici()

    def gonder(self, metin):
        paket = self._ayristir.coz(metin)
        if not self._dogrula.gecerli_mi(paket):
            return None
        return self._sikistir.paketle(metin)


if __name__ == "__main__":
    f = TelemetriFasad()
    g = f.gonder("ARAC7;23.5")
    print("sikistirilmis bayt:", len(g))
    print("geri acildi:", zlib.decompress(g).decode())
    print("gecersiz:", f.gonder("ARAC7;999"))
