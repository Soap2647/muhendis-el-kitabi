# -*- coding: utf-8 -*-
"""Mini: uçtan uca hat: kaynak -> AST -> analiz -> bayt kodu."""
from mini_on import tokenize, HataDerleme
from mini_ayr import Ayristirici
from anlam import Analizci
from derle import Derleyici, VM
from agac import AgacYorumcu


def on_isle(kaynak):
    """Ortak ön uç: ayrıştır ve anlamsal denetim yap."""
    program = Ayristirici(tokenize(kaynak)).program()
    main_locals = Analizci(program).analiz()
    return program, main_locals


def vm_ile_calistir(kaynak):
    program, main_locals = on_isle(kaynak)
    kodlar = Derleyici().derle(program, main_locals)
    vm = VM(kodlar)
    vm.calistir()
    return vm


def agacla_calistir(kaynak):
    program, main_locals = on_isle(kaynak)
    return AgacYorumcu().calistir(program, main_locals)


if __name__ == "__main__":
    ornek = """
fn kare(x) { return x * x; }
let a = 3;
let b = kare(a) + 1;
print b;
let i = 0;
let s = 0;
while (i < 5) {
    s = s + i * i;
    i = i + 1;
}
print s;
"""
    vm = vm_ile_calistir(ornek)
    print("VM      :", vm.ciktilar)
    print("agac    :", agacla_calistir(ornek))
