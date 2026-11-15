# -*- coding: utf-8 -*-
"""Sablonlardaki {{KOD:...}} yer tutucularini gercek kod parcalariyla degistirir.

{{KOD:kod/dosya.py}}                  tum dosya
{{KOD:kod/dosya.py@BAS@SON}}          BAS iceren satirdan, SON iceren satirdan
                                      once biten kesit (BAS/SON bos olabilir)
kod/ -> scratch/kod_b21/, kesit/ -> scratch/md_b21/kesit/
"""
import os, re, sys
S = "C:/Users/merty/AppData/Local/Temp/claude/D--Mevcut-Projeler-Kitap/cb731bd7-a681-4dce-86ad-586fb39601bd/scratchpad"
KOK = {"kod": os.path.join(S, "kod_b21"), "kesit": os.path.join(S, "md_b21", "kesit")}
DIL = {".py": "python", ".c": "c", ".cpp": "cpp"}
UYARI = []

def kesit_al(yol, bas, son):
    with open(yol, encoding="utf-8") as h:
        ls = h.read().split("\n")
    if ls and ls[0].startswith("# -*- coding"):
        ls = ls[1:]
    bi = 0
    if bas:
        bi = next(i for i, l in enumerate(ls) if bas in l)
    si = len(ls)
    if son:
        si = next(i for i in range(bi + 1, len(ls)) if son in ls[i])
    parca = ls[bi:si]
    while parca and parca[0].strip() == "":
        parca = parca[1:]
    while parca and parca[-1].strip() == "":
        parca = parca[:-1]
    return parca

def blok(m):
    arg = m.group(1)
    parcalar = arg.split("@")
    yol = parcalar[0]
    kok, rel = yol.split("/", 1)
    tam = os.path.join(KOK[kok], *rel.split("/"))
    bas = parcalar[1] if len(parcalar) > 1 else ""
    son = parcalar[2] if len(parcalar) > 2 else ""
    satirlar = kesit_al(tam, bas, son)
    for i, l in enumerate(satirlar, 1):
        if len(l) > 70:
            UYARI.append("%s satir %d: %d karakter" % (yol, i, len(l)))
    if len(satirlar) > 40:
        UYARI.append("%s: blok %d satir" % (yol, len(satirlar)))
    dil = DIL.get(os.path.splitext(tam)[1], "text")
    return "```%s\n%s\n```" % (dil, "\n".join(satirlar))

def main(girdiler, cikti):
    metin = []
    for g in girdiler:
        with open(g, encoding="utf-8") as h:
            metin.append(h.read())
    tam = "\n\n".join(metin)
    tam = re.sub(r"\{\{KOD:([^}]+)\}\}", blok, tam)
    with open(cikti, "w", encoding="utf-8") as h:
        h.write(tam)
    print("yazildi:", cikti, "satir:", tam.count("\n"))
    for u in UYARI:
        print("UYARI:", u)

if __name__ == "__main__":
    main(sys.argv[2:], sys.argv[1])
