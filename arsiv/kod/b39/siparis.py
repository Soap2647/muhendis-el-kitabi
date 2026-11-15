"""Test ikizlerini göstermek için küçük bir sipariş servisi."""


class StokYetersiz(Exception):
    pass


class SiparisServisi:
    def __init__(self, depo, eposta):
        self.depo = depo          # bağımlılık: stok deposu
        self.eposta = eposta      # bağımlılık: bildirim gönderici

    def olustur(self, urun, adet):
        if adet <= 0:
            raise ValueError("adet pozitif olmalı")
        if self.depo.stok_al(urun) < adet:
            raise StokYetersiz(urun)
        self.depo.stok_dus(urun, adet)
        self.eposta.gonder("siparis", urun, adet)
        return "onay"


class SiparisServisiV2(SiparisServisi):
    """Dış davranış aynı; stok kontrolü ve düşüm tek çağrıda."""

    def olustur(self, urun, adet):
        if adet <= 0:
            raise ValueError("adet pozitif olmalı")
        if not self.depo.stok_dus_dene(urun, adet):
            raise StokYetersiz(urun)
        self.eposta.gonder("siparis", urun, adet)
        return "onay"


class BellekDeposu:
    """Fake: gerçek davranışı olan, bellekte çalışan hafif depo."""

    def __init__(self, stoklar):
        self.stoklar = dict(stoklar)

    def stok_al(self, urun):
        return self.stoklar.get(urun, 0)

    def stok_dus(self, urun, adet):
        self.stoklar[urun] -= adet

    def stok_dus_dene(self, urun, adet):
        if self.stoklar.get(urun, 0) < adet:
            return False
        self.stoklar[urun] -= adet
        return True


class KayitliEposta:
    """Spy: gönderilen mesajları kaydeder, gerçekte göndermez."""

    def __init__(self):
        self.mesajlar = []

    def gonder(self, tur, urun, adet):
        self.mesajlar.append((tur, urun, adet))
