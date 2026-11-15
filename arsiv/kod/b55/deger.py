# deger.py: skaler ters mod otomatik türev motoru (micrograd tarzı).
# Her Deger bir sayı (veri), onun gradyanı (grad), kendisini üreten
# işlemin geri yayılım adımı (_geri) ve girdileri (_ebeveynler) tutar.
import math

# Deney anahtarı. True: gradyan birikir (+=), doğru davranış.
# False: gradyan üzerine yazılır (=), bilerek yapılan hatalı sürüm.
BIRIKIR = True


def _ekle(dugum, g):
    # Gradyan katkısını düğüme ekler. Aynı düğüm birden fazla yoldan
    # kullanılıyorsa katkılar toplanır (çok değişkenli zincir kuralı).
    if BIRIKIR:
        dugum.grad += g
    else:
        dugum.grad = g


def topo(kok):
    # Bölüm 17.3'teki DFS tabanlı topolojik sıralama: bir düğüm,
    # girdilerinin hepsinden sonra gelir.
    sira, ziyaret = [], set()

    def dfs(v):
        if v in ziyaret:
            return
        ziyaret.add(v)
        for e in v._ebeveynler:
            dfs(e)
        sira.append(v)

    dfs(kok)
    return sira


class Deger:
    def __init__(self, veri, ebeveynler=(), islem=""):
        self.veri = float(veri)
        self.grad = 0.0
        self._geri = lambda: None
        self._ebeveynler = tuple(ebeveynler)
        self._islem = islem

    def __repr__(self):
        return f"Deger({self.veri:.4f}, grad={self.grad:.4f})"

    @staticmethod
    def _sar(x):
        return x if isinstance(x, Deger) else Deger(x)

    def __add__(self, diger):
        diger = self._sar(diger)
        cikis = Deger(self.veri + diger.veri, (self, diger), "+")

        def _geri():
            _ekle(self, cikis.grad)
            _ekle(diger, cikis.grad)
        cikis._geri = _geri
        return cikis

    def __mul__(self, diger):
        diger = self._sar(diger)
        cikis = Deger(self.veri * diger.veri, (self, diger), "*")

        def _geri():
            _ekle(self, diger.veri * cikis.grad)
            _ekle(diger, self.veri * cikis.grad)
        cikis._geri = _geri
        return cikis

    def __pow__(self, n):
        # Yalnızca sabit (int/float) üs desteklenir.
        assert isinstance(n, (int, float))
        cikis = Deger(self.veri ** n, (self,), f"**{n}")

        def _geri():
            _ekle(self, n * self.veri ** (n - 1) * cikis.grad)
        cikis._geri = _geri
        return cikis

    def exp(self):
        e = math.exp(self.veri)
        cikis = Deger(e, (self,), "exp")

        def _geri():
            _ekle(self, e * cikis.grad)
        cikis._geri = _geri
        return cikis

    def log(self):
        cikis = Deger(math.log(self.veri), (self,), "log")

        def _geri():
            _ekle(self, cikis.grad / self.veri)
        cikis._geri = _geri
        return cikis

    def tanh(self):
        t = math.tanh(self.veri)
        cikis = Deger(t, (self,), "tanh")

        def _geri():
            _ekle(self, (1 - t * t) * cikis.grad)
        cikis._geri = _geri
        return cikis

    def relu(self):
        cikis = Deger(max(0.0, self.veri), (self,), "relu")

        def _geri():
            _ekle(self, float(cikis.veri > 0) * cikis.grad)
        cikis._geri = _geri
        return cikis

    def geri(self):
        # Çıkıştan girdilere doğru her düğümün _geri adımını çalıştır.
        sira = topo(self)
        self.grad = 1.0          # d(self)/d(self) = 1
        for v in reversed(sira):
            v._geri()

    def __neg__(self):
        return self * -1

    def __radd__(self, diger):
        return self + diger

    def __sub__(self, diger):
        return self + (-self._sar(diger))

    def __rsub__(self, diger):
        return self._sar(diger) + (-self)

    def __rmul__(self, diger):
        return self * diger

    def __truediv__(self, diger):
        return self * self._sar(diger) ** -1

    def __rtruediv__(self, diger):
        return self._sar(diger) * self ** -1
