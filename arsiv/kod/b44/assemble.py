# -*- coding: utf-8 -*-
"""Bolum 44 kaynaklarini birlestirir.

Parcalar: tpl_a/b/c/d/e/f.md. Isaretleyiciler:
  <<KOD dosya|BAS|SON|dil>>   kod karti (dosya kitap/ altinda)
  <<EXT yol|BAS|SON|dil>>     kod karti (dis dosya, mutlak yol)
  <<TERM komut|dosya|BAS|N>>  terminal kutusu: '$ komut' + cikti
BAS/SON: tam sayi (1-tabanli; SON=0 ya da bos: dosya sonu) ya da
'^regex' (ilk eslesen satir; SON regex ise o satir haric tutulur).
Kullanim: python assemble.py  -> ../bolumler/bolum_44.md
"""
import os
import re
import sys

KITAP = os.path.dirname(os.path.abspath(__file__))
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_44.md"
EXT_KOK = "D:/Mevcut Projeler/GitHub/Operating-System/"


def satirlar(yol):
    with open(yol, encoding="utf-8") as f:
        return f.read().split("\n")


def bul(liste, ifade, baslangic=0):
    if ifade.isdigit():
        return int(ifade) - 1
    if ifade.startswith("^"):
        r = re.compile(ifade[1:])
        for i in range(baslangic, len(liste)):
            if r.search(liste[i]):
                return i
    else:
        for i in range(baslangic, len(liste)):
            if ifade in liste[i]:
                return i
    raise SystemExit("bulunamadi: %r" % ifade)


def aralik(liste, bas, son):
    """Dondurulen: [i0, i1) (0-tabanli)."""
    i0 = 0 if bas in ("", "$") else bul(liste, bas)
    if son in ("", "$"):
        i1 = len(liste)
    elif son.startswith("^"):
        i1 = bul(liste, son, i0 + 1)          # haric
    else:
        s = int(son)
        i1 = len(liste) if s == 0 else s     # dahil (1-tabanli)
    while i1 > i0 and liste[i1 - 1].strip() == "":
        i1 -= 1
    return i0, i1


def kod_blok(yol, bas, son, dil):
    L = satirlar(yol)
    i0, i1 = aralik(L, bas, son)
    govde = "\n".join(L[i0:i1])
    return "```%s\n%s\n```" % (dil, govde)


def term_blok(komut, dosya, bas, n):
    cikti = ""
    if dosya != "-":
        L = satirlar(os.path.join(KITAP, "out", dosya))
        i0 = 0 if bas in ("", "1") else bul(L, bas)
        if n == "0" or n == 0:
            i1 = len(L)
        else:
            i1 = min(len(L), i0 + int(n))
        while i1 > i0 and L[i1 - 1].strip() == "":
            i1 -= 1
        cikti = "\n".join(L[i0:i1])
    govde = "$ " + komut + ("\n" + cikti if cikti else "")
    return "```term\n%s\n```" % govde


def isle(metin):
    def kod(m):
        p = m.group(1).split("|")
        yol = os.path.join(KITAP, p[0]) if not os.path.isabs(p[0]) else p[0]
        return kod_blok(yol, p[1], p[2], p[3])

    def ext(m):
        p = m.group(1).split("|")
        yol = p[0] if os.path.isabs(p[0]) else EXT_KOK + p[0]
        return kod_blok(yol, p[1], p[2], p[3])

    def term(m):
        p = m.group(1).split("|")
        return term_blok(p[0], p[1], p[2], p[3])

    metin = re.sub(r"<<KOD (.+?)>>", kod, metin)
    metin = re.sub(r"<<EXT (.+?)>>", ext, metin)
    metin = re.sub(r"<<TERM (.+?)>>", term, metin)
    return metin


def oku(ad):
    with open(os.path.join(KITAP, ad), encoding="utf-8") as f:
        return f.read()


def kod_okuma_ayir(d_metin):
    i = d_metin.index("## Kod Okuma Egzersizi")
    return d_metin[:i], d_metin[i:]


def f_ayir(f_metin):
    i = f_metin.index("## Bölüm Özeti")
    return f_metin[:i], f_metin[i:]


def main():
    a = oku("tpl_a.md")
    b = oku("tpl_b.md")
    c = oku("tpl_c.md")
    d_teori, kod_okuma = kod_okuma_ayir(oku("tpl_d.md"))
    e = oku("tpl_e.md")
    f1, f2 = f_ayir(oku("tpl_f.md"))
    metin = "\n".join([a, b, c, d_teori, e, f1, kod_okuma, f2])
    metin = isle(metin)
    if re.search(r"<<(KOD|EXT|TERM) ", metin):
        raise SystemExit("cozulmeyen isaretleyici var")
    metin = re.sub(r"\n{3,}", "\n\n", metin).rstrip() + "\n"
    with open(HEDEF, "w", encoding="utf-8") as f:
        f.write(metin)
    print("yazildi:", HEDEF, "satir:", metin.count("\n"))


if __name__ == "__main__":
    main()
