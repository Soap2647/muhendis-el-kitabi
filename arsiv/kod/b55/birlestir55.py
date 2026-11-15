# birlestir55.py: md_a, md_b, md_c parçalarını birleştirir; @@KOD, @@CIKTI
# ve @@DOSYA yer tutucularını gerçek kod ve çıktı satırlarıyla doldurur,
# sonucu bolumler/bolum_55.md dosyasına yazar.
import io
import os
import re

TEMP = r"C:\Users\merty\AppData\Local\Temp\b55"
HEDEF = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_55.md"
PARCALAR = ["md_a.md", "md_b.md", "md_c.md"]


def oku(yol):
    with io.open(yol, encoding="utf-8", newline=None) as f:
        return f.read().split("\n")


def kirp(satirlar):
    while satirlar and satirlar[-1].strip() == "":
        satirlar.pop()
    while satirlar and satirlar[0].strip() == "":
        satirlar.pop(0)
    return satirlar


def fonksiyon_blogu(satirlar, ad):
    # "def ad" ya da "class ad" satırından, bir sonraki sütun-0 satırına kadar
    kalip = re.compile(r"^(def|class) %s\b" % re.escape(ad))
    bas = None
    for i, s in enumerate(satirlar):
        if kalip.match(s):
            bas = i
            break
    if bas is None:
        raise SystemExit("fonksiyon bulunamadi: " + ad)
    son = len(satirlar)
    for j in range(bas + 1, len(satirlar)):
        s = satirlar[j]
        if s.strip() and s[0] not in " \t":
            son = j
            break
    return kirp(satirlar[bas:son])


def kod_al(dosya, aralik):
    satirlar = oku(os.path.join(TEMP, dosya))
    if aralik is None:
        return kirp(satirlar)
    if aralik.startswith("def "):
        return fonksiyon_blogu(satirlar, aralik[4:].strip())
    m = re.match(r"^(\d+)-(\d+)$", aralik)
    if not m:
        raise SystemExit("gecersiz aralik: " + aralik)
    bas, son = int(m.group(1)), int(m.group(2))
    return kirp(satirlar[bas - 1:son])


def isle(metin):
    cikti = []
    for satir in metin.split("\n"):
        if satir.startswith("@@KOD "):
            spec = satir[len("@@KOD "):].strip()
            if ":" in spec:
                dosya, aralik = spec.split(":", 1)
            else:
                dosya, aralik = spec, None
            cikti.append("```python")
            cikti.extend(kod_al(dosya, aralik))
            cikti.append("```")
            continue
        if satir.startswith("@@DOSYA "):
            spec = satir[len("@@DOSYA "):].strip()
            dosya, aralik = spec.split(":", 1)
            cikti.append("```python")
            cikti.extend(kod_al(dosya, aralik))
            cikti.append("```")
            continue
        if satir.startswith("@@CIKTI "):
            parcalar = satir[len("@@CIKTI "):].strip().split()
            dosya = parcalar[-1]
            komut = " ".join(parcalar[:-1])
            cikti.append("```term")
            cikti.append("$ " + komut)
            cikti.extend(kirp(oku(os.path.join(TEMP, dosya))))
            cikti.append("```")
            continue
        cikti.append(satir)
    return "\n".join(cikti)


if __name__ == "__main__":
    metin = "\n".join(io.open(os.path.join(TEMP, p), encoding="utf-8").read()
                      for p in PARCALAR)
    sonuc = isle(metin)
    if "@@" in sonuc:
        raise SystemExit("cozulmemis yer tutucu var")
    with io.open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(sonuc)
    print("yazildi:", HEDEF, len(sonuc), "karakter")
