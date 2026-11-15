import pytest

from siparis import (BellekDeposu, KayitliEposta, SiparisServisi,
                     SiparisServisiV2, StokYetersiz)


@pytest.fixture(params=[SiparisServisi, SiparisServisiV2],
                ids=lambda c: c.__name__)
def servis_sinifi(request):
    return request.param


def test_yeterli_stokta_siparis_onaylanir(servis_sinifi):
    depo = BellekDeposu({"kalem": 5})
    servis = servis_sinifi(depo, KayitliEposta())
    assert servis.olustur("kalem", 2) == "onay"
    assert depo.stoklar["kalem"] == 3


def test_stok_yetersizse_hata_ve_stok_degismez(servis_sinifi):
    depo = BellekDeposu({"kalem": 1})
    servis = servis_sinifi(depo, KayitliEposta())
    with pytest.raises(StokYetersiz):
        servis.olustur("kalem", 2)
    assert depo.stoklar["kalem"] == 1


def test_basarili_siparis_bildirim_gonderir(servis_sinifi):
    eposta = KayitliEposta()
    servis = servis_sinifi(BellekDeposu({"kalem": 5}), eposta)
    servis.olustur("kalem", 2)
    assert eposta.mesajlar == [("siparis", "kalem", 2)]


def test_sifir_adet_reddedilir(servis_sinifi):
    servis = servis_sinifi(BellekDeposu({"kalem": 5}),
                           KayitliEposta())
    with pytest.raises(ValueError):
        servis.olustur("kalem", 0)
