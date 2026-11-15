# -*- coding: utf-8 -*-
"""md parcalarini birlestirir; {{KOD:..}}, {{CIKTI:..}}, {{TABLO:..}}
yer tutucularini dosya iceriginin birebir kopyasiyla degistirir."""
import os
import re
import sys

B = "C:/Users/merty/AppData/Local/Temp/b43"
PARCALAR = ["md/a.md", "md/b.md", "md/b2.md", "md/c.md"]
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_43.md"

DIL = {".c": "c", ".h": "c", ".ld": "c", ".py": "python"}


def oku(yol):
    with open(os.path.join(B, yol), encoding="utf-8") as f:
        return f.read().rstrip("\n").split("\n")


def kod_satirlari(spec):
    parca = spec.split("|")
    yol = parca[0].strip()
    satirlar = oku(yol)
    if len(parca) > 1 and parca[1].strip():
        aralik = parca[1].strip()
        a, _, b = aralik.partition("-")
        a = int(a)
        b = int(b) if b else len(satirlar)
        satirlar = satirlar[a - 1:b]
    dil = DIL.get(os.path.splitext(yol)[1].lower(), "")
    return dil, satirlar


KOD_RE = re.compile(r"^\{\{KOD:([^}]+)\}\}\s*$")
CIKTI_RE = re.compile(r"^\{\{CIKTI:([^}]+)\}\}\s*$")
TABLO_RE = re.compile(r"^\{\{TABLO:([^}]+)\}\}\s*$")


def birlestir():
    metin = []
    for p in PARCALAR:
        metin.append("\n".join(oku(p)))
    satirlar = "\n\n".join(metin).split("\n")
    cikti = []
    i = 0
    n = len(satirlar)
    while i < n:
        s = satirlar[i]
        if s.startswith("```"):
            # kapanisi bul
            j = i + 1
            while j < n and not satirlar[j].startswith("```"):
                j += 1
            govde = satirlar[i + 1:j]
            dil_md = s[3:].strip()
            if len(govde) == 1 and KOD_RE.match(govde[0]):
                spec = KOD_RE.match(govde[0]).group(1)
                dil, kod = kod_satirlari(spec)
                cikti.append("```" + (dil or dil_md))
                cikti.extend(kod)
                cikti.append("```")
            else:
                cikti.append(s)
                for g in govde:
                    m = CIKTI_RE.match(g)
                    if m:
                        cikti.extend(oku(m.group(1)))
                        continue
                    m = KOD_RE.match(g)
                    if m:
                        raise SystemExit("ic ice KOD: " + g)
                    cikti.append(g)
                if j < n:
                    cikti.append(satirlar[j])
            i = j + 1
            continue
        m = KOD_RE.match(s)
        if m:
            dil, kod = kod_satirlari(m.group(1))
            cikti.append("```" + dil)
            cikti.extend(kod)
            cikti.append("```")
        else:
            m = TABLO_RE.match(s)
            if m:
                cikti.extend(oku(m.group(1)))
            else:
                if CIKTI_RE.match(s):
                    raise SystemExit("fence disinda CIKTI: " + s)
                cikti.append(s)
        i += 1
    sonuc = "\n".join(cikti)
    if "{{" in sonuc:
        raise SystemExit("cozulmemis yer tutucu var")
    with open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(sonuc.rstrip("\n") + "\n")
    print("yazildi:", HEDEF, "satir:", sonuc.count("\n") + 1)


if __name__ == "__main__":
    birlestir()
