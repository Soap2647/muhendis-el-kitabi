# Ad bozma (name mangling): __x sinif adiyla degisir
class Hesap:
    def __init__(self):
        self._ic = 1        # tek alt cizgi: "dokunma" kurali
        self.__gizli = 2    # cift alt cizgi: ad bozulur

h = Hesap()
print(sorted(vars(h)))
print(h._Hesap__gizli)
print(hasattr(h, "__gizli"))
