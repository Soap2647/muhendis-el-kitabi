# -*- coding: utf-8 -*-
"""Bölüm 65 birleştiricisi.

md_kaynak/p01.md ... p07.md dosyalarındaki yönergeleri, arşivdeki
kaynak betiklerle ve çıktı dosyalarıyla değiştirip
bolumler/bolum_65.md dosyasını üretir.

Yönergeler (satır başında):
  @@KOD dosya.py            Betiğin TAM metnini ```python bloklarına böler.
  @@CIKTI cikti.txt komut   Çıktıyı ```term bloğu olarak ekler: "$ python komut".
Kural: her betik tam olarak gömülür; satır genişliği kod için ≤70,
terminal için ≤74 karakter (denetlenir).
"""
import os
import re
import sys

KOK = os.path.dirname(os.path.abspath(__file__))
KAYNAK = os.path.join(KOK, "md_kaynak")
HEDEF = os.path.join(KOK, "..", "..", "..", "bolumler", "bolum_65.md")
PARCALAR = ["p01.md", "p02.md", "p03.md", "p04.md", "p05.md",
            "p06.md", "p07.md"]
ASAMA = 40          # bir kod bloğunda en çok satır (kabaca)


def oku(ad):
    with open(os.path.join(KOK, ad), encoding="utf-8") as f:
        return f.read().rstrip("\n").split("\n")


def kod_blok(ad):
    satirlar = oku(ad)
    for i, l in enumerate(satirlar, 1):
        if len(l) > 70:
            sys.exit("%s:%d kod satırı 70 karakteri aşıyor" % (ad, i))
        if "\t" in l:
            sys.exit("%s:%d sekme karakteri" % (ad, i))
    # Parçalara böl: en yakın boş satırdan kır.
    parcalar, bas = [], 0
    while bas < len(satirlar):
        son = min(bas + ASAMA, len(satirlar))
        if son < len(satirlar):
            k = son
            while k > bas and satirlar[k - 1].strip() != "":
                k -= 1
            if k > bas:
                son = k
        parcalar.append((bas, son))
        bas = son
    cikti = []
    for n, (a, b) in enumerate(parcalar):
        if n > 0:
            cikti.append("")
            cikti.append("Programın devamı (satır %d–%d):"
                         % (a + 1, b))
            cikti.append("")
        cikti.append("```python")
        cikti.extend(satirlar[a:b])
        cikti.append("```")
    return cikti


def cikti_blok(ad, komut):
    satirlar = oku(ad)
    for i, l in enumerate(satirlar, 1):
        if len(l) > 74:
            sys.exit("%s:%d terminal satırı 74 karakteri aşıyor" % (ad, i))
    return (["```term", "$ python " + komut] + satirlar + ["```"])


def ayrıştır(satir):
    m = re.match(r"^@@(KOD|CIKTI)\s+(.+)$", satir)
    if not m:
        return None
    return m.group(1), m.group(2).split()


def main():
    cikti_satirlari = []
    for p in PARCALAR:
        with open(os.path.join(KAYNAK, p), encoding="utf-8") as f:
            for satir in f.read().split("\n"):
                y = ayrıştır(satir)
                if y is None:
                    cikti_satirlari.append(satir)
                    continue
                tur, arg = y
                if tur == "KOD":
                    cikti_satirlari.extend(kod_blok(arg[0]))
                else:
                    cikti_satirlari.extend(cikti_blok(arg[0], arg[1]))
    metin = "\n".join(cikti_satirlari)
    metin = re.sub(r"\n{3,}", "\n\n", metin)
    with open(HEDEF, "w", encoding="utf-8") as f:
        f.write(metin.rstrip("\n") + "\n")
    print("yazıldı:", os.path.normpath(HEDEF),
          "satır:", metin.count("\n") + 1)


if __name__ == "__main__":
    main()
