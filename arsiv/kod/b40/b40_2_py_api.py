# -*- coding: utf-8 -*-
"""b40_2_py_api.py: Hata modeli ve anahtar kelime argumanlari."""


class SensorHatasi(Exception):
    """Bu kutuphanenin tum hatalarinin koku."""


class ArgumanHatasi(SensorHatasi):
    """Cagiran yanlis deger verdi; ayni cagri yeniden denenmez."""


class AralikHatasi(SensorHatasi):
    """Deger kabul edilebilir aralikta degil."""


def kaydet(ad, deger, *, birim="C", tavan=100.0):
    """Degeri kaydeder. birim ve tavan yalnizca anahtar kelimedir."""
    if not ad:
        raise ArgumanHatasi("ad bos olamaz")
    if birim not in ("C", "F"):
        raise ArgumanHatasi("birim C ya da F olmali: %r" % birim)
    if not -tavan <= deger <= tavan:
        raise AralikHatasi(
            "%s: %.1f, aralik [-%g, %g]" % (ad, deger, tavan, tavan)
        )
    return {"ad": ad, "deger": deger, "birim": birim}


if __name__ == "__main__":
    print(kaydet("EV-batarya", 23.5))
    print(kaydet("EV-batarya", 23.5, birim="F"))
    cagrilar = [
        lambda: kaydet("", 1.0),
        lambda: kaydet("x", 500.0),
        lambda: kaydet("x", 1.0, "C"),
    ]
    for cagri in cagrilar:
        try:
            cagri()
        except SensorHatasi as e:  # alt siniflarin hepsini yakalar
            print(type(e).__name__, "-", e)
        except TypeError as e:
            print("TypeError -", e)
