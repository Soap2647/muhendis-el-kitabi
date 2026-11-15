# -*- coding: utf-8 -*-
# dpll.py - birim yayilimi ve geri izlemeli kucuk SAT cozucu.
import itertools
import random


def birim_yay(form, atama):
    """Birim maddeleri atar. Celiski varsa False doner."""
    while True:
        birim = None
        for c in form:
            kalan, sat = [], False
            for lit in c:
                v = abs(lit)
                if v in atama:
                    if atama[v] == (lit > 0):
                        sat = True
                        break
                else:
                    kalan.append(lit)
            if sat:
                continue
            if not kalan:
                return False          # madde yalanlandi: celiski
            if len(kalan) == 1 and birim is None:
                birim = kalan[0]
        if birim is None:
            return True
        atama[abs(birim)] = birim > 0


def dpll(form, atama=None):
    atama = dict(atama or {})
    if not birim_yay(form, atama):
        return None
    vars_ = sorted({abs(l) for c in form for l in c})
    bos = [v for v in vars_ if v not in atama]
    if not bos:
        return atama
    for deger in (True, False):
        sonuc = dpll(form, {**atama, bos[0]: deger})
        if sonuc is not None:
            return sonuc
    return None


def kaba(form, n):
    for bits in itertools.product([False, True], repeat=n):
        a = dict(zip(range(1, n + 1), bits))
        if all(any(a[abs(l)] == (l > 0) for l in c) for c in form):
            return True
    return False


if __name__ == "__main__":
    iz = [[1, 2], [-1, 3], [-2, -3], [-3, 1]]
    print("iz:", dpll(iz))
    rnd = random.Random(47)
    sat = uyusmaz = 0
    for _ in range(300):
        n = 8
        m = rnd.randint(10, 40)
        form = [[v if rnd.random() < 0.5 else -v
                 for v in rnd.sample(range(1, n + 1), 3)]
                for _ in range(m)]
        a = dpll(form)
        sat += a is not None
        uyusmaz += (a is not None) != kaba(form, n)
    print("sat:", sat, "/ 300  uyusmazlik:", uyusmaz)
