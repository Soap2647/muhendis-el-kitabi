# -*- coding: utf-8 -*-
"""Bolum 80 birlestirici: parts/*.md icindeki isaretcileri gercek
dosya icerigiyle degistirir ve bolumler/bolum_80.md uretir.

Isaretciler (ayri satirda):
  {{KOD ad k}}          b80_<ad>.py dosyasinin k. parcasi (python)
  {{KAYNAK yol a b}}    kaynak dosyadan a..b satirlari (python)
  {{CIKTI cikti.txt komut}}  terminal blogu: '$ komut' + cikti dosyasi
"""
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
B80 = "C:/Users/merty/AppData/Local/Temp/b80"
KITAP = "D:/Mevcut Projeler/Kitap"
HEAD = ("%% kisim_no: XVI\n%% kisim_ad: ML Mühendisliği & Araştırma\n"
        "%% bolum_no: 80\n%% baslik: Bitirme: Uçtan Uca Sistem\n")
MAX = 38
hatalar = []


def satirlar(yol):
    with open(yol, encoding="utf-8") as f:
        return f.read().replace("\r", "").split("\n")


def parcala(L):
    """_plan.py ile ayni algoritma: en fazla MAX satir, bos satirdan."""
    n = len(L)
    while n and L[n - 1] == "":
        n -= 1
    parcalar, i = [], 0
    while i < n:
        son = min(i + MAX, n)
        if son < n:
            k = son
            while k > i + 8 and L[k - 1].strip() != "":
                k -= 1
            if k > i + 8:
                son = k
        parcalar.append((i + 1, son))
        i = son
        while i < n and L[i].strip() == "":
            i += 1
    return parcalar


def kod_blok(L, a, b, ad, dil="python"):
    parca = L[a - 1:b]
    while parca and parca[-1] == "":
        parca.pop()
    if len(parca) > 40:
        hatalar.append("%s %d-%d: %d satir" % (ad, a, b, len(parca)))
    for i, s in enumerate(parca, a):
        if len(s) > 70:
            hatalar.append("%s:%d genislik %d" % (ad, i, len(s)))
    return "```%s\n%s\n```" % (dil, "\n".join(parca))


def isle(metin):
    cikti = []
    for satir in metin.split("\n"):
        m = re.match(r"^\{\{(KOD|KAYNAK|CIKTI) (.*)\}\}\s*$", satir)
        if not m:
            cikti.append(satir)
            continue
        tur, arg = m.group(1), m.group(2).split()
        if tur == "KOD":
            ad, k = arg[0], int(arg[1])
            dosya = os.path.join(B80, "b80_%s.py" % ad)
            L = satirlar(dosya)
            a, b = parcala(L)[k - 1]
            cikti.append(kod_blok(L, a, b, "b80_%s.py" % ad))
        elif tur == "KAYNAK":
            L = satirlar(arg[0])
            a, b = int(arg[1]), int(arg[2])
            cikti.append(kod_blok(L, a, b, "kaynak", dil="python"))
        else:
            dosya = os.path.join(B80, "cikti", arg[0])
            L = satirlar(dosya)
            while L and L[-1] == "":
                L.pop()
            for i, s in enumerate(L, 1):
                if len(s) > 74:
                    hatalar.append("cikti %s:%d genislik %d"
                                   % (arg[0], i, len(s)))
            cikti.append("```term\n$ %s\n%s\n```"
                         % (" ".join(arg[1:]), "\n".join(L)))
    return "\n".join(cikti)


def main():
    parcalar = sorted(glob.glob(os.path.join(B80, "parts", "*.md")))
    govde = []
    for p in parcalar:
        with open(p, encoding="utf-8") as f:
            govde.append(f.read().strip())
    metin = isle("\n\n".join(govde))
    cikis = os.path.join(KITAP, "bolumler", "bolum_80.md")
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
