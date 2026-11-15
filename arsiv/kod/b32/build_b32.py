# -*- coding: utf-8 -*-
"""Bolum 32 md kaynagini sablonlardan uretir.

Isaretler:
  @@KOD dosya@@              dosyayi bos satirlardan bolerek (<=36 satir)
                             kod bloklari olarak gomer
  @@KOD dosya a b@@          dosyanin a..b satirlarini tek blok olarak gomer
  @@TERM§gorunen§calistir@@  WSL'de calistirir; ```term blogu uretir
  @@TERMW§gorunen§calistir@@ Windows'ta calistirir; ```term blogu
  @@SRC yol a b@@            harici kaynak dosyadan a..b (birebir)
  @@CSV ad@@                 engine/veri/ad.csv -> markdown tablo
"""
import csv
import os
import re
import subprocess
import sys

B32 = r"C:\Users\merty\AppData\Local\Temp\b32"
KITAP = r"D:\Mevcut Projeler\Kitap"
WSL_B32 = "/mnt/c/Users/merty/AppData/Local/Temp/b32"
DIL = {".c": "c", ".py": "python"}
SINIR = 36
PARCALAR = ["sablon_32_a.md", "sablon_32_b.md", "sablon_32_c.md",
            "sablon_32_d.md"]


def oku(p):
    with open(p, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n").split("\n")


def dil_of(p):
    return DIL.get(os.path.splitext(p)[1], "")


def bloklar(satirlar):
    """Satirlari bos satirlardan bolerek <= SINIR'lik parcalara ayirir."""
    parcalar, cur = [], []
    for s in satirlar:
        cur.append(s)
        if len(cur) >= SINIR and s.strip() == "":
            parcalar.append(cur)
            cur = []
    if cur:
        parcalar.append(cur)
    out = []
    for p in parcalar:
        while p and p[-1].strip() == "":
            p.pop()
        if p:
            out.append(p)
    son = []
    for p in out:
        while len(p) > SINIR + 8:
            son.append(p[:SINIR])
            p = p[SINIR:]
        son.append(p)
    return son


def kod_bloku(dosya, satirlar, dil):
    return "```%s\n%s\n```" % (dil, "\n".join(satirlar))


def kod_marker(args):
    p = args[0]
    satirlar = oku(os.path.join(B32, p))
    dil = dil_of(p)
    if len(args) == 3:
        a, b = int(args[1]), int(args[2])
        return kod_bloku(p, satirlar[a - 1:b], dil)
    parcalar = bloklar(satirlar)
    cikti, bas = [], 1
    for i, parca in enumerate(parcalar):
        if i > 0:
            cikti.append("*Kodun devamı (%s, satır %d–%d):*"
                         % (p, bas, bas + len(parca) - 1))
        cikti.append(kod_bloku(p, parca, dil))
        bas += len(parca) + 1
    return "\n\n".join(cikti)


def temizle(satirlar):
    out = [s.rstrip() for s in satirlar]
    while out and out[-1] == "":
        out.pop()
    return [s for s in out if "screen size is bogus" not in s]


def wsl(komut):
    r = subprocess.run(["wsl", "-e", "bash", "-c",
                        "cd '%s' && %s 2>&1" % (WSL_B32, komut)],
                       capture_output=True)
    out = r.stdout.decode("utf-8", "replace").replace("\x00", "")
    return temizle(out.replace("\r", "").split("\n"))


def windows(komut):
    """Sabit, yazar kontrolundeki komutu kabuksuz (liste olarak) calistirir."""
    import shlex
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(shlex.split(komut), cwd=B32, env=env,
                       capture_output=True)
    out = (r.stdout + r.stderr).decode("utf-8", "replace")
    return temizle(out.replace("\r", "").split("\n"))


def term_blok(gorunen, satirlar):
    govde = ["$ " + gorunen] + satirlar
    for s in govde:
        if len(s) > 74:
            print("UYARI terminal satiri >74:", len(s), s[:60],
                  file=sys.stderr)
    return "```term\n%s\n```" % "\n".join(govde)


def csv_marker(ad):
    with open(os.path.join(KITAP, "engine", "veri", ad + ".csv"),
              encoding="utf-8") as f:
        satirlar = list(csv.reader(f))
    baslik, veri = satirlar[0], satirlar[1:]
    out = ["| " + " | ".join(baslik) + " |",
           "|" + "---|" * len(baslik)]
    for r in veri:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def isle(metin):
    def repl(m):
        ic = m.group(1)
        if ic.startswith("KOD "):
            return kod_marker(ic[4:].split())
        if ic.startswith("SRC "):
            parca = ic[4:].split()
            satirlar = oku(parca[0])
            a, b = int(parca[1]), int(parca[2])
            return kod_bloku(parca[0], satirlar[a - 1:b], "python")
        if ic.startswith("TERMW§"):
            _, gor, cal = ic.split("§", 2)
            return term_blok(gor, windows(cal))
        if ic.startswith("TERM§"):
            _, gor, cal = ic.split("§", 2)
            return term_blok(gor, wsl(cal))
        if ic.startswith("CSV "):
            return csv_marker(ic[4:].strip())
        raise ValueError("bilinmeyen isaret: " + ic)
    return re.sub(r"@@(.+?)@@", repl, metin, flags=re.S)


def main():
    metin = ""
    for p in PARCALAR:
        yol = os.path.join(B32, p)
        if os.path.exists(yol):
            with open(yol, encoding="utf-8") as f:
                metin += f.read().rstrip() + "\n\n"
    metin = isle(metin)
    hedef = os.path.join(KITAP, "bolumler", "bolum_32.md")
    with open(hedef, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin.rstrip() + "\n")
    print("yazildi:", hedef, len(metin), "karakter")


if __name__ == "__main__":
    main()
