import sys
import unittest

import pytest


def test_kayan_nokta_yaklasik():
    assert 0.1 + 0.2 == pytest.approx(0.3)
    assert 0.1 + 0.2 != 0.3      # IEEE-754 (Bölüm 1)


@pytest.mark.skipif(sys.platform != "linux",
                    reason="yalnız Linux'ta")
def test_linux_ozel():
    assert sys.platform == "linux"


@pytest.mark.xfail(reason="bilinen hata: kayan nokta yuvarlama")
def test_bilinen_hata():
    assert 0.1 + 0.2 == 0.3


class BolumUnittest(unittest.TestCase):
    # pytest, unittest.TestCase sınıflarını da çalıştırır (Bölüm 21).
    def test_alan(self):
        self.assertEqual(2 * 3, 6)
