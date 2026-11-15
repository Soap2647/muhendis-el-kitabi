"""Uzunluk önekli çerçeveler (Bölüm 31.4'teki düzen)."""
import struct

MAKS = 1 << 16


def tam_oku(sock, n):
    """Tam n bayt oku: recv kısmi dönebilir (Bölüm 31)."""
    parca = bytearray()
    while len(parca) < n:
        b = sock.recv(n - len(parca))
        if not b:
            raise ConnectionError("karşı taraf kapattı")
        parca += b
    return bytes(parca)


def cerceve_gonder(sock, yuk):
    sock.sendall(struct.pack("!I", len(yuk)) + yuk)


def cerceve_al(sock):
    (n,) = struct.unpack("!I", tam_oku(sock, 4))
    if n > MAKS:
        raise ValueError("çerçeve çok büyük: %d" % n)
    return tam_oku(sock, n)
