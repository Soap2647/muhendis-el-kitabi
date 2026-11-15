# -*- coding: utf-8 -*-
"""Bolum 20 sablonunu gercek dosya icerikleriyle doldurur.

[[KOD dosya ilk son dil]]  -> kod blogu (dosyanin ilk..son satirlari)
[[TERM ad]]                -> terminal blogu (cikti/ad.txt)
[[TABLO bellek|sanal]]     -> engine/veri CSV'sinden markdown tablosu
Cikti: bolumler/bolum_20.md  (sablon sabit, yalnizca gomme yapilir)
"""
import csv
import os
import re
import sys

BAS = r"C:\Users\merty\AppData\Local\Temp\b20"
KOK = r"D:\Mevcut Projeler\Kitap"
SABLON = os.path.join(BAS, "sablon_20.md")
CIKTI = os.path.join(KOK, "bolumler", "bolum_20.md")
HEDEF_KOD, HEDEF_TERM = 70, 74

hatalar = []


def dosya_satirlari(yol):
    tam = os.path.join(BAS, yol) if "/" not in yol else \
        os.path.join(BAS, *yol.split("/"))
    with open(tam, encoding="utf-8") as f:
        return f.read().split("\n")


def kod(m):
    dosya, ilk, son, dil = m.group(1), m.group(2), m.group(3), m.group(4)
    satirlar = dosya_satirlari(dosya)
    if son is None:
        parca = satirlar[:-1] if satirlar[-1] == "" else satirlar
    else:
        a, b = int(ilk), int(son)
        if b > len(satirlar):
            hatalar.append("aralik asildi: %s %d-%d (dosya %d)"
                           % (dosya, a, b, len(satirlar)))
            b = len(satirlar)
        parca = satirlar[a - 1:b]
    while parca and parca[-1].strip() == "":
        parca = parca[:-1]
    for no, s in enumerate(parca, 1):
        if len(s) > HEDEF_KOD:
            hatalar.append("kod >70: %s satir %d (%d)" % (dosya, no, len(s)))
    return "```%s\n%s\n```" % (dil, "\n".join(parca))


def kaydir(satir, komut):
    """74 karakteri asan satiri kelime sinirindan boler.
    Komut satirinda devam '\' ile isaretlenir; devam satirlari
    4 bosluk girintilidir. Icerik degismez, yalnizca sayfa duzeni."""
    sonuc = []
    kalan = satir
    ilk = True
    while len(kalan) > HEDEF_TERM:
        kes = kalan.rfind(" ", 0, HEDEF_TERM - 2)
        if kes <= 0:
            break
        if ilk and komut:
            sonuc.append(kalan[:kes] + " \\")
        else:
            sonuc.append(kalan[:kes])
        kalan = "    " + kalan[kes + 1:]
        ilk = False
    sonuc.append(kalan)
    return sonuc


def terminal(m):
    ad = m.group(1)
    yol = os.path.join(BAS, "cikti", ad + ".txt")
    with open(yol, encoding="utf-8") as f:
        metin = f.read().rstrip("\n")
    cikti = []
    for s in metin.split("\n"):
        cikti.extend(kaydir(s, s.startswith("$ ")))
    for no, s in enumerate(cikti, 1):
        if len(s) > HEDEF_TERM:
            hatalar.append("terminal >74: %s satir %d (%d)"
                           % (ad, no, len(s)))
    return "```term\n%s\n```" % "\n".join(cikti)


def tablo(m):
    ad = m.group(1)
    yol = os.path.join(KOK, "engine", "veri", "b20_%s_olcum.csv" % ad)
    with open(yol, encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    if ad == "bellek":
        satir = ["| n | `__dict__` (bayt/nesne) | `__slots__` (bayt/nesne) |",
                 "|---:|---:|---:|"]
        for r in satirlar:
            satir.append("| %s | %s | %s |" % (r["n"], r["dict_bayt"],
                                             r["slots_bayt"]))
        return "\n".join(satir)
    # sanal: n, yontem, dagitim, ms
    tbl = {}
    for r in satirlar:
        tbl.setdefault(int(r["n"]), {})[(r["yontem"], r["dagitim"])] = \
            float(r["ms"])
    satir = ["| n | Etiketli (dal), tek tür | Sanal, tek tür | "
             "Etiketli (dal), karışık | Sanal, karışık |",
             "|---:|---:|---:|---:|---:|"]
    for n in sorted(tbl):
        d = tbl[n]
        satir.append("| %d | %.3f | %.3f | %.3f | %.3f |" % (
            n, d[("etiketli", "tek_tur")], d[("sanal", "tek_tur")],
            d[("etiketli", "karisik")], d[("sanal", "karisik")]))
    return "\n".join(satir)


def main():
    with open(SABLON, encoding="utf-8") as f:
        metin = f.read()
    metin = re.sub(r"\[\[KOD ([^\s\]]+) (\d+) (\d+) (\w+)\]\]", kod, metin)
    metin = re.sub(r"\[\[TERM (\w+)\]\]", terminal, metin)
    metin = re.sub(r"\[\[TABLO (\w+)\]\]", tablo, metin)
    kalan = re.findall(r"\[\[[^\]]*\]\]", metin)
    if kalan:
        hatalar.append("cozulmemis isaretci: %s" % kalan[:5])
    # kod dosyasi gorunumlu tek satir kisaltmalar icin ek denetim
    if "\t" in metin:
        hatalar.append("sekme karakteri var")
    with open(CIKTI, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin.rstrip("\n") + "\n")
    print("yazildi:", CIKTI, "satir:", metin.count("\n"))
    if hatalar:
        print("HATALAR:")
        for h in hatalar:
            print("  -", h)
        sys.exit(1)
    print("denetim temiz")


if __name__ == "__main__":
    main()
