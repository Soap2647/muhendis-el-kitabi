# -*- coding: utf-8 -*-
"""Bolum 54 taslagini (part1-3.md) bolumler/bolum_54.md'ye cevirir.
Yer tutucular:
  @@SEKIL|dosya|baslik@@         -> gorsel
  @@KODTAM|dosya@@               -> tum program kodu
  @@KOD|dosya|bas|son@@          -> programin satir araligi
  @@CIKTI|dosya@@                -> programi calistirir, terminal blogu
"""
import os, re, subprocess, sys

TEMP = "C:/Users/merty/AppData/Local/Temp/b54"
KOK = "D:/Mevcut Projeler/Kitap"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
hatalar = []

def kod_blok(satirlar, ad):
    if len(satirlar) > 40:
        hatalar.append("%s: %d satir (>40)" % (ad, len(satirlar)))
    for i, s in enumerate(satirlar, 1):
        if len(s) > 70:
            hatalar.append("%s:%d genislik %d" % (ad, i, len(s)))
    return "```python\n" + "\n".join(s.rstrip() for s in satirlar) + "\n```"

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
            ad = args[0]
            return kod_blok(open(os.path.join(TEMP, ad), encoding="utf-8")
                            .read().split("\n")[:-1], ad)
        if tip == "KOD":
            ad, a, b = args[0], int(args[1]), int(args[2])
            satirlar = open(os.path.join(TEMP, ad), encoding="utf-8").read().split("\n")
            return kod_blok(satirlar[a - 1:b], "%s[%d-%d]" % (ad, a, b))
        if tip == "CIKTI":
            return cikti_blok(args[0])
        raise SystemExit("bilinmeyen: " + tip)
    return re.sub(r"^@@(SEKIL|KODTAM|KOD|CIKTI)\|([^@]*)@@$", rep, metin, flags=re.M)

parcalar = [open(os.path.join(TEMP, "part%d.md" % i), encoding="utf-8").read()
            for i in (1, 2, 3)]
metin = cevir("\n".join(parcalar)).rstrip() + "\n"
hedef = os.path.join(KOK, "bolumler", "bolum_54.md")
open(hedef, "w", encoding="utf-8", newline="\n").write(metin)
print("yazildi:", hedef, "satir:", metin.count("\n"))
print("UYARILAR:" if hatalar else "uyari yok")
for h in hatalar:
    print("  ", h)
