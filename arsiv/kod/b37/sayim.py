# -*- coding: utf-8 -*-
"""Komut sayısı ve ziyaret sayısı: neden iki yürütücü farklı hızda?"""
from mini import on_isle
from derle import Derleyici, VM
from agac import AgacYorumcu
from olcum import KAYNAK


class Sayan(AgacYorumcu):
    sayac = 0

    def ifade(self, e, env):
        Sayan.sayac += 1
        return super().ifade(e, env)

    def deyim(self, s, env):
        Sayan.sayac += 1
        return super().deyim(s, env)


n = 100000
program, ml = on_isle(KAYNAK.format(n=n))
vm = VM(Derleyici().derle(program, ml))
vm.calistir()
Sayan().calistir(program, ml)
print("iterasyon:", n)
print("VM komut sayısı:", vm.komut_sayisi,
      "-> iterasyon başına", vm.komut_sayisi // n)
print("ağaç ziyaret sayısı:", Sayan.sayac,
      "-> iterasyon başına", Sayan.sayac // n)
