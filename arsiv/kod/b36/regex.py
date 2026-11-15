# regex.py: düzenli ifade motoru (ayrıştırıcı + Thompson NFA)
import random
import re
from itertools import product


class Ayristirici:
    """birlesim := sira ('|' sira)*
    sira     := tekrar+
    tekrar   := atom ('*' | '+' | '?')?
    atom     := harf | '(' birlesim ')'"""

    def __init__(self, desen):
        self.s, self.i = desen, 0

    def bak(self):
        return self.s[self.i] if self.i < len(self.s) else None

    def tuket(self, bekl=None):
        c = self.bak()
        if bekl is not None and c != bekl:
            raise SyntaxError("%r bekleniyordu" % bekl)
        self.i += 1
        return c

    def birlesim(self):
        dallar = [self.sira()]
        while self.bak() == "|":
            self.tuket()
            dallar.append(self.sira())
        return ("alt", dallar) if len(dallar) > 1 else dallar[0]

    def sira(self):
        parca = [self.tekrar()]
        while self.bak() not in (None, "|", ")"):
            parca.append(self.tekrar())
        return ("cat", parca) if len(parca) > 1 else parca[0]

    def tekrar(self):
        n = self.atom()
        if self.bak() in ("*", "+", "?"):
            n = (self.tuket(), n)
        return n

    def atom(self):
        c = self.bak()
        if c == "(":
            self.tuket("(")
            n = self.birlesim()
            self.tuket(")")
            return n
        if c is None or c in "|)*+?":
            raise SyntaxError("beklenmeyen %r" % c)
        return ("chr", self.tuket())


def ayristir(desen):
    p = Ayristirici(desen)
    ag = p.birlesim()
    if p.bak() is not None:
        raise SyntaxError("fazladan %r" % p.bak())
    return ag


class Grafik:
    def __init__(self):
        self.n, self.kenar = 0, []     # kenar: (kaynak, harf, hedef)

    def yeni(self):
        self.n += 1
        return self.n - 1

    def ekle(self, a, h, b):
        self.kenar.append((a, h, b))


def thompson(ag, g):
    """AST'den (baslangic, bitis) kurar. Harf None ise ε-kenardır."""
    tur = ag[0]
    if tur == "chr":
        s, t = g.yeni(), g.yeni()
        g.ekle(s, ag[1], t)
        return s, t
    if tur == "cat":
        s, t = thompson(ag[1][0], g)
        for alt in ag[1][1:]:
            s2, t2 = thompson(alt, g)
            g.ekle(t, None, s2)
            t = t2
        return s, t
    if tur == "alt":
        s, t = g.yeni(), g.yeni()
        for dal in ag[1]:
            s2, t2 = thompson(dal, g)
            g.ekle(s, None, s2)
            g.ekle(t2, None, t)
        return s, t
    s2, t2 = thompson(ag[1], g)        # '*', '+', '?'
    s, t = g.yeni(), g.yeni()
    g.ekle(s, None, s2)
    g.ekle(t2, None, t)
    if tur in ("*", "?"):
        g.ekle(s, None, t)             # sıfır tekrar
    if tur in ("*", "+"):
        g.ekle(t2, None, s2)           # tekrar
    return s, t


class Motor:
    """Derlenmiş düzenli ifade; tam eşleşme simülasyonu."""

    def __init__(self, desen):
        g = Grafik()
        self.bas, self.son = thompson(ayristir(desen), g)
        self.n = g.n
        self.komsu = {}
        for a, h, b in g.kenar:
            self.komsu.setdefault(a, []).append((h, b))

    def kapanis(self, S):
        yigin, sonuc = list(S), set(S)
        while yigin:
            q = yigin.pop()
            for h, b in self.komsu.get(q, ()):
                if h is None and b not in sonuc:
                    sonuc.add(b)
                    yigin.append(b)
        return sonuc

    def tam_eslesir(self, w):
        S = self.kapanis({self.bas})
        for c in w:
            T = {b for q in S for h, b in self.komsu.get(q, ())
                 if h == c}
            S = self.kapanis(T)
            if not S:
                return False
        return self.son in S


def desen_uret(rng, d):
    """(desen, boş_eşleşir) çifti. Boş eşleşen grup üzerine * ve +
    konmaz: Python re bu tür iç içe döngülerde takılabiliyor."""
    if d <= 0 or rng.random() < 0.35:
        atom, bos = rng.choice("ab"), False
    else:
        s, bos = birlesim_uret(rng, d - 1)
        atom = "(" + s + ")"
    op = rng.choice(["?", "", "*", "+"])
    if op in ("*", "+") and bos:
        op = ""
    if op in ("?", "*"):
        bos = True
    return atom + op, bos


def sira_uret(rng, d):
    parca = [desen_uret(rng, d) for _ in range(rng.randint(1, 3))]
    return "".join(s for s, _ in parca), all(b for _, b in parca)


def birlesim_uret(rng, d):
    dallar = [sira_uret(rng, d) for _ in range(rng.randint(1, 2))]
    return "|".join(s for s, _ in dallar), any(b for _, b in dallar)


def dogrula(seed=36, n_desen=600, boy=6):
    rng = random.Random(seed)
    sinanan = 0
    for _ in range(n_desen):
        desen = birlesim_uret(rng, 2)[0]
        m, ref = Motor(desen), re.compile(desen)
        for k in range(boy + 1):
            for t in product("ab", repeat=k):
                w = "".join(t)
                beklenen = bool(ref.fullmatch(w))
                assert m.tam_eslesir(w) == beklenen, (desen, w)
                sinanan += 1
    return sinanan


if __name__ == "__main__":
    m = Motor("(a|b)*abb")
    print("düğüm:", m.n, "kenar:",
          sum(len(v) for v in m.komsu.values()))
    for w in ["abb", "aabb", "abab", "ab"]:
        print(w, m.tam_eslesir(w),
              bool(re.fullmatch("(a|b)*abb", w)))
    print("sinanan dizge:", dogrula())
