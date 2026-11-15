# -*- coding: utf-8 -*-
"""Çözümlü Örnek 3 için: küçük LSM'de durum izi."""
import os
import shutil
from lsm import LSM

dizin = "iz_dizin"
shutil.rmtree(dizin, ignore_errors=True)
db = LSM(dizin, esik=2, m=256, k=3)


def durum(ad):
    tablolar = [os.path.basename(t.yol) for t in db.tablolar]
    print("%-14s bellek=%s tablolar=%s"
          % (ad, db.memtable, tablolar))


db.put("a", "1")
durum("put a=1")
db.put("b", "2")
durum("put b=2")
db.put("a", "3")
durum("put a=3")
db.sil("b")
durum("sil b")
print("get b ->", db.get("b"), "| get a ->", db.get("a"))
db.birlestir()
durum("birlestir")
print("get a ->", db.get("a"), "| get b ->", db.get("b"))
with open(os.path.join(dizin, "000002.sst"), encoding="utf-8") as f:
    print("000002.sst:", f.read().strip())
shutil.rmtree(dizin, ignore_errors=True)
