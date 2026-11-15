import pytest

from halka import HalkaTampon


def test_yeni_tampon_bostur():
    t = HalkaTampon(3)
    assert t.bos()
    assert len(t) == 0


def test_fifo_sirasi():
    t = HalkaTampon(3)
    t.ekle(1)
    t.ekle(2)
    assert t.al() == 1
    assert t.al() == 2


def test_bosken_al_hata_verir():
    with pytest.raises(IndexError):
        HalkaTampon(3).al()
