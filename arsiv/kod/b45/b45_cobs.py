# -*- coding: utf-8 -*-
"""b45_cobs.py: COBS (Consistent Overhead Byte Stuffing) kodlayici/cozucu.

Kodlanmis cikti hic 0x00 icermez; cerceve sonu 0x00 ile isaretlenir.
"""
import random


def cobs_kodla(veri):
    cikis = bytearray([0])        # ilk kod baytinin yeri
    kod_yeri = 0
    kod = 1                       # bu blokta bir sonraki kod degeri
    for b in veri:
        if b == 0:
            cikis[kod_yeri] = kod
            kod_yeri = len(cikis)
            cikis.append(0)
            kod = 1
        else:
            cikis.append(b)
            kod += 1
            if kod == 0xFF:       # 254 veri baytı: blok kapanır
                cikis[kod_yeri] = kod
                kod_yeri = len(cikis)
                cikis.append(0)
                kod = 1
    cikis[kod_yeri] = kod
    return bytes(cikis)


def cobs_coz(kodlu):
    cikis = bytearray()
    i, n = 0, len(kodlu)
    while i < n:
        kod = kodlu[i]
        if kod == 0:
            raise ValueError("kodlu veride 0x00 var")
        i += 1
        if i + kod - 1 > n:
            raise ValueError("eksik veri")
        cikis += kodlu[i:i + kod - 1]
        i += kod - 1
        if kod != 0xFF and i < n:
            cikis.append(0)
    return bytes(cikis)


def cerceve(veri):
    """Kodlanmis veriyi 0x00 sonlandiriciyla cerceveler."""
    return cobs_kodla(veri) + b"\x00"


if __name__ == "__main__":
    import sys
    sabitler = [b"", b"\x00", b"\x00\x00", b"\x01", b"\x01\x00\x02",
                bytes(range(1, 255)), bytes(range(1, 256)) + b"\x00"]
    for v in sabitler:
        assert cobs_coz(cobs_kodla(v)) == v, v
        assert 0 not in cobs_kodla(v)
    print("sinir durumlari: TAMAM")
    rnd = random.Random(45)
    maks_ek = 0
    for _ in range(20000):
        n = rnd.randint(0, 700)
        p = rnd.random()
        v = bytes(0 if rnd.random() < p else rnd.randrange(1, 256)
                  for _ in range(n))
        k = cobs_kodla(v)
        assert cobs_coz(k) == v
        assert 0 not in k
        ek = len(k) - len(v)
        assert ek <= 1 + len(v) // 254, (len(v), ek)
        maks_ek = max(maks_ek, ek - len(v) // 254)
    print("20000 rastgele gidis-donus: TAMAM")
    print("ek yuk sinir (1 + n//254) asilmadi, n//254 sonrasi fazla:",
          maks_ek)
    ornek = bytes([0x11, 0x22, 0x00, 0x33])
    print("ornek 11 22 00 33 ->", cobs_kodla(ornek).hex(" "))
    print("cerceveli       ->", cerceve(ornek).hex(" "))
    sys.exit(0)
