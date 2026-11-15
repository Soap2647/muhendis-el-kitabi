# -*- coding: utf-8 -*-
"""Bolum 57 birlestirici: md/p*.md parcalarini okur, yonergeleri
kod ve terminal bloklarina cevirir, bolumler/bolum_57.md yazar.

Yonergeler (satir basinda):
  @KOD dosya.py a b         -> python kod blogu (satir a..b)
  @TERM cikti.txt komut     -> term blogu: "$ komut" + cikti satirlari
"""
import glob, os, sys

TEMP = r"C:\Users\merty\AppData\Local\Temp\b57"
KOK = r"D:\Mevcut Projeler\Kitap"
HEDEF = os.path.join(KOK, "bolumler", "bolum_57.md")


def oku_satirlar(yol):
    with open(yol, encoding="utf-8") as f:
        return [s.rstrip("\r\n").rstrip() for s in f.readlines()]


def kirp(satirlar):
    while satirlar and satirlar[0] == "":
        satirlar = satirlar[1:]
    while satirlar and satirlar[-1] == "":
        satirlar = satirlar[:-1]
    return satirlar


def kod_blogu(dosya, a, b):
    satirlar = oku_satirlar(os.path.join(TEMP, dosya))
    parca = kirp(satirlar[a - 1:b])
    en_uzun = max(len(s) for s in parca)
    if en_uzun > 70:
        raise SystemExit("KOD > 70: %s %d-%d (%d)" % (dosya, a, b, en_uzun))
    return "```python\n" + "\n".join(parca) + "\n```\n"


def term_blogu(dosya, komut, a=None, b=None, komutsuz=False):
    satirlar = oku_satirlar(os.path.join(TEMP, dosya))
    if a is not None:
        satirlar = satirlar[a - 1:b]
    satirlar = kirp(satirlar)
    if komutsuz:
        if max(len(s) for s in satirlar) > 74:
            raise SystemExit("TERM > 74: %s" % dosya)
        return "```term\n" + "\n".join(satirlar) + "\n```\n"
    en_uzun = max(len(s) for s in ["$ " + komut] + satirlar)
    if en_uzun > 74:
        raise SystemExit("TERM > 74: %s (%d)" % (dosya, en_uzun))
    return "```term\n$ " + komut + "\n" + "\n".join(satirlar) + "\n```\n"


def main():
    parcalar = sorted(glob.glob(os.path.join(TEMP, "md", "p*.md")))
    cikti = []
    for yol in parcalar:
        for satir in oku_satirlar(yol):
            if satir.startswith("@KOD "):
                _, dosya, a, b = satir.split()
                cikti.append(kod_blogu(dosya, int(a), int(b)))
            elif satir.startswith("@TERM "):
                # @TERM dosya|komut[|a|b]   veya   @TERM2 dosya|a|b
                parca = satir.split(" ", 1)[1].split("|")
                if len(parca) == 4:
                    cikti.append(term_blogu(parca[0], parca[1],
                                            int(parca[2]), int(parca[3])))
                else:
                    cikti.append(term_blogu(parca[0], parca[1]))
            elif satir.startswith("@TERM2 "):
                parca = satir.split(" ", 1)[1].split("|")
                cikti.append(term_blogu(parca[0], "", int(parca[1]),
                                        int(parca[2]), komutsuz=True))
            else:
                cikti.append(satir + "\n")
        cikti.append("\n")
    metin = "".join(cikti)
    while "\n\n\n" in metin:
        metin = metin.replace("\n\n\n", "\n\n")
    with open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin)
    print("yazildi:", HEDEF, len(metin.split("\n")), "satir")


if __name__ == "__main__":
    main()
