# -*- coding: utf-8 -*-
"""p*.md parcalarini birlestirir; @@KOD / @@CIKTI yonergelerini acar.

@@KOD dosya.py          -> dosyanin tamami, <=40 satirlik ```python bloklari
                           (bos satirdan boler). Ayni dosya ikinci kez
                           gelirse kisa atif cumlesi yazar.
@@CIKTI tNN_cikti.txt a-b -> ```term blogu; ilk satir "$ python betik.py".
"""
import os
import re
import sys

B = "C:/Users/merty/AppData/Local/Temp/b73"
PARCALAR = ["p1.md", "p3.md", "p4.md", "p5.md", "p6.md", "p7.md",
            "p8.md", "p9.md", "p10.md"]
BETIK = {"t01": "t01_nt_xent.py", "t02": "t02_egri.py",
         "t03": "t03_coll.py", "t04": "t04_olcum.py",
         "t05": "t05_ablasyon.py", "t06": "t06_on_gorev.py",
         "t07": "t07_clip_egit.py", "t08": "t08_clip_olcum.py",
         "t09": "t09_saglamlik.py", "t10": "t10_kisa_yol.py",
         "t11": "t11_ornekler.py"}
gorulen = set()


def kod_bloklari(yol):
    satirlar = open(yol, encoding="utf-8").read().rstrip("\n").split("\n")
    out, cur = [], []
    for s in satirlar:
        cur.append(s)
        if len(cur) >= 40 and s.strip() == "":
            out.append(cur)
            cur = []
        elif len(cur) >= 40 and len(cur) % 40 == 0:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return ["```python\n" + "\n".join(b).rstrip("\n") + "\n```" for b in out]


def cikti_blogu(dosya, aralik, betik):
    satirlar = open(os.path.join(B, dosya), encoding="utf-8").read()
    satirlar = satirlar.replace("\r\n", "\n").rstrip("\n").split("\n")
    if aralik:
        a, b = aralik
        satirlar = satirlar[a - 1:b]
    satirlar = [s.rstrip() for s in satirlar]
    return "```term\n$ python %s\n%s\n```" % (betik, "\n".join(satirlar))


def yonerge(m):
    ad = m.group(2).strip()
    if m.group(1) == "KOD":
        if ad in gorulen:
            return ("Kodun tamamı yukarıda verilmişti; burada yalnızca "
                    "ilgili bölümü anılıyor.")
        gorulen.add(ad)
        return "\n\n".join(kod_bloklari(os.path.join(B, ad)))
    parca = ad.split()
    dosya = parca[0]
    aralik = None
    if len(parca) > 1 and "-" in parca[1]:
        a, b = parca[1].split("-")
        aralik = (int(a), int(b))
    anahtar = dosya[:3]
    return cikti_blogu(dosya, aralik, BETIK[anahtar])


def main():
    metin = []
    for p in PARCALAR:
        yol = os.path.join(B, p)
        if os.path.exists(yol):
            metin.append(open(yol, encoding="utf-8").read().rstrip("\n"))
    tam = "\n\n".join(metin) + "\n"
    tam = re.sub(r"@@(KOD|CIKTI) ([^@]+)@@", yonerge, tam)
    hedef = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        "D:/Mevcut Projeler/Kitap/bolumler", "bolum_73.md")
    open(hedef, "w", encoding="utf-8", newline="\n").write(tam)
    print("yazildi", hedef, len(tam))


if __name__ == "__main__":
    main()
