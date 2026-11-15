# -*- coding: utf-8 -*-
"""Orkestrasyon: adimlari sirayla cagirir, kendisi hesap yapmaz."""
import alarm
import bicim
import istatistik


class RaporYoneticisi:
    def __init__(self, sensorler, yol):
        self.sensorler = sensorler
        self.yol = yol

    def calistir(self):
        olcumler = [s.olc() for s in self.sensorler]
        ort = istatistik.ortalama(olcumler)
        with open(self.yol, "w", encoding="utf-8") as f:
            f.write(bicim.metin(olcumler, ort))
        return ort, alarm.alarmlar(olcumler)
