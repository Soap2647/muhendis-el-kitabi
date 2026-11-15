# fabrika.py: kayit tablosuyla sensor fabrikasi (Bolum 22.3)
_KAYIT = {}


class Sensor:
    def oku(self):
        raise NotImplementedError


def kayit(ad):
    """Sinifi fabrika tablosuna ad ile ekleyen dekorator."""
    def ekle(sinif):
        _KAYIT[ad] = sinif
        return sinif
    return ekle


@kayit("termistor")
class Termistor(Sensor):
    def oku(self):
        return 23.5


@kayit("nem")
class Nem(Sensor):
    def oku(self):
        return 61.0


def sensor_olustur(ad):
    try:
        sinif = _KAYIT[ad]
    except KeyError:
        raise ValueError("bilinmeyen sensor: " + ad) from None
    return sinif()


if __name__ == "__main__":
    for ad in ["termistor", "nem"]:
        s = sensor_olustur(ad)
        print(ad, type(s).__name__, s.oku())
    try:
        sensor_olustur("basinc")
    except ValueError as e:
        print("hata:", e)
    from pathlib import Path
    print("pathlib:", type(Path("a.txt")).__name__)
