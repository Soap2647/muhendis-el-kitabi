# -*- coding: utf-8 -*-
"""Küçük üç adresli IR: sabit katlama, ölü kod ve temel bloklar.

Komutlar (her satır bir komut):
  x = y          kopyalama (y sabit ya da isim)
  x = y op z     ikili işlem, op: + - *
  if_false x goto L
  goto L
  L:             etiket
  print x
"""
OPS = {"+": lambda a, b: a + b, "-": lambda a, b: a - b,
       "*": lambda a, b: a * b}


def sayi(x):
    return x.lstrip("-").isdigit()


def ayristir(metin):
    out = []
    for s in metin.strip().splitlines():
        p = s.split()
        if p[0].endswith(":"):
            out.append(("LABEL", p[0][:-1]))
        elif p[0] == "goto":
            out.append(("GOTO", p[1]))
        elif p[0] == "print":
            out.append(("PRINT", p[1]))
        elif p[0] == "if_false":
            out.append(("IFFALSE", p[1], p[3]))
        elif len(p) == 3:                    # x = y
            out.append(("COPY", p[0], p[2]))
        else:                                # x = y op z
            out.append(("BIN", p[0], p[3], p[2], p[4]))
    return out


def calistir(prog, girdi):
    """Yorumcu: (print çıktıları, çalışan komut sayısı)."""
    env = dict(girdi)
    etiket = {k[1]: i for i, k in enumerate(prog) if k[0] == "LABEL"}

    def v(x):
        return int(x) if sayi(x) else env[x]
    pc, cikti, adim = 0, [], 0
    while pc < len(prog):
        k = prog[pc]
        pc += 1
        adim += 1
        if k[0] == "COPY":
            env[k[1]] = v(k[2])
        elif k[0] == "BIN":
            env[k[1]] = OPS[k[2]](v(k[3]), v(k[4]))
        elif k[0] == "IFFALSE" and not v(k[1]):
            pc = etiket[k[2]]
        elif k[0] == "GOTO":
            pc = etiket[k[1]]
        elif k[0] == "PRINT":
            cikti.append(v(k[1]))
    return cikti, adim


def _kaydet(sabit, ad, a):
    if sayi(a):
        sabit[ad] = int(a)
    else:
        sabit.pop(ad, None)


def sabit_katla(prog):
    """Blok içi sabit yayılımı ve katlama; koşulu sadeleştirir."""
    out, sabit = [], {}

    def c(x):
        return str(sabit[x]) if x in sabit else x
    for k in prog:
        if k[0] == "LABEL":
            sabit = {}                       # bloğa giriş: sıfırla
            out.append(k)
        elif k[0] == "COPY":
            a = c(k[2])
            _kaydet(sabit, k[1], a)
            out.append(("COPY", k[1], a))
        elif k[0] == "BIN":
            a, b = c(k[3]), c(k[4])
            if sayi(a) and sayi(b):
                v = str(OPS[k[2]](int(a), int(b)))
                _kaydet(sabit, k[1], v)
                out.append(("COPY", k[1], v))
            else:
                sabit.pop(k[1], None)
                out.append(("BIN", k[1], k[2], a, b))
        elif k[0] == "IFFALSE":
            kosul = c(k[1])
            if not sayi(kosul):
                out.append(("IFFALSE", kosul, k[2]))
            elif int(kosul) == 0:            # her zaman atlar
                out.append(("GOTO", k[2]))   # sıfırsa dal yok
        elif k[0] == "PRINT":
            out.append(("PRINT", c(k[1])))
        else:
            out.append(k)
    return out


def hedefler(prog):
    return {k[-1] for k in prog if k[0] in ("GOTO", "IFFALSE")}


def erisilemez_sil(prog):
    """goto'dan sonra, HEDEFİ OLAN bir etikete kadar sil."""
    hedef = hedefler(prog)
    out, olu = [], False
    for k in prog:
        if k[0] == "LABEL" and k[1] in hedef:
            olu = False
        if not olu:
            out.append(k)
            if k[0] == "GOTO":
                olu = True
    return out


