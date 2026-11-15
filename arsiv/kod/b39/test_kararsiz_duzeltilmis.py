import random

import pytest

KAYITLAR = []


@pytest.fixture(autouse=True)
def temiz_durum():
    # Her test kendi durumuyla başlar; sıraya bağlı değildir.
    KAYITLAR.clear()
    yield


def test_yaz():
    KAYITLAR.append("a")
    assert KAYITLAR == ["a"]


def test_oku_kendi_kurulumunu_yapar():
    KAYITLAR.extend(["a"])
    assert KAYITLAR == ["a"]


def test_rastgele_zar_tohumlu():
    rng = random.Random(42)           # her çalıştırmada aynı dizi
    assert rng.random() > 0.1
