# -*- coding: utf-8 -*-
# build_md.py: Bolum 62 md dosyasini birlestirir. Yer tutucular:
#   {{KOD dosya a b}}        Temp/b62 altindaki dosyanin a..b satirlari (python)
#   {{CIKTI cikti.txt | komut}}  cikti dosyasi (terminal blogu)
#   {{SRC yol a b}}          dis kaynak dosyanin a..b satirlari (python)
import os
import re
import sys

TMP = "C:/Users/merty/AppData/Local/Temp/b62"
MD_DIR = os.path.join(TMP, "md")
KITAP = "D:/Mevcut Projeler/Kitap"
CIKIS = os.path.join(KITAP, "bolumler", "bolum_62.md")
PARCALAR = ["01_giris_teori_a.md", "02_teori_b.md", "03_teori_c.md",
            "04_ornekler_yap_kodokuma_ozet.md"]
hatalar = []


def satirlar(yol, a, b):
    with open(yol, encoding="utf-8") as f:
        L = f.read().split("\n")
    return L[a - 1:b]


def kod_blok(L, dil, etiket):
    for i, l in enumerate(L):
        if len(l) > 70:
            hatalar.append("%s satir %d: %d karakter" % (etiket, i + 1, len(l)))
    if len(L) > 42:
        hatalar.append("%s: %d satir (en fazla 42)" % (etiket, len(L)))
    return "```%s\n%s\n```" % (dil, "\n".join(L))


def kod(m):
    dosya, a, b = m.group(1), int(m.group(2)), int(m.group(3))
    L = satirlar(os.path.join(TMP, dosya), a, b)
    return kod_blok(L, "python", "%s %d-%d" % (dosya, a, b))


BOLUNEN = {
    "self.P = dot(dot(I_KH, self.P), I_KH.T) + dot(dot(self.K, R), self.K.T)":
    ["        self.P = dot(dot(I_KH, self.P), I_KH.T) + dot(",
     "            dot(self.K, R), self.K.T",
     "        )"],
}


def src(m):
    yol, a, b = m.group(1), int(m.group(2)), int(m.group(3))
    L0 = satirlar(yol, a, b)
    L = []
    for l in L0:
        if l.strip() in BOLUNEN and len(l) > 70:
            L.extend(BOLUNEN[l.strip()])
        else:
            L.append(l)
    return kod_blok(L, "python", "SRC %s %d-%d" % (os.path.basename(yol), a, b))


def cikti(m):
    dosya, komut = m.group(1).strip(), m.group(2).strip()
    with open(os.path.join(TMP, dosya), encoding="utf-8") as f:
        L = f.read().rstrip("\n").split("\n")
    for i, l in enumerate(L):
        if len(l) > 74:
            hatalar.append("%s satir %d: %d karakter" % (dosya, i + 1, len(l)))
    if len(L) > 45:
        hatalar.append("%s: %d satir (terminal en fazla 45)" % (dosya, len(L)))
    return "```term\n$ %s\n%s\n```" % (komut, "\n".join(L))


metin = "\n\n".join(open(os.path.join(MD_DIR, p), encoding="utf-8").read().rstrip("\n")
                    for p in PARCALAR) + "\n"
metin = re.sub(r"\{\{KOD (\S+) (\d+) (\d+)\}\}", kod, metin)
metin = re.sub(r"\{\{SRC (\S+) (\d+) (\d+)\}\}", src, metin)
metin = re.sub(r"\{\{CIKTI ([^|]+?) \| ([^}]+?)\}\}", cikti, metin)
kalan = re.findall(r"\{\{.*?\}\}", metin)
if kalan:
    hatalar.append("cozulmemis yer tutucu: %s" % kalan[:5])
if hatalar:
    print("HATALAR:")
    for h in hatalar:
        print("  ", h)
    sys.exit(1)
with open(CIKIS, "w", encoding="utf-8", newline="\n") as f:
    f.write(metin)
print("yazildi:", CIKIS, "satir:", metin.count("\n"))
