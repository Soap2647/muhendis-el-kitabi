import random

KAYITLAR = []           # paylaşılan (global) durum


def test_yaz():
    KAYITLAR.append("a")
    assert len(KAYITLAR) == 1


def test_oku():
    # Sıra bağımlılığı: yalnızca test_yaz önce çalıştıysa geçer.
    assert KAYITLAR == ["a"]


def test_rastgele_zar():
    # Tohumsuz rastgelelik: her çalıştırmada farklı bir sonuç.
    assert random.random() > 0.1
