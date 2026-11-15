# -*- coding: utf-8 -*-
"""Karşılaştırma için İngilizce düz metin.
Kaynaklar (yerel kurulum): Python 3.12 pydoc_data/topics.py (dil
belgesi;
yalnızca girintisiz düz cümleler alınır) ve site-packages altındaki
README/RST belgeleri (kod blokları atılır). Çıktı: korpus_en.txt"""

import glob, os, re

PY = "C:/Users/merty/AppData/Local/Programs/Python/Python312/Lib"
KOK = PY + "/site-packages"
parcalar = []
import sys

sys.path.insert(0, PY)
import pydoc_data.topics as tp

for metin in tp.topics.values():
    satirlar = [
        s
        for s in metin.splitlines()
        if s and not s.startswith(" ") and not s.startswith("\t")
    ]
    parcalar.append(" ".join(satirlar))
for yol in sorted(
    glob.glob(KOK + "/**/*.md", recursive=True)
    + glob.glob(KOK + "/**/*.rst", recursive=True)
):
    try:
        s = open(yol, encoding="utf-8").read()
    except Exception:
        continue
    s = re.sub(r"```.*?```", " ", s, flags=re.S)
    s = re.sub(r"`[^`]*`", " ", s)
    s = re.sub(r"https?://\S+", " ", s)
    harf = sum(c.isascii() and c.isalpha() for c in s)
    if len(s) >= 500 and harf / max(1, len(s)) >= 0.7:
        parcalar.append(re.sub(r"[ \t]+", " ", s))
metin = re.sub(r"[ \t]+", " ", "\n".join(parcalar))
metin = re.sub(r"\n\s*\n+", "\n", metin)[:1000000]
open(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "korpus_en.txt"
    ),
    "w",
    encoding="utf-8",
).write(metin)
print("karakter", len(metin))
