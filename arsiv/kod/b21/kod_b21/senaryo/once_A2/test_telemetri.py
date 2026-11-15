# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from unittest import mock

import olcum
from rapor import RaporYoneticisi


class OlcumTesti(unittest.TestCase):
    def test_termistor(self):
        with mock.patch("olcum._adc_oku", return_value=1100):
            (tur, deger, birim, _), = olcum.olcumleri_oku(
                [("termistor", 1)])
        self.assertEqual((tur, birim), ("termistor", "C"))
        self.assertAlmostEqual(deger, 70.0)

    def test_gerilim(self):
        with mock.patch("olcum._adc_oku", return_value=2048):
            (_, deger, birim, _), = olcum.olcumleri_oku([("gerilim", 2)])
        self.assertEqual(birim, "V")
        self.assertAlmostEqual(deger, 2048 * 3.3 / 4095)


class RaporTesti(unittest.TestCase):
    def setUp(self):
        self.yol = os.path.join(tempfile.mkdtemp(), "r.txt")
        self.adc = lambda k: {1: 1100, 2: 2048, 3: 1300}[k]

    def test_ortalama_ve_dosya(self):
        with mock.patch("olcum._adc_oku", side_effect=self.adc):
            ort, _ = RaporYoneticisi([("termistor", 1),
                                      ("gerilim", 2)], self.yol).calistir()
        beklenen = (70.0 + 2048 * 3.3 / 4095) / 2
        self.assertAlmostEqual(ort, beklenen)
        with open(self.yol, encoding="utf-8") as f:
            self.assertIn("ORT", f.read())

    def test_alarm(self):
        with mock.patch("olcum._adc_oku", side_effect=self.adc):
            _, alarmlar = RaporYoneticisi([("termistor", 3)],
                                          self.yol).calistir()
        self.assertEqual(len(alarmlar), 1)

    def test_bos_liste_hata(self):
        with self.assertRaises(ValueError):
            RaporYoneticisi([], self.yol).calistir()


if __name__ == "__main__":
    unittest.main()
