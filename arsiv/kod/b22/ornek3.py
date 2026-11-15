# ornek3.py: esik alarmi, abonelikten cikma, zayif referans (Ornek 3)
from gozlemci import Konu, Alarm

k = Konu()
kritik = Alarm("kritik", 80)
gecici = Alarm("gecici", 50)
k.abone_ol(kritik.olay)
k.abone_ol(gecici.olay)
for d in [40, 60, 85]:
    print("olcum", d)
    k.bildir(d)
k.cik(gecici.olay)                  # gecici abonelikten cikar
print("cikis sonrasi olcum 90")
k.bildir(90)
print("gecici:", gecici.kayitlar, "| kritik:", kritik.kayitlar)
ge = Alarm("ge", 0)
k.abone_ol(ge.olay)
del ge                              # Konu nesneyi tutmaz
k.bildir(5)
print("abone sayisi:", len(k._gozlemciler))
