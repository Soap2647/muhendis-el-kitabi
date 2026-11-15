import socket
import threading

import pytest

from cerceve import cerceve_al, cerceve_gonder


@pytest.fixture(scope="session")
def yanki_sunucu():
    """Oturum boyunca yaşayan, çerçeveyi geri yollayan sunucu."""
    dinleyici = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dinleyici.bind(("127.0.0.1", 0))    # port 0: çekirdek seçer
    dinleyici.listen(1)
    port = dinleyici.getsockname()[1]

    def calis():
        conn, _ = dinleyici.accept()
        with conn:
            while True:
                try:
                    yuk = cerceve_al(conn)
                except ConnectionError:
                    break
                cerceve_gonder(conn, yuk)
        dinleyici.close()

    threading.Thread(target=calis, daemon=True).start()
    return port
