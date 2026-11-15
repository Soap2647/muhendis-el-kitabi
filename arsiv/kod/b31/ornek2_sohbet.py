# -*- coding: utf-8 -*-
"""Ornek 2: yayin ve istemci ayrilmasi (soket yerine sahte nesne)."""


class Sahte:
    def __init__(self, ad):
        self.ad = ad
        self.kutu = []
        self.acik = True

    def gonder(self, metin):
        if not self.acik:
            raise BrokenPipeError(self.ad)
        self.kutu.append(metin)


def yayinla(kullanicilar, gonderen, metin):
    kopuk = []
    for ad, soket in list(kullanicilar.items()):
        if ad == gonderen:
            continue                      # gonderene geri yollama yok
        try:
            soket.gonder("%s: %s" % (gonderen, metin))
        except BrokenPipeError:
            kopuk.append(ad)
    for ad in kopuk:                      # kopani listeden cikar
        del kullanicilar[ad]
    return kopuk


kullanicilar = {"ali": Sahte("ali"), "ayse": Sahte("ayse"),
                "mert": Sahte("mert")}
kullanicilar["ayse"].acik = False         # ayse baglantiyi kesti
print("kopan:", yayinla(kullanicilar, "ali", "merhaba"))
print("kullanicilar:", sorted(kullanicilar))
print("mert kutusu:", kullanicilar["mert"].kutu)
print("ali kutusu:", kullanicilar["ali"].kutu)
print("kopan:", yayinla(kullanicilar, "mert", "nasilsin"))
