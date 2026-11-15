# b34_upsert.py: UPSERT ile günlük özet, toplama ve yerine koyma
import sqlite3
import sys

kaynak = sqlite3.connect(sys.argv[1])
c = sqlite3.connect(":memory:")
c.execute(
    "CREATE TABLE ozet (ucak_id INTEGER, gun TEXT, "
    "ucus INTEGER, PRIMARY KEY (ucak_id, gun))"
)
parti = kaynak.execute(
    "SELECT g.ucak_id, DATE(x.kalkis), COUNT(*) FROM ucus x "
    "JOIN gorev g ON g.id = x.gorev_id "
    "WHERE g.ucak_id IN (1, 2, 3) AND x.kalkis < '2026-03-08' "
    "GROUP BY g.ucak_id, DATE(x.kalkis)"
).fetchall()
print("parti satır sayısı:", len(parti))

TOPLA = """INSERT INTO ozet VALUES (?, ?, ?)
  ON CONFLICT (ucak_id, gun) DO UPDATE
  SET ucus = ucus + excluded.ucus"""
YERINE = """INSERT INTO ozet VALUES (?, ?, ?)
  ON CONFLICT (ucak_id, gun) DO UPDATE
  SET ucus = excluded.ucus"""
for ad, sql in [("toplama", TOPLA), ("yerine koyma", YERINE)]:
    c.execute("DELETE FROM ozet")
    c.executemany(sql, parti)
    c.executemany(sql, parti)  # aynı partiyi ikinci kez yükle
    toplam = c.execute("SELECT SUM(ucus) FROM ozet").fetchone()[0]
    print("%-13s iki yükleme sonrası toplam uçuş = %s" % (ad, toplam))
print("kaynakta gerçek uçuş sayısı =", sum(p[2] for p in parti))
