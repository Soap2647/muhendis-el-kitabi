# komut.py: komutlari kapanislarla (closure) nesneleştirmek (22.11)
class Komut:
    """Calistir ve geri al islevlerini bir arada tutar."""
    def __init__(self, ad, calistir, geri_al):
        self.ad = ad
        self.calistir = calistir
        self.geri_al = geri_al


class Editor:
    def __init__(self):
        self.metin = ""
        self._geri = []     # geri al yigini
        self._ileri = []    # yinele yigini

    def yap(self, k):
        k.calistir()
        self._geri.append(k)
        self._ileri.clear()

    def geri(self):
        if not self._geri:
            return False
        k = self._geri.pop()
        k.geri_al()
        self._ileri.append(k)
        return True

    def yinele(self):
        if not self._ileri:
            return False
        k = self._ileri.pop()
        k.calistir()
        self._geri.append(k)
        return True


def ekle(ed, yazi):
    onceki = None                      # kapanisin yakaladigi durum

    def calistir():
        nonlocal onceki
        onceki = ed.metin
        ed.metin = ed.metin + yazi

    def geri_al():
        ed.metin = onceki
    return Komut("ekle(%s)" % yazi, calistir, geri_al)


def sil(ed, k):
    silinen = ""

    def calistir():
        nonlocal silinen
        silinen = ed.metin[len(ed.metin) - k:]
        ed.metin = ed.metin[:len(ed.metin) - k]

    def geri_al():
        ed.metin = ed.metin + silinen
    return Komut("sil(%d)" % k, calistir, geri_al)


if __name__ == "__main__":
    ed = Editor()
    ed.yap(ekle(ed, "Merhaba"))
    ed.yap(ekle(ed, " dunya"))
    ed.yap(sil(ed, 5))
    print(repr(ed.metin))
    ed.geri()
    ed.geri()
    print(repr(ed.metin))
    ed.yinele()
    print(repr(ed.metin))
