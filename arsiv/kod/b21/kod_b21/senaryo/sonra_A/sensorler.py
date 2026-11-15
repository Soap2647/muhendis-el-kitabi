# -*- coding: utf-8 -*-
"""Somut sensorler. Her sinif kendi birimini ve esigini bilir."""
from kayit import kaydet
from sozlesme import Olcum


@kaydet("termistor")
class TermistorSensor:
    birim = "C"
    esik = 80.0

    def __init__(self, adc, kanal):
        self.adc = adc
        self.kanal = kanal

    def olc(self):
        ham = self.adc.oku(self.kanal)
        return Olcum("termistor", ham * 0.1 - 40.0,
                     self.birim, self.esik)


@kaydet("gerilim")
class GerilimSensor:
    birim = "V"
    esik = None

    def __init__(self, adc, kanal):
        self.adc = adc
        self.kanal = kanal

    def olc(self):
        ham = self.adc.oku(self.kanal)
        return Olcum("gerilim", ham * 3.3 / 4095,
                     self.birim, self.esik)
