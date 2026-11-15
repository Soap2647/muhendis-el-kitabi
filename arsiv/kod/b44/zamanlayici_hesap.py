# -*- coding: utf-8 -*-
"""Zamanlayici icin PSC/ARR bulucu ve PWM hesabi.

f_guncelleme = f_tim / ((PSC + 1) * (ARR + 1))
gorev (%)    = CCR / (ARR + 1)        (kenar hizali PWM)
f_tim: sayacin giris saati (kartina gore kontrol et). 16 bit:
PSC ve ARR en fazla 65535.
"""
import math

F_TIM = 84_000_000
MAKS = 65535


def adaylar(hedef_hz, f_tim=F_TIM, n=4):
    """Her PSC icin en yakin ARR; hataya gore ilk n aday."""
    liste = []
    for psc in range(MAKS + 1):
        arr1 = round(f_tim / (hedef_hz * (psc + 1)))
        if 1 <= arr1 <= MAKS + 1:
            arr = arr1 - 1
            gercek = f_tim / ((psc + 1) * (arr + 1))
            hata = abs(gercek - hedef_hz) / hedef_hz * 100.0
            liste.append((psc, arr, hata, gercek))
    liste.sort(key=lambda x: (round(x[2], 9), x[0]))
    return liste[:n]


def en_iyi(hedef_hz, f_tim=F_TIM):
    """En dusuk hata; esitlikte en kucuk PSC."""
    return adaylar(hedef_hz, f_tim, n=1)[0]


def ccr_hesap(gorev, arr):
    ccr = round(gorev * (arr + 1))
    return ccr, ccr / (arr + 1)


if __name__ == "__main__":
    print("f_tim = %.0f MHz" % (F_TIM / 1e6))
    print()
    print("== PWM 1 kHz, gorev %37.5 ==")
    psc, arr, hata, gercek = en_iyi(1000)
    print("secilen PSC=%d ARR=%d f=%.3f Hz hata=%.6f %%"
          % (psc, arr, gercek, hata))
    ccr, g = ccr_hesap(0.375, arr)
    print("CCR=%d  gercek gorev=%.4f %%" % (ccr, g * 100))
    print()
    print("== Aday tablosu: 333 Hz (tam bolunmez) ==")
    for psc, arr, h, f in adaylar(333, n=5):
        print("PSC=%5d ARR=%6d f=%.6f Hz hata=%.6f %%"
              % (psc, arr, f, h))
    print()
    print("== Servo: 50 Hz, darbe 1 ms ile 2 ms arasi ==")
    psc, arr, hata, gercek = en_iyi(50)
    print("PSC=%d ARR=%d f=%.4f Hz hata=%.6f %%"
          % (psc, arr, gercek, hata))
    sayim_us = (psc + 1) / F_TIM * 1e6
    print("bir sayim = %.4f us" % sayim_us)
    print("1 ms = %d sayim, 2 ms = %d sayim"
          % (round(1000 / sayim_us), round(2000 / sayim_us)))
    print()
    print("== Frekans - cozunurluk takasi ==")
    for f in (50, 1000, 5000, 20000, 50000):
        psc, arr, hata, gercek = en_iyi(f)
        print("f=%6d Hz PSC=%5d ARR=%6d adim=%6d ~%.1f bit"
              % (f, psc, arr, arr + 1, math.log2(arr + 1)))
