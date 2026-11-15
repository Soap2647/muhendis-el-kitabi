# -*- coding: utf-8 -*-
"""Kompozisyon koku: somut siniflar yalnizca burada secilir."""
import basinc  # noqa: F401
import sensorler  # noqa: F401  (import, sinifların kaydolmasını saglar)
from kayit import SENSORLER
from rapor import RaporYoneticisi


class DonanimAdc:
    def oku(self, kanal):
        return 1000 + 100 * kanal


YAPILANDIRMA = [("termistor", 1), ("gerilim", 2), ("basinc", 3)]


def main(yol):
    adc = DonanimAdc()
    liste = [SENSORLER[tur](adc, kanal) for tur, kanal in YAPILANDIRMA]
    return RaporYoneticisi(liste, yol).calistir()


if __name__ == "__main__":
    print(main("rapor.txt"))
