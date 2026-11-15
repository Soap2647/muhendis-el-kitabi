# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

import alarm
import istatistik
import sensorler
from rapor import RaporYoneticisi


class SahteAdc:
    """Donanim yerine test sahtesi: AdcKaynagi arayuzunu uygular."""

    def __init__(self, tablo):
        self.tablo = tablo

    def oku(self, kanal):
        return self.tablo[kanal]


class SensorTesti(unittest.TestCase):
    def test_termistor(self):
        s = sensorler.TermistorSensor(SahteAdc({1: 1100}), 1)
        o = s.olc()
        self.assertEqual((o.tur, o.birim), ("termistor", "C"))
        self.assertAlmostEqual(o.deger, 70.0)

    def test_gerilim(self):
        s = sensorler.GerilimSensor(SahteAdc({2: 2048}), 2)
        o = s.olc()
        self.assertEqual(o.birim, "V")
        self.assertAlmostEqual(o.deger, 2048 * 3.3 / 4095)


class RaporTesti(unittest.TestCase):
    def setUp(self):
        self.yol = os.path.join(tempfile.mkdtemp(), "r.txt")
        self.adc = SahteAdc({1: 1100, 2: 2048, 3: 1300})

    def test_ortalama_ve_dosya(self):
        liste = [sensorler.TermistorSensor(self.adc, 1),
                 sensorler.GerilimSensor(self.adc, 2)]
        ort, _ = RaporYoneticisi(liste, self.yol).calistir()
        beklenen = (70.0 + 2048 * 3.3 / 4095) / 2
        self.assertAlmostEqual(ort, beklenen)
        with open(self.yol, encoding="utf-8") as f:
            self.assertIn("ORT", f.read())

    def test_alarm(self):
        liste = [sensorler.TermistorSensor(self.adc, 3)]
        _, alarmlar = RaporYoneticisi(liste, self.yol).calistir()
        self.assertEqual(len(alarmlar), 1)

    def test_bos_liste_hata(self):
        with self.assertRaises(ValueError):
            RaporYoneticisi([], self.yol).calistir()


if __name__ == "__main__":
    unittest.main()
