# -*- coding: utf-8 -*-
"""Ağaç yorumcusu ile bayt kodu VM'in hız ölçümü (deterministik)."""
import csv
import sys
import time
from mini import vm_ile_calistir, agacla_calistir, on_isle
from derle import Derleyici
from vm2 import VMHizli
from mini_ayr import Ayristirici
from mini_on import tokenize

KAYNAK = """
let i = 0;
let s = 0;
while (i < {n}) {{
    s = s + i * 3 % 7 - (i / 5);
    i = i + 1;
}}
print s;
"""

def en_iyi(f, tekrar=3):
    en = None
    for _ in range(tekrar):
        t0 = time.perf_counter()
        sonuc = f()
        dt = time.perf_counter() - t0
        en = dt if en is None or dt < en else en
    return en, sonuc

def ana(cikti):
    satirlar = [("n", "agac_s", "vm_s", "vm_hizli_s", "sonuç")]
    for n in (10000, 30000, 100000, 300000):
        k = KAYNAK.format(n=n)
        prog, ml = on_isle(k)
        kod = Derleyici().derle(prog, ml)
        ta, sa = en_iyi(lambda: agacla_calistir(k))
        tv, sv = en_iyi(lambda: vm_ile_calistir(k).ciktilar)
        th, sh = en_iyi(lambda: VMHizli(kod).calistir())
        assert sa == sv == sh, (n, sa, sv, sh)
        satirlar.append((n, f"{ta:.4f}", f"{tv:.4f}", f"{th:.4f}",
                         sv[0]))
        print(n, f"agac={ta:.4f}s vm={tv:.4f}s vmhizli={th:.4f}s",
              "sonuç", sv[0])
    with open(cikti, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(satirlar)

def derinlik_siniri():
    """İç içe parantezde ayrıştırıcı hangi derinlikte patlar?"""
    lo, hi = 1, 2000
    while lo < hi:
        orta = (lo + hi + 1) // 2
        kaynak = "(" * orta + "1" + ")" * orta
        try:
            Ayristirici(tokenize(kaynak)).ifade()
            lo = orta
        except RecursionError:
            hi = orta - 1
    return lo

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "derinlik":
        print("maks parantez derinligi:", derinlik_siniri())
    else:
        ana(sys.argv[1] if len(sys.argv) > 1 else "b37_zaman.csv")
