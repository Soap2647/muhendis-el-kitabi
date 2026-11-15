# -*- coding: utf-8 -*-
"""Eklenti kaydi: yeni sensor sinifi kendini bu tabloya ekler."""
SENSORLER = {}


def kaydet(tur):
    def sar(sinif):
        SENSORLER[tur] = sinif
        return sinif
    return sar
