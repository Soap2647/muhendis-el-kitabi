# -*- coding: utf-8 -*-
"""LSP: Dikdortgen/Kare ihlali, onkosul guclendirme, ortak test paketi."""
import unittest


class Dikdortgen:
    def __init__(self, en, boy):
        self._en = en
        self._boy = boy

    def en_ayarla(self, en):
        self._en = en

    def boy_ayarla(self, boy):
        self._boy = boy

    def alan(self):
        return self._en * self._boy


class Kare(Dikdortgen):
    def __init__(self, kenar):
        super().__init__(kenar, kenar)

    def en_ayarla(self, en):
        self._en = self._boy = en

    def boy_ayarla(self, boy):
        self._en = self._boy = boy


class DikdortgenTesti(unittest.TestCase):
    """Dikdortgen sozlesmesi: her alt sinif bu testleri gecmeli."""

    def yarat(self):
        return Dikdortgen(2, 3)

    def test_en_degisince_alan_degisir(self):
        s = self.yarat()
        s.en_ayarla(4)
        self.assertEqual(s.alan(), 12)

    def test_boy_degisince_alan_degisir(self):
        s = self.yarat()
        s.boy_ayarla(5)
        self.assertEqual(s.alan(), 10)


class KareTesti(DikdortgenTesti):
    def yarat(self):
        return Kare(2)


class Okuyucu:
    def kalibre(self, katsayi):
        self.k = katsayi

    def olc(self, ham):
        return ham * self.k


class PozitifOkuyucu(Okuyucu):
    def kalibre(self, katsayi):
        if katsayi <= 0:
            raise ValueError("katsayi pozitif olmali")
        self.k = katsayi


class OkuyucuTesti(unittest.TestCase):
    def yarat(self):
        return Okuyucu()

    def test_negatif_katsayi_kabul_edilir(self):
        o = self.yarat()
        o.kalibre(-2)
        self.assertEqual(o.olc(5), -10)


class PozitifOkuyucuTesti(OkuyucuTesti):
    def yarat(self):
        return PozitifOkuyucu()


if __name__ == "__main__":
    unittest.main(verbosity=1)
