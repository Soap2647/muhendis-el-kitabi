# -*- coding: utf-8 -*-
"""p1..p4 parcalarini birlestirir, @@CODE/@@OUT yer tutucularini doldurur."""
import os
import re
import subprocess
import sys

TMP = "C:/Users/merty/AppData/Local/Temp/b52"
KOK = "D:/Mevcut Projeler/Kitap"
ARM_TERM = """```term
$ arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard \\
    -mfpu=fpv4-sp-d16 -Os -c q15_fir.c -o q15_fir.o
$ arm-none-eabi-size -A q15_fir.o
section           size   addr
.text              136      0
.data                0      0
.bss                 0      0
.rodata             10      0
.comment            68      0
.ARM.attributes     52      0
Total              266
```"""
HOST_TERM = """```term
$ gcc -O2 -Wall -Wextra -std=c11 q15_fir.c q15_test.c -lm -o q15_test
$ ./q15_test
ilk 6 cikti: -161 -3193 -1514 12944 5350 -4125
max |Q15 - (Q15 katsayi float)| = 0.50 LSB
max |Q15 - (kesin float)|       = 1.60 LSB
DC 32767 girisi, cikis = 32767
```"""


def lang(ad):
    return {".py": "python", ".c": "c", ".h": "c"}[os.path.splitext(ad)[1]]


def yol(ad):
    return ad if os.path.isabs(ad) else os.path.join(TMP, ad)


def kod_blok(satirlar, dil):
    """Uzun kodu 36 satira yakin, mantikli sinirlardan boler."""
    while satirlar and satirlar[-1].strip() == "":
        satirlar = satirlar[:-1]
    parcalar = []
    kalan = list(satirlar)
    while len(kalan) > 36:
        kes = None
        for k in range(36, 24, -1):
            if kalan[k - 1].strip() == "" or (
                    kalan[k].strip() and not kalan[k].startswith((" ", "	", "}", ")"))):
                kes = k
                break
        if kes is None:
            kes = 34
        parcalar.append(kalan[:kes])
        kalan = kalan[kes:]
    parcalar.append(kalan)
    cikti = []
    for p in parcalar:
        while p and p[-1].strip() == "":
            p = p[:-1]
        while p and p[0].strip() == "":
            p = p[1:]
        cikti.append("```%s\n%s\n```" % (dil, "\n".join(p)))
    return "\n\nKodun devamı:\n\n".join(cikti)


def kod(m):
    args = m.group(1).split()
    ad = args[0]
    satirlar = open(yol(ad), encoding="utf-8").read().split("\n")
    if len(args) == 3:
        satirlar = satirlar[int(args[1]) - 1:int(args[2])]
    return kod_blok(satirlar, lang(ad))


def cikti(m):
    ad = m.group(1).strip()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    sonuc = subprocess.run([sys.executable, yol(ad)], cwd=KOK, env=env,
                           capture_output=True, text=True, encoding="utf-8")
    if sonuc.returncode != 0:
        raise SystemExit("HATA %s\n%s" % (ad, sonuc.stderr))
    satirlar = [s.rstrip() for s in sonuc.stdout.split("\n")]
    while satirlar and satirlar[-1] == "":
        satirlar = satirlar[:-1]
    return "```term\n$ python %s\n%s\n```" % (ad, "\n".join(satirlar))


def main():
    s = ""
    for p in ("p1.md", "p2.md", "p3.md", "p4.md"):
        s += open(os.path.join(TMP, p), encoding="utf-8").read().rstrip() + "\n\n"
    s = s.replace("@@TERM_ARM@@", ARM_TERM).replace("@@TERM@@", HOST_TERM)
    s = re.sub(r"@@CODE ([^@]+?)@@", kod, s)
    s = re.sub(r"@@OUT ([^@]+?)@@", cikti, s)
    assert "@@" not in s, "yer tutucu kaldi"
    hedef = os.path.join(KOK, "bolumler", "bolum_52.md")
    open(hedef, "w", encoding="utf-8").write(s)
    print("yazildi:", hedef, "satir:", s.count("\n"))


if __name__ == "__main__":
    main()
