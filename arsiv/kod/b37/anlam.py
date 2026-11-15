# -*- coding: utf-8 -*-
"""Anlamsal analiz: kapsam, tur denetimi, slot atamasi."""
from mini_on import (HataDerleme, Sayi, Degisken, Ikili, Tekli, Cagri,
                     Let, Ata, Yaz, Eger, Dongu, Don, Fonksiyon,
                     Ifade)

KARSILASTIRMA = {"<", "<=", ">", ">="}
ARITMETIK = {"+", "-", "*", "/", "%"}


class Analizci:
    def __init__(self, program):
        self.program = program
        self.fonksiyonlar = {}
        self.kapsam = []        # yığın: her blok bir sozluk
        self.slot_sayaci = 0
        self.en_fazla = 0       # bu govdenin yerel slot sayısi
        self.fn_icinde = False

    def analiz(self):
        for d in self.program:              # 1. imzalar (ileri atif)
            if isinstance(d, Fonksiyon):
                if d.ad in self.fonksiyonlar:
                    raise HataDerleme(f"'{d.ad}' zaten tanımlı",
                                      d.satir, d.sutun)
                self.fonksiyonlar[d.ad] = d
        for d in self.program:              # 2. govdeler
            if isinstance(d, Fonksiyon):
                self.fonksiyon(d)
        # 3. ust duzey deyimler: "__main__" govdesi
        self.kapsam, self.slot_sayaci, self.en_fazla = [{}], 0, 0
        self.fn_icinde = False
        for d in self.program:
            if not isinstance(d, Fonksiyon):
                self.deyim(d)
        return self.en_fazla

    def fonksiyon(self, d):
        ust = (self.kapsam, self.slot_sayaci, self.en_fazla)
        self.kapsam, self.slot_sayaci, self.en_fazla = [{}], 0, 0
        self.fn_icinde = True
        for p in d.params:
            self.bildir(p, "int", d.satir, d.sutun)
        for s in d.govde:
            self.deyim(s)
        d.nlocals = self.en_fazla
        self.kapsam, self.slot_sayaci, self.en_fazla = ust
        self.fn_icinde = False

    def bildir(self, ad, tur, satir, sutun):
        cari = self.kapsam[-1]
        if ad in cari:
            raise HataDerleme(f"'{ad}' bu kapsamda zaten var",
                              satir, sutun)
        slot = self.slot_sayaci
        self.slot_sayaci += 1
        self.en_fazla = max(self.en_fazla, self.slot_sayaci)
        cari[ad] = (slot, tur)
        return slot

    def bul(self, ad, satir, sutun):
        for kap in reversed(self.kapsam):   # ic kapsamdan disa
            if ad in kap:
                return kap[ad]
        raise HataDerleme(f"tanımsız değişken '{ad}'",
                          satir, sutun)

    def beklenen(self, gercek, bekl, dugum):
        if gercek != bekl:
            raise HataDerleme(f"tür uyuşmazlığı: {bekl} "
                              f"bekleniyordu, "
                              f"{gercek} bulundu",
                              getattr(dugum, "satir", 0),
                              getattr(dugum, "sutun", 0))

    def blok(self, ss):
        self.kapsam.append({})
        for s in ss:
            self.deyim(s)
        self.kapsam.pop()

    def deyim(self, s):
        if isinstance(s, Let):
            tur = self.ifade(s.ifade)       # önce ifade, sonra tanım
            s.slot = self.bildir(s.ad, tur, s.satir, s.sutun)
        elif isinstance(s, Ata):
            slot, tur0 = self.bul(s.ad, s.satir, s.sutun)
            self.beklenen(self.ifade(s.ifade), tur0, s)
            s.slot = slot
        elif isinstance(s, Yaz):
            self.ifade(s.ifade)
        elif isinstance(s, Ifade):
            self.ifade(s.ifade)
        elif isinstance(s, Eger):
            self.beklenen(self.ifade(s.kosul), "bool", s.kosul)
            self.blok(s.dal)
            if s.dal_degil is not None:
                self.blok(s.dal_degil)
        elif isinstance(s, Dongu):
            self.beklenen(self.ifade(s.kosul), "bool", s.kosul)
            self.blok(s.govde)
        elif isinstance(s, Don):
            if not self.fn_icinde:
                raise HataDerleme("'return' yalnız fn içinde",
                                  s.satir, s.sutun)
            self.beklenen(self.ifade(s.ifade), "int", s.ifade)
        else:
            raise AssertionError(f"bilinmeyen deyim {type(s)}")

    def ifade(self, e):
        if isinstance(e, Sayi):
            return "bool" if isinstance(e.deger, bool) else "int"
        if isinstance(e, Degisken):
            slot, tur = self.bul(e.ad, e.satir, e.sutun)
            e.slot = slot
            return tur
        if isinstance(e, Tekli):
            self.beklenen(self.ifade(e.ey), "int", e.ey)
            return "int"
        if isinstance(e, Ikili):
            a = self.ifade(e.sol)
            b = self.ifade(e.sag)
            if e.op in ("==", "!="):
                self.beklenen(b, a, e.sag)
                return "bool"
            self.beklenen(a, "int", e.sol)
            self.beklenen(b, "int", e.sag)
            return "bool" if e.op in KARSILASTIRMA else "int"
        if isinstance(e, Cagri):
            f = self.fonksiyonlar.get(e.ad)
            if f is None:
                raise HataDerleme(f"tanımsız fonksiyon '{e.ad}'",
                                  e.satir, e.sutun)
            if len(e.args) != len(f.params):
                raise HataDerleme(
                    f"'{e.ad}' {len(f.params)} argüman ister, "
                    f"{len(e.args)} verildi", e.satir, e.sutun)
            for a in e.args:
                self.beklenen(self.ifade(a), "int", a)
            return "int"
        raise AssertionError(f"bilinmeyen ifade {type(e)}")
