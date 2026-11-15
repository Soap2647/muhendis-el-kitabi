# -*- coding: utf-8 -*-
"""Bolum 37 md birlestirici: {{...}} yer tutucularini dosyadan doldurur."""
import glob, os, re, sys
T = r"C:\Users\merty\AppData\Local\Temp\b37"
DORUK = r"D:\Mevcut Projeler\GitHub\Mert-Studio-Code-v2\doruk"
OUT = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_37.md"

def dosya(yol):
    return open(yol, encoding="utf-8").read()

def kod_blok(dil, yol, a=None, b=None):
    satirlar = dosya(yol).split("\n")
    if a is not None:
        satirlar = satirlar[a - 1:b]
    while satirlar and satirlar[-1] == "":
        satirlar.pop()
    return "```%s\n%s\n```" % (dil, "\n".join(satirlar))

def expand(m):
    tur, arg = m.group(1), m.group(2)
    if tur == "PY":                       # PY:dosya:a:b
        parca = arg.split(":")
        yol = os.path.join(T, "mini", parca[0])
        a = int(parca[1]) if len(parca) > 1 else None
        b = int(parca[2]) if len(parca) > 2 else None
        return kod_blok("python", yol, a, b)
    if tur == "CPP":                      # CPP:yol:a:b (Doruk)
        parca = arg.split(":")
        yol = os.path.join(DORUK, parca[0])
        return kod_blok("cpp", yol, int(parca[1]), int(parca[2]))
    if tur == "C":                        # C:dosya (gcc klasoru)
        return kod_blok("c", os.path.join(T, "gcc", arg))
    if tur == "TERM":                     # TERM:dosya|komut
        dosya_adi, _, komut = arg.partition("|")
        govde = dosya(os.path.join(T, dosya_adi)).rstrip("\n")
        icerik = (komut + "\n" if komut else "") + govde
        return "```term\n%s\n```" % icerik
    if tur == "RAW":                      # RAW:mutlak_yol:a:b
        parca = arg.split(":")
        yol = parca[0] if len(parca) < 4 else parca[0] + ":" + parca[1]
        kalan = parca[1:] if len(parca) < 4 else parca[2:]
        a, b = int(kalan[0]), int(kalan[1])
        return kod_blok("python", yol, a, b)
    if tur == "TXT":                      # duz metin dosyasi
        return dosya(os.path.join(T, arg)).rstrip("\n")
    raise ValueError(tur)

def main():
    parcalar = sorted(glob.glob(os.path.join(T, "md", "p*.md")))
    metin = "\n\n".join(dosya(p).strip("\n") for p in parcalar)
    metin = re.sub(r"\{\{(PY|CPP|C|TERM|TXT|RAW):([^}]*)\}\}", expand, metin)
    open(OUT, "w", encoding="utf-8", newline="\n").write(metin + "\n")
    print("yazildi:", OUT, len(metin), "karakter")

if __name__ == "__main__":
    main()
