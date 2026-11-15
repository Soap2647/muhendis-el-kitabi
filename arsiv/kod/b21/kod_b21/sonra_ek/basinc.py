# -*- coding: utf-8 -*-
"""Basinc sensoru: yeni tur, mevcut dosyalar degismeden eklenir."""
from kayit import kaydet
from sozlesme import Olcum


@kaydet("basinc")
class BasincSensor:
    birim = "kPa"
    esik = 110.0

    def __init__(self, adc, kanal):
        self.adc = adc
        self.kanal = kanal

    def olc(self):
        ham = self.adc.oku(self.kanal)
        return Olcum("basinc", ham * 0.05, self.birim, self.esik)
