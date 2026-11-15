# -*- coding: utf-8 -*-
"""ISP: sisik arayuz ve kucuk arayuzler (typing.Protocol)."""
from typing import Protocol


class Cihaz(Protocol):          # sisik: her sey tek arayuzde
    def oku(self) -> float: ...
    def kalibre(self, k: float) -> None: ...
    def firmware_guncelle(self, dosya: bytes) -> None: ...


class Okunabilir(Protocol):     # kucuk: yalnizca okuma
    def oku(self) -> float: ...


class Kalibre(Protocol):        # kucuk: yalnizca kalibrasyon
    def kalibre(self, k: float) -> None: ...


class SaltOkunurTermistor:
    def oku(self) -> float:
        return 25.0

    def kalibre(self, k: float) -> None:
        raise NotImplementedError("kalibrasyon desteklenmiyor")

    def firmware_guncelle(self, dosya: bytes) -> None:
        raise NotImplementedError("firmware desteklenmiyor")


def olc_ve_kaydet(kaynak: Okunabilir) -> float:
    return kaynak.oku()        # yalnizca oku() kullanilir


if __name__ == "__main__":
    t = SaltOkunurTermistor()
    print(olc_ve_kaydet(t))
    try:
        t.firmware_guncelle(b"\x00")   # sisik arayuz yuzunden cagrilabilir
    except NotImplementedError as e:
        print("hata:", e)
