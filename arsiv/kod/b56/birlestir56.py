# -*- coding: utf-8 -*-
"""Bolum 56 taslagini bolumler/bolum_56.md'ye cevirir.

Yer tutucular (satir tamamen bu olmali):
  @@SEKIL|dosya|baslik@@        -> gorsel (dosya gorseller/ altinda)
  @@KODTAM|dosya@@              -> dosyanin tamami (en fazla 40 satir)
  @@KOD|dosya|bas|son@@         -> dosyanin satir araligi
  @@CIKTI|dosya@@               -> programi calistirir, terminal blogu
"""
import os
import re
import subprocess
import sys

TEMP = "C:/Users/merty/AppData/Local/Temp/b56"
KOK = "D:/Mevcut Projeler/Kitap"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
hatalar = []


def kod_blok(satirlar, ad):
    if len(satirlar) > 40:
        hatalar.append("%s: %d satir (>40)" % (ad, len(satirlar)))
    for i, s in enumerate(satirlar, 1):
        if len(s) > 70:
            hatalar.append("%s:%d genislik %d" % (ad, i, len(s)))
    return "```python\n" + "\n".join(s.rstrip() for s in satirlar) + \
        "\n```"


def kaynak(ad):
    with open(os.path.join(TEMP, ad), encoding="utf-8") as f:
        return f.read().split("\n")[:-1]


def cikti_blok(ad):
    p = subprocess.run([sys.executable, ad], cwd=TEMP, env=ENV,
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise SystemExit("program hatasi: %s\n%s" % (ad, p.stderr))
    satir = ["$ python " + ad] + p.stdout.rstrip("\n").split("\n")
    for s in satir:
        if len(s) > 74:
            hatalar.append("%s terminal %d karakter" % (ad, len(s)))
    return "```term\n" + "\n".join(satir) + "\n```"


def cevir(metin):
    def rep(m):
        tip, args = m.group(1), m.group(2).split("|")
        if tip == "SEKIL":
            return "![%s](gorseller/%s)" % (args[1], args[0])
        if tip == "KODTAM":
            return kod_blok(kaynak(args[0]), args[0])
        if tip == "KOD":
            ad, a, b = args[0], int(args[1]), int(args[2])
            return kod_blok(kaynak(ad)[a - 1:b],
                            "%s[%d-%d]" % (ad, a, b))
        if tip == "CIKTI":
            return cikti_blok(args[0])
        raise SystemExit("bilinmeyen: " + tip)
    return re.sub(r"^@@(SEKIL|KODTAM|KOD|CIKTI)\|([^@]*)@@$", rep,
                  metin, flags=re.M)


parcalar = []
for i in (1, 2, 3, 4):
    yol = os.path.join(TEMP, "part%d.md" % i)
    if os.path.exists(yol):
        parcalar.append(open(yol, encoding="utf-8").read())
metin = cevir("\n".join(parcalar)).rstrip() + "\n"
hedef = os.path.join(KOK, "bolumler", "bolum_56.md")
open(hedef, "w", encoding="utf-8", newline="\n").write(metin)
print("yazildi:", hedef, "satir:", metin.count("\n"))
print("UYARILAR:" if hatalar else "uyari yok")
for h in hatalar:
    print("  ", h)
