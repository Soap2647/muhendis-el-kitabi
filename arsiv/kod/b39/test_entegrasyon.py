import socket
import struct

import pytest

from cerceve import cerceve_al, cerceve_gonder
from depo import OlcumDeposu


def test_sqlite_veri_yeniden_acilinca_kalir(tmp_path):
    yol = tmp_path / "olcum.db"
    d = OlcumDeposu(yol)
    d.ekle(1, 20.5)
    d.ekle(1, 21.0)
    d.kapat()
    d2 = OlcumDeposu(yol)               # yeni bağlantı, aynı dosya
    assert d2.son(1, 2) == [21.0, 20.5]
    d2.kapat()


def test_soket_yanki(yanki_sunucu):
    with socket.create_connection(("127.0.0.1", yanki_sunucu)) as s:
        cerceve_gonder(s, b"merhaba")
        assert cerceve_al(s) == b"merhaba"


def test_bolunmus_akis_dogru_okunur():
    # Gönderici veriyi 7 baytlık parçalara böler: recv tek seferde
    # tamamını vermez, tam_oku bunu toplamalıdır.
    a, b = socket.socketpair()
    with a, b:
        yuk = b"x" * 1000
        cerceve = struct.pack("!I", len(yuk)) + yuk
        for i in range(0, len(cerceve), 7):
            a.sendall(cerceve[i:i + 7])
        assert cerceve_al(b) == yuk


def test_buyuk_cercevede_bellek_ayrilmadan_reddedilir():
    a, b = socket.socketpair()
    with a, b:
        a.sendall(struct.pack("!I", 1 << 20))
        with pytest.raises(ValueError):
            cerceve_al(b)
