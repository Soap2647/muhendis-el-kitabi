# -*- coding: utf-8 -*-
"""Bilerek hatalı LSM: birleştirmede en ESKİ değeri tutar."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lsm, lsm_test

def birlestir_hatali(self):
    self.flush()
    if len(self.tablolar) <= 1:
        return
    birlesik = {}
    for t in reversed(self.tablolar):  # HATA: eskiden değil yeniden
        for k, v in t.tum_kayitlar(self.say):
            birlesik[k] = v
    kayitlar = [(k, v) for k, v in sorted(birlesik.items()) if v is not None]
    for t in self.tablolar:
        os.remove(t.yol)
    self.tablolar = [self._yeni_tablo(kayitlar)] if kayitlar else []

lsm.LSM.birlestir = birlestir_hatali
toplam = 0
for seed in range(1, 6):
    h, k, t = lsm_test.model_karsilastir(seed)
    toplam += h
print("Hatalı sürümde toplam hata:", toplam)
