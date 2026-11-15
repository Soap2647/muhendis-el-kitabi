# sarici.py: nesne dekoratorleri ve fonksiyon dekoratorleri (22.7)
import functools


class Okuyucu:
    def oku(self):
        raise NotImplementedError


class Ham(Okuyucu):
    """Donanim taklidi: 2. cagri gecici hata verir."""
    def __init__(self):
        self.cagri = 0

    def oku(self):
        self.cagri += 1
        if self.cagri == 2:
            raise IOError("gecici hata")
        return 20.0 + self.cagri


class Onbellek(Okuyucu):
    def __init__(self, ic):
        self._ic = ic
        self._son = None

    def oku(self):
        if self._son is None:
            self._son = self._ic.oku()
        return self._son


class Yeniden(Okuyucu):
    def __init__(self, ic, deneme=3):
        self._ic = ic
        self._deneme = deneme

    def oku(self):
        for i in range(self._deneme):
            try:
                return self._ic.oku()
            except IOError:
                if i == self._deneme - 1:
                    raise


def olcum(f):
    @functools.wraps(f)
    def sarici(*args, **kwargs):
        sarici.cagri += 1
        return f(*args, **kwargs)
    sarici.cagri = 0
    return sarici


@olcum
def topla(a, b):
    """Iki sayiyi toplar."""
    return a + b


if __name__ == "__main__":
    ham = Ham()
    ham.cagri = 1                      # sonraki cagri 2. cagri olur
    print("yeniden:", Yeniden(ham).oku(), "ham cagri:", ham.cagri)
    print("topla:", topla(2, 3), "sayac:", topla.cagri)
    print("ad:", topla.__name__, "| __wrapped__:",
          topla.__wrapped__.__name__)
    f = open(__file__, "rb")
    print("nesne katmani:", type(f).__name__, "->",
          type(f.raw).__name__)
    f.close()
