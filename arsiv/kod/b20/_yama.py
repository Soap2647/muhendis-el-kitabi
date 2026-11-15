p = "md_uret.py"
s = open(p, encoding="utf-8").read()
i = s.index("def terminal(m):")
j = s.index("def tablo(m):")
yeni = '''def kaydir(satir, komut):
    """74 karakteri asan satiri kelime sinirindan boler.
    Komut satirinda devam '\\' ile isaretlenir; devam satirlari
    4 bosluk girintilidir. Icerik degismez, yalnizca sayfa duzeni."""
    sonuc = []
    kalan = satir
    ilk = True
    while len(kalan) > HEDEF_TERM:
        kes = kalan.rfind(" ", 0, HEDEF_TERM - 2)
        if kes <= 0:
            break
        if ilk and komut:
            sonuc.append(kalan[:kes] + " \\\\")
        else:
            sonuc.append(kalan[:kes])
        kalan = "    " + kalan[kes + 1:]
        ilk = False
    sonuc.append(kalan)
    return sonuc


def terminal(m):
    ad = m.group(1)
    yol = os.path.join(BAS, "cikti", ad + ".txt")
    with open(yol, encoding="utf-8") as f:
        metin = f.read().rstrip("\n")
    cikti = []
    for s in metin.split("\n"):
        cikti.extend(kaydir(s, s.startswith("$ ")))
    for no, s in enumerate(cikti, 1):
        if len(s) > HEDEF_TERM:
            hatalar.append("terminal >74: %s satir %d (%d)"
                           % (ad, no, len(s)))
    return "```term\n%s\n```" % "\n".join(cikti)


'''
s = s[:i] + yeni + s[j:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
