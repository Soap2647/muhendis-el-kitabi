# b34_ornek1.py: her uçağın son uçuşu, iki yöntem
import sqlite3
import sys

SQL_PENCERE = """
WITH s AS (
  SELECT g.ucak_id AS ucak, x.id AS ucus, x.kalkis,
    ROW_NUMBER() OVER (PARTITION BY g.ucak_id
                       ORDER BY x.kalkis DESC, x.id DESC) AS rn
  FROM ucus x JOIN gorev g ON g.id = x.gorev_id
  WHERE g.ucak_id IS NOT NULL)
SELECT ucak, ucus, kalkis FROM s WHERE rn = 1 ORDER BY ucak
"""

SQL_ALT = """
SELECT g.ucak_id, x.id, x.kalkis
FROM ucus x JOIN gorev g ON g.id = x.gorev_id
WHERE g.ucak_id IS NOT NULL
  AND x.id = (SELECT x2.id FROM ucus x2
              JOIN gorev g2 ON g2.id = x2.gorev_id
              WHERE g2.ucak_id = g.ucak_id
              ORDER BY x2.kalkis DESC, x2.id DESC
              LIMIT 1)
ORDER BY g.ucak_id
"""


def iz():
    c = sqlite3.connect(":memory:")
    c.executescript("""
    CREATE TABLE gorev (id INTEGER PRIMARY KEY, ucak_id INTEGER);
    CREATE TABLE ucus (id INTEGER PRIMARY KEY, gorev_id INTEGER,
                       kalkis TEXT);
    INSERT INTO gorev VALUES (1,7),(2,7),(3,8),(4,8),(5,7);
    INSERT INTO ucus VALUES (10,1,'2026-03-01 10:00'),
      (11,2,'2026-03-05 09:00'),(12,3,'2026-02-20 08:00'),
      (13,4,'2026-03-05 09:00'),(14,5,'2026-03-02 12:00'),
      (15,2,'2026-03-05 09:00');
    """)
    print("küçük küme, pencere:")
    for satir in c.execute(SQL_PENCERE):
        print("  ", satir)
    print("küçük küme, alt sorgu:")
    for satir in c.execute(SQL_ALT):
        print("  ", satir)
    c.close()


if __name__ == "__main__":
    iz()
    c = sqlite3.connect(sys.argv[1])
    a = c.execute(SQL_PENCERE).fetchall()
    b = c.execute(SQL_ALT).fetchall()
    print("veri: uçak sayısı =", len(a), ", eşit =", a == b)
    print("ilk üç satır:")
    for satir in a[:3]:
        print("  ", satir)
