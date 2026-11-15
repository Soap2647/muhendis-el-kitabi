# -*- coding: utf-8 -*-
"""Pratt (ustten isleyen operator önceligi) ayrıştırıcısi."""
from mini_on import (HataDerleme, Sayi, Degisken, Ikili, Tekli, Cagri,
                     Let, Ata, Yaz, Eger, Dongu, Don, Fonksiyon,
                     Ifade)

# Baglama gucu: büyük sayı = daha sikı bağlar.
GUC = {"==": 10, "!=": 10,
       "<": 20, "<=": 20, ">": 20, ">=": 20,
       "+": 30, "-": 30,
       "*": 40, "/": 40, "%": 40,
       "(": 60}            # çağrı parantezi en sikı bağlar
ONEK_GUC = 50              # tekli eksi: '*'dan sıkı, çağrıdan gevşek


class Ayristirici:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def bak(self, ileri=0):
        return self.toks[self.i + ileri]

    def ilerle(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def bekle(self, tur):
        t = self.bak()
        if t.tur != tur:
            raise HataDerleme(f"'{tur}' bekleniyordu, "
                              f"'{t.lexem}' bulundu",
                              t.satir, t.sutun)
        return self.ilerle()

    def program(self):
        out = []
        while self.bak().tur != "EOF":
            out.append(self.deyim())
        return out

    def blok(self):
        self.bekle("{")
        out = []
        while self.bak().tur != "}":
            out.append(self.deyim())
        self.bekle("}")
        return out

    def deyim(self):
        t = self.bak()
        if t.tur == "let":
            self.ilerle()
            ad = self.bekle("KIMLIK").lexem
            self.bekle("=")
            e = self.ifade()
            self.bekle(";")
            return Let(ad, e, t.satir, t.sutun)
        if t.tur == "KIMLIK" and self.bak(1).tur == "=":
            self.ilerle()
            self.ilerle()
            e = self.ifade()
            self.bekle(";")
            return Ata(t.lexem, e, t.satir, t.sutun)
        if t.tur == "print":
            self.ilerle()
            e = self.ifade()
            self.bekle(";")
            return Yaz(e)
        if t.tur == "return":
            self.ilerle()
            e = self.ifade()
            self.bekle(";")
            return Don(e, t.satir, t.sutun)
        if t.tur == "if":
            self.ilerle()
            kosul = self.ifade()
            dal = self.blok()
            dal_degil = None
            if self.bak().tur == "else":
                self.ilerle()
                dal_degil = self.blok()
            return Eger(kosul, dal, dal_degil)
        if t.tur == "while":
            self.ilerle()
            kosul = self.ifade()
            return Dongu(kosul, self.blok())
        if t.tur == "fn":
            return self.fonksiyon()
        e = self.ifade()
        self.bekle(";")
        return Ifade(e)

    def fonksiyon(self):
        t = self.ilerle()                       # 'fn'
        ad = self.bekle("KIMLIK").lexem
        self.bekle("(")
        params = []
        if self.bak().tur != ")":
            params.append(self.bekle("KIMLIK").lexem)
            while self.bak().tur == ",":
                self.ilerle()
                params.append(self.bekle("KIMLIK").lexem)
        self.bekle(")")
        return Fonksiyon(ad, params, self.blok(), t.satir, t.sutun)

    # ---------- Pratt cekirdegi ----------
    def ifade(self, guc=0):
        sol = self.oneki()
        while GUC.get(self.bak().tur, 0) > guc:
            op = self.ilerle()
            if op.tur == "(":
                if not isinstance(sol, Degisken):
                    raise HataDerleme("yalnız isimler çağrılabilir",
                                      op.satir, op.sutun)
                sol = Cagri(sol.ad, self.argumanlar(),
                            sol.satir, sol.sutun)
            else:
                sag = self.ifade(GUC[op.tur])   # sol birleşim için
                sol = Ikili(op.tur, sol, sag, op.satir, op.sutun)
        return sol

    def oneki(self):
        t = self.ilerle()
        if t.tur == "SAYI":
            return Sayi(int(t.lexem), t.satir, t.sutun)
        if t.tur in ("true", "false"):
            return Sayi(t.tur == "true", t.satir, t.sutun)
        if t.tur == "KIMLIK":
            return Degisken(t.lexem, t.satir, t.sutun)
        if t.tur == "(":
            e = self.ifade()
            self.bekle(")")
            return e
        if t.tur == "-":
            return Tekli("-", self.ifade(ONEK_GUC), t.satir, t.sutun)
        raise HataDerleme(f"ifade bekleniyordu, "
                          f"'{t.lexem or t.tur}' bulundu",
                          t.satir, t.sutun)

    def argumanlar(self):
        args = []
        if self.bak().tur != ")":
            args.append(self.ifade())
            while self.bak().tur == ",":
                self.ilerle()
                args.append(self.ifade())
        self.bekle(")")
        return args


def ayristir(kaynak):
    from mini_on import tokenize
    return Ayristirici(tokenize(kaynak)).program()
