# -*- coding: utf-8 -*-
"""Yığın ve çerçeve izi: her komuttan sonra durum."""
from mini import on_isle
from derle import Derleyici, BIN, VM

def iz(kaynak, goster_cerceve=True):
    program, ml = on_isle(kaynak)
    kodlar = Derleyici().derle(program, ml)
    ana = kodlar["__main__"]
    yigin = []
    cerceve = [["__main__", 0, [0] * ana.nlocals]]
    satirlar = []
    while True:
        c = cerceve[-1]
        kod = kodlar[c[0]]
        op, arg = kod.komutlar[c[1]]
        c[1] += 1
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
            if not yigin.pop(): c[1] = arg
        elif op == "JMP":
            c[1] = arg
        elif op == "PRINT":
            yigin.pop()
        elif op == "CALL":
            ad, argc = arg
            h = kodlar[ad]; ilk = len(yigin) - argc
            args = yigin[ilk:]; del yigin[ilk:]
            cerceve.append([ad, 0, args + [0] * (h.nlocals - argc)])
        elif op == "RET":
            d = yigin.pop(); cerceve.pop(); yigin.append(d)
        elif op == "HALT":
            break
        satirlar.append((c[0] if op not in ("CALL","RET") else c[0],
                         f"{op:6} {'' if arg is None else arg!s:12}",
                         list(yigin),
                         [(f[0], f[1], f[2][:]) for f in cerceve]))
    return satirlar, kodlar

if __name__ == "__main__":
    import sys
    ornek = sys.argv[1] if len(sys.argv) > 1 else "print 2 + 3 * 4;"
    s, kodlar = iz(ornek)
    for ad, k in kodlar.items():
        print(ad, k.nlocals, k.komutlar)
    for f, op, y, cer in s:
        cz = [(q[0], q[1]) for q in cer]
        yr = [q[2] for q in cer]
        print(f"{f:9} {op}  yigin={y}  cerceve={cz} yerel={yr}")
