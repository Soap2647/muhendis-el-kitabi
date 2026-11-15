# -*- coding: utf-8 -*-
"""Bolum 77 birlestirici: parts/*.md icindeki isaretcileri gercek
dosya icerigiyle degistirir ve bolumler/bolum_77.md uretir.

Isaretciler (ayri satirda):
  {{KOD dosya.py a b}}       dosyanin a..b satirlari (python blogu)
  {{CIKTI cikti.txt komut}}  terminal blogu: '$ komut' + cikti dosyasi
  {{KAYNAK yol a b}}         kaynak dosyadan a..b satirlari (kod okuma)
"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
B77 = "C:/Users/merty/AppData/Local/Temp/b77"
CIKTI = os.path.join(B77, "cikti")
KITAP = "D:/Mevcut Projeler/Kitap"
HEAD = ("%% kisim_no: XVI\n%% kisim_ad: ML Mühendisliği & Araştırma\n"
        "%% bolum_no: 77\n%% baslik: MLOps\n")
hatalar = []


def satirlar(yol):
    with open(yol, encoding="utf-8") as f:
        return f.read().split("\n")


def kod_blok(dosya, a=None, b=None, dil="python", kok=B77):
    yol = dosya if os.path.isabs(dosya) else os.path.join(kok, dosya)
    L = satirlar(yol)
    if a is None:
        a, b = 1, len(L)
    parca = L[int(a) - 1:int(b)]
    while parca and parca[-1] == "":
        parca.pop()
    if len(parca) > 40:
        hatalar.append("%s %s-%s: %d satir (>40)" % (dosya, a, b, len(parca)))
    for i, s in enumerate(parca, int(a)):
        if len(s) > 70:
            hatalar.append("%s:%d genislik %d" % (dosya, i, len(s)))
    return "```%s\n%s\n```" % (dil, "\n".join(parca))


def cikti_blok(dosya, komut):
    L = satirlar(os.path.join(CIKTI, dosya))
    while L and L[-1] == "":
        L.pop()
    for i, s in enumerate(L, 1):
        if len(s) > 74:
            hatalar.append("cikti %s:%d genislik %d" % (dosya, i, len(s)))
    return "```term\n$ %s\n%s\n```" % (komut, "\n".join(L))


def isle(metin):
    cikti = []
    for satir in metin.split("\n"):
        m = re.match(r"^\{\{(KOD|CIKTI|KAYNAK) (.*)\}\}\s*$", satir)
        if not m:
            cikti.append(satir)
            continue
        tur, arg = m.group(1), m.group(2).split()
        if tur == "KOD":
            if len(arg) == 1:
                cikti.append(kod_blok(arg[0]))
            else:
                cikti.append(kod_blok(arg[0], arg[1], arg[2]))
        elif tur == "KAYNAK":
            cikti.append(kod_blok(arg[0], arg[1], arg[2], dil="python",
                                  kok="/"))
        else:
            cikti.append(cikti_blok(arg[0], " ".join(arg[1:])))
    return "\n".join(cikti)


def main():
    parcalar = sorted(glob.glob(os.path.join(B77, "parts", "*.md")))
    govde = []
    for p in parcalar:
        with open(p, encoding="utf-8") as f:
            govde.append(f.read().strip())
    metin = isle("\n\n".join(govde))
    cikis = os.path.join(KITAP, "bolumler", "bolum_77.md")
    with open(cikis, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEAD + "\n" + metin + "\n")
    print("yazildi:", cikis, "satir:", metin.count("\n") + 1)
    if hatalar:
        print("UYARI:")
        for h in hatalar:
            print("  ", h)
    else:
        print("kod/cikti denetimi temiz")


if __name__ == "__main__":
    main()
