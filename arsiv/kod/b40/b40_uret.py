# -*- coding: utf-8 -*-
"""Bolum 40 birlestirici: sablon parcalarini gercek kod ve ciktilarla
birlestirir, bolumler/bolum_40.md dosyasini yazar ve genislikleri denetler.

Yer tutucular:
  {{KOD dosya a b}}            dosyanin a..b satirlari (kod blogu)
  {{KESIT yol 1-7,26-32,...}}  kaynak dosyadan secili satirlar
  {{TERM komut ;; +devam | cikti}}  terminal blogu: komutlar + cikti dosyasi
"""
import io
import os
import re
import sys

TEMP = "C:/Users/merty/AppData/Local/Temp/b40"
PROJE = "D:/Mevcut Projeler/Kitap"
PARCALAR = ["p1.md", "p2.md", "p3.md"]
HEDEF = os.path.join(PROJE, "bolumler", "bolum_40.md")
MAX_KOD, MAX_TERM, MAX_BLOK = 70, 74, 40
hatalar = []


def oku(yol):
    with io.open(yol, encoding="utf-8") as f:
        return f.read()


def dil(dosya):
    return "c" if dosya.endswith((".c", ".h")) else "python"


def kod_blogu(dosya, satirlar, ad):
    if len(satirlar) > MAX_BLOK:
        hatalar.append("%s: blok %d satir (>%d)" % (ad, len(satirlar),
                                                   MAX_BLOK))
    for i, s in enumerate(satirlar, 1):
        if len(s) > MAX_KOD:
            hatalar.append("%s satir %d: %d karakter" % (ad, i, len(s)))
    return "```%s\n%s\n```" % (dil(dosya), "\n".join(satirlar))


def kod(m):
    dosya, a, b = m.group(1), int(m.group(2)), int(m.group(3))
    satirlar = oku(os.path.join(TEMP, dosya)).split("\n")
    if satirlar and satirlar[-1] == "":
        satirlar = satirlar[:-1]
    secim = satirlar[a - 1:b]
    if len(secim) != b - a + 1:
        hatalar.append("%s: aralik %d-%d disari" % (dosya, a, b))
    return kod_blogu(dosya, secim, "%s %d-%d" % (dosya, a, b))


def kesit(m):
    yol, spec = m.group(1), m.group(2)
    satirlar = oku(yol).split("\n")
    cikti, onceki_son = [], None
    for aralik in spec.split(","):
        a, b = [int(x) for x in aralik.split("-")]
        if onceki_son is not None and a != onceki_son + 1:
            cikti.append("    # ... (kısaltıldı)")
        cikti.extend(satirlar[a - 1:b])
        onceki_son = b
    return kod_blogu("x.py", cikti, "KESIT")


def terminal(m):
    govde = m.group(1)
    if " | " in govde:
        komut_kismi, cikti_adi = govde.rsplit(" | ", 1)
    else:
        komut_kismi, cikti_adi = govde, None
    satirlar = []
    for seg in komut_kismi.split(" ;; "):
        seg = seg.strip()
        if not seg:
            continue
        if seg.startswith("+"):
            # devam satiri: onceki satira ek; girintili yaz
            satirlar.append("    " + seg[1:].lstrip().rstrip(" \\"))
            if seg.rstrip().endswith("\\"):
                satirlar[-1] += " \\"
        else:
            kuyruk_ters = seg.endswith("\\")
            temiz = seg.rstrip(" \\").rstrip()
            satirlar.append("$ " + temiz + (" \\" if kuyruk_ters else ""))
    if cikti_adi:
        yol = os.path.join(TEMP, "cikti", cikti_adi + ".txt")
        cikti = oku(yol).rstrip("\n").split("\n")
        satirlar.extend(cikti)
    for i, s in enumerate(satirlar, 1):
        if len(s) > MAX_TERM:
            hatalar.append("TERM %s satir %d: %d karakter"
                           % (cikti_adi, i, len(s)))
    return "```term\n%s\n```" % "\n".join(satirlar)


def main():
    metin = "\n\n".join(oku(os.path.join(TEMP, "sablon", p)).rstrip("\n")
                        for p in PARCALAR) + "\n"
    metin = re.sub(r"\{\{KOD (\S+) (\d+) (\d+)\}\}", kod, metin)
    metin = re.sub(r"\{\{KESIT (\S+) (\S+)\}\}", kesit, metin)
    metin = re.sub(r"\{\{TERM (.+?)\}\}", terminal, metin)
    kalan = re.findall(r"\{\{[^}]*\}\}", metin)
    if kalan:
        hatalar.append("cozulmemis yer tutucu: %s" % kalan[:3])
    with io.open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin)
    print("yazildi:", HEDEF, "satir:", metin.count("\n"),
          "bayt:", len(metin.encode("utf-8")))
    print("hata sayisi:", len(hatalar))
    for h in hatalar[:60]:
        print("  -", h)
    return 1 if hatalar else 0


if __name__ == "__main__":
    sys.exit(main())
