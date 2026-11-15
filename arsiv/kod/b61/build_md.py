# -*- coding: utf-8 -*-
"""Bolum 61 birlestiricisi.

Sablon (bolum61_sablon.md) icindeki yer tutucular:
  @@KOD dosya|baslangic|bitis@@
      dosyanin satirlarindan ```python blogu uretir. baslangic: bu
      metni iceren ilk satir (onceki blogun bittigi yerden aranir);
      bitis: bu metni iceren ilk satir (dahil edilmez). Bos ise dosya
      sonuna kadar.
  @@OUT dosya|komut|baslangic|bitis@@
      cikti dosyasindan ```term blogu uretir; ilk satir "$ komut".
"""
import os
import sys

TMP = "C:/Users/merty/AppData/Local/Temp/b61/"
KOK = "D:/Mevcut Projeler/Kitap/"
SABLON = TMP + "bolum61_sablon.md"
HEDEF = KOK + "bolumler/bolum_61.md"

imlec = {}
uyari = []


def satirlar(yol):
    with open(yol, encoding="utf-8") as f:
        return f.read().split("\n")


def aralik(lines, anahtar, bas, bit, yol_adi):
    key = (yol_adi, bas, bit)
    i = imlec.get(yol_adi, 0)
    if bas:
        s = None
        for k in range(0, len(lines)):
            if bas in lines[k]:
                s = k
                break
        if s is None:
            raise SystemExit("baslangic bulunamadi: %s | %s" % (yol_adi, bas))
    else:
        s = i
    e = len(lines)
    if bit:
        for k in range(s + 1, len(lines)):
            if bit in lines[k]:
                e = k
                break
        else:
            raise SystemExit("bitis bulunamadi: %s | %s" % (yol_adi, bit))
    while e > s and lines[e - 1].strip() == "":
        e -= 1
    imlec[yol_adi] = e
    return lines[s:e]


def kod_blogu(parca, dil):
    return ["```" + dil] + [x.rstrip() for x in parca] + ["```"]


def cozum(metin):
    cikti = []
    for satir in metin.split("\n"):
        if satir.startswith("@@KOD "):
            govde = satir[len("@@KOD "):].rstrip("@").strip()
            yol, bas, bit = (govde.split("|") + ["", ""])[:3]
            yol = TMP + yol
            L = satirlar(yol)
            blok = aralik(L, None, bas, bit, yol)
            if len(blok) > 40:
                uyari.append("KOD >40 satir: %s (%d)" % (yol, len(blok)))
            for x in blok:
                if len(x) > 70:
                    uyari.append("KOD >70: %s: %s" % (yol, x[:50]))
            cikti += kod_blogu(blok, "python")
        elif satir.startswith("@@OUT "):
            govde = satir[len("@@OUT "):].rstrip("@").strip()
            yol, komut, bas, bit = (govde.split("|") + ["", "", ""])[:4]
            yol = TMP + yol
            L = satirlar(yol)
            blok = aralik(L, None, bas, bit, yol)
            for x in blok:
                if len(x) > 74:
                    uyari.append("TERM >74: %s: %s" % (yol, x[:50]))
            cikti += ["```term", "$ " + komut] + [x.rstrip() for x in blok]
            cikti += ["```"]
        else:
            cikti.append(satir)
    return "\n".join(cikti)


def main():
    with open(SABLON, encoding="utf-8") as f:
        metin = f.read()
    sonuc = cozum(metin)
    with open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(sonuc)
    print("yazildi:", HEDEF, "satir:", sonuc.count("\n") + 1)
    for u in uyari:
        print("UYARI:", u)


if __name__ == "__main__":
    main()
