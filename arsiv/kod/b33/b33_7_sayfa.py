# -*- coding: utf-8 -*-
# b33_7_sayfa.py: gerçek bir SQLite dosyasını ve sayfalarını oku
import os
import sqlite3
import struct

YOL = "b33_ornek.db"
for f in (YOL, YOL + "-wal", YOL + "-shm"):
    if os.path.exists(f):
        os.remove(f)

db = sqlite3.connect(YOL)
db.execute("PRAGMA journal_mode = DELETE")
db.execute("CREATE TABLE ogrenci(no INTEGER PRIMARY KEY, ad TEXT)")
db.execute("CREATE INDEX i_ad ON ogrenci(ad)")
db.executemany("INSERT INTO ogrenci(ad) VALUES (?)",
               [("ogr%04d" % i,) for i in range(300)])
db.commit()
db.close()

with open(YOL, "rb") as f:
    veri = f.read()


def u16(bas):
    return struct.unpack(">H", veri[bas:bas + 2])[0]


def u32(bas):
    return struct.unpack(">I", veri[bas:bas + 4])[0]


ilk = veri[:100]
sayfa = u16(16)
print("sqlite", sqlite3.sqlite_version)
print("baslik:", ilk[0:16])
print("sayfa boyutu (16-17):", sayfa)
print("yazma/okuma surumu (18,19):", ilk[18], ilk[19])
print("degisiklik sayaci (24):", u32(24))
print("veritabani boyutu (28):", u32(28), "sayfa")
print("sema cerezi (40):", u32(40))
print("metin kodlamasi (56):", u32(56))
print("dosya boyutu:", len(veri), "=", len(veri) // sayfa,
      "sayfa")
print()
TUR = {0x0D: "yaprak tablo", 0x05: "iç tablo",
       0x0A: "yaprak indeks", 0x02: "iç indeks"}


def baslik_konumu(no):
    """Sayfa başlığının bayt konumu (1. sayfada 100 bayt sonra)."""
    return (no - 1) * sayfa + (100 if no == 1 else 0)


def cocuklar(no):
    """İç sayfanın çocukları: ilk hücre + en sağ işaretçi."""
    bas = baslik_konumu(no)
    sag = u32(bas + 8)
    hucre = u16(bas + 12)
    sol = u32((no - 1) * sayfa + hucre)
    return [sol, sag]


for no in range(1, len(veri) // sayfa + 1):
    bas = baslik_konumu(no)
    tur = TUR.get(veri[bas], "?")
    ek = ""
    if tur.startswith("iç"):
        ek = "  cocuklar=%s" % cocuklar(no)
    print("sayfa %d: %-13s hucre=%d%s"
          % (no, tur, u16(bas + 3), ek))
