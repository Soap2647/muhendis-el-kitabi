class HalkaTampon:
    """Sabit kapasiteli FIFO halka tamponu (dizi tabanlı)."""

    def __init__(self, kapasite):
        if kapasite <= 0:
            raise ValueError("kapasite pozitif olmalı")
        self._veri = [None] * kapasite
        self._bas = 0       # en eski elemanın indeksi
        self._boyut = 0     # tampondaki eleman sayısı

    def __len__(self):
        return self._boyut

    def bos(self):
        return self._boyut == 0

    def ekle(self, x):
        if self._boyut == len(self._veri):
            raise BufferError("tampon dolu")
        son = (self._bas + self._boyut) % len(self._veri)
        self._veri[son] = x
        self._boyut += 1

    def al(self):
        if self._boyut == 0:
            raise IndexError("tampon boş")
        x = self._veri[self._bas]
        self._veri[self._bas] = None
        self._bas = (self._bas + 1) % len(self._veri)
        self._boyut -= 1
        return x
