# -*- coding: utf-8 -*-
"""Ana dongu ile kesme isleyicisi arasinda paylasilan sayac yarisi.

Her iki taraf  g = g + 1  ifadesini uc mikro-islemle yapar:
  LOAD (g'yi yazmaca al), ADD (+1), STORE (geri yaz).
Iki dizinin 20 olasi sirasi tek tek sinanir. Bu, donanim olcumu
degil, mikro-islem duzeyinde ayrik bir modeldir.
"""
from itertools import combinations


def calistir(sira, g0=0):
    """sira: 'M' (ana kod) ve 'I' (kesme) harflerinden bir dizi.
    Her harf, o tarafin bir sonraki mikro-islemini calistirir."""
    g = g0
    yazmac = {"M": 0, "I": 0}
    adim = {"M": 0, "I": 0}
    for taraf in sira:
        k = adim[taraf]
        if k == 0:
            yazmac[taraf] = g                  # LOAD
        elif k == 1:
            yazmac[taraf] += 1                 # ADD
        else:
            g = yazmac[taraf]                  # STORE
        adim[taraf] += 1
    return g


def tum_siralar():
    """6 konumdan 3'u 'M' olacak sekilde C(6,3) = 20 sira."""
    for konum in combinations(range(6), 3):
        sira = ["I"] * 6
        for k in konum:
            sira[k] = "M"
        yield "".join(sira)


if __name__ == "__main__":
    print("== Kilitsiz: kesme her yerde girebilir ==")
    sonuc = {}
    for sira in tum_siralar():
        sonuc.setdefault(calistir(sira), []).append(sira)
    for v in sorted(sonuc):
        print("son deger = %d : %d sira" % (v, len(sonuc[v])))
    print("kaybolan siralar:")
    for s in sonuc.get(1, []):
        print("  ", s)
    print("== PRIMASK: ana kodun 3 adimi bolunmez ==")
    for sira in ("MMMIII", "IIIMMM"):
        print(sira, "->", calistir(sira))
