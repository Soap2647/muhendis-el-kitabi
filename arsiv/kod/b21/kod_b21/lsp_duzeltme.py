# -*- coding: utf-8 -*-
"""LSP duzeltmesi: kalitim yok; ortak arayuz yalnizca alan() icerir."""
import unittest
from typing import Protocol


class Sekil(Protocol):
    def alan(self) -> float: ...


class Dikdortgen:
    def __init__(self, en, boy):
        self.en = en
        self.boy = boy

    def alan(self):
        return self.en * self.boy


class Kare:
    def __init__(self, kenar):
        self.kenar = kenar

    def alan(self):
        return self.kenar * self.kenar


class SekilTesti(unittest.TestCase):
    def test_alan_sozlesmesi(self):
        for s, beklenen in ((Dikdortgen(2, 3), 6), (Kare(2), 4)):
            with self.subTest(sekil=type(s).__name__):
                self.assertEqual(s.alan(), beklenen)


if __name__ == "__main__":
    unittest.main(verbosity=2)
