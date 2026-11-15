# -*- coding: utf-8 -*-
"""Bolum 39 taslagindaki {{KOD:..}} ve {{TERM:..}} yer tutucularini
gercek dosya iceriklerinden doldurur ve bolumler/bolum_39.md yazar."""
import os, re, sys
B = os.path.dirname(os.path.abspath(__file__))
HEDEF = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_39.md"
s = open(os.path.join(B, "bolum39_birlesik.md"), encoding="utf-8").read()

def oku(p):
    return open(os.path.join(B, p), encoding="utf-8").read().rstrip("\n")

# 1) term blogu: ```term\n{{TERM:ad}}\n```
def term(m):
    return "```term\n" + oku(os.path.join("cikti", m.group(1) + ".txt")) + "\n```"
s = re.sub(r"```term\n\{\{TERM:([^}]+)\}\}\n```", term, s)
s = re.sub(r"^\{\{TERM:([^}]+)\}\}$", term, s, flags=re.M)

# 2) bagimsiz {{KOD:yol}} satirlari -> dil etiketli kod blogu
def dil(yol):
    u = yol.lower()
    if u.endswith(".py"): return "python"
    if u.endswith(".c") or u.endswith(".h"): return "c"
    return "text"
def kod(m):
    yol = m.group(1)
    return "```" + dil(yol) + "\n" + oku(yol) + "\n```"
s = re.sub(r"^\{\{KOD:([^}]+)\}\}$", kod, s, flags=re.M)

assert "{{" not in s, "doldurulmamis yer tutucu var"
open(HEDEF, "w", encoding="utf-8", newline="\n").write(s)
print("yazildi:", HEDEF, len(s))
