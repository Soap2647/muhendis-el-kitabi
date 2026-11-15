# -*- coding: utf-8 -*-
# Bolum 48 md birlestirici: parts/p1..p6 + kod/cikti gomme -> bolumler/bolum_48.md
import glob
import os
import re

T = r"C:\Users\merty\AppData\Local\Temp\b48"
ROOT = r"D:\Mevcut Projeler\Kitap"
PARTS = os.path.join(T, "parts")
KAYNAK = os.path.join(T, "kaynak", "_linalg_v2.3.5_norm.py")


def oku(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def kod_blok(dosya, aralik=None):
    satirlar = oku(os.path.join(T, dosya)).rstrip("\n").split("\n")
    if aralik:
        a, b = aralik
        satirlar = satirlar[a - 1:b]
    return "```python\n" + "\n".join(satirlar) + "\n```"


def cikti_blok(prog, out):
    icerik = oku(os.path.join(T, out)).rstrip("\n")
    return "```term\n$ python " + prog + "\n" + icerik + "\n```"


def kaynak_kesit():
    satirlar = oku(KAYNAK).split("\n")
    # 1-indeksli: 383 = def solve; 456 = gövde başı
    bas = 383
    govde = 456
    son = None
    for i in range(govde, len(satirlar) + 1):
        if "return wrap(r.astype(result_t, copy=False))" in satirlar[i - 1]:
            son = i
            break
    assert satirlar[bas - 1].startswith("def solve(a, b):"), satirlar[bas - 1]
    assert son is not None
    parca = [satirlar[bas - 1],
             "    # [384-455. satirlar: docstring atlandi]"]
    parca += satirlar[govde - 1:son]
    orij = "    # We use the b = (..., M,) logic, only if the number of extra dimensions"
    yeni = ("    # We use the b = (..., M,) logic, only if the number of\n"
            "    # extra dimensions")
    parca = [x.replace(orij, yeni) for x in parca]
    return "```python\n" + "\n".join(parca) + "\n```"


def main():
    metin = ""
    for p in sorted(glob.glob(os.path.join(PARTS, "p*.md"))):
        metin += oku(p).rstrip("\n") + "\n\n"

    def kod_repl(m):
        dosya = m.group(1)
        if m.group(2):
            a, b = m.group(2).split("-")
            return kod_blok(dosya, (int(a), int(b)))
        return kod_blok(dosya)

    metin = re.sub(r"@@KOD:([\w\.]+)(?::(\d+-\d+))?@@", kod_repl, metin)
    metin = re.sub(r"@@CIKTI:([\w\.]+):([\w\.]+)@@",
                   lambda m: cikti_blok(m.group(1), m.group(2)), metin)
    metin = metin.replace("@@KAYNAK_KESIT@@", kaynak_kesit())
    kalan = re.findall(r"@@[^@]*@@", metin)
    assert not kalan, kalan[:5]
    hedef = os.path.join(ROOT, "bolumler", "bolum_48.md")
    with open(hedef, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin.rstrip("\n") + "\n")
    print("yazildi:", hedef, len(metin), "karakter")


if __name__ == "__main__":
    main()
