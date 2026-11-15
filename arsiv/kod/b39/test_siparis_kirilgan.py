from unittest.mock import Mock

import pytest

from siparis import SiparisServisi, SiparisServisiV2


@pytest.fixture(params=[SiparisServisi, SiparisServisiV2],
                ids=lambda c: c.__name__)
def servis_sinifi(request):
    return request.param


def test_cagri_sirasi_kirilgan(servis_sinifi):
    # AŞIRI MOCK: test, davranış yerine iç çağrı dizisini sınar.
    depo = Mock()
    depo.stok_al.return_value = 5
    eposta = Mock()
    servis_sinifi(depo, eposta).olustur("kalem", 2)
    ad = [c[0] for c in depo.mock_calls]
    assert ad == ["stok_al", "stok_dus"]
    eposta.gonder.assert_called_once_with("siparis", "kalem", 2)
