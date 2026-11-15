# -*- coding: utf-8 -*-
"""Bölüm 69 md parçalarını birleştirir; @@KOD / @@CIKTI yer tutucularını açar."""
import glob, os, re
TMP = "C:/Users/merty/AppData/Local/Temp/b69"
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_69.md"
KOD_BOY = 40


def oku(ad):
    with open(os.path.join(TMP, ad), encoding="utf-8") as f:
        return [l.rstrip() for l in f.read().replace("\r\n", "\n").split("\n")]


def kodu_parcala(satirlar):
    while satirlar and not satirlar[-1]:
        satirlar = satirlar[:-1]
    segs, cur = [], []
    for l in satirlar:
        if l == "":
            segs.append(cur)
            cur = []
        else:
            cur.append(l)
    segs.append(cur)
    segs = [s + [""] for s in segs if s]
    parcalar, aktif = [], []
    for seg in segs:
        if len(seg) > KOD_BOY:
            if aktif:
                parcalar.append(aktif)
                aktif = []
            for k in range(0, len(seg), KOD_BOY):
                parcalar.append(seg[k:k + KOD_BOY])
            continue
        if len(aktif) + len(seg) > KOD_BOY and aktif:
            parcalar.append(aktif)
            aktif = []
        aktif = aktif + seg
    if aktif:
        parcalar.append(aktif)
    out = []
    for p in parcalar:
        while p and p[-1] == "":
            p = p[:-1]
        out.append("```python\n" + "\n".join(p) + "\n```")
    return "\n\n".join(out)


def cikti_blok(ad):
    satirlar = oku(ad)
    while satirlar and not satirlar[-1]:
        satirlar = satirlar[:-1]
    betik = re.sub(r"^out_", "", ad)
    betik = re.sub(r"\.txt$", ".py", betik)
    kom = "$ python " + betik
    return "```term\n" + kom + "\n" + "\n".join(satirlar) + "\n```"


def main():
    parcalar = sorted(glob.glob(os.path.join(TMP, "md", "p0*.md")))
    metin = "\n\n".join(open(p, encoding="utf-8").read().replace("\r\n", "\n")
                        .strip("\n") for p in parcalar) + "\n"
    metin = re.sub(r"@@KOD (\S+?)@@", lambda m: kodu_parcala(oku(m.group(1))),
                   metin)
    metin = re.sub(r"@@CIKTI (\S+?)@@", lambda m: cikti_blok(m.group(1)),
                   metin)
    metin = re.sub(r"\n{3,}", "\n\n", metin)
    assert "@@" not in metin, "açılmamış yer tutucu"
    with open(HEDEF, "w", encoding="utf-8") as f:
        f.write(metin)
    print("yazıldı:", HEDEF, len(metin.split("\n")), "satır")


if __name__ == "__main__":
    main()