def gereksiz_atlama_sil(prog):
    """'goto L' hemen 'L:' önceyse atlama boştur: sil."""
    out = []
    for i, k in enumerate(prog):
        sonraki = prog[i + 1] if i + 1 < len(prog) else None
        if k[0] == "GOTO" and sonraki == ("LABEL", k[1]):
            continue
        out.append(k)
    return out


def etiket_sil(prog):
    hedef = hedefler(prog)
    return [k for k in prog if k[0] != "LABEL" or k[1] in hedef]


def ardil(prog, i, etiket):
    k = prog[i]
    if k[0] == "GOTO":
        return [etiket[k[1]]]
    if k[0] == "IFFALSE":
        return [i + 1, etiket[k[2]]]
    return [i + 1] if i + 1 < len(prog) else []


def kullanim(k):
    """(okunan isimler, yazılan isim): sabitler okunmaz."""
    if k[0] == "COPY":
        oku, yaz = [k[2]], k[1]
    elif k[0] == "BIN":
        oku, yaz = [k[3], k[4]], k[1]
    elif k[0] in ("IFFALSE", "PRINT"):
        oku, yaz = [k[1]], None
    else:
        oku, yaz = [], None
    return {x for x in oku if not sayi(x)}, yaz


def olu_atamalari_sil(prog):
    """Canlı değişken analizi (geriye doğru sabit nokta)."""
    etiket = {k[1]: i for i, k in enumerate(prog) if k[0] == "LABEL"}
    n = len(prog)
    canli = [set() for _ in range(n)]
    degisti = True
    while degisti:
        degisti = False
        for i in range(n - 1, -1, -1):
            cikis = set().union(*[canli[j]
                                  for j in ardil(prog, i, etiket)])
            oku, yaz = kullanim(prog[i])
            giris = oku | (cikis - {yaz})
            if giris != canli[i]:
                canli[i] = giris
                degisti = True
    out = []
    for i, k in enumerate(prog):
        if k[0] in ("COPY", "BIN"):
            cikis = set().union(*[canli[j]
                                  for j in ardil(prog, i, etiket)])
            if k[1] not in cikis:            # hiç okunmuyor: ölü
                continue
        out.append(k)
    return out


def blok_bol(prog):
    """Lider: ilk komut, atlama hedefleri, atlamadan sonraki komut."""
    etiket = {k[1]: i for i, k in enumerate(prog) if k[0] == "LABEL"}
    lider = {0} | set(etiket.values())
    for i, k in enumerate(prog):
        if k[0] in ("GOTO", "IFFALSE"):
            lider |= {i + 1, etiket[k[-1]]}
    lider = sorted(x for x in lider if x < len(prog))
    return [(a, prog[a:b])
            for a, b in zip(lider, lider[1:] + [len(prog)])]


def optimize(prog):
    """Geçişleri değişiklik kalmayana dek uygula."""
    while True:
        t = prog
        for g in (sabit_katla, erisilemez_sil, gereksiz_atlama_sil,
                  etiket_sil, olu_atamalari_sil):
            t = g(t)
        if t == prog:
            return prog
        prog = t


ORNEK = """
x = 2 * 3
t1 = x + 4
y = t1 * a
t2 = 5 * 5
if_false t2 goto L1
goto L2
y = 0
L1:
print y
L2:
print x
"""

if __name__ == "__main__":
    once = ayristir(ORNEK)
    sonra = optimize(once)
    girdi = {"a": 7}
    c1, a1 = calistir(once, girdi)
    c2, a2 = calistir(sonra, girdi)
    say = lambda p: len([k for k in p if k[0] != "LABEL"])
    print("önce  komut:", say(once), " çalışma adımı:", a1)
    print("sonra komut:", say(sonra), " çalışma adımı:", a2)
    print("çıktı önce :", c1, " sonra:", c2)
    assert c1 == c2
    for i, (b, komutlar) in enumerate(blok_bol(sonra)):
        print(f"B{i} (komut {b}): {komutlar}")
