# -*- coding: utf-8 -*-
# Taslak (taslak.md) -> bolumler/bolum_58.md
# @@KODTAM|dosya@@  : dosyanin tamami, <=40 satirlik kod kartlari
# @@CIKTI|dosya@@   : betigi calistirir, terminal blogu (<=74 karakter)
# @@SEKIL|png|alt@@ : sekil, Sekil 58.N olarak numaralanir
import os
import re
import subprocess
import sys

TEMP = "C:/Users/merty/AppData/Local/Temp/b58"
KOK = "D:/Mevcut Projeler/Kitap"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
uyarilar = []
sekil_no = [0]


def kart(satirlar, dil):
    # <=40 satirlik parcalara bol; mumkunse bos satirdan kes
    parcalar = []
    kalan = satirlar
    while len(kalan) > 40:
        kes = 40
        for i in range(40, 20, -1):
            if kalan[i - 1].strip() == "":
                kes = i
                break
        parcalar.append(kalan[:kes])
        kalan = kalan[kes:]
    parcalar.append(kalan)
    blok = []
    for p in parcalar:
        p = [x.rstrip() for x in p]
        while p and p[0] == "":
            p = p[1:]
        while p and p[-1] == "":
            p = p[:-1]
        for i, x in enumerate(p, 1):
            if len(x) > 70:
                uyarilar.append("kod satiri %d: %d karakter: %s"
                                % (i, len(x), x[:50]))
        blok.append("```%s\n%s\n```" % (dil, "\n".join(p)))
    return "\n\n".join(blok)


def kodtam(m):
    ad = m.group(1)
    dil = "c" if ad.endswith(".c") else "python"
    metin = open(os.path.join(TEMP, ad), encoding="utf-8").read()
    return kart(metin.rstrip("\n").split("\n"), dil)


def cikti(m):
    ad = m.group(1)
    p = subprocess.run([sys.executable, ad], cwd=TEMP, env=ENV,
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise SystemExit("betik hatasi: %s\n%s" % (ad, p.stderr))
    satirlar = ["$ python " + ad] + p.stdout.rstrip("\n").split("\n")
    for i, x in enumerate(satirlar, 1):
        if len(x) > 74:
            uyarilar.append("terminal satiri (%s) %d karakter: %s"
                            % (ad, len(x), x[:50]))
    return "```term\n" + "\n".join(x.rstrip() for x in satirlar) + "\n```"


def sekil(m):
    sekil_no[0] += 1
    png, alt = m.group(1), m.group(2)
    return "![Şekil 58.%d: %s](gorseller/%s)" % (sekil_no[0], alt, png)


def main():
    s = open(os.path.join(TEMP, "taslak.md"), encoding="utf-8").read()
    s = re.sub(r"^@@KODTAM\|([^@|]+)@@$", kodtam, s, flags=re.M)
    s = re.sub(r"^@@CIKTI\|([^@|]+)@@$", cikti, s, flags=re.M)
    s = re.sub(r"^@@SEKIL\|([^@|]+)\|([^@]+)@@$", sekil, s, flags=re.M)
    kalan = re.findall(r"@@[A-Z]+\|", s)
    if kalan:
        raise SystemExit("cozulmemis yer tutucu: %s" % kalan)
    s = re.sub(r"\n{3,}", "\n\n", s).rstrip() + "\n"
    hedef = os.path.join(KOK, "bolumler", "bolum_58.md")
    open(hedef, "w", encoding="utf-8", newline="\n").write(s)
    print("yazildi:", hedef, "satir:", s.count("\n"),
          "sekil:", sekil_no[0])
    print("UYARI:" if uyarilar else "genislik uyarisi yok")
    for u in uyarilar:
        print("  ", u)


if __name__ == "__main__":
    main()
