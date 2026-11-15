"""Ozyinelemeli inis (recursive descent) ile aritmetik ifade.

Dilbilgisi:
    ifade := terim (('+' | '-') terim)*
    terim := carpan (('*' | '/') carpan)*
    carpan := SAYI | '(' ifade ')' | '-' carpan
"""


class AyristiHatasi(Exception):
    pass


def belirtecle(metin):
    sonuc = []
    i = 0
    while i < len(metin):
        c = metin[i]
        if c.isspace():
            i += 1
        elif c.isdigit():
            j = i
            while j < len(metin) and metin[j].isdigit():
                j += 1
            sonuc.append(metin[i:j])
            i = j
        elif c in "+-*/()":
            sonuc.append(c)
            i += 1
        else:
            raise AyristiHatasi("beklenmeyen karakter %r" % c)
    return sonuc


class Ayristirici:
    def __init__(self, metin):
        self.belirtec = belirtecle(metin)
        self.konum = 0

    def _bak(self):
        if self.konum < len(self.belirtec):
            return self.belirtec[self.konum]
        return None

    def _al(self):
        t = self._bak()
        self.konum += 1
        return t

    def ifade(self):
        deger = self.terim()
        while self._bak() in ("+", "-"):
            op = self._al()
            sag = self.terim()
            deger = deger + sag if op == "+" else deger - sag
        return deger

    def terim(self):
        deger = self.carpan()
        while self._bak() in ("*", "/"):
            op = self._al()
            sag = self.carpan()
            if op == "*":
                deger = deger * sag
            else:
                if sag == 0:
                    raise AyristiHatasi("sifira bolme")
                deger = deger / sag
        return deger

    def carpan(self):
        t = self._al()
        if t is None:
            raise AyristiHatasi("beklenmeyen ifade sonu")
        if t == "-":
            return -self.carpan()
        if t == "(":
            deger = self.ifade()
            if self._al() != ")":
                raise AyristiHatasi("')' bekleniyordu")
            return deger
        if t.isdigit():
            return int(t)
        raise AyristiHatasi("beklenmeyen belirtec %r" % t)


def hesapla(metin):
    p = Ayristirici(metin)
    deger = p.ifade()
    if p.konum != len(p.belirtec):
        raise AyristiHatasi("fazla belirtec: %r" % p._bak())
    return deger


def en_derin_parantez():
    lo, hi = 1, 2000
    while lo < hi:
        orta = (lo + hi + 1) // 2
        try:
            hesapla("(" * orta + "1" + ")" * orta)
            lo = orta
        except RecursionError:
            hi = orta - 1
    return lo


if __name__ == "__main__":
    ornekler = [
        "2 + 3 * 4",
        "(2 + 3) * 4",
        "10 - 4 - 3",
        "-(2 + 3) * 2",
        "7 / 2",
        "(2 + 3",
        "",
        "8 / (4 - 4)",
        "2 $ 3",
    ]
    for metin in ornekler:
        try:
            sonuc = hesapla(metin)
        except AyristiHatasi as hata:
            sonuc = "HATA: " + str(hata)
        print("%-14r -> %s" % (metin, sonuc))
    for d in (100, 500, 1000):
        metin = "(" * d + "1" + ")" * d
        try:
            print("%4d parantez -> %s" % (d, hesapla(metin)))
        except RecursionError:
            print("%4d parantez -> RecursionError" % d)
    print("en derin calisan parantez:", en_derin_parantez())
