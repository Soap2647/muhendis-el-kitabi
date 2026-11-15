from tarih import artik_yil_mi, gecerli_tarih


def test_temel():
    assert gecerli_tarih(2024, 1, 1)
    assert not gecerli_tarih(2023, 2, 29)
    assert artik_yil_mi(2024)
