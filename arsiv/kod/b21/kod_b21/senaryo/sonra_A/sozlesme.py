# -*- coding: utf-8 -*-
"""Ortak sozlesme: olcum veri yapisi ve ADC arayuzu."""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Olcum:
    tur: str
    deger: float
    birim: str
    esik: float | None = None
    guven: float = 1.0


class AdcKaynagi(Protocol):
    """Tek metot: kanal -> ham ADC degeri (ISP: kucuk arayuz)."""

    def oku(self, kanal: int) -> int: ...
