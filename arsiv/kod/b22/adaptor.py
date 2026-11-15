# adaptor.py: eski surucuyu yeni arayuze uyarlamak (Bolum 22.6)
from typing import Protocol


class Sicaklik(Protocol):          # yeni arayuz (hedef)
    def celsius(self) -> float: ...


class EskiSurucu:                  # uyarlanan: ham ADC sayisi
    """Eski API: 12 bit ham deger (0..4095) dondurur."""
    def __init__(self, ham_degerler):
        self._degerler = ham_degerler

    def adc_oku(self, kanal):
        return self._degerler[kanal]


class Uyarlayici:                  # adapter
    """10 mV/derece, 3.3 V referans varsayimi (ornek amacli)."""
    def __init__(self, eski, kanal):
        self._eski = eski
        self._kanal = kanal

    def celsius(self):
        ham = self._eski.adc_oku(self._kanal)
        gerilim = ham / 4095 * 3.3
        return gerilim / 0.010


def olc(sensor: Sicaklik) -> str:
    return "%.1f C" % sensor.celsius()


if __name__ == "__main__":
    eski = EskiSurucu([1024, 2048, 3000])
    for k in range(3):
        print("kanal", k, "->", olc(Uyarlayici(eski, k)))
    import io
    m = io.TextIOWrapper(io.BytesIO("merhaba\n".encode()),
                         encoding="utf-8")
    print("TextIOWrapper:", m.readline().rstrip())
