# -*- coding: utf-8 -*-
from typing import Protocol


class ToplamaStratejisi(Protocol):
    def topla(self, sayilar: list[float]) -> float: ...


class NormalToplama:
    def topla(self, sayilar: list[float]) -> float:
        return sum(sayilar)


class ToplayiciFabrika:
    def olustur(self) -> ToplamaStratejisi:
        return NormalToplama()


if __name__ == "__main__":
    print(ToplayiciFabrika().olustur().topla([1.5, 2.5]))
    print(sum([1.5, 2.5]))
