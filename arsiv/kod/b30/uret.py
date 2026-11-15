# -*- coding: utf-8 -*-
"""Bolum 30 kaynagini sablondan uretir.

@@KOD dosya bas son dil@@        -> dosyanin bas..son satirlari kod blogu
@@KAYNAK bas son@@              -> CPython client.py kesiti (python)
@@CIKTI dosya "komut"@@         -> terminal blogu; komut bossa $ satiri yok
"""
import os
import re

B = "C:/Users/merty/AppData/Local/Temp/b30"
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_30.md"
KAYNAK_PY = os.path.join(B, "kaynak_cpython", "cpython312_client.py")

s = open(os.path.join(B, "bolum30.tpl"), encoding="utf-8").read()


def dosya_satirlari(yol):
    with open(yol, encoding="utf-8") as f:
        return f.read().rstrip("\n").split("\n")


def kod_blok(satirlar, dil):
    return "```%s\n%s\n```" % (dil, "\n".join(satirlar))


def kod_repl(m):
    dosya, bas, son, dil = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
    satirlar = dosya_satirlari(os.path.join(B, dosya))
    return kod_blok(satirlar[bas - 1:son], dil)


def kaynak_repl(m):
    bas, son = int(m.group(1)), int(m.group(2))
    satirlar = dosya_satirlari(KAYNAK_PY)
    return kod_blok(satirlar[bas - 1:son], "python")


def cikti_repl(m):
    dosya, komut = m.group(1), m.group(2)
    satirlar = dosya_satirlari(os.path.join(B, dosya))
    satirlar = [l for l in satirlar if not l.startswith("dinleniyor")]
    govde = "\n".join(satirlar)
    if komut:
        govde = "$ " + komut + "\n" + govde
    return "```term\n%s\n```" % govde


s = re.sub(r"^@@KOD (\S+) (\d+) (\d+) (\w+)@@$", kod_repl, s, flags=re.M)
s = re.sub(r"^@@KAYNAK (\d+) (\d+)@@$", kaynak_repl, s, flags=re.M)
s = re.sub(r'^@@CIKTI (\S+) "([^"]*)"@@$', cikti_repl, s, flags=re.M)

kalan = re.findall(r"^@@.*$", s, flags=re.M)
if kalan:
    print("ISLENMEMIS:", kalan)

os.makedirs(os.path.dirname(HEDEF), exist_ok=True)
with open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
    f.write(s if s.endswith("\n") else s + "\n")
print("yazildi:", HEDEF, len(s), "karakter")
