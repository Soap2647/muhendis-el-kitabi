# -*- coding: utf-8 -*-
"""Bölüm 63 birleştirici: md/a.md içindeki belirteçleri gerçek kod ve
çıktı dosyalarıyla değiştirip bolumler/bolum_63.md üretir.

Belirteçler:
  @@KOD dosya a b@@          Temp\\b63\\dosya.py satır a..b (python bloğu)
  @@SKL dosya a b@@          scikit-learn 1.8.0 kesiti (python bloğu)
  @@CIKTI dosya.py cikti.txt $ komutu + çıktı (term bloğu)
  @@SEKIL dosya.png N aciklama   ![Şekil 63.N: açıklama](gorseller/dosya.png)
"""
import io
import os
import re

TEMP = r"C:\Users\merty\AppData\Local\Temp\b63"
SKL = (r"C:\Users\merty\AppData\Local\Programs\Python\Python312"
       r"\Lib\site-packages\sklearn\neural_network")
KOK = r"D:\Mevcut Projeler\Kitap"
MD = os.path.join(TEMP, "md", "a.md")
CIKTI_HEDEF = os.path.join(KOK, "bolumler", "bolum_63.md")

hatalar = []


def oku(yol):
    with io.open(yol, encoding="utf-8") as f:
        return f.read()


def satirlar(yol, a, b):
    L = oku(yol).split("\n")
    parca = L[a - 1:b]
    while parca and parca[-1].strip() == "":
        parca.pop()
    return parca


def kod_blok(dil, satir_listesi, etiket):
    for i, l in enumerate(satir_listesi, 1):
        if len(l) > 70:
            hatalar.append("%s satır %d: %d karakter" % (etiket, i, len(l)))
    if len(satir_listesi) > 40:
        hatalar.append("%s: %d satır (>40)" % (etiket, len(satir_listesi)))
    return "```%s\n%s\n```" % (dil, "\n".join(satir_listesi))


def kod(m):
    dosya, a, b = m.group(1), int(m.group(2)), int(m.group(3))
    yol = os.path.join(TEMP, dosya)
    return kod_blok("python", satirlar(yol, a, b), "%s %d-%d" % (dosya, a, b))


def sar(l, genislik=70):
    """Uzun satırı boşluktan böler; devam satırı 4 boşluk girintili."""
    if len(l) <= genislik:
        return [l]
    kes = l.rfind(" ", 0, genislik)
    if kes <= 8:
        return [l]
    return [l[:kes]] + sar("    " + l[kes + 1:], genislik)


def skl(m):
    dosya, a, b = m.group(1), int(m.group(2)), int(m.group(3))
    yol = os.path.join(SKL, dosya)
    parca = []
    for l in satirlar(yol, a, b):
        parca.extend(sar(l))
    return kod_blok("python", parca, "sklearn %s" % dosya)


def cikti(m):
    script, out = m.group(1), m.group(2)
    L = oku(os.path.join(TEMP, out)).split("\n")
    while L and L[-1].strip() == "":
        L.pop()
    for i, l in enumerate(L, 1):
        if len(l) > 74:
            hatalar.append("terminal %s satır %d: %d karakter"
                           % (out, i, len(l)))
    return "```term\n$ python %s\n%s\n```" % (script, "\n".join(L))


def sekil(m):
    dosya, no, aciklama = m.group(1), m.group(2), m.group(3)
    return "![Şekil %s: %s](gorseller/%s)" % (no, aciklama, dosya)


def main():
    s = oku(MD)
    s = re.sub(r"@@KOD (\S+) (\d+) (\d+)@@", kod, s)
    s = re.sub(r"@@SKL (\S+) (\d+) (\d+)@@", skl, s)
    s = re.sub(r"@@CIKTI (\S+) (\S+)@@", cikti, s)
    s = re.sub(r"@@SEKIL (\S+) (63\.\d+) (.+?)@@", sekil, s)
    kalan = re.findall(r"@@\w+", s)
    if kalan:
        hatalar.append("işlenmemiş belirteç: %s" % kalan[:5])
    # Paragrafların arasında boş satır: üst üste gelen kod bloklarını ayır
    s = re.sub(r"```\n```python", "```\n\n```python", s)
    io.open(CIKTI_HEDEF, "w", encoding="utf-8", newline="\n").write(s)
    print("yazıldı:", CIKTI_HEDEF, "satır:", s.count("\n"))
    if hatalar:
        print("UYARILAR:")
        for h in hatalar:
            print("  -", h)
    else:
        print("sıfır uyarı")


if __name__ == "__main__":
    main()
