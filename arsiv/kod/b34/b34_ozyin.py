# b34_ozyin.py: özyinelemeli CTE: Fibonacci, erişilebilirlik, ağaç
import sqlite3
import sys

c = sqlite3.connect(sys.argv[1])

FIB = """
WITH RECURSIVE f(n, a, b) AS (
  SELECT 1, 0, 1
  UNION ALL
  SELECT n + 1, b, a + b FROM f WHERE n < 93)
SELECT n, b, typeof(b) FROM f WHERE n IN (2, 10, 92, 93)
"""
print("Fibonacci (n, F(n), tür):")
for satir in c.execute(FIB):
    print("  ", satir)

ERISIM = """
WITH RECURSIVE r(id) AS (
  SELECT ?
  UNION
  SELECT b.hedef FROM r JOIN baglanti b ON b.kaynak = r.id)
SELECT COUNT(*) FROM r
"""
print(
    "Ana Üs'ten erişilebilen üs:",
    c.execute(ERISIM, (1,)).fetchone()[0],
)
print(
    "Kapalı Üs'ten erişilebilen:",
    c.execute(ERISIM, (12,)).fetchone()[0],
)

MESAFE = """
WITH RECURSIVE r(id, d) AS (
  SELECT ?, 0
  UNION
  SELECT b.hedef, r.d + 1 FROM r JOIN baglanti b ON b.kaynak = r.id
  WHERE r.d < 10)
SELECT id, MIN(d) AS adim FROM r GROUP BY id ORDER BY adim, id LIMIT 4
"""
print("Ana Üs'ten en az adım (ilk 4):")
for satir in c.execute(MESAFE, (1,)):
    print("  ", satir)

AGAC = """
WITH RECURSIVE alt(kok, id) AS (
  SELECT id, id FROM ekipman
  UNION ALL
  SELECT alt.kok, e.id FROM alt JOIN ekipman e ON e.ust_id = alt.id)
SELECT e.ad, ROUND(SUM(b.maliyet_tl), 2) AS toplam
FROM alt JOIN ekipman e ON e.id = alt.kok
JOIN bakim b ON b.ekipman_id = alt.id
GROUP BY e.id ORDER BY toplam DESC LIMIT 4
"""
print("Alt ağaç toplam bakım maliyeti (TL, ilk 4):")
for satir in c.execute(AGAC):
    print("  ", satir)
