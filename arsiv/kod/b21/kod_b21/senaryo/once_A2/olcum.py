# -*- coding: utf-8 -*-
"""ONCE: ADC okuma ve kalibrasyon. Donus: (tur, deger, birim)."""


def _adc_oku(kanal):
    """Donanim yerine sahte okuma (gercekte SPI/ADC surucusu)."""
    return 1000 + 100 * kanal


def olcumleri_oku(sensorler):
    """[(tur, kanal)] -> [(tur, deger, birim)]"""
    sonuc = []
    for tur, kanal in sensorler:
        ham = _adc_oku(kanal)
        if tur == "termistor":
            deger, birim = ham * 0.1 - 40.0, "C"
        elif tur == "gerilim":
            deger, birim = ham * 3.3 / 4095, "V"
        else:
            raise ValueError("bilinmeyen sensor: %s" % tur)
        sonuc.append((tur, deger, birim, 1.0))
    return sonuc
