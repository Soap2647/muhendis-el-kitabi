# -*- coding: utf-8 -*-
"""Proje ici import grafi ve Ca / Ce / I olcumu (ast ile).

Kullanim: python baglilik.py <klasor> [--kenar]
"""
import ast
import os
import sys


def modulleri_bul(kok):
    return sorted(f[:-3] for f in os.listdir(kok)
                  if f.endswith(".py") and not f.startswith("test_"))


def import_kenarlari(kok):
    mods = set(modulleri_bul(kok))
    kenarlar = set()
    for m in mods:
        yol = os.path.join(kok, m + ".py")
        with open(yol, encoding="utf-8") as f:
            agac = ast.parse(f.read(), filename=yol)
        for dugum in ast.walk(agac):
            if isinstance(dugum, ast.Import):
                adlar = [a.name for a in dugum.names]
            elif isinstance(dugum, ast.ImportFrom) and dugum.module:
                adlar = [dugum.module]
            else:
                continue
            for ad in adlar:
                hedef = ad.split(".")[0]
                if hedef in mods and hedef != m:
                    kenarlar.add((m, hedef))
    return sorted(kenarlar), sorted(mods)


def metrikler(kok):
    kenarlar, mods = import_kenarlari(kok)
    # afferent (Ca): bu module bagli olan modul sayisi
    ca = dict.fromkeys(mods, 0)
    # efferent (Ce): bu modulun bagli oldugu modul sayisi
    ce = dict.fromkeys(mods, 0)
    for a, b in kenarlar:
        ce[a] += 1
        ca[b] += 1
    satirlar = []
    for m in mods:
        toplam = ca[m] + ce[m]
        i = ce[m] / toplam if toplam else 0.0    # kararsizlik
        satirlar.append((m, ca[m], ce[m], i))
    return kenarlar, satirlar


if __name__ == "__main__":
    kenarlar, satirlar = metrikler(sys.argv[1])
    if "--kenar" in sys.argv:
        for a, b in kenarlar:
            print("%s,%s" % (a, b))
    else:
        print("modul       Ca  Ce     I")
        for m, ca, ce, i in satirlar:
            print("%-9s %3d %3d  %5.2f" % (m, ca, ce, i))
