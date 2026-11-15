# b34_ornek3.py: gerilim çöküşü aralıkları (gaps-and-islands)
import sqlite3
import sys

ESIK = 23.0
SQL = """
WITH ort AS (
  SELECT zaman_sn,
    AVG(gerilim_v) OVER (ORDER BY zaman_sn
      ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING) AS m,
    ROW_NUMBER() OVER (ORDER BY zaman_sn) AS sira
  FROM telemetri WHERE ucus_id = ?
),
dusuk AS (
  SELECT zaman_sn, sira,
    sira - ROW_NUMBER() OVER (ORDER BY sira) AS grup
  FROM ort WHERE m < ?
)
SELECT MIN(zaman_sn), MAX(zaman_sn), COUNT(*)
FROM dusuk GROUP BY grup ORDER BY MIN(zaman_sn)
"""


def kucuk_dizi():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE t (sira INTEGER)")
    c.executemany(
        "INSERT INTO t VALUES (?)",
        [(s,) for s in (2, 3, 4, 7, 8, 11)],
    )
    sql = """SELECT sira, sira - ROW_NUMBER() OVER (ORDER BY sira)
             FROM t"""
    print("sira, grup:", c.execute(sql).fetchall())
    c.close()


def aralik_bul(c, ucus):
    return c.execute(SQL, (ucus, ESIK)).fetchall()


def python_ile(c, ucus):
    """Aynı sonucu düz Python ile bağımsız hesapla."""
    satir = c.execute(
        "SELECT zaman_sn, gerilim_v FROM telemetri "
        "WHERE ucus_id = ? ORDER BY zaman_sn",
        (ucus,),
    ).fetchall()
    g = [v for _, v in satir]
    m = []
    for i in range(len(g)):
        pen = g[max(0, i - 2) : i + 3]  # kenarda pencere kısalır
        m.append(sum(pen) / len(pen))
    aralik, acik = [], None
    for i, (zs, _) in enumerate(satir):
        if m[i] < ESIK:
            if acik is None:
                acik = [zs, zs, 0]
            acik[1] = zs
            acik[2] += 1
        elif acik is not None:
            aralik.append(tuple(acik))
            acik = None
    if acik is not None:
        aralik.append(tuple(acik))
    return aralik


if __name__ == "__main__":
    kucuk_dizi()
    c = sqlite3.connect(sys.argv[1])
    adaylar = [
        r[0]
        for r in c.execute(
            "SELECT DISTINCT ucus_id FROM telemetri "
            "WHERE gerilim_v < 23.5 ORDER BY ucus_id LIMIT 200"
        )
    ]
    bulunan = []
    for u in adaylar:
        aralik = aralik_bul(c, u)
        if aralik:
            bulunan.append(u)
            print("uçuş %d:" % u)
            for bas, son, n in aralik:
                print("  %5d .. %5d sn, %d örnek" % (bas, son, n))
            print("  Python ile aynı mı:", python_ile(c, u) == aralik)
        if len(bulunan) == 2:
            break
