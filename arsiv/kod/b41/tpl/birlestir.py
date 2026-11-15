# -*- coding: utf-8 -*-
"""Bölüm 41 şablonunu birleştirir.

Yer tutucular:
  [[KOD dosya.py k]]   dosyanın k. bloğu (#@@ işaretçileri arası)
  [[KOD dosya.py]]     dosyanın tamamı (işaretçi yoksa)
  [[CIKTI dosya.txt]]             çıktı (term bloğu)
  [[CIKTI dosya.txt | komut args]] önce "$ komut args", sonra çıktı
Kodlar gerçek betiklerden okunur; elle kopyalanmaz.
"""
import os
import re
import sys

TMP = os.path.dirname(os.path.abspath(__file__))
ANA = os.path.dirname(TMP)
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_41.md"
PARCALAR = ["p1.md", "p2.md", "p3.md", "p4.md", "p4b.md",
            "p5.md", "p6.md"]
DOSYA_DIZIN = {
    ".py": ANA,
    ".txt": ANA,
}


def oku(ad):
    with open(os.path.join(ANA, ad), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def bloklar(kaynak):
    satirlar = kaynak.split("\n")
    bl, cur = [], []
    for s in satirlar:
        if s == "#@@":
            bl.append(cur)
            cur = []
        else:
            cur.append(s)
    bl.append(cur)
    out = []
    for b in bl:
        while b and b[0].strip() == "":
            b.pop(0)
        while b and b[-1].strip() == "":
            b.pop()
        out.append("\n".join(b))
    return out


def kod_yer(m):
    ad = m.group(1)
    k = m.group(2)
    kaynak = oku(ad)
    if k is None:
        if "\n#@@" in kaynak or kaynak.startswith("#@@"):
            raise SystemExit("işaretçili dosyada blok numarası gerek: "
                             + ad)
        icerik = kaynak.rstrip("\n")
    else:
        bl = bloklar(kaynak)
        if "-" in k:
            a, b = [int(x) for x in k.split("-")]
        else:
            a = b = int(k)
        if a < 1 or b > len(bl) or a > b:
            raise SystemExit("blok yok: %s %s (toplam %d)"
                             % (ad, k, len(bl)))
        icerik = "\n\n".join(bl[a - 1:b])
    return "```python\n" + icerik + "\n```"


def cikti_yer(m):
    govde = m.group(1).strip()
    komut = m.group(2)
    icerik = oku(govde).rstrip("\n")
    satir = []
    if komut:
        satir.append("$ " + komut.strip())
    satir.append(icerik)
    return "```term\n" + "\n".join(satir) + "\n```"


def main():
    metin = []
    for p in PARCALAR:
        yol = os.path.join(TMP, p)
        if os.path.exists(yol):
            with open(yol, encoding="utf-8") as f:
                metin.append(f.read().rstrip("\n") + "\n")
    tam = "\n".join(metin)
    tam = re.sub(r"\[\[KOD (\S+?)(?: (\d+(?:-\d+)?))?\]\]", kod_yer, tam)
    tam = re.sub(r"\[\[CIKTI (\S+?)(?: \| ([^\]]+))?\]\]", cikti_yer,
                 tam)
    kalan = re.findall(r"\[\[[^\]]*\]\]", tam)
    if kalan:
        raise SystemExit("çözülmeyen yer tutucu: %s" % kalan[:5])
    with open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(tam)
    print("yazıldı:", HEDEF, len(tam.split("\n")), "satır")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "bloklar":
        for ad in sys.argv[2:]:
            for i, b in enumerate(bloklar(oku(ad)), 1):
                print(ad, i, len(b.split("\n")))
    else:
        main()
