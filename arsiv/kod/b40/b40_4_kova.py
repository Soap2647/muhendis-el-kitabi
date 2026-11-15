# -*- coding: utf-8 -*-
"""b40_4_kova.py: Token bucket (jeton kovasi) hiz sinirlayicisi."""

import csv
import sys


class KovaSinirlayici:
    def __init__(self, kapasite, hiz):
        if kapasite <= 0 or hiz <= 0:
            raise ValueError("kapasite ve hiz pozitif olmali")
        self.kapasite = float(kapasite)  # biriken en fazla jeton
        self.hiz = float(hiz)  # saniyede eklenen jeton
        self.jeton = float(kapasite)  # baslangicta kova dolu
        self.son = None  # son guncelleme zamani

    def _yenile(self, simdi):
        if self.son is None:
            self.son = simdi
        gecen = simdi - self.son
        self.jeton = min(self.kapasite, self.jeton + gecen * self.hiz)
        self.son = simdi

    def izin_ver(self, simdi, maliyet=1.0):
        """(izin, bekleme_s). izin True ise jeton dusulur."""
        self._yenile(simdi)
        if self.jeton >= maliyet:
            self.jeton -= maliyet
            return True, 0.0
        return False, (maliyet - self.jeton) / self.hiz


OLAYLAR = [0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.2, 3.0, 3.0, 3.0, 3.0]

if __name__ == "__main__":
    kova = KovaSinirlayici(kapasite=3, hiz=1.0)
    print("%6s %6s %7s %9s" % ("zaman", "izin", "jeton", "bekleme"))
    satirlar = []
    for t in OLAYLAR:
        izin, bekle = kova.izin_ver(t)
        print("%6.2f %6s %7.2f %9.2f" % (t, izin, kova.jeton, bekle))
        satirlar.append(
            (t, int(izin), round(kova.jeton, 4), round(bekle, 4))
        )
    if len(sys.argv) > 1:  # CSV'yi istenen yola yaz
        with open(
            sys.argv[1], "w", newline="", encoding="utf-8"
        ) as f:
            w = csv.writer(f)
            w.writerow(["zaman_s", "izin", "jeton", "bekleme_s"])
            w.writerows(satirlar)
