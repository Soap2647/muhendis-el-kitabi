# Coklu kalitim: elmas problemi ve C3 dogrusallastirma (MRO)
class A:
    def hazirla(self):
        print("A.hazirla")
        return ["A"]

class B(A):
    def hazirla(self):
        print("B.hazirla")
        return ["B"] + super().hazirla()

class C(A):
    def hazirla(self):
        print("C.hazirla")
        return ["C"] + super().hazirla()

class D(B, C):
    def hazirla(self):
        print("D.hazirla")
        return ["D"] + super().hazirla()

print([k.__name__ for k in D.__mro__])
print(D().hazirla())

# Yanlis siralama: once A, sonra B: MRO kurulamaz
try:
    class E(A, B):
        pass
except TypeError as e:
    print("TypeError:", e)

# Ad bozma (name mangling)
class Hesap:
    def __init__(self):
        self._ic = 1        # tek alt cizgi: "lutfen dokunma" kurali
        self.__gizli = 2    # cift alt cizgi: ad bozulur
h = Hesap()
print(sorted(vars(h)))
print(h._Hesap__gizli)
