# hesap_grafi.py: f(a, b) = (a + b) * tanh(a * b) hesap grafiği.
# İleri geçiş değerleri, geri geçiş gradyanları ve sayısal denetim.
import csv
import math

from deger import Deger
from ortak import merkezi_fark


def f_float(v):
    a, b = v
    return (a + b) * math.tanh(a * b)


def ileri_geri(a0, b0):
    a = Deger(a0)            # girdi düğümleri
    b = Deger(b0)
    c = a * b                # c = a b
    t = c.tanh()             # t = tanh(c)
    s = a + b                # s = a + b
    f = s * t                # f = s t
    f.geri()
    return [("a", "girdi", a), ("b", "girdi", b), ("c", "a*b", c),
            ("t", "tanh", t), ("s", "a+b", s), ("f", "s*t", f)]


if __name__ == "__main__":
    a0, b0 = 1.0, 0.5
    dugumler = ileri_geri(a0, b0)
    print("%-4s %-6s %10s %10s" % ("ad", "islem", "veri", "grad"))
    for ad, islem, v in dugumler:
        print("%-4s %-6s %10.6f %10.6f" % (ad, islem, v.veri, v.grad))
    sayisal = merkezi_fark(f_float, [a0, b0])
    print("sayisal: df/da = %.6f, df/db = %.6f" % tuple(sayisal))
    with open("olcum_graf.csv", "w", encoding="utf-8") as fh:
        yaz = csv.writer(fh)
        yaz.writerow(["ad", "islem", "veri", "grad"])
        for ad, islem, v in dugumler:
            yaz.writerow([ad, islem, "%.6f" % v.veri,
                          "%.6f" % v.grad])
