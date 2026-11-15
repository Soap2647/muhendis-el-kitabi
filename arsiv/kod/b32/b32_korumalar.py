#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""b32_korumalar.py: ELF ikilisindeki koruma bayraklarini denetler.

Yalnizca readelf ciktisini okur; ikiliyi calistirmaz.
Kullanim: python3 b32_korumalar.py IKILI [IKILI ...]
"""

import re
import subprocess
import sys


def readelf(bayrak, yol):
    cikti = subprocess.run(["readelf", bayrak, yol],
                           capture_output=True, text=True)
    return cikti.stdout


def denetle(yol):
    prog = readelf("-lW", yol)
    baslik = readelf("-hW", yol)
    dinamik = readelf("-dW", yol)
    semb = readelf("-sW", yol)
    sonuc = {}
    # GNU_STACK satirinin bayrak alani sondan ikinci sutundadir
    for satir in prog.splitlines():
        if "GNU_STACK" in satir:
            bayrak = satir.split()[-2]
            sonuc["NX (yigin calistirilamaz)"] = "E" not in bayrak
            sonuc["yigin bayragi"] = bayrak
    sonuc["PIE (DYN tipi)"] = "Type:" in baslik and "DYN" in baslik
    sonuc["RELRO (bolum)"] = "GNU_RELRO" in prog
    sonuc["BIND_NOW (tam RELRO)"] = bool(
        re.search(r"\bBIND_NOW\b|Flags: .*\bNOW\b", dinamik))
    sonuc["yigin kanarisi"] = "__stack_chk_fail" in semb
    sonuc["FORTIFY (__*_chk)"] = bool(
        re.search(r"\b__\w+_chk\b", semb))
    return sonuc


def main(args):
    if not args:
        print("kullanim: python3 b32_korumalar.py IKILI ...")
        return 2
    for yol in args:
        print("== %s" % yol)
        for ad, deger in denetle(yol).items():
            if isinstance(deger, bool):
                deger = "VAR" if deger else "YOK"
            print("  %-26s %s" % (ad, deger))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
