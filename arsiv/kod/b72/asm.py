# -*- coding: utf-8 -*-
"""bolum_72.md birlestirici.
@@KODTAM dosya@@   : dosyanin TAMAMI, <=40 satirlik kod bloklarina bolunur,
                     bloklar arasina otomatik aciklama paragrafi girer.
@@KODTAM dosya@@ ayrica kullanildiginda her satir bir kez gomulur (kapsam).
@@CIKTI ad@@       : 'python ad.py' komutu + out/ad.txt ciktisi (term).
@@KAYNAK yol a b@@ : kaynak dosyanin a..b satirlari (python bloku)."""
import os
import re
import sys

B = "C:/Users/merty/AppData/Local/Temp/b72"
PARTS = os.path.join(B, "parts")
OUT = os.path.join(B, "out")
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_72.md"
KOD_MAX = 40

kullanilan = {}   # dosya -> satir sayisi kapsami
uyari = []


def oku(p):
    with open(p, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n").split("\n")


def tanim_aciklama(parca):
    adlar = []
    for l in parca:
        m = re.match(r"(def|class) (\w+)", l)
        if m:
            adlar.append("`%s`" % m.group(2))
    if adlar:
        return ("Aşağıdaki parça %s tanımlarını içerir; önceki parçada "
                "gelen değişkenler bu tanımlarda kullanılır." %
                ", ".join(adlar))
    return ("Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan "
            "değişkenleri ve modelleri kullanarak işi tamamlar.")


def kod_blogu(satirlar):
    satirlar = [s.rstrip() for s in satirlar]
    while satirlar and satirlar[-1] == "":
        satirlar.pop()
    for s in satirlar:
        if len(s) > 70:
            uyari.append("KOD >70: %d" % len(s))
    return "```python\n" + "\n".join(satirlar) + "\n```\n"


def kodtam(ad):
    yol = os.path.join(B, ad)
    L = oku(yol)
    if L and L[-1] == "":
        L = L[:-1]
    n = len(L)
    parcalar = []
    bas = 0
    while bas < n:
        son = min(bas + KOD_MAX, n)
        if son < n:
            kes = None
            for i in range(son, bas + 15, -1):
                if L[i - 1].strip() == "":
                    kes = i
                    break
            son = kes if kes else son
        parcalar.append(L[bas:son])
        bas = son
    kullanilan[ad] = n
    cikti = []
    for k, p in enumerate(parcalar):
        # bos satirlari parca basinda/sonunda at
        while p and p[0].strip() == "":
            p = p[1:]
        if k > 0:
            cikti.append(tanim_aciklama(p) + "\n")
        cikti.append(kod_blogu(p))
    return "\n".join(cikti)


def cikti(ad):
    yol = os.path.join(OUT, ad + ".txt")
    satirlar = [s.rstrip() for s in oku(yol)]
    while satirlar and satirlar[-1] == "":
        satirlar.pop()
    for s in satirlar:
        if len(s) > 74:
            uyari.append("TERM >74: %s" % s[:40])
    return ("```term\n$ python %s.py\n" % ad + "\n".join(satirlar) +
            "\n```\n")


def kaynak(yol, a, b):
    L = oku(os.path.join(B, yol))
    parca = []
    for l in L[int(a) - 1:int(b)]:
        if len(l) > 70 and "_standard_normal(" in l:
            k = l.index("device=")
            parca.append(l[:k].rstrip())
            parca.append(" " * (len(l) - len(l.lstrip()) + 23) + l[k:])
        elif len(l) > 70 and ") -> " in l:
            k = l.index(") -> ")
            parca.append(l[:k])
            parca.append(" " * 12 + l[k:])
        else:
            parca.append(l)
    kullanilan[yol] = (int(a), int(b))
    return kod_blogu(parca)


def main():
    metin = ""
    for f in sorted(os.listdir(PARTS)):
        if f.endswith(".md"):
            metin += open(os.path.join(PARTS, f), encoding="utf-8").read()
            metin += "\n"
    satirlar = metin.split("\n")
    cikis = []
    for l in satirlar:
        m = re.match(r"^@@KODTAM (\S+)@@$", l.strip())
        if m:
            cikis.append(kodtam(m.group(1)))
            continue
        m = re.match(r"^@@CIKTI (\S+)@@$", l.strip())
        if m:
            cikis.append(cikti(m.group(1)))
            continue
        m = re.match(r"^@@KAYNAK (\S+) (\d+) (\d+)@@$", l.strip())
        if m:
            cikis.append(kaynak(m.group(1), m.group(2), m.group(3)))
            continue
        cikis.append(l)
    cikti_metin = "\n".join(cikis)
    cikti_metin = re.sub(r"\n{3,}", "\n\n", cikti_metin).rstrip() + "\n"
    with open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(cikti_metin)
    print("yazildi:", HEDEF, "satir:", cikti_metin.count("\n"))
    print("kod kapsami:", kullanilan)
    print("uyari sayisi:", len(uyari))
    for u in uyari[:20]:
        print("  ", u)


if __name__ == "__main__":
    main()
