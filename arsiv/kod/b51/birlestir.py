# birlestir.py: md_a..md_d parçalarını birleştirir, @@KOD / @@CIKTI /
# @@DOSYA yer tutucularını gerçek kod, çıktı ve kaynak satırlarıyla
# doldurur ve bolumler/bolum_51.md dosyasını yazar.
import io
import os
import re
import sys

TEMP = r"C:\Users\merty\AppData\Local\Temp\b51"
HEDEF = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_51.md"
PARCALAR = ["md_a.md", "md_b.md", "md_c.md", "md_d.md"]


def oku_satirlar(yol):
    with io.open(yol, encoding="utf-8", newline=None) as f:
        return f.read().split("\n")


def kirp(satirlar):
    # Sondaki boş satırları at; kod/çıktı bloklarında fazladan boşluk olmasın
    while satirlar and satirlar[-1].strip() == "":
        satirlar.pop()
    return satirlar


def kod_blogu(dosya, bas=None, son=None, dil="python"):
    satirlar = oku_satirlar(os.path.join(TEMP, dosya))
    if bas is not None:
        satirlar = satirlar[bas - 1:son]
    satirlar = kirp(satirlar)
    return ["```" + dil] + satirlar + ["```"]


def kaynak_blogu(yol, bas, son, dil):
    satirlar = oku_satirlar(os.path.join(TEMP, yol))
    satirlar = satirlar[bas - 1:son]
    satirlar = kirp(satirlar)
    return ["```" + dil] + satirlar + ["```"]


def cikti_blogu(komut, cikti_dosya):
    satirlar = oku_satirlar(os.path.join(TEMP, cikti_dosya))
    satirlar = kirp(satirlar)
    return ["```term", "$ " + komut] + satirlar + ["```"]


def isle(metin):
    cikti = []
    for satir in metin.split("\n"):
        m = re.match(r"^@@KOD (\S+)(?: (\d+) (\d+))?@@$", satir)
        if m:
            bas = int(m.group(2)) if m.group(2) else None
            son = int(m.group(3)) if m.group(3) else None
            cikti.extend(kod_blogu(m.group(1), bas, son))
            continue
        m = re.match(r"^@@DOSYA (\S+) (\d+) (\d+) (\w+)@@$", satir)
        if m:
            cikti.extend(kaynak_blogu(m.group(1), int(m.group(2)),
                                      int(m.group(3)), m.group(4)))
            continue
        m = re.match(r"^@@CIKTI (.+) (\S+)@@$", satir)
        if m:
            cikti.extend(cikti_blogu(m.group(1).strip(), m.group(2)))
            continue
        cikti.append(satir)
    return "\n".join(cikti)


def main():
    parcalar = []
    for p in PARCALAR:
        with io.open(os.path.join(TEMP, p), encoding="utf-8") as f:
            parcalar.append(f.read().rstrip("\n"))
    birlesik = "\n\n".join(parcalar) + "\n"
    sonuc = isle(birlesik)
    sonuc = re.sub(r"\n{3,}", "\n\n", sonuc)
    with io.open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(sonuc)
    kalan = re.findall(r"@@\w+", sonuc)
    print("yazildi:", HEDEF, "satir:", sonuc.count("\n"))
    print("kalan yer tutucu:", len(kalan))


if __name__ == "__main__":
    main()
