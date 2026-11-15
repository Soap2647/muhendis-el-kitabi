# -*- coding: utf-8 -*-
"""Bolum 15 taslagini derler. @@CODE isaretleri dosyalardan kod bloklari
uretir; @@TERM isaretleri, spec dosyasindaki komutlari gercekten calistirip
ciktilarini terminal blogu olarak yazar."""
import os, re, subprocess, sys

B15 = "C:/Users/merty/AppData/Local/Temp/b15"
KOD = B15 + "/kod"
WSL_KOD = "/mnt/c/Users/merty/AppData/Local/Temp/b15/kod"
TERM_DIR = os.path.join(B15, "md", "term")
PARTS = ["p%02d.md" % i for i in range(1, 40)]
hatalar = []


def dil(p):
    return {".c": "c", ".py": "python", ".h": "c"}.get(
        os.path.splitext(p)[1], "")


def kod_blogu(spec):
    yol, _, aralik = spec.partition(":")
    tam = os.path.join(B15, yol)
    with open(tam, encoding="utf-8") as f:
        satirlar = f.read().rstrip("\n").split("\n")
    if aralik:
        a, b = aralik.split("-")
        satirlar = satirlar[int(a) - 1:int(b)]
    for i, s in enumerate(satirlar, 1):
        if len(s) > 70:
            hatalar.append("KOD >70: %s satir %d (%d)" % (spec, i, len(s)))
    return "```" + dil(yol) + "\n" + "\n".join(satirlar) + "\n```"


def calistir_wsl(komut):
    betik = os.path.join(B15, "md", "tmp_run.sh")
    with open(betik, "w", encoding="utf-8", newline="\n") as f:
        f.write("#!/bin/bash\ncd " + WSL_KOD + "\n" + komut + "\n")
    r = subprocess.run(
        ["wsl", "bash", "-c",
         "bash /mnt/c/Users/merty/AppData/Local/Temp/b15/md/tmp_run.sh"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return r.stdout.decode("utf-8", "replace")


def calistir_py(komut):
    argumanlar = komut.split()
    r = subprocess.run(argumanlar, cwd=KOD,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.stdout.decode("utf-8", "replace")


def satirlara(metin):
    metin = metin.rstrip("\n")
    return metin.split("\n") if metin.strip() else []


def term_blogu(ad):
    satirlar = []
    with open(os.path.join(TERM_DIR, ad + ".spec"), encoding="utf-8") as f:
        for raw in f:
            raw = raw.rstrip("\n")
            if not raw.strip():
                continue
            goster, _, calis = raw.partition(" ||| ")
            goster = goster.strip()
            calis = calis.strip()
            satirlar.append("$ " + goster)
            if calis.startswith("wsl:"):
                cikti = calistir_wsl(calis[4:].strip())
            else:
                cikti = calistir_py(calis[3:].strip())
            for s in satirlara(cikti):
                satirlar.append(s.rstrip())
    for s in satirlar:
        if len(s) > 74:
            hatalar.append("TERM >74: %s: %s" % (ad, s))
    return "```term\n" + "\n".join(satirlar) + "\n```"


def derle():
    metin = []
    for p in PARTS:
        yol = os.path.join(B15, "md", p)
        if os.path.exists(yol):
            with open(yol, encoding="utf-8") as f:
                metin.append(f.read())
    md = "\n".join(metin)
    md = re.sub(r"@@CODE (\S+)@@", lambda m: kod_blogu(m.group(1)), md)
    md = re.sub(r"@@TERM (\S+)@@", lambda m: term_blogu(m.group(1)), md)
    return md


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "term":
        print(term_blogu(sys.argv[2]))
    else:
        md = derle()
        cikis = os.path.join(B15, "md", "bolum_15_uretilen.md")
        with open(cikis, "w", encoding="utf-8") as f:
            f.write(md)
        print("yazildi:", cikis, "satir:", md.count("\n"))
    for h in hatalar:
        print("UYARI", h)
