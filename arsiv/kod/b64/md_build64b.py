# -*- coding: utf-8 -*-
"""Bolum 64 Markdown birlestirici (surum 2).

Sablon (sablon64.md) icindeki isaretleri dosyalardan doldurur:
  {{KOD|dosya|BAS|BIT}}
      BAS: satirin icerdigi metin; ^ = dosya basi.
      BIT: satirin icerdigi metin (o satir dahil); $ = dosya sonu.
           "<metin" = metnin ilk gectigi satirdan ONCE bitir.
           "metin#k" = BAS'tan sonra metnin k. gectigi satir.
  {{CIKTI|script|cikti_dosyasi}}
      Terminal blogu: "$ python script" + cikti dosyasinin icerigi.
Kullanim: python md_build64b.py  (KONTROL=1 ile parca bilgisi basar)
"""
import os
import re
import sys

KLASOR = r"C:\Users\merty\AppData\Local\Temp\b64"
SABLON = os.path.join(KLASOR, "sablon64.md")
HEDEF = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_64.md"
KONTROL = bool(os.environ.get("KONTROL"))
HATALAR = []
_cache = {}
_son = {}


def satirlar(dosya):
    if dosya not in _cache:
        yol = os.path.join(KLASOR, dosya)
        with open(yol, encoding="utf-8") as f:
            _cache[dosya] = f.read().rstrip("\n").split("\n")
    return _cache[dosya]


def bul_ilk(L, metin, bas):
    for k in range(bas, len(L)):
        if metin in L[k]:
            return k
    raise ValueError("bulunamadi: %r (baslangic %d)" % (metin, bas))


def kod(dosya, bas, bit):
    L = satirlar(dosya)
    if bas == "^":
        i = 0
    elif bas == "@":
        i = _son.get(dosya, -1) + 1
    else:
        i = bul_ilk(L, bas, 0)
    if bit == "$":
        j = len(L) - 1
    elif bit.startswith("<"):
        j = bul_ilk(L, bit[1:], i + 1) - 1
    elif "#" in bit:
        metin, kth = bit.rsplit("#", 1)
        esl = [k for k in range(i, len(L)) if metin in L[k]]
        j = esl[int(kth) - 1]
    else:
        j = bul_ilk(L, bit, i)
    _son[dosya] = j
    parca = L[i:j + 1]
    while parca and not parca[0].strip():
        parca = parca[1:]
    while parca and not parca[-1].strip():
        parca = parca[:-1]
    n = len(parca)
    if KONTROL:
        print("KOD %-28s [%s .. %s] %3d satir | %s | %s"
              % (dosya, bas[:16], bit[:16], n,
                 parca[0][:34], parca[-1][:34]))
    if n > 42:
        HATALAR.append("uzun kod blogu (%d): %s %s" % (n, dosya, bas))
    for l in parca:
        if len(l) > 70:
            HATALAR.append("kod >70: %s: %s" % (dosya, l[:40]))
    return "```python\n" + "\n".join(parca) + "\n```"


def cikti(script, dosya):
    yol = os.path.join(KLASOR, dosya)
    if not os.path.exists(yol):
        HATALAR.append("cikti eksik: " + dosya)
        icerik = "[CIKTI EKSIK]"
    else:
        with open(yol, encoding="utf-8") as f:
            icerik = f.read().rstrip("\n")
    for l in icerik.split("\n"):
        if len(l) > 74:
            HATALAR.append("terminal >74: %s: %s" % (dosya, l[:40]))
    if KONTROL:
        print("CIKTI %-28s %s (%d satir)"
              % (script, dosya, icerik.count("\n") + 1))
    return "```term\n$ python %s\n%s\n```" % (script, icerik)


def genislet(metin):
    metin = re.sub(
        r"\{\{KOD\|([^|}]+)\|([^|}]+)\|([^|}]+)\}\}",
        lambda m: kod(m.group(1), m.group(2), m.group(3)), metin)
    metin = re.sub(
        r"\{\{CIKTI\|([^|}]+)\|([^|}]+)\}\}",
        lambda m: cikti(m.group(1), m.group(2)), metin)
    return metin


def main():
    with open(SABLON, encoding="utf-8") as f:
        metin = f.read()
    sonuc = genislet(metin)
    if "{{" in sonuc:
        HATALAR.append("genislemeyen isaret kaldi")
    with open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(sonuc)
    print("yazildi:", HEDEF, sonuc.count("\n") + 1, "satir")
    for h in HATALAR:
        print("UYARI:", h)


if __name__ == "__main__":
    main()
