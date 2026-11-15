# build36.py: bölüm 36 parçalarını birleştirir, işaretleri gerçek
# kaynaktan doldurur. İşaretler:
#   @@KOD dosya a b dil@@      Temp/b36 dosyasından satır aralığı
#   @@SRC a b@@                Doruk Lexer.cpp satır aralığı
#   @@TOKEN a b@@              Doruk Token.h satır aralığı
#   @@CIKTI "komut" dosya@@    komut satırı ve çıktı dosyası (term)
import os
import re

BASE = "C:/Users/merty/AppData/Local/Temp/b36"
DORUK = "D:/Mevcut Projeler/GitHub/Mert-Studio-Code-v2/doruk/engine"
KITAP = "D:/Mevcut Projeler/Kitap/bolumler/bolum_36.md"
hatalar = []


def satirlar(yol, enc="utf-8", hata="strict"):
    with open(yol, encoding=enc, errors=hata, newline="") as f:
        return [s.rstrip("\r") for s in f.read().split("\n")]


def kod_blok(sat, dil, kaynak, genislik=70):
    for no, s in enumerate(sat, 1):
        if len(s) > genislik:
            hatalar.append("%s satır %d: %d kr" % (kaynak, no, len(s)))
    if len(sat) > 40:
        hatalar.append("%s: blok %d satır (40 aşıldı)" % (kaynak, len(sat)))
    while sat and sat[-1].strip() == "":
        sat = sat[:-1]
    govde = "\n".join(s.rstrip() for s in sat)
    return "```%s\n%s\n```" % (dil, govde)


def isle(metin):
    def kod(m):
        d, a, b, dil = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        sat = satirlar(os.path.join(BASE, d))[a - 1:b]
        return kod_blok(sat, dil, d)

    def src(m):
        a, b = int(m.group(1)), int(m.group(2))
        sat = satirlar(os.path.join(DORUK, "src", "Lexer.cpp"),
                       enc="utf-8-sig")[a - 1:b]
        return kod_blok(sat, "cpp", "Lexer.cpp %d-%d" % (a, b))

    def tok(m):
        a, b = int(m.group(1)), int(m.group(2))
        sat = satirlar(os.path.join(DORUK, "include", "Token.h"),
                       enc="utf-8-sig")[a - 1:b]
        return kod_blok(sat, "cpp", "Token.h %d-%d" % (a, b))

    def cikti(m):
        komut, d = m.group(1), m.group(2)
        sat = satirlar(os.path.join(BASE, d), hata="replace")
        while sat and sat[-1].strip() == "":
            sat = sat[:-1]
        for no, s in enumerate(sat, 1):
            if len(s) > 74:
                hatalar.append("%s satır %d: %d kr" % (d, no, len(s)))
        govde = "\n".join(s.rstrip() for s in sat)
        if not govde:
            return "```term\n$ %s\n```" % komut
        return "```term\n$ %s\n%s\n```" % (komut, govde)

    metin = re.sub(r"@@KOD (\S+) (\d+) (\d+) (\S+)@@", kod, metin)
    metin = re.sub(r"@@SRC (\d+) (\d+)@@", src, metin)
    metin = re.sub(r"@@TOKEN (\d+) (\d+)@@", tok, metin)
    metin = re.sub(r'@@CIKTI "([^"]+)" (\S+)@@', cikti, metin)
    return metin


def main():
    dizin = os.path.join(BASE, "md")
    parcalar = sorted(f for f in os.listdir(dizin) if f.endswith(".md"))
    metin = "\n\n".join(
        open(os.path.join(dizin, p), encoding="utf-8").read().strip("\n")
        for p in parcalar)
    kalan = re.findall(r"@@\w+", metin)
    metin = isle(metin) + "\n"
    with open(KITAP, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin)
    print("parcalar:", parcalar)
    print("yazildi:", KITAP, len(metin), "karakter; isaret:", len(kalan))
    if hatalar:
        print("UYARILAR:")
        for h in hatalar:
            print("  ", h)
    else:
        print("genislik ve blok denetimi temiz")


if __name__ == "__main__":
    main()
