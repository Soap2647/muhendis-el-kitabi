# -*- coding: utf-8 -*-
"""md parcalarini birlestirir; @@ isaretcilerini gercek dosya icerigiyle doldurur."""
import os, re, sys

T = "C:/Users/merty/AppData/Local/Temp/b24"
PARCALAR = ["p1.md", "p2.md", "p3.md", "p4.md", "p5.md", "p6.md", "p7.md"]
HEDEF = "D:/Mevcut Projeler/Kitap/bolumler/bolum_24.md"
DIREKTIFLER = re.compile(r"^\s*\.(?!L[FE]B)")


def yol(p):
    return p if os.path.isabs(p.replace("\\", "/")) or ":" in p else os.path.join(T, p)


def oku(p):
    with open(yol(p), encoding="utf-8") as f:
        return f.read().rstrip("\n").split("\n")


def asm_fn(dosya, fn):
    satirlar = oku(dosya)
    bas = next(i for i, s in enumerate(satirlar) if s.startswith(fn + ":"))
    son = next(i for i in range(bas + 1, len(satirlar))
               if satirlar[i].lstrip().startswith(".size") and fn in satirlar[i])
    cikti = []
    for s in satirlar[bas:son]:
        if re.match(r"^\.L[FE]B\d+:", s):
            continue
        if DIREKTIFLER.match(s):
            continue
        if s.strip() == "":
            continue
        cikti.append(s.expandtabs(8).rstrip())
    return cikti


def cit(lines, lang):
    return "```%s\n%s\n```" % (lang, "\n".join(lines))


def cozum(metin):
    def code(m):
        dosya, a, b, lang = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        s = oku(dosya)
        parca = s[a - 1:b]
        return cit([x.expandtabs(4) for x in parca], lang)
    metin = re.sub(r"@@CODE:(.+):(\d+)-(\d+):(\w+)@@", code, metin)

    def txt(m):
        dosya, lang = m.group(1), m.group(2)
        return cit([x.expandtabs(4) for x in oku(dosya)], lang)
    metin = re.sub(r"@@TXT:(.+):(\w+)@@", txt, metin)

    def term(m):
        komut, dosya = m.group(1), m.group(2)
        satir = ["$ " + komut] + [x.expandtabs(4) for x in oku(dosya)]
        return cit(satir, "term")
    metin = re.sub(r"@@TERM:([^:@]+):([^:@]+)@@", term, metin)

    def asm(m):
        dosya, fn = m.group(1), m.group(2)
        return cit(asm_fn(dosya, fn), "asm")
    metin = re.sub(r"@@ASM:([^:@]+):(\w+)@@", asm, metin)
    return metin


def main():
    parcalar = []
    for p in PARCALAR:
        with open(os.path.join(T, "md", p), encoding="utf-8") as f:
            parcalar.append(f.read().strip())
    metin = "\n\n".join(parcalar) + "\n"
    metin = cozum(metin)
    if "@@" in metin:
        print("UYARI: cozulmemis isaretci var:", re.findall(r"@@[^@]{0,60}@@", metin)[:5])
    with open(HEDEF, "w", encoding="utf-8") as f:
        f.write(metin)
    print("yazildi:", HEDEF, len(metin), "karakter,", metin.count("\n"), "satir")


if __name__ == "__main__":
    main()
