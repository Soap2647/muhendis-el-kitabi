# -*- coding: utf-8 -*-
"""Pratt izi: ifade(guc) çağrılarini girintili yazdirir."""
from mini_on import tokenize
from mini_ayr import Ayristirici, GUC

class Izli(Ayristirici):
    derin = 0
    def ifade(self, guc=0):
        pad = "  " * Izli.derin
        print(f"{pad}ifade(guc={guc}) başlar, "
              f"şimdiki='{self.bak().lexem}'")
        Izli.derin += 1
        sonuc = super().ifade(guc)
        Izli.derin -= 1
        print(f"{pad}-> döndü: {sonuc_yaz(sonuc)}")
        return sonuc

def sonuc_yaz(d):
    from mini_on import Sayi, Degisken, Ikili, Tekli
    if isinstance(d, Sayi): return str(d.deger)
    if isinstance(d, Degisken): return d.ad
    if isinstance(d, Tekli): return f"({d.op}{sonuc_yaz(d.ey)})"
    return f"({sonuc_yaz(d.sol)} {d.op} {sonuc_yaz(d.sag)})"

if __name__ == "__main__":
    Izli(tokenize("2 + 3 * (4 - 1)")).ifade()
