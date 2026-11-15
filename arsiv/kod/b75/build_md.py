# -*- coding: utf-8 -*-
"""Bolum 75 metnini birlestirir: @@KOD ve @@TERM yer tutucularini
gercek betik ve gunluk satirlariyla degistirir (kopyala-yapistir yok).

@@KOD | dosya | dil | baslangic_icerir | bitis_icerir (ya da EOF)
@@TERM | dosya | a | b | komut (b=0: sona kadar; komut bos olabilir)
"""
import sys, re, os
B = "C:/Users/merty/AppData/Local/Temp/b75/"
MCU = B + "mcu/"
DOS = {"ortak": B + "b75_ortak.py", "nicemleme": B + "b75_nicemleme.py",
       "aykiri": B + "b75_aykiri.py", "budama": B + "b75_budama.py",
       "damitma": B + "b75_damitma.py", "onnx": B + "b75_onnx.py",
       "olcum": B + "b75_olcum.py", "mimari": B + "b75_mimari.py",
       "ozet": B + "b75_ozet.py", "ornek": B + "ornek_dogrula.py",
       "gen": MCU + "gen_mcu.py", "cfile": MCU + "mlp_int8.c",
       "host": MCU + "test_host.c", "derle": MCU + "derle.sh", "goster": B + "b75_goster.py"}
uyari = []


def satirlar(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")


def kod(ad, dil, bas, bit):
    L = satirlar(DOS[ad])
    i = next(k for k, l in enumerate(L) if bas in l)
    if bit == "EOF":
        j = len(L)
        while j > i and L[j - 1].strip() == "":
            j -= 1
    else:
        j = next(k for k in range(i + 1, len(L)) if bit in L[k])
        while j > i and L[j - 1].strip() == "":
            j -= 1
    blk = L[i:j]
    for n, l in enumerate(blk):
        if len(l) > 70:
            uyari.append("KOD %s satir %d uzun (%d)" % (ad, i + n + 1, len(l)))
    if len(blk) > 42:
        uyari.append("KOD %s blok %d satir" % (ad, len(blk)))
    return "```%s\n%s\n```" % (dil, "\n".join(blk))


def term(path, a, b, komut):
    L = satirlar(path)
    b = len(L) if b == 0 else b
    cikti = L[a - 1:b]
    while cikti and cikti[-1].strip() == "":
        cikti.pop()
    sat = (["$ " + komut] if komut else []) + cikti
    for l in sat:
        if len(l) > 74:
            uyari.append("TERM %s uzun: %s" % (path, l[:40]))
    return "```term\n%s\n```" % "\n".join(sat)


def cevir(metin):
    def kod_r(m):
        p = [x.strip() for x in m.group(1).lstrip("| ").split("|")]
        return kod(p[0], p[1], p[2], p[3])

    def term_r(m):
        p = [x.strip() for x in m.group(1).lstrip("| ").split("|")]
        yol = p[0] if os.path.isabs(p[0]) else B + p[0]
        return term(yol, int(p[1]), int(p[2]),
                    p[3] if len(p) > 3 else "")
    metin = re.sub(r"^@@KOD (.+)$", kod_r, metin, flags=re.M)
    metin = re.sub(r"^@@TERM (.+)$", term_r, metin, flags=re.M)
    return metin


if __name__ == "__main__":
    parcalar = sys.argv[2:]
    out = sys.argv[1]
    metin = "\n\n".join(open(p, encoding="utf-8").read().strip("\n")
                        for p in parcalar) + "\n"
    metin = cevir(metin)
    with open(out, "w", encoding="utf-8") as f:
        f.write(metin)
    print("yazildi:", out, "satir:", metin.count("\n"))
    for u in uyari:
        print("UYARI:", u)
