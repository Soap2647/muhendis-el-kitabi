# -*- coding: utf-8 -*-
"""Degisikligin etkisini sayar: dosya, satir, kirilan test.

Kullanim:  python olc_etki.py <taban_klasor> <senaryo_klasoru>...
Degisen satir: difflib birlesik farkindaki +/- satirlarinin sayisi.
Kirilan test: senaryo klasorundeki test_telemetri calistirildiginda
basarisiz (failure + error) olan test sayisi.
"""
import difflib
import os
import re
import subprocess
import sys


def dosyalar(kok):
    sozluk = {}
    for f in os.listdir(kok):
        if f.endswith(".py"):
            with open(os.path.join(kok, f), encoding="utf-8") as h:
                sozluk[f] = h.read().splitlines()
    return sozluk


def degisim(taban, yeni):
    a, b = dosyalar(taban), dosyalar(yeni)
    dosya, satir = 0, 0
    for f in sorted(set(a) | set(b)):
        x, y = a.get(f, []), b.get(f, [])
        if x == y:
            continue
        dosya += 1
        for l in difflib.unified_diff(x, y, lineterm="", n=0):
            if l[:3] not in ("+++", "---") and l[:1] in ("+", "-"):
                satir += 1
    return dosya, satir


def testler(kok):
    p = subprocess.run(
        [sys.executable, "-m", "unittest", "test_telemetri"],
        cwd=kok, capture_output=True, text=True, encoding="utf-8")
    kosan = int(re.search(r"Ran (\d+) test", p.stderr).group(1))
    f = re.search(r"failures=(\d+)", p.stderr)
    e = re.search(r"errors=(\d+)", p.stderr)
    f_say = int(f.group(1)) if f else 0
    e_say = int(e.group(1)) if e else 0
    return kosan, f_say + e_say


if __name__ == "__main__":
    taban = sys.argv[1]
    print(",".join(["senaryo", "degisen_dosya", "degisen_satir",
                     "kosan_test", "kirilan_test"]))
    for yeni in sys.argv[2:]:
        d, s = degisim(taban, yeni)
        kosan, kirilan = testler(yeni)
        print("%s,%d,%d,%d,%d" % (os.path.basename(yeni), d, s,
                                  kosan, kirilan))
