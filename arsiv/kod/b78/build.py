# -*- coding: utf-8 -*-
"""Bolum 78 birlestirici: p*.md parcalarini okur, yer tutucu kod ve
terminal bloklarini dosyalardan gomer, bolumler/bolum_78.md yazar.

Yer tutucular (tek satir):
  @@CODE dosya.py@@          kodu gom; 40 satirdan uzunsa bloklara bolerek
  @@TERM cikti.out|komut@@   terminal blogu: "$ komut" + cikti satirlari
"""
import glob
import os
import re
import sys

B = r"C:\Users\merty\AppData\Local\Temp\b78"
HEDEF = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_78.md"
MAKS_KOD = 70
MAKS_TERM = 74
BLOK = 40


def kod_bloklari(satirlar):
    """Satirlari <= BLOK satirlik parcalara bol; bolme noktasi bos satir."""
    parcalar, i = [], 0
    while i < len(satirlar):
        son = min(i + BLOK, len(satirlar))
        if son < len(satirlar):
            kes = None
            for j in range(son, i + BLOK // 2, -1):
                if satirlar[j - 1].strip() == "":
                    kes = j
                    break
            son = kes if kes else son
        parcalar.append(satirlar[i:son])
        i = son
        while i < len(satirlar) and satirlar[i].strip() == "":
            i += 1
    return parcalar


def ayikla(metin):
    cikti, hata = [], []
    for satir in metin.split("\n"):
        m = re.match(r"^@@CODE (\S+)@@$", satir)
        if m:
            yol = os.path.join(B, m.group(1))
            with open(yol, encoding="utf-8") as f:
                s = f.read().rstrip("\n").split("\n")
            for k, p in enumerate(kod_bloklari(s)):
                if k:
                    cikti.append("")
                cikti.append("```python")
                for x in p:
                    if len(x) > MAKS_KOD:
                        hata.append("%s: %d karakter" % (m.group(1), len(x)))
                    cikti.append(x)
                cikti.append("```")
            cikti.append("")
            continue
        m = re.match(r"^@@TERM (\S+)\|(.+)@@$", satir)
        if m:
            yol = os.path.join(B, "out", m.group(1))
            with open(yol, encoding="utf-8") as f:
                s = f.read().rstrip("\n").split("\n")
            cikti += ["```term", "$ " + m.group(2)]
            for x in s:
                if len(x) > MAKS_TERM:
                    hata.append("%s: terminal %d karakter"
                                % (m.group(1), len(x)))
                cikti.append(x)
            cikti += ["```", ""]
            continue
        cikti.append(satir)
    return "\n".join(cikti), hata


def main():
    parcalar = sorted(glob.glob(os.path.join(B, "md", "p*.md")))
    metin = "\n".join(open(p, encoding="utf-8").read().rstrip("\n")
                      + "\n" for p in parcalar)
    cikti, hata = ayikla(metin)
    if hata:
        print("HATA:")
        for h in hata:
            print("  " + h)
        sys.exit(1)
    with open(HEDEF, "w", encoding="utf-8") as f:
        f.write(cikti)
    print("yazildi:", HEDEF, "satir:", cikti.count("\n"))


if __name__ == "__main__":
    main()
