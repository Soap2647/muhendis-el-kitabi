# -*- coding: utf-8 -*-
"""parts/*.md dosyalarini birlestirir; yer tutucularini dosya iceriginden
doldurur, sonucu bolumler/bolum_74.md'ye yazar.

Yer tutucular (satir basinda tek basina):
  @@CODE dosya.py@@        -> dosyanin tamami, ```python bloklari
                              (en fazla 38 satir; bos satirdan bolunur)
  @@TERM dosya.txt@@       -> terminal ciktisi (```term)
  @@DOC dosya.txt@@        -> duz metin dosyasi (ornek tablosu vb.)
"""
import glob
import os
import re
import sys

BASE = "C:/Users/merty/AppData/Local/Temp/b74"
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_74.md"
MAX = 38


def bol(satirlar):
    """Kod satirlarini <= MAX'lik parcalara, mumkunse bos satirdan bol."""
    parcalar, cur = [], []
    for s in satirlar:
        cur.append(s)
        if len(cur) >= MAX and s.strip() == "":
            parcalar.append(cur)
            cur = []
    if cur:
        parcalar.append(cur)
    # hala uzun parcalar varsa zorla bol
    son = []
    for p in parcalar:
        while len(p) > MAX + 8:
            son.append(p[:MAX])
            p = p[MAX:]
        son.append(p)
    return son


def kod_blok(ad, dil="python"):
    yol = os.path.join(BASE, ad)
    satirlar = open(yol, encoding="utf-8").read().rstrip("\n").split("\n")
    out = []
    for p in bol(satirlar):
        while p and p[-1].strip() == "":
            p = p[:-1]
        if not p:
            continue
        out.append("```%s\n%s\n```" % (dil, "\n".join(p)))
    return "\n\n".join(out)


def term_blok(ad):
    yol = os.path.join(BASE, ad)
    satirlar = open(yol, encoding="utf-8").read().rstrip("\n").split("\n")
    return "```term\n%s\n```" % "\n".join(satirlar)


def main():
    parts = sorted(glob.glob(os.path.join(BASE, "parts", "*.md")))
    metin = []
    for p in parts:
        metin.append(open(p, encoding="utf-8").read().rstrip("\n") + "\n")
    s = "\n".join(metin)

    def repl(m):
        tur, ad = m.group(1), m.group(2)
        if tur == "CODE":
            return kod_blok(ad)
        if tur == "TERM":
            return term_blok(ad)
        if tur == "DOC":
            return open(os.path.join(BASE, ad), encoding="utf-8").read()
        raise ValueError(tur)

    s = re.sub(r"^@@(CODE|TERM|DOC) ([^@]+)@@$", repl, s, flags=re.M)
    if "@@" in s:
        print("UYARI: cozulmemis yer tutucu var")
        sys.exit(1)
    os.makedirs(os.path.dirname(HEDEF), exist_ok=True)
    with open(HEDEF, "w", encoding="utf-8") as f:
        f.write(s)
    print("yazildi:", HEDEF, len(s.split("\n")), "satir")


if __name__ == "__main__":
    main()
