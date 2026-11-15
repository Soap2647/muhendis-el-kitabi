# b34_pencere.py: pencere fonksiyonları, sıralama ve zaman serisi
import sqlite3
import sys

c = sqlite3.connect(sys.argv[1])
print("sıralama farkı (küçük örnek: 10, 10, 8):")
for satir in c.execute("""
  SELECT v, ROW_NUMBER() OVER (ORDER BY v DESC),
         RANK() OVER (ORDER BY v DESC),
         DENSE_RANK() OVER (ORDER BY v DESC)
  FROM (SELECT 10 AS v UNION ALL SELECT 10 UNION ALL SELECT 8)"""):
    print("  ", satir)

print("uçak toplam uçuş dakikası, ilk 5 (RANK / DENSE_RANK):")
for satir in c.execute("""
  SELECT u, toplam, RANK() OVER (ORDER BY toplam DESC),
         DENSE_RANK() OVER (ORDER BY toplam DESC)
  FROM (SELECT g.ucak_id AS u, SUM(x.sure_dk) AS toplam
        FROM ucus x JOIN gorev g ON g.id = x.gorev_id
        WHERE g.ucak_id IS NOT NULL GROUP BY g.ucak_id)
  ORDER BY 3 LIMIT 5"""):
    print("  ", satir)

print("kümülatif dakika, uçak 1 ve 2 (PARTITION BY):")
for satir in c.execute("""
  SELECT g.ucak_id, x.kalkis, x.sure_dk,
    SUM(x.sure_dk) OVER (PARTITION BY g.ucak_id ORDER BY x.kalkis
      ROWS UNBOUNDED PRECEDING) AS kumulatif
  FROM ucus x JOIN gorev g ON g.id = x.gorev_id
  WHERE g.ucak_id IN (1, 2) ORDER BY g.ucak_id, x.kalkis LIMIT 4"""):
    print("  ", satir)

print("telemetri, LAG ile örnekler arası fark (uçuş 2, ilk 4):")
for satir in c.execute("""
  SELECT zaman_sn, gerilim_v,
    ROUND(gerilim_v - LAG(gerilim_v) OVER (ORDER BY zaman_sn), 2)
  FROM telemetri WHERE ucus_id = 2 ORDER BY zaman_sn LIMIT 4"""):
    print("  ", satir)
