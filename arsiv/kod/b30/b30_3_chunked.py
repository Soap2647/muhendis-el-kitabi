# -*- coding: utf-8 -*-
"""b30_3_chunked.py: Chunked (parcali) HTTP govdesini cozer."""


def chunked_coz(ham):
    """ham: chunked govde baytlari. Donus: (govde, artan_bayt)."""
    i, parcalar = 0, []
    while True:
        son = ham.find(b"\r\n", i)
        if son < 0:
            raise ValueError("boyut satiri eksik")
        boyut = int(ham[i:son].split(b";", 1)[0].strip(), 16)
        i = son + 2
        if boyut == 0:                # son parca; sonra bos satir
            while True:
                son = ham.find(b"\r\n", i)
                if son < 0:
                    raise ValueError("son satir eksik")
                bos = (son == i)
                i = son + 2
                if bos:
                    return b"".join(parcalar), ham[i:]
        if len(ham) < i + boyut + 2:
            raise ValueError("parca eksik")
        parcalar.append(ham[i:i + boyut])
        if ham[i + boyut:i + boyut + 2] != b"\r\n":
            raise ValueError("parca sonunda CRLF bekleniyordu")
        i += boyut + 2


def yanit_ayir(ham):
    """Ham yaniti (durum, basliklar, govde) olarak ayirir."""
    bas, sep, govde = ham.partition(b"\r\n\r\n")
    if not sep:
        raise ValueError("baslik sonu bulunamadi")
    satirlar = bas.decode("latin-1").split("\r\n")
    basliklar = {}
    for s in satirlar[1:]:
        ad, _, deger = s.partition(":")
        basliklar[ad.strip().lower()] = deger.strip()
    return satirlar[0], basliklar, govde


if __name__ == "__main__":
    ornek = (b"4\r\nWiki\r\n5;ad=deger\r\npedia\r\n"
             b"E\r\n in\r\n\r\nchunks.\r\n0\r\n\r\n")
    govde, kalan = chunked_coz(ornek)
    print(repr(govde), "kalan:", kalan)
    try:
        chunked_coz(b"5\r\nabc\r\n0\r\n\r\n")
    except ValueError as e:
        print("hata:", e)
