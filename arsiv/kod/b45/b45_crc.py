# -*- coding: utf-8 -*-
"""b45_crc.py: CRC-16/CCITT-FALSE, CRC-15/CAN ve toplama sagamasi.

Bitsel (bit bit) ve tablo tabanli iki gerceklemeyi karsilastirir.
"""


def crc16_ccitt_false(veri):
    """CRC-16/CCITT-FALSE: poli 0x1021, ilk 0xFFFF, xorout yok."""
    crc = 0xFFFF
    for b in veri:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def _tablo_16():
    tablo = []
    for i in range(256):
        c = i << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) if (c & 0x8000) else (c << 1)
            c &= 0xFFFF
        tablo.append(c)
    return tablo


TABLO16 = _tablo_16()


def crc16_tablo(veri):
    """Ayni CRC, 256 girisli tablo ile (bayt basina bir adim)."""
    crc = 0xFFFF
    for b in veri:
        crc = ((crc << 8) & 0xFFFF) ^ TABLO16[((crc >> 8) ^ b) & 0xFF]
    return crc


def crc15_can(bitler):
    """CAN CRC-15: poli 0x4599, baslangic 0. Girdi bit listesi."""
    crc = 0
    for bit in bitler:
        geri = ((crc >> 14) & 1) ^ bit
        crc = (crc << 1) & 0x7FFF
        if geri:
            crc ^= 0x4599
    return crc


def toplama8(veri):
    """Daly BMS tarzi toplama sagamasi: bayt toplaminin alt 8 biti."""
    return sum(veri) & 0xFF


if __name__ == "__main__":
    import random
    print("CRC-16/CCITT-FALSE('123456789') = 0x%04X" %
          crc16_ccitt_false(b"123456789"))
    print("tablo ile aynı mı:", crc16_tablo(b"123456789") == 0x29B1)
    rnd = random.Random(45)
    for _ in range(2000):
        n = rnd.randint(0, 64)
        v = bytes(rnd.randrange(256) for _ in range(n))
        assert crc16_ccitt_false(v) == crc16_tablo(v)
    print("2000 rastgele girdide bitsel = tablo: TAMAM")
    # CAN: CRC'yi mesajin sonuna eklemek kalani sifira indirir
    mesaj = [rnd.randrange(2) for _ in range(40)]
    c = crc15_can(mesaj)
    kalan = [(c >> (14 - i)) & 1 for i in range(15)]
    print("CAN CRC-15 sifir kalan testi:", crc15_can(mesaj + kalan) == 0)
