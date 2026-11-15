# -*- coding: utf-8 -*-
"""Bolum 46 sablonunu dosyalardan kod ve cikti bloklariyla birlestirir."""
import os
import re
import sys

B = os.path.dirname(os.path.abspath(__file__))
KOK = "D:/Mevcut Projeler/Kitap"
TPL = os.path.join(B, "tpl")
CIKTI = os.path.join(KOK, "bolumler", "bolum_46.md")
PAR = ["p1.md", "p2.md", "p3.md", "p4.md"]
RE_KOD = re.compile(r"^@@KOD\|([^|]+)\|(\d+)\|(\d+)\|(\w+)@@$")
RE_CIKTI = re.compile(r"^@@CIKTI\|([^|]+)\|(.+)@@$")


def kod_blok(ad, a, b, dil):
    yol = os.path.join(B, ad)
    satirlar = open(yol, encoding="utf-8").read().split("\n")
    parca = [s.rstrip() for s in satirlar[int(a) - 1:int(b)]]
    while parca and parca[-1] == "":
        parca.pop()
    return "```%s\n%s\n```" % (dil, "\n".join(parca))


def cikti_blok(ad, komut):
    yol = os.path.join(B, ad)
    satirlar = open(yol, encoding="utf-8").read().split("\n")
    temiz = [s.rstrip() for s in satirlar
             if not s.startswith("EXIT=")]
    while temiz and temiz[-1] == "":
        temiz.pop()
    return "```term\n$ %s\n%s\n```" % (komut, "\n".join(temiz))


def main():
    govde = []
    for p in PAR:
        govde.append(open(os.path.join(TPL, p), encoding="utf-8").read())
    metin = "\n".join(g.rstrip("\n") + "\n" for g in govde)
    cikti = []
    for satir in metin.split("\n"):
        m = RE_KOD.match(satir.strip())
        if m:
            cikti.append(kod_blok(m.group(1), m.group(2), m.group(3),
                                  m.group(4)))
            continue
        m = RE_CIKTI.match(satir.strip())
        if m:
            cikti.append(cikti_blok(m.group(1), m.group(2)))
            continue
        if "@@" in satir:
            print("UYARI: yer tutucu cozulmedi:", satir[:80])
        cikti.append(satir)
    sonuc = "\n".join(cikti)
    sonuc = re.sub(r"\n{3,}", "\n\n", sonuc)
    with open(CIKTI, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sonuc)
    print("yazildi:", CIKTI, "satir:", sonuc.count("\n"))


if __name__ == "__main__":
    main()
