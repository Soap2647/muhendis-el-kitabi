from dataclasses import dataclass

ESIK = 3.6
BASLIK = "CIHAZ       ADET      MIN      MAX    ORT  DURUM"


@dataclass
class CihazOzeti:
    minimum: float
    maksimum: float
    toplam: float = 0.0
    adet: int = 0

    def ekle(self, volt):
        self.minimum = min(self.minimum, volt)
        self.maksimum = max(self.maksimum, volt)
        self.toplam += volt
        self.adet += 1

    def ortalama(self):
        return self.toplam / self.adet

    def durum(self):
        return "UYARI" if self.maksimum > ESIK else "TAMAM"


def satir_ayristir(satir):
    cihaz, zaman, deger, birim = satir.split(";")
    if not zaman.isdigit():
        raise ValueError("zaman")
    deger = float(deger)
    if birim == "mV":
        deger = deger / 1000
    elif birim != "V":
        raise ValueError("birim")
    return cihaz, deger


def ozetle(satirlar):
    cihazlar = {}
    hatalar = 0
    for satir in satirlar:
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        try:
            cihaz, deger = satir_ayristir(satir)
        except ValueError:
            hatalar += 1
            continue
        if cihaz not in cihazlar:
            cihazlar[cihaz] = CihazOzeti(deger, deger)
        cihazlar[cihaz].ekle(deger)
    return cihazlar, hatalar


def satir_bicimle(ad, c):
    return "%-10s %5d %8.3f %8.3f %6.3f  %s" % (
        ad, c.adet, c.minimum, c.maksimum, c.ortalama(), c.durum())


def rapor_uret(satirlar):
    cihazlar, hatalar = ozetle(satirlar)
    cikti = [BASLIK]
    for ad in sorted(cihazlar):
        cikti.append(satir_bicimle(ad, cihazlar[ad]))
    cikti.append("hatali satir: %d" % hatalar)
    return "\n".join(cikti) + "\n"
