# -*- coding: utf-8 -*-
"""md/p01..p04 sablonlarini birlestirir; kod ve cikti yer tutucularini
gercek betik ve cikti dosyalariyla degistirir."""
import glob
import os
import re

TEMP = "C:/Users/merty/AppData/Local/Temp/b71"
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_71.md"

parcalar = [open(p, encoding="utf-8").read().rstrip("\n")
            for p in sorted(glob.glob(TEMP + "/md/p0*.md"))]
s = "\n\n".join(parcalar) + "\n"


def kod_yer(m):
    dosya, a, b = m.group(1), int(m.group(2)), m.group(3)
    satirlar = open(os.path.join(TEMP, dosya),
                    encoding="utf-8").read().rstrip("\n").split("\n")
    if b == "end":
        b = len(satirlar)
    satirlar = satirlar[a - 1:int(b)]
    while satirlar and not satirlar[-1].strip():
        satirlar.pop()
    while satirlar and not satirlar[0].strip():
        satirlar.pop(0)
    return "```python\n" + "\n".join(satirlar) + "\n```"


def cikti_yer(m):
    ad, parca = m.group(1), m.group(2)
    metin = open(os.path.join(TEMP, "cikti", ad + ".txt"),
                 encoding="utf-8").read()
    metin = metin.replace(TEMP + "/", "")
    satirlar = [x.rstrip() for x in metin.split("\n")
                if not x.startswith("[exited") and not x.startswith("HATA")]
    while satirlar and not satirlar[-1].strip():
        satirlar.pop()
    a = 1
    if parca:
        a_s, b_s = parca.split("|")
        a = int(a_s)
        b = len(satirlar) if b_s == "end" else int(b_s)
        satirlar = satirlar[a - 1:b]
    cikis = []
    if a == 1:
        cikis.append("$ python %s.py" % ad)
    cikis += satirlar
    return "```term\n" + "\n".join(cikis) + "\n```"


s = re.sub(r"\{\{KOD:([^|}]+)\|(\d+)\|(\d+|end)\}\}", kod_yer, s)
s = re.sub(r"\{\{CIKTI:([^|}]+)(?:\|([^}]+))?\}\}", cikti_yer, s)
open(HEDEF, "w", encoding="utf-8").write(s)
print("yazildi:", HEDEF, len(s.split("\n")), "satir")
kalan = re.findall(r"\{\{[^}]*\}\}", s)
print("kalan yer tutucu:", kalan)
