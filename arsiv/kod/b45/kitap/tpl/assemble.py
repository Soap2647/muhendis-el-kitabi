# -*- coding: utf-8 -*-
"""Bolum 45 kaynagini birlestirir: parcalari sirala, {{KOD}} ve {{CIKTI}}
isaretcilerini gercek dosya satirlari ve program ciktilariyla degistirir.
Cikti: bolumler/bolum_45.md
"""
import os
import re
import sys

KITAP_KOD = "C:/Users/merty/AppData/Local/Temp/b45/kitap"
TPL = os.path.join(KITAP_KOD, "tpl")
EV_KOK = ("D:/Mevcut Projeler/0-Bitmiş Projeler/Elektrikli Araba "
          "Dökümantasyon/ev-dashboard")
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_45.md"


def oku(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def dosya_yolu(ad):
    if ad.startswith("EV:"):
        return os.path.join(EV_KOK, ad[3:])
    return os.path.join(KITAP_KOD, ad)


def sar(satirlar, genislik=70):
    """Kaynak satirlarini dizgi icin sarar; devam satirlari 4 bosluk."""
    cikis = []
    for satir in satirlar:
        while len(satir) > genislik:
            kes = satir.rfind(" ", 0, genislik)
            if kes <= 0:
                kes = genislik
            cikis.append(satir[:kes].rstrip())
            satir = "    " + satir[kes:].lstrip()
        cikis.append(satir)
    return cikis


def kod_blogu(m, onceki_dosya):
    ad, a, b, dil = m.group(1), int(m.group(2)), m.group(3), m.group(4)
    satirlar = oku(dosya_yolu(ad)).split("\n")
    son = len(satirlar) if b in ("", None) else int(b)
    parca = satirlar[a - 1:son]
    while parca and parca[-1].strip() == "":
        parca.pop()
    if ad.startswith("EV:"):
        parca = sar(parca)
    govde = "\n".join(parca)
    return "```%s\n%s\n```" % (dil, govde)


def cikti_blogu(m):
    komut, dosya = m.group(1), m.group(2)
    cikti = oku(os.path.join(KITAP_KOD, dosya)).rstrip("\n")
    return "```term\n$ %s\n%s\n```" % (komut, cikti)


def birlestir():
    parcalar = []
    for ad in ("p1.md", "p2.md", "p3a.md", "p4.md", "p3b.md"):
        parcalar.append(oku(os.path.join(TPL, ad)).rstrip("\n") + "\n")
    md = "\n".join(parcalar)
    # Kesit 3: fonksiyon baslangici dahil
    md = md.replace("{{KOD|EV:stm32/main.c|90|93|c}}",
                    "{{KOD|EV:stm32/main.c|83|93|c}}")
    md = md.replace("**Kesit 3: `stm32/main.c`, satır 90–93 (Kelly motor sürücüsü).**",
                    "**Kesit 3: `stm32/main.c`, satır 83–93 (Kelly motor sürücüsü).**")
    # Ardisik kod bloklari arasina baglayici cumle
    def ara(m):
        return m.group(0)
    md = re.sub(r"\}\}\n\n\{\{KOD\|",
                "}}\n\nKodun devamı şöyledir:\n\n{{KOD|", md)
    # Kod ve cikti isaretcileri
    md = re.sub(r"\{\{KOD\|([^|]+)\|(\d+)\|(\d*)\|([a-z]+)\}\}",
                lambda m: kod_blogu(m, None), md)
    md = re.sub(r"\{\{CIKTI\|([^|]+)\|([^}]+)\}\}",
                lambda m: cikti_blogu(m), md)
    assert "{{" not in md, "cozulmemis isaretci var"
    return md


if __name__ == "__main__":
    md = birlestir()
    with open(HEDEF, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print("yazildi:", HEDEF, "satir:", md.count("\n"))
