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


def test_dolu_iken_ekle_hata_verir():
    t = HalkaTampon(2)
    t.ekle(1)
    t.ekle(2)
    with pytest.raises(BufferError):
        t.ekle(3)


def test_sarma_kapasite_asilmadan_yeniden_kullanilir():
    t = HalkaTampon(3)
    for x in (1, 2, 3):
        t.ekle(x)
    assert t.al() == 1       # bas ilerler, yer açılır
    t.ekle(4)                # 4, 1'in eski yerine yazılır
    assert [t.al(), t.al(), t.al()] == [2, 3, 4]
