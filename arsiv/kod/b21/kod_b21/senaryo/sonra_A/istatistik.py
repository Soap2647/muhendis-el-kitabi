# -*- coding: utf-8 -*-
"""Tek is: olcumlerin ortalamasi."""


def ortalama(olcumler):
    if not olcumler:
        raise ValueError("olcum yok")
    return sum(o.deger for o in olcumler) / len(olcumler)
