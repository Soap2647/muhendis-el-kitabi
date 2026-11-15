# gen_b18.py: sablon/p1.md .. p5.md parcalarini birlestirir; her
# {{...}} yonergesini gercek dosyadan / gercek calistirmadan doldurup
# bolumler/bolum_18.md dosyasini yazar.
#   {{KOD|dosya.py|a-b}}          dosyanin a..b satirlari (```python)
#   {{SRC|dosya|a-b|v|s|sd}}      zlib kaynagi: v=birebir, s=yorumsuz,
#                                 sd=yorumsuz + DUMP_BL_TREE blogu yok
#   {{TERM|komut;;komut}}         Python komutlarini calistirir, ciktiyi
#                                 terminal bloguna koyar
#   {{WSL|komut;;komut}}          komutlari WSL icinde calistirir
import glob
import os
import re
import shlex
import subprocess

TEMP = "C:/Users/merty/AppData/Local/Temp/b18"
KITAP = "D:/Mevcut Projeler/Kitap"
SABLON = os.path.join(TEMP, "sablon")
CIKIS = os.path.join(KITAP, "bolumler", "bolum_18.md")
WSL_DIZIN = "/mnt/c/Users/merty/AppData/Local/Temp/b18"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
MAX_KOD, MAX_TERM = 70, 74


def oku(dosya):
    with open(os.path.join(TEMP, dosya), encoding="utf-8") as f:
        return f.read().split("\n")


def aralik(metin, n):
    if not metin:
        return 1, n
    a, b = metin.split("-")
    return int(a), int(b)


def kod_blok(satirlar, dil):
    while satirlar and not satirlar[-1].strip():
        satirlar = satirlar[:-1]
    return "```%s\n%s\n```" % (dil, "\n".join(satirlar))


def kod(arg):
    parca = arg.split("|")
    dosya = parca[0]
    satirlar = oku(dosya)
    if len(parca) > 1 and parca[1]:
        a, b = aralik(parca[1], 0)
    else:
        a, b = 1, len(satirlar)
    dil = "c" if dosya.endswith(".c") else "python"
    return kod_blok(satirlar[a - 1:b], dil)


def strip_yorum(satirlar):
    cikis, icerde = [], False
    for ln in satirlar:
        res, i = "", 0
        while i < len(ln):
            if icerde:
                j = ln.find("*/", i)
                if j == -1:
                    i = len(ln)
                    break
                i, icerde = j + 2, False
                continue
            j = ln.find("/*", i)
            if j == -1:
                res += ln[i:]
                break
            res += ln[i:j]
            icerde, i = True, j + 2
        if res.strip() == "" and ln.strip() != "":
            continue
        cikis.append(res.rstrip())
    return cikis


def src(arg):
    parca = arg.split("|")
    dosya = parca[0]
    a, b = aralik(parca[1], 0)
    mod = parca[2] if len(parca) > 2 else "v"
    satirlar = oku(dosya)[a - 1:b]
    if mod in ("s", "sd"):
        satirlar = strip_yorum(satirlar)
    if mod == "sd":
        cikis, atla = [], False
        for ln in satirlar:
            if ln.strip() == "#ifdef DUMP_BL_TREE":
                atla = True
            if not atla:
                cikis.append(ln)
            if atla and ln.strip() == "#endif":
                atla = False
        satirlar = cikis
    return kod_blok(satirlar, "c")


def calistir_py(komut):
    sonuc = subprocess.run(shlex.split(komut), cwd=TEMP, env=ENV,
                           capture_output=True, text=True,
                           encoding="utf-8")
    if sonuc.returncode != 0:
        raise SystemExit("HATA: %s\n%s" % (komut, sonuc.stderr))
    if sonuc.stderr.strip():
        raise SystemExit("UYARI (stderr): %s\n%s" % (komut, sonuc.stderr))
    return sonuc.stdout.rstrip("\n").split("\n") if sonuc.stdout.strip() else []


def calistir_wsl(komut):
    tam = "cd %s && %s" % (WSL_DIZIN, komut)
    sonuc = subprocess.run(["wsl", "-e", "bash", "-lc", tam],
                           capture_output=True, text=True,
                           encoding="utf-8", env=dict(os.environ,
                                                      MSYS_NO_PATHCONV="1"))
    if sonuc.returncode != 0:
        raise SystemExit("WSL HATA: %s\n%s" % (komut, sonuc.stderr))
    if sonuc.stderr.strip():
        raise SystemExit("WSL UYARI: %s\n%s" % (komut, sonuc.stderr))
    return sonuc.stdout.rstrip("\n").split("\n") if sonuc.stdout.strip() else []


def term(arg, wsl=False):
    satirlar, onek = [], ""
    for komut in arg.split(";;"):
        komut = komut.strip()
        satirlar.append("$ " + komut)
        if wsl and komut.startswith("export "):
            onek += komut + "; "   # sonraki komutlara ortam olarak ekle
            continue
        if wsl:
            cikti = calistir_wsl(onek + komut)
        else:
            cikti = calistir_py(komut)
        satirlar.extend(cikti)
    return "```term\n" + "\n".join(satirlar) + "\n```"


def yonerge(m):
    tur, arg = m.group(1), m.group(2)
    if tur == "KOD":
        return kod(arg)
    if tur == "SRC":
        return src(arg)
    if tur == "TERM":
        return term(arg)
    if tur == "WSL":
        return term(arg, wsl=True)
    raise SystemExit("bilinmeyen yonerge: " + tur)


def denetle(md):
    sorun = 0
    icerde, dil = False, ""
    for no, ln in enumerate(md.split("\n"), 1):
        s = ln.strip()
        if s.startswith("```"):
            if not icerde:
                icerde, dil = True, s[3:].strip()
            else:
                icerde = False
            continue
        if icerde:
            sinir = MAX_TERM if dil == "term" else MAX_KOD
            if len(ln) > sinir:
                print("UZUN SATIR", no, len(ln), ln[:50])
                sorun += 1
    return sorun


def main():
    parcalar = sorted(glob.glob(os.path.join(SABLON, "p*.md")))
    metin = "\n".join(open(p, encoding="utf-8").read().rstrip("\n")
                      + "\n" for p in parcalar)
    metin = re.sub(r"\{\{(KOD|SRC|TERM|WSL)\|([^}]*)\}\}", yonerge, metin)
    kalan = re.findall(r"\{\{[^}]*\}\}", metin)
    if kalan:
        raise SystemExit("cozulmemis yonerge: %s" % kalan[:3])
    sorun = denetle(metin)
    with open(CIKIS, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin)
    print("yazildi:", CIKIS, "satir:", metin.count("\n"),
          "uzun satir sorunu:", sorun)


if __name__ == "__main__":
    main()
