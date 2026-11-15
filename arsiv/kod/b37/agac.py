# -*- coding: utf-8 -*-
"""Agac gezen yorumlayici: AST'yi doğrudan çalıştırir."""
from mini_on import (Sayi, Degisken, Ikili, Tekli, Cagri, Let, Ata,
                     Yaz, Eger, Dongu, Don, Ifade, Fonksiyon)
from derle import BIN, IKILI_OP


class DonusSinyali(Exception):
    """'return' için: üst çağrıya değer taşır."""

    def __init__(self, deger):
        self.deger = deger


class AgacYorumcu:
    def __init__(self):
        self.ciktilar = []
        self.fonk = {}
        # Dugum turunden metoda: ziyaretci kalibinin dict hali
        self.ifade_tablo = {
            Sayi: self.e_sayi, Degisken: self.e_deg,
            Tekli: self.e_tekli, Ikili: self.e_ikili,
            Cagri: self.e_cagri}
        self.deyim_tablo = {
            Let: self.d_ata, Ata: self.d_ata, Yaz: self.d_yaz,
            Ifade: self.d_ifade, Eger: self.d_eger,
            Dongu: self.d_dongu, Don: self.d_don}

    def calistir(self, program, main_locals):
        self.fonk = {d.ad: d for d in program
                     if isinstance(d, Fonksiyon)}
        env = [0] * main_locals
        for d in program:
            if not isinstance(d, Fonksiyon):
                self.deyim(d, env)
        return self.ciktilar

    # ---- deyimler ----
    def deyim(self, s, env):
        self.deyim_tablo[type(s)](s, env)

    def d_ata(self, s, env):
        env[s.slot] = self.ifade(s.ifade, env)

    def d_yaz(self, s, env):
        self.ciktilar.append(self.ifade(s.ifade, env))

    def d_ifade(self, s, env):
        self.ifade(s.ifade, env)

    def d_don(self, s, env):
        raise DonusSinyali(self.ifade(s.ifade, env))

    def d_eger(self, s, env):
        if self.ifade(s.kosul, env):
            govde = s.dal
        else:
            govde = s.dal_degil or []
        for x in govde:
            self.deyim(x, env)

    def d_dongu(self, s, env):
        while self.ifade(s.kosul, env):
            for x in s.govde:
                self.deyim(x, env)

    # ---- ifadeler ----
    def ifade(self, e, env):
        return self.ifade_tablo[type(e)](e, env)

    def e_sayi(self, e, env):
        return e.deger

    def e_deg(self, e, env):
        return env[e.slot]

    def e_tekli(self, e, env):
        return -self.ifade(e.ey, env)

    def e_ikili(self, e, env):
        a = self.ifade(e.sol, env)
        b = self.ifade(e.sag, env)
        return BIN[IKILI_OP[e.op]](a, b)

    def e_cagri(self, e, env):
        f = self.fonk[e.ad]
        args = [self.ifade(a, env) for a in e.args]
        yerel = args + [0] * (f.nlocals - len(args))
        try:
            for x in f.govde:
                self.deyim(x, yerel)
        except DonusSinyali as r:
            return r.deger
        return 0
