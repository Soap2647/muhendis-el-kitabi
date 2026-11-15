# -*- coding: utf-8 -*-
# karnaugh.py - f(a,b,c) = Σm(0,1,2,5,6,7) icin SOP dogrulamasi.
import itertools

ON = {0, 1, 2, 5, 6, 7}


def f_sop(a, b, c):
    """Karnaugh gruplari: a'b' + ac + bc'."""
    return (not a and not b) or (a and c) or (b and not c)


if __name__ == "__main__":
    print("a b c  f  SOP")
    hata = 0
    for a, b, c in itertools.product([0, 1], repeat=3):
        m = 4 * a + 2 * b + c
        f = int(m in ON)
        s = int(bool(f_sop(a, b, c)))
        print(a, b, c, " ", f, " ", s)
        hata += f != s
    print("hata:", hata)
