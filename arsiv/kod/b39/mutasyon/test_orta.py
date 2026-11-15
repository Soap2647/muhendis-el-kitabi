import pytest

from tarih import artik_yil_mi, gecerli_tarih


@pytest.mark.parametrize("yil, ay, gun, beklenen", [
    (2024, 1, 1, True),
    (2024, 12, 31, True),
    (2024, 1, 0, False),
    (2024, 1, 32, False),
    (2024, 0, 15, False),
    (2024, 13, 15, False),
    (2023, 2, 28, True),
    (2023, 2, 29, False),
    (2024, 2, 29, True),
    (2000, 2, 29, True),
    (1900, 2, 29, False),
    (2024, 4, 30, True),
    (2024, 4, 31, False),
])
def test_sinir_degerler(yil, ay, gun, beklenen):
    assert gecerli_tarih(yil, ay, gun) is beklenen


@pytest.mark.parametrize("yil, beklenen", [
    (1900, False), (2000, True), (2024, True), (2023, False),
])
def test_artik_yil(yil, beklenen):
    assert artik_yil_mi(yil) is beklenen
