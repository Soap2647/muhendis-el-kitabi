# ornek2.py: IHA durum tablosunun tam taranmasi (Ornek 2)
from durum import YERDE, KALKIS, SEYIR, INIS, Ucak, GecersizGecis

OLAYLAR = ["kalkis_emri", "irtifa_ulasti", "inis_emri", "pist_temas"]
DURUMLAR = [YERDE, KALKIS, SEYIR, INIS]

print("%-8s" % "durum" + "".join("%-14s" % e for e in OLAYLAR))
gecerli = 0
for d in DURUMLAR:
    satir = []
    for e in OLAYLAR:
        u = Ucak()
        u.durum = d
        try:
            satir.append(u.olay(e))
            gecerli += 1
        except GecersizGecis:
            assert u.durum is d            # red: durum degismedi
            satir.append("X")
    print("%-8s" % d.ad + "".join("%-14s" % s for s in satir))
print("gecerli gecis:", gecerli, "/ 16")
