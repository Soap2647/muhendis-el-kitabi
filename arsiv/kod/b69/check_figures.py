# -*- coding: utf-8 -*-
"""Şekil denetimi: her bölümde şekil numaraları görünüş sırasıyla 1..n mi,
atıf yapılan her şekil var mı, şekil dosyası mevcut mu."""
import glob, os, re, sys
kok = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sorun = 0
for f in sorted(glob.glob(os.path.join(kok, "bolumler", "bolum_*.md"))):
    n = int(re.search(r"bolum_(\d+)", f).group(1))
    s = open(f, encoding="utf-8").read()
    nums = [int(x) for x in re.findall(r"^!\[Şekil %d\.(\d+)" % n, s, re.M)]
    if nums != list(range(1, len(nums) + 1)):
        print("bolum_%02d: şekil sırası %s" % (n, nums)); sorun += 1
    atif = {int(x) for x in re.findall(r"Şekil %d\.(\d+)" % n, s)}
    eksik = sorted(atif - set(nums))
    if eksik:
        print("bolum_%02d: atıf var, şekil yok: %s" % (n, eksik)); sorun += 1
    for yol in re.findall(r"^!\[Şekil[^\]]*\]\(([^)]+)\)", s, re.M):
        if not os.path.exists(os.path.join(kok, yol)):
            print("bolum_%02d: dosya yok: %s" % (n, yol)); sorun += 1
print("TEMİZ" if not sorun else "SORUN: %d" % sorun)
sys.exit(1 if sorun else 0)
