# -*- coding: utf-8 -*-
"""Bölüm 42 birleştiricisi: tpl/p1..p4.md içindeki işaretçileri
kaynak dosyalardan gerçek kod ve çıktı bloklarına çevirir.

@@KOD dil|yol|BAŞLANGIÇ|BİTİŞ@@  -> dosyanın [BAŞLANGIÇ, BİTİŞ) satırları
@@CIKTI dosya@@                  -> çıktı dosyası, term bloğu olarak
"""
import io
import os
import sys

KOK = r"C:\Users\merty\AppData\Local\Temp\b42"
HEDEF = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_42.md"
PARCALAR = ["tpl/p1.md", "tpl/p2.md", "tpl/p3.md", "tpl/p4.md"]
MAX_KOD, MAX_TERM = 70, 74
hatalar = []


def oku(yol):
    with io.open(os.path.join(KOK, yol), encoding="utf-8") as f:
        return f.read().split("\n")


def kod_blok(args, satir_no):
    dil, yol, bas, bit = args.split("|")
    satirlar = oku(yol)
    if bas == "":
        i0 = 0
    else:
        i0 = next((i for i, s in enumerate(satirlar) if s.startswith(bas)),
                  None)
        if i0 is None:
            hatalar.append("%d: başlangıç bulunamadı: %s (%s)"
                           % (satir_no, bas, yol))
            return ""
    if bit == "EOF":
        i1 = len(satirlar)
    else:
        i1 = next((i for i in range(i0 + 1, len(satirlar))
                   if satirlar[i].startswith(bit)), None)
        if i1 is None:
            hatalar.append("%d: bitiş bulunamadı: %s (%s)"
                           % (satir_no, bit, yol))
            return ""
    secilen = satirlar[i0:i1]
    while secilen and secilen[-1] == "":
        secilen.pop()
    if len(secilen) > 40:
        hatalar.append("%d: blok %d satır (>40): %s" %
                       (satir_no, len(secilen), yol))
    for k, s in enumerate(secilen, 1):
        if len(s) > MAX_KOD:
            hatalar.append("%d: %s satır %d: %d karakter"
                           % (satir_no, yol, k, len(s)))
    return "```%s\n%s\n```" % (dil, "\n".join(secilen))


def cikti_blok(arg, satir_no):
    yol, _, onek = arg.partition("|")
    satirlar = oku(yol)
    if onek:
        satirlar = [onek] + satirlar
    while satirlar and satirlar[-1] == "":
        satirlar.pop()
    for k, s in enumerate(satirlar, 1):
        if len(s) > MAX_TERM:
            hatalar.append("%d: çıktı %s satır %d: %d karakter"
                           % (satir_no, yol, k, len(s)))
    return "```term\n%s\n```" % "\n".join(satirlar)


def cevir(metin):
    cikti = []
    for satir_no, satir in enumerate(metin.split("\n"), 1):
        t = satir.strip()
        if t.startswith("@@KOD ") and t.endswith("@@"):
            cikti.append(kod_blok(t[len("@@KOD "):-2], satir_no))
        elif t.startswith("@@CIKTI ") and t.endswith("@@"):
            cikti.append(cikti_blok(t[len("@@CIKTI "):-2].strip(), satir_no))
        else:
            cikti.append(satir)
    return "\n".join(cikti)


def main():
    birlesik = []
    for p in PARCALAR:
        with io.open(os.path.join(KOK, p), encoding="utf-8") as f:
            birlesik.append(cevir(f.read()))
    metin = "\n".join(birlesik)
    # çıktı bloklarında ardışık boş satırlar olmasın
    while "\n\n\n" in metin:
        metin = metin.replace("\n\n\n", "\n\n")
    kalan = [s for s in metin.split("\n") if "@@" in s]
    if kalan:
        hatalar.append("işlenmemiş işaretçi: %s" % kalan[:3])
    with io.open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin.rstrip() + "\n")
    print("yazıldı:", HEDEF, "satır:", metin.count("\n") + 1)
    if hatalar:
        print("HATALAR:")
        for h in hatalar:
            print("  ", h)
        return 1
    print("işaretçiler çözüldü, sınır denetimi temiz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
