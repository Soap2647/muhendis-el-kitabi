# -*- coding: utf-8 -*-
"""Bolum 74 - Odul hackleme (reward hacking): kucuk bir koridor.

Koridor: konumlar 0..5, baslangic 0, hedef 5 (odul +10, biter).
Konum 2'de +1 odul var. Iki tasarim:
  yenilenir=True : +1 her girisinde (sinirsiz tekrar) -> ajan dongu
                   kurup hedefe hic gitmeyebilir
  yenilenir=False: +1 yalnizca ilk girişte (tuketilir)
Model bilindigi icin deger iterasyonu (dp74.py) ile optimum bulunur.
gamma = 0.99.
"""

import textwrap
import numpy as np
from dp74 import deger_iterasyonu

GAMMA = 0.99


class Koridor:
    def __init__(self, yenilenir):
        self.y = yenilenir
        self.L, self.hedef, self.bonus = 6, 5, 2
        self.nA = 2  # 0 sol, 1 sag
        self.S = 6 if yenilenir else 12  # konum (ve tuketim)
        self.P = {}
        for p in range(6):
            for c in ((0,) if yenilenir else (0, 1)):
                s = self.idx(p, c)
                for a in (0, 1):
                    if p == self.hedef:
                        self.P[(s, a)] = [(1.0, s, 0.0, True)]
                        continue
                    p2 = max(0, p - 1) if a == 0 else min(5, p + 1)
                    if p2 == self.hedef:
                        self.P[(s, a)] = [
                            (1.0, self.idx(p2, c), 10.0, True)
                        ]
                        continue
                    r, c2 = 0.0, c
                    if p2 == self.bonus and (yenilenir or c == 0):
                        r = 1.0
                        c2 = c if yenilenir else 1
                    self.P[(s, a)] = [
                        (1.0, self.idx(p2, c2), r, False)
                    ]

    def idx(self, p, c=0):
        return p if self.y else 2 * p + c


def iz(env, pi, s0_p, adim=12):
    """Acgozlu politikanin izini (konum, odul) olarak dondur."""
    p, c = s0_p, 0
    s = env.idx(p, c)
    kayit = []
    for _ in range(adim):
        a = int(pi[s])
        ((_, s2, r, bitti),) = env.P[(s, a)]
        kayit.append(("sol" if a == 0 else "sag", s2, r))
        if bitti:
            break
        s = s2
    return kayit


if __name__ == "__main__":
    for yenilenir in (True, False):
        env = Koridor(yenilenir)
        V, pi, kal = deger_iterasyonu(env, GAMMA)
        ad = (
            "yenilenir (hack)"
            if yenilenir
            else "tuketilir (duzeltilmis)"
        )
        print("%s: V(baslangic=0)=%.3f" % (ad, V[env.idx(0, 0)]))
        yol = iz(env, pi, 0)
        satir = " ".join("%s->%d(r=%g)" % y for y in yol)
        print("  acgozlu iz:")
        for parca in textwrap.wrap(satir, 68):
            print("    " + parca)
        toplam, gamma_k = 0.0, 1.0
        for k, (_, _, r) in enumerate(yol):
            toplam += gamma_k * r
            gamma_k *= GAMMA
        print("  ilk 12 adimin indirimli toplam odulu: %.3f" % toplam)
    # Hackle: sadece ilk gecisin ortalama odulu vs sinirsiz dongu
    # degeri
    print(
        "Sinirsiz dongu (konum 2<->3, her 2 adimda +1) degeri: %.3f"
        % (GAMMA**2 / (1 - GAMMA**2))
    )
    print("Hedefe gitme degeri (2 -> 5, +10): %.3f" % (GAMMA**2 * 10))
