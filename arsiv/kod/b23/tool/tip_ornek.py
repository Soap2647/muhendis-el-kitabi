from typing import Optional


def kullanici_bul(kimlik: int) -> Optional[str]:
    isimler = {1: "Ayse", 2: "Mert"}
    return isimler.get(kimlik)


def selam(kimlik: int) -> str:
    isim = kullanici_bul(kimlik)
    return "Merhaba " + isim.upper()


def selam_guvenli(kimlik: int) -> str:
    isim = kullanici_bul(kimlik)
    if isim is None:
        return "Merhaba misafir"
    return "Merhaba " + isim.upper()
