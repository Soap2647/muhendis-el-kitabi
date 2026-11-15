# -*- coding: utf-8 -*-
"""b31_baslik.py: surumlenebilir mesaj basligi (12 bayt) + CRC-32.
Kullanim: python b31_baslik.py   (testleri calistirir)"""

import struct
import zlib

BASLIK = struct.Struct("!HBBII")  # sihir, surum, tur, uzunluk, crc
SIHIR = 0xB31C
SURUM = 1
MAKS = 1 << 20


def paketle(tur, yuk):
    ust = struct.pack("!HBBI", SIHIR, SURUM, tur, len(yuk))
    crc = zlib.crc32(yuk, zlib.crc32(ust))  # CRC basligi da kapsar
    return ust + struct.pack("!I", crc) + yuk


def coz(b):
    if len(b) < BASLIK.size:
        raise ValueError("kisa paket")
    sihir, surum, tur, n, crc = BASLIK.unpack_from(b, 0)
    if sihir != SIHIR:
        raise ValueError("sihir uyusmuyor: 0x%04X" % sihir)
    if surum != SURUM:
        raise ValueError("desteklenmeyen surum: %d" % surum)
    if n > MAKS:
        raise ValueError("uzunluk sinirin ustunde: %d" % n)
    yuk = bytes(b[BASLIK.size : BASLIK.size + n])
    if len(yuk) != n:
        raise ValueError("eksik paket")
    ust = struct.pack("!HBBI", sihir, surum, tur, n)
    if zlib.crc32(yuk, zlib.crc32(ust)) != crc:
        raise ValueError("CRC uyusmuyor")
    return tur, yuk


if __name__ == "__main__":
    print("BASLIK boyutu:", BASLIK.size)
    p = paketle(3, b"merhaba")
    print("paket:", p.hex(" "))
    print("coz:", coz(p))
    for ad, bozuk in [
        ("tur bayti", p[:3] + bytes([p[3] ^ 1]) + p[4:]),
        ("yuk biti", p[:-1] + bytes([p[-1] ^ 0x10])),
        ("sihir", b"\x00" + p[1:]),
    ]:
        try:
            coz(bozuk)
            print(ad, "kabul edildi")
        except ValueError as e:
            print("%-10s reddedildi: %s" % (ad, e))
    try:
        coz(struct.pack("!HBBII", SIHIR, SURUM, 1, 0xFFFFFFFF, 0))
    except ValueError as e:
        print("asiri uzunluk reddedildi: %s" % e)
