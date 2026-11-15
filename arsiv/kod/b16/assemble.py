# -*- coding: utf-8 -*-
"""Bolum 16 kaynagini birlestirir: md parcalarini okur, yer tutucu
bloklari dosyadan (kod) ya da gercek calistirmadan (terminal) doldurur.

Yer tutucular:
  {{KOD:dosya.py}}  veya  {{KOD:dosya.py:bas:son}}  -> ```python blok
  {{KOD_C:dosya.c}}                                  -> ```c blok
  {{SNIP:difflib:bas:son}}  -> ```python blok (kaynaktan birebir)
  {{TERM}} ... {{/TERM}}    -> ```term blok; her satir
                               "gorunen ||| gercek" olarak calistirilir.
"""
import os
import re
import shlex
import subprocess

T = r"C:\Users\merty\AppData\Local\Temp\b16"
KOD = os.path.join(T, "kod")
PARTS = os.path.join(T, "md")
OUT = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_16.md"


def oku(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def kod_blok(dil, satirlar):
    for s in satirlar:
        if len(s) > 70:
            raise SystemExit("70 karakteri asan kod satiri: " + s)
    return "```" + dil + "\n" + "\n".join(satirlar) + "\n```"


def kod_aralik(ad, bas, son):
    satirlar = oku(os.path.join(KOD, ad)).rstrip("\n").split("\n")
    if bas is not None:
        satirlar = satirlar[int(bas) - 1:int(son)]
    return kod_blok("python", satirlar)


def wrap(satir, sinir=70):
    # Yalnizca uzun yorum satirlari, icerik degismeden ikiye bolunur.
    if len(satir) <= sinir:
        return [satir]
    girinti = len(satir) - len(satir.lstrip(" "))
    s = satir.lstrip(" ")
    if not s.startswith("#"):
        raise SystemExit("Bolunemeyen uzun kod satiri: " + satir)
    kes = satir.rfind(" ", 0, 60)
    birinci = satir[:kes]
    ikinci = " " * girinti + "# " + satir[kes + 1:].lstrip("# ").strip()
    return [birinci, ikinci]


def snip(ad, bas, son):
    dosya = "difflib_3_12_10.py" if ad == "difflib" else ad + ".py"
    satirlar = oku(os.path.join(T, dosya)).split("\n")
    parca = satirlar[int(bas) - 1:int(son)]
    cikti = []
    for s in parca:
        cikti.extend(wrap(s))
    return kod_blok("python", cikti)


def calistir(satir):
    gorunen, gercek = satir.split(" ||| ")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", MSYS_NO_PATHCONV="1")
    r = subprocess.run(shlex.split(gercek), cwd=KOD, env=env,
                       capture_output=True)
    cikti = (r.stdout + r.stderr).decode("utf-8", "replace")
    if r.returncode != 0:
        raise SystemExit("Komut basarisiz: %s\n%s" % (gercek, cikti))
    cikti = cikti.replace("\r\n", "\n").rstrip("\n")
    return "$ " + gorunen + ("\n" + cikti if cikti else "")


def terminal(govde):
    satirlar = [s.strip() for s in govde.strip("\n").split("\n")
                if s.strip()]
    bloklar = [calistir(s) for s in satirlar]
    for b in bloklar:
        for s in b.split("\n"):
            if len(s) > 74:
                raise SystemExit("74 karakteri asan terminal satiri: " + s)
    return "```term\n" + "\n".join(bloklar) + "\n```"


def birlestir():
    dosyalar = sorted(f for f in os.listdir(PARTS) if f.endswith(".md"))
    metin = "\n\n".join(oku(os.path.join(PARTS, f)).strip("\n")
                        for f in dosyalar) + "\n"
    metin = re.sub(r"\{\{KOD:([^:}]+)(?::(\d+):(\d+))?\}\}",
                   lambda m: kod_aralik(m.group(1), m.group(2), m.group(3)),
                   metin)
    metin = re.sub(r"\{\{KOD_C:([^}]+)\}\}",
                   lambda m: kod_blok("c", oku(os.path.join(
                       KOD, m.group(1))).rstrip("\n").split("\n")),
                   metin)
    metin = re.sub(r"\{\{SNIP:([^:}]+):(\d+):(\d+)\}\}",
                   lambda m: snip(m.group(1), m.group(2), m.group(3)),
                   metin)
    metin = re.sub(r"\{\{TERM\}\}\n(.*?)\n\{\{/TERM\}\}",
                   lambda m: terminal(m.group(1)), metin, flags=re.S)
    kalan = re.findall(r"\{\{[^}]*\}\}", metin)
    if kalan:
        raise SystemExit("Cozulmemis yer tutucu: %s" % kalan[:5])
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin)
    print("yazildi:", OUT, "satir:", metin.count("\n"))


if __name__ == "__main__":
    birlestir()
