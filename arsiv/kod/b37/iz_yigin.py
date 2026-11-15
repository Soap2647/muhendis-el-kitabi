# -*- coding: utf-8 -*-
"""Yığın ve çerçeve izi: VM'in her komuttan önceki durumu."""
from mini import on_isle
from derle import Derleyici, VM

ornek = "fn kare(x) { return x * x; } print kare(3) + 1;"
program, ml = on_isle(ornek)
vm = VM(Derleyici().derle(program, ml))
iz = []
vm.calistir(iz)
for ad, op, arg, yigin, derinlik in iz:
    print(f"{ad:9} {op:6} {str(arg or ''):10} "
          f"yigin={yigin} derinlik={derinlik}")
