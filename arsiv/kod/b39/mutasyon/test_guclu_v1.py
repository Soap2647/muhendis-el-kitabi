import datetime

import pytest

from tarih import artik_yil_mi, gecerli_tarih


# Sınır değer analizi: her aralığın iki ucu ve bir dışı.
@pytest.mark.parametrize("yil, ay, gun, beklenen", [
    (2024, 1, 1, True),      # ilk gün
    (2024, 12, 31, True),    # son gün
    (2024, 1, 0, False),     # bir altı
    (2024, 1, 32, False),    # bir üstü
    (2024, 0, 15, False),    # ay alt sınırın dışı
    (2024, 13, 15, False),   # ay üst sınırın dışı
    (2023, 2, 28, True),     # normal yıl, Şubat'ın son günü
    (2023, 2, 29, False),    # normal yıl, 29 Şubat yok
    (2024, 2, 29, True),     # artık yıl
    (2000, 2, 29, True),     # 400'e bölünen artık yıl
    (1900, 2, 29, False),    # 100'e bölünen, 400'e bölünmeyen
    (2024, 4, 30, True),     # 30 çeken ay
    (2024, 4, 31, False),    # 30 çeken ayın 31'i
])
def test_sinir_degerler(yil, ay, gun, beklenen):
    assert gecerli_tarih(yil, ay, gun) is beklenen


@pytest.mark.parametrize("yil, beklenen", [
    (1900, False), (2000, True), (2024, True), (2023, False),
])
def test_artik_yil(yil, beklenen):
    assert artik_yil_mi(yil) is beklenen


def test_1900_2100_tum_gunler_datetime_ile_ayni():
    # datetime.date geçersiz tarihte ValueError verir: bağımsız
    # bir referans. Her yıl, ay ve gün için karşılaştır.
    for yil in range(1900, 2101):
        for ay in range(1, 13):
            for gun in range(1, 32):
                try:
                    datetime.date(yil, ay, gun)
                    ref = True
                except ValueError:
                    ref = False
                assert gecerli_tarih(yil, ay, gun) == ref, (yil, ay, gun)
