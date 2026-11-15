# durum.py: IHA ucus modlari, durum nesneleri (Bolum 22.12)
class GecersizGecis(Exception):
    pass


class Durum:
    ad = "?"

    def olay(self, ucak, e):
        mesaj = "%s durumunda %s olayi yok" % (self.ad, e)
        raise GecersizGecis(mesaj)


class Yerde(Durum):
    ad = "YERDE"

    def olay(self, ucak, e):
        if e == "kalkis_emri":
            return KALKIS
        return super().olay(ucak, e)


class Kalkis(Durum):
    ad = "KALKIS"

    def olay(self, ucak, e):
        if e == "irtifa_ulasti":
            return SEYIR
        return super().olay(ucak, e)


class Seyir(Durum):
    ad = "SEYIR"

    def olay(self, ucak, e):
        if e == "inis_emri":
            return INIS
        return super().olay(ucak, e)


class Inis(Durum):
    ad = "INIS"

    def olay(self, ucak, e):
        if e == "pist_temas":
            return YERDE
        return super().olay(ucak, e)


YERDE, KALKIS, SEYIR, INIS = Yerde(), Kalkis(), Seyir(), Inis()


class Ucak:
    def __init__(self):
        self.durum = YERDE

    def olay(self, e):
        self.durum = self.durum.olay(self, e)   # hata varsa atama yok
        return self.durum.ad


OLAYLAR = ["kalkis_emri", "irtifa_ulasti", "inis_emri", "pist_temas"]
BEKLENEN = {("YERDE", "kalkis_emri"): "KALKIS",
            ("KALKIS", "irtifa_ulasti"): "SEYIR",
            ("SEYIR", "inis_emri"): "INIS",
            ("INIS", "pist_temas"): "YERDE"}


if __name__ == "__main__":
    gecerli = reddedilen = 0
    for d in [YERDE, KALKIS, SEYIR, INIS]:
        for e in OLAYLAR:
            u = Ucak()
            u.durum = d
            try:
                sonuc = u.olay(e)
                assert BEKLENEN[(d.ad, e)] == sonuc
                gecerli += 1
            except GecersizGecis:
                assert (d.ad, e) not in BEKLENEN
                assert u.durum is d
                reddedilen += 1
    print("gecerli:", gecerli, "reddedilen:", reddedilen)
    u = Ucak()
    for e in OLAYLAR:
        print(e, "->", u.olay(e))
