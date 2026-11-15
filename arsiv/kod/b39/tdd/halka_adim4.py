class HalkaTampon:
    """Adım 2: en basit çözüm, düz liste."""

    def __init__(self, kapasite):
        self.kapasite = kapasite
        self.veri = []

    def __len__(self):
        return len(self.veri)

    def bos(self):
        return not self.veri

    def ekle(self, x):
        if len(self.veri) >= self.kapasite:
            raise BufferError("tampon dolu")
        self.veri.append(x)

    def al(self):
        if not self.veri:
            raise IndexError("tampon boş")
        return self.veri.pop(0)
