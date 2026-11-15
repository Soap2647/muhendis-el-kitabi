# -*- coding: utf-8 -*-
"""Yigin makinesi bayt kodu derleyicisi ve sanal makine (VM)."""
import operator
from mini_on import (Sayi, Degisken, Ikili, Tekli, Cagri, Let, Ata,
                     Yaz, Eger, Dongu, Don, Ifade, Fonksiyon)


class CalismaHatasi(Exception):
    pass


def c_bol(a, b):
    """C99 gibi: tam sayı bölme sıfıra doğru yuvarlar (-7/2=-3)."""
    if b == 0:
        raise CalismaHatasi("sıfıra bölme")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def c_mod(a, b):
    return a - b * c_bol(a, b)


BIN = {"ADD": operator.add, "SUB": operator.sub,
       "MUL": operator.mul, "DIV": c_bol, "MOD": c_mod,
       "LT": operator.lt, "LE": operator.le,
       "GT": operator.gt, "GE": operator.ge,
       "EQ": operator.eq, "NE": operator.ne}
IKILI_OP = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV",
            "%": "MOD", "<": "LT", "<=": "LE", ">": "GT",
            ">=": "GE", "==": "EQ", "!=": "NE"}


class Kod:
    def __init__(self, ad, nlocals, nargs):
        self.ad = ad
        self.nlocals = nlocals
        self.nargs = nargs
        self.komutlar = []      # [op, arg] listesi


class Derleyici:
    def __init__(self):
        self.kod = None
        self.kodlar = {}

    def yay(self, op, arg=None):
        self.kod.komutlar.append([op, arg])
        return len(self.kod.komutlar) - 1

    def yama(self, idx):
        """Atlama hedefini simdiki konuma (sonraki komut) bağla."""
        self.kod.komutlar[idx][1] = len(self.kod.komutlar)

    def derle(self, program, main_locals):
        for d in program:
            if isinstance(d, Fonksiyon):
                self.kod = Kod(d.ad, d.nlocals, len(d.params))
                for s in d.govde:
                    self.deyim(s)
                self.yay("PUSH", 0)     # dusersen 0 dondur
                self.yay("RET")
                self.kodlar[d.ad] = self.kod
        self.kod = Kod("__main__", main_locals, 0)
        for d in program:
            if not isinstance(d, Fonksiyon):
                self.deyim(d)
        self.yay("HALT")
        self.kodlar["__main__"] = self.kod
        return self.kodlar

    def deyim(self, s):
        if isinstance(s, (Let, Ata)):
            self.ifade(s.ifade)
            self.yay("STORE", s.slot)
        elif isinstance(s, Yaz):
            self.ifade(s.ifade)
            self.yay("PRINT")
        elif isinstance(s, Ifade):
            self.ifade(s.ifade)
            self.yay("POP")
        elif isinstance(s, Don):
            self.ifade(s.ifade)
            self.yay("RET")
        elif isinstance(s, Eger):
            self.ifade(s.kosul)
            jz = self.yay("JZ")
            for x in s.dal:
                self.deyim(x)
            if s.dal_degil is None:
                self.yama(jz)
            else:
                jmp = self.yay("JMP")
                self.yama(jz)
                for x in s.dal_degil:
                    self.deyim(x)
                self.yama(jmp)
        elif isinstance(s, Dongu):
            bas = len(self.kod.komutlar)
            self.ifade(s.kosul)
            jz = self.yay("JZ")
            for x in s.govde:
                self.deyim(x)
            self.yay("JMP", bas)
            self.yama(jz)

    def ifade(self, e):
        if isinstance(e, Sayi):
            self.yay("PUSH", e.deger)
        elif isinstance(e, Degisken):
            self.yay("LOAD", e.slot)
        elif isinstance(e, Tekli):
            self.ifade(e.ey)
            self.yay("NEG")
        elif isinstance(e, Ikili):
            self.ifade(e.sol)
            self.ifade(e.sag)
            self.yay(IKILI_OP[e.op])
        elif isinstance(e, Cagri):
            for a in e.args:
                self.ifade(a)
            self.yay("CALL", (e.ad, len(e.args)))
        else:
            raise AssertionError(type(e))


class VM:
    def __init__(self, kodlar):
        self.kodlar = kodlar
        self.ciktilar = []
        self.komut_sayisi = 0

    def calistir(self, izle=None):
        """izle bir listeyse her komut için bilgi eklenir."""
        ana = self.kodlar["__main__"]
        yigin = []                             # islenen yığın
        # Cerceve: [kod, pc, yerel_slotlar]; çağrı = yeni çerçeve
        cerceve = [[ana, 0, [0] * ana.nlocals]]
        while True:
            c = cerceve[-1]
            op, arg = c[0].komutlar[c[1]]
            c[1] += 1
            self.komut_sayisi += 1
            if izle is not None:
                izle.append((c[0].ad, op, arg, list(yigin),
                             len(cerceve)))
            if op == "PUSH":
                yigin.append(arg)
            elif op == "LOAD":
                yigin.append(c[2][arg])
            elif op == "STORE":
                c[2][arg] = yigin.pop()
            elif op == "POP":
                yigin.pop()
            elif op in BIN:
                b = yigin.pop()
                a = yigin.pop()
                yigin.append(BIN[op](a, b))
            elif op == "NEG":
                yigin.append(-yigin.pop())
            elif op == "JZ":
                if not yigin.pop():
                    c[1] = arg
            elif op == "JMP":
                c[1] = arg
            elif op == "PRINT":
                self.ciktilar.append(yigin.pop())
            elif op == "CALL":
                ad, argc = arg
                hedef = self.kodlar[ad]
                ilk = len(yigin) - argc
                args = yigin[ilk:]
                del yigin[ilk:]
                yerel = args + [0] * (hedef.nlocals - argc)
                cerceve.append([hedef, 0, yerel])
            elif op == "RET":
                deger = yigin.pop()
                cerceve.pop()
                yigin.append(deger)
            elif op == "HALT":
                return self.ciktilar
            else:
                raise AssertionError(op)
