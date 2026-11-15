# -*- coding: utf-8 -*-
# birlestir.py: bolum_67 metnini parcalardan birlestirir.
# @@KOD dosya.py BAS SON@@ -> python kod blogu. BAS/SON:
#   ^ dosya basi, $ dosya sonu, def:AD, class:AD, sab:METIN (satir basi),
#   L123 (1 tabanli satir no). Blok SON satirindan ONCE biter.
# @@CIKTI cikti.txt komut@@ -> term blogu ($ komut + cikti dosyasi).
# Uzun satirlar (kod >70, terminal >74) anlam degistirmeden bolunur:
# yorumlar iki satira, kod ters egik cizgiyle, terminal girintiyle.
import glob
import os
import re

BASE = "C:/Users/merty/AppData/Local/Temp/b67"
OUT = os.path.join(BASE, "out")
PARTS = sorted(glob.glob(os.path.join(BASE, "parts", "p*.md")))
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_67.md"
uyari = []
bolunen = {"kod": 0, "terminal": 0}


def bul(satirlar, arama):
    if arama == "^":
        return 0
    if arama == "$":
        return len(satirlar)
    if arama.startswith("L"):
        return int(arama[1:]) - 1
    for i, l in enumerate(satirlar):
        if arama.startswith("def:") and l.startswith(
                "def " + arama[4:] + "("):
            return i
        if arama.startswith("class:") and l.startswith(
                "class " + arama[6:]):
            return i
        if arama.startswith("sab:") and l.startswith(arama[4:]):
            return i
    raise SystemExit("bulunamadi: " + arama)


def kod_satiri_bol(l, docstring):
    """Uzun kod satirini 70 karakterin altina boler (anlam korunur)."""
    if len(l) <= 70:
        return [l]
    girinti = len(l) - len(l.lstrip(" "))
    govde = l.lstrip(" ")
    if govde.startswith("#"):
        metin = govde[1:].strip()
        on = " " * girinti + "# "
        satirlar, satir = [], ""
        for kelime in metin.split(" "):
            aday = (satir + " " + kelime).strip()
            if len(on) + len(aday) > 70 and satir:
                satirlar.append(on + satir)
                satir = kelime
            else:
                satir = aday
        satirlar.append(on + satir)
        return satirlar
    if docstring:
        # docstring metni: bosluktan bol, ters egik cizgi ekleme
        kes = l.rfind(" ", 0, 68)
        if kes <= girinti + 8:
            return [l]
        return [l[:kes]] + kod_satiri_bol(
            " " * (girinti + 4) + l[kes + 1:], True)
    kes = -1
    for i in range(min(68, len(l) - 1), girinti + 8, -1):
        if l[i] == " " and l[:i].count('"') % 2 == 0 \
                and l[:i].count("'") % 2 == 0:
            kes = i
            break
    if kes < 0:
        return [l]
    ilk = l[:kes] + " \\"
    ikinci = " " * (girinti + 4) + l[kes + 1:]
    return [ilk] + kod_satiri_bol(ikinci, False)


def kod_blok(dosya, bas, son):
    yol = os.path.join(BASE, dosya)
    satirlar = open(yol, encoding="utf-8").read().split("\n")
    if satirlar and satirlar[-1] == "":
        satirlar = satirlar[:-1]
    i0 = bul(satirlar, bas)
    i1 = bul(satirlar, son)
    blok = satirlar[i0:i1]
    if blok and blok[0].startswith("# -*- coding"):
        blok = blok[1:]
    while blok and blok[-1].strip() == "":
        blok = blok[:-1]
    cikti, docstring = [], False
    for l in blok:
        if len(l) > 70:
            bolunen["kod"] += 1
        cikti.extend(kod_satiri_bol(l, docstring))
        if l.count('"""') % 2 == 1:
            docstring = not docstring
    for l in cikti:
        if len(l) > 70:
            uyari.append("KOD>70 %s: %s" % (dosya, l[:50]))
    return "```python\n" + "\n".join(cikti) + "\n```"


def term_satiri_bol(l):
    if len(l) <= 74:
        return [l]
    satirlar, satir = [], ""
    for kelime in l.split(" "):
        aday = (satir + " " + kelime) if satir else kelime
        if len(aday) > 74 and satir:
            satirlar.append(satir)
            satir = "    " + kelime
        else:
            satir = aday
    satirlar.append(satir)
    return satirlar


def cikti_blok(dosya, komut):
    metin = open(os.path.join(OUT, dosya), encoding="utf-8").read()
    satirlar = metin.replace("\r\n", "\n").split("\n")
    while satirlar and satirlar[-1].strip() == "":
        satirlar = satirlar[:-1]
    yeni = []
    for l in satirlar:
        if len(l) > 74:
            bolunen["terminal"] += 1
        yeni.extend(term_satiri_bol(l))
    for l in yeni:
        if len(l) > 74:
            uyari.append("CIKTI>74 %s: %s" % (dosya, l[:50]))
    return "```term\n$ " + komut + "\n" + "\n".join(yeni) + "\n```"


def isle(metin):
    metin = re.sub(r"@@KOD (\S+) (\S+) (\S+)@@",
                   lambda m: kod_blok(m.group(1), m.group(2),
                                      m.group(3)), metin)
    metin = re.sub(r"@@CIKTI (\S+) (.+?)@@",
                   lambda m: cikti_blok(m.group(1), m.group(2)), metin)
    return metin


if __name__ == "__main__":
    parcalar = [open(p, encoding="utf-8").read().rstrip() + "\n"
                for p in PARTS]
    tam = isle("\n".join(parcalar))
    if "@@" in tam:
        print("UYARI: islenmemis isaretci var")
    with open(HEDEF, "w", encoding="utf-8") as f:
        f.write(tam)
    print("yazildi:", HEDEF, "satir:", tam.count("\n"))
    print("parca:", len(PARTS), "bolunen kod:", bolunen["kod"],
          "terminal:", bolunen["terminal"])
    for u in uyari:
        print(u)
