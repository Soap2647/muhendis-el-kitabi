# -*- coding: utf-8 -*-
"""VM'in hizlandirilmis surumu: ayni bayt kodu, ayni anlam."""
from derle import VM, BIN

class VMHizli(VM):
    """Sayac yok, sik komutlar basta, yerel değişkenler."""
    def calistir(self):
        ana = self.kodlar["__main__"]
        yigin = []
        pop = yigin.pop
        push = yigin.append
        cerceve = [[ana, 0, [0] * ana.nlocals]]
        ciktilar = self.ciktilar
        while True:
            c = cerceve[-1]
            op, arg = c[0].komutlar[c[1]]
            c[1] += 1
            if op == "LOAD":
                push(c[2][arg])
            elif op == "PUSH":
                push(arg)
            elif op in BIN:
                b = pop()
                push(BIN[op](pop(), b))
            elif op == "STORE":
                c[2][arg] = pop()
            elif op == "JZ":
                if not pop():
                    c[1] = arg
            elif op == "JMP":
                c[1] = arg
            elif op == "PRINT":
                ciktilar.append(pop())
            elif op == "POP":
                pop()
            elif op == "NEG":
                push(-pop())
            elif op == "CALL":
                ad, argc = arg
                hedef = self.kodlar[ad]
                ilk = len(yigin) - argc
                args = yigin[ilk:]
                del yigin[ilk:]
                cerceve.append([hedef, 0,
                                args + [0] * (hedef.nlocals - argc)])
            elif op == "RET":
                deger = pop()
                cerceve.pop()
                push(deger)
            elif op == "HALT":
                return ciktilar
