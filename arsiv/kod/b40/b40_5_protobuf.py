# -*- coding: utf-8 -*-
"""b40_5_protobuf.py: Protocol Buffers kodlamasini elle yapar.

Mesaj: message Telemetri { uint32 id = 1; sint32 sicaklik = 2;
                           string ad = 4; }
"""


def varint_kodla(n):
    cikti = bytearray()
    while True:
        bayt = n & 0x7F  # alttaki 7 bit
        n >>= 7
        if n:
            cikti.append(bayt | 0x80)  # devam biti: sonra gelen var
        else:
            cikti.append(bayt)
            return bytes(cikti)


def varint_coz(veri, i):
    """(deger, yeni_konum) dondurur."""
    n, kayma = 0, 0
    while True:
        b = veri[i]
        i += 1
        n |= (b & 0x7F) << kayma
        kayma += 7
        if not b & 0x80:
            return n, i
        if kayma > 63:
            raise ValueError("varint cok uzun")


def zigzag_kodla(n):
    return (n << 1) ^ (n >> 31)  # sint32 icin: -3 -> 5, 3 -> 6


def zigzag_coz(z):
    return (z >> 1) ^ -(z & 1)


def alan_kodla(no, tip, deger):
    anahtar = varint_kodla((no << 3) | tip)
    if tip == 0:  # varint
        return anahtar + varint_kodla(deger)
    if tip == 2:  # uzunluk onekli
        return anahtar + varint_kodla(len(deger)) + deger
    raise ValueError("desteklenmeyen tip")


def telemetri_kodla(id_, sicaklik, ad):
    return (
        alan_kodla(1, 0, id_)
        + alan_kodla(2, 0, zigzag_kodla(sicaklik))
        + alan_kodla(4, 2, ad.encode("utf-8"))
    )


def telemetri_coz(veri):
    i, alanlar = 0, {}
    while i < len(veri):
        anahtar, i = varint_coz(veri, i)
        no, tip = anahtar >> 3, anahtar & 0x7
        if tip == 0:
            deger, i = varint_coz(veri, i)
        elif tip == 2:
            uz, i = varint_coz(veri, i)
            deger = veri[i : i + uz]
            i += uz
        else:
            raise ValueError("tip %d desteklenmiyor" % tip)
        alanlar[no] = (tip, deger)
    return alanlar


if __name__ == "__main__":
    print("150 varint:", varint_kodla(150).hex(" "))
    print(
        "zigzag(-3) = %d, zigzag(3) = %d"
        % (zigzag_kodla(-3), zigzag_kodla(3))
    )
    m = telemetri_kodla(150, -3, "EV")
    print("mesaj (%d bayt): %s" % (len(m), m.hex(" ")))
    a = telemetri_coz(m)
    print("alan 1 id       =", a[1][1])
    print("alan 2 sicaklik =", zigzag_coz(a[2][1]))
    print("alan 4 ad       =", a[4][1].decode("utf-8"))
